import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.arena.models import (
    AIReview,
    ArenaUser,
    AssessmentContainer,
    AssessmentContainerPart,
    AttemptSession,
    EvaluationRun,
    ExerciseDefinition,
    Submission,
    SubmissionSnapshot,
    UserExerciseProgress,
)
from apps.practice.application.registry import OBJECTIVE_SNIPPET_TEMPLATES, get_family_spec, resolve_surface_key
from apps.practice.domain import (
    evaluate_component_behavior_submission,
    build_objective_option_catalog,
    evaluate_http_contract_submission,
    evaluate_restricted_code_submission,
    evaluate_objective_selection,
    format_execution_results_console,
    normalize_objective_template_key,
    normalize_restricted_template_key,
    normalize_text,
    outputs_match_robust,
    render_blank_template,
)
from apps.progress.application.services import apply_submission_progress, build_exercise_progress_payload, build_user_progress_summary
from apps.review.application.services import schedule_submission_feedback


DEFAULT_EXERCISE_TYPE_SLUG = 'drill-de-implementacao'
DEFAULT_EXERCISE_TYPE_LABEL = 'Drill de implementação'
DEFAULT_OBJECTIVE_ITEM_XP = 35
DEFAULT_RESTRICTED_CODE_XP = 40
DEFAULT_CONTRACT_BEHAVIOR_XP = 40


def _normalize_workspace_file_entry(file_name: str, raw_entry: object, *, default_read_only: bool = False) -> dict:
    if isinstance(raw_entry, dict):
        return {
            'path': str(raw_entry.get('path') or file_name),
            'content': str(raw_entry.get('content') or ''),
            'read_only': bool(raw_entry.get('read_only', default_read_only)),
            'label': str(raw_entry.get('label') or file_name),
            'role': str(raw_entry.get('role') or ''),
        }
    return {
        'path': str(file_name),
        'content': str(raw_entry or ''),
        'read_only': bool(default_read_only),
        'label': str(file_name),
        'role': '',
    }


def _normalize_workspace_files(raw_files: object, *, readonly_files: list[str] | None = None) -> dict[str, dict]:
    normalized: dict[str, dict] = {}
    readonly_set = {str(path) for path in (readonly_files or [])}
    if not isinstance(raw_files, dict):
        return normalized

    for file_name, raw_entry in raw_files.items():
        file_key = str(file_name)
        normalized[file_key] = _normalize_workspace_file_entry(
            file_key,
            raw_entry,
            default_read_only=file_key in readonly_set,
        )
    return normalized


def _serialize_workspace_files_for_runner(files: dict[str, dict] | None) -> dict[str, str]:
    serialized: dict[str, str] = {}
    for file_name, descriptor in (files or {}).items():
        if isinstance(descriptor, dict):
            serialized[str(file_name)] = str(descriptor.get('content') or '')
        else:
            serialized[str(file_name)] = str(descriptor or '')
    return serialized


def _deep_merge_dicts(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _coerce_string_list(values: object) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        cleaned = values.strip()
        return [cleaned] if cleaned else []
    if isinstance(values, (list, tuple, set)):
        return [str(value).strip() for value in values if str(value).strip()]
    return [str(values).strip()]


def _build_code_lab_workspace_spec(exercise: ExerciseDefinition) -> dict:
    family_spec = get_family_spec(exercise.family_key)
    evaluation_plan = exercise.evaluation_plan or {}
    base_workspace_spec = dict(exercise.workspace_spec or {})
    language = str(
        base_workspace_spec.get('language')
        or evaluation_plan.get('language')
        or exercise.language
        or 'python'
    )
    default_entrypoint = 'main.py' if language == 'python' else f'main.{language}'
    entrypoint = str(base_workspace_spec.get('entrypoint') or default_entrypoint)
    workspace_kind = str(base_workspace_spec.get('workspace_kind') or 'single_file')
    readonly_files = [str(path) for path in (base_workspace_spec.get('readonly_files') or evaluation_plan.get('readonly_files') or [])]
    starter_files = _normalize_workspace_files(base_workspace_spec.get('files'), readonly_files=readonly_files)

    if not starter_files:
        starter_files = {
            entrypoint: _normalize_workspace_file_entry(
                entrypoint,
                {
                    'content': exercise.starter_code,
                    'label': entrypoint,
                    'role': 'entrypoint',
                },
            )
        }
    elif entrypoint not in starter_files:
        starter_files[entrypoint] = _normalize_workspace_file_entry(
            entrypoint,
            {
                'content': exercise.starter_code,
                'label': entrypoint,
                'role': 'entrypoint',
            },
        )

    if workspace_kind == 'multifile':
        starter_files[entrypoint]['role'] = starter_files[entrypoint].get('role') or 'entrypoint'

    file_order = [str(path) for path in (base_workspace_spec.get('file_order') or starter_files.keys())]
    active_file = str(base_workspace_spec.get('active_file') or entrypoint)

    return {
        **base_workspace_spec,
        'surface_key': base_workspace_spec.get('surface_key') or resolve_surface_key(exercise),
        'workspace_kind': workspace_kind,
        'language': language,
        'entrypoint': entrypoint,
        'active_file': active_file,
        'readonly_files': readonly_files,
        'file_order': file_order,
        'files': starter_files,
        'runner_supports_files': True,
    }


def _build_passed_once_reward_payload(exercise: ExerciseDefinition) -> dict:
    if exercise.family_key == ExerciseDefinition.FAMILY_RESTRICTED_CODE:
        return {
            'milestone_key': 'passed_once',
            'label': 'Correção validada',
            'xp_awarded': DEFAULT_RESTRICTED_CODE_XP,
        }
    if exercise.family_key == ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB:
        return {
            'milestone_key': 'passed_once',
            'label': 'Contrato validado',
            'xp_awarded': DEFAULT_CONTRACT_BEHAVIOR_XP,
        }
    return {
        'milestone_key': 'passed_once',
        'label': 'Primeira aprovação',
        'xp_awarded': DEFAULT_OBJECTIVE_ITEM_XP,
    }


def _resolve_objective_choice_mode(template_key: str, evaluation_plan: dict, correct_options: list[object], workspace_spec: dict | None = None) -> str:
    workspace_spec = workspace_spec or {}
    choice_mode = str(
        workspace_spec.get('choice_mode')
        or evaluation_plan.get('choice_mode')
        or evaluation_plan.get('selection_mode')
        or ('multiple' if template_key == 'multi-select' or len(correct_options) > 1 else 'single')
    ).strip().lower()
    if choice_mode not in {'single', 'multiple'}:
        return 'single'
    return choice_mode


def _build_objective_template_meta(
    exercise: ExerciseDefinition,
    *,
    template_key: str,
    choice_mode: str,
    option_catalog: list[dict],
    snippet_block: dict | None,
) -> dict:
    template_titles = {
        'single-choice': 'Escolha objetiva',
        'multi-select': 'Seleção de afirmações',
        'snippet-read-only': 'Leitura de snippet',
        'compile-runtime-output': 'Compile / Runtime / Output',
        'behavior-classification': 'Behavior classification',
        'output-prediction': 'Previsão de saída',
    }
    analysis_steps = {
        'single-choice': [
            'Leia o estímulo até localizar a regra que decide a alternativa correta.',
            'Compare a alternativa escolhida com os distratores mais plausíveis.',
        ],
        'multi-select': [
            'Avalie cada afirmação separadamente antes de concluir o conjunto final.',
            'Procure omissões e falsos positivos, não só a primeira impressão.',
        ],
        'snippet-read-only': [
            'Leia o snippet como evidência, sem reescrever mentalmente o código.',
            'Valide escopo, tipos e fluxo antes de decidir.',
        ],
        'compile-runtime-output': [
            'Decida primeiro se o código compila.',
            'Se compilar, separe falha em runtime de saída observável.',
            'Só preencha a saída quando o veredito correto for output.',
        ],
        'behavior-classification': [
            'Observe o comportamento real do trecho, não só a intenção aparente.',
            'Considere dispatch, efeitos colaterais e ordem de execução.',
        ],
        'output-prediction': [
            'Simule a execução linha a linha antes de escolher a saída.',
            'Confirme ordem, espaçamento e valores finais do output.',
        ],
    }
    response_shape = {
        'single-choice': 'single_choice',
        'multi-select': 'multi_select',
        'snippet-read-only': 'single_choice',
        'compile-runtime-output': 'classifier_with_optional_output',
        'behavior-classification': 'single_choice',
        'output-prediction': 'single_choice',
    }
    evaluation_plan = exercise.evaluation_plan or {}
    expected_output_text = normalize_text(
        evaluation_plan.get('expected_output_text')
        or evaluation_plan.get('expected_output')
        or evaluation_plan.get('correct_output_text')
        or evaluation_plan.get('output_text')
        or ''
    )
    requires_output_text = template_key == 'compile-runtime-output' and bool(expected_output_text)

    return {
        'key': template_key,
        'title': template_titles.get(template_key, 'Template objetivo'),
        'stimulus_kind': 'snippet' if snippet_block is not None else 'statement',
        'choice_mode': choice_mode,
        'response_shape': response_shape.get(template_key, 'single_choice'),
        'requires_output_text': requires_output_text,
        'response_input_label': 'Saída esperada' if requires_output_text else '',
        'response_input_placeholder': 'INSIRA A SAÍDA ESPERADA...' if requires_output_text else '',
        'analysis_steps': analysis_steps.get(template_key, []),
        'verdict_options': [
            {
                'key': option['canonical_key'],
                'label': option['label'],
            }
            for option in option_catalog
        ],
    }


def _build_objective_workspace_spec(exercise: ExerciseDefinition) -> dict:
    family_spec = get_family_spec(exercise.family_key)
    evaluation_plan = exercise.evaluation_plan or {}
    base_workspace_spec = dict(exercise.workspace_spec or {})
    option_catalog = build_objective_option_catalog(evaluation_plan, exercise.content_blocks or [])
    correct_options = evaluation_plan.get('correct_options') or evaluation_plan.get('correct_answers') or evaluation_plan.get('correct_answer') or evaluation_plan.get('answer_key') or []
    if not isinstance(correct_options, (list, tuple, set)):
        correct_options = [correct_options]
    snippet_block = _extract_objective_snippet_block(exercise)
    snippet_code = base_workspace_spec.get('snippet')
    if snippet_block is None and snippet_code not in (None, ''):
        snippet_block = {
            'kind': 'snippet',
            'title': base_workspace_spec.get('snippet_title') or base_workspace_spec.get('snippet_filename') or 'Trecho de código',
            'language': base_workspace_spec.get('snippet_language') or exercise.language or 'python',
            'read_only': bool(base_workspace_spec.get('snippet_read_only', True)),
            'code': str(snippet_code),
        }

    template_key = normalize_objective_template_key(
        base_workspace_spec.get('template')
        or evaluation_plan.get('template')
        or evaluation_plan.get('kind')
        or 'single-choice'
    )
    choice_mode = _resolve_objective_choice_mode(template_key, evaluation_plan, list(correct_options), base_workspace_spec)
    template_meta = _build_objective_template_meta(
        exercise,
        template_key=template_key,
        choice_mode=choice_mode,
        option_catalog=option_catalog,
        snippet_block=snippet_block,
    )

    return {
        **base_workspace_spec,
        'surface_key': base_workspace_spec.get('surface_key') or family_spec.default_surface_key,
        'workspace_kind': base_workspace_spec.get('workspace_kind') or 'objective_form',
        'stimulus_kind': base_workspace_spec.get('stimulus_kind') or ('snippet' if snippet_block is not None else 'statement'),
        'choice_mode': choice_mode,
        'template': template_key,
        'template_meta': template_meta,
        'snippet': base_workspace_spec.get('snippet', snippet_block['code'] if snippet_block is not None else ''),
        'snippet_language': base_workspace_spec.get('snippet_language', snippet_block['language'] if snippet_block is not None else exercise.language),
        'snippet_read_only': base_workspace_spec.get('snippet_read_only', bool(snippet_block)),
        'options': base_workspace_spec.get('options') or option_catalog,
        'selected_options': list(base_workspace_spec.get('selected_options') or []),
        'response_text': str(base_workspace_spec.get('response_text') or ''),
        'allow_multiple': bool(base_workspace_spec.get('allow_multiple')) or choice_mode == 'multiple',
    }


def _extract_objective_snippet_block(exercise: ExerciseDefinition) -> dict | None:
    evaluation_plan = exercise.evaluation_plan or {}
    template = normalize_objective_template_key(evaluation_plan.get('template') or evaluation_plan.get('kind') or '')
    snippet = (
        evaluation_plan.get('snippet')
        or evaluation_plan.get('snippet_code')
        or evaluation_plan.get('read_only_snippet')
        or evaluation_plan.get('code')
    )
    if not snippet and template not in OBJECTIVE_SNIPPET_TEMPLATES:
        return None
    if not snippet:
        return None

    snippet_language = (
        evaluation_plan.get('snippet_language')
        or evaluation_plan.get('language')
        or exercise.language
        or 'python'
    )
    return {
        'kind': 'snippet',
        'title': evaluation_plan.get('snippet_title') or 'Trecho de código',
        'language': snippet_language,
        'read_only': True,
        'code': str(snippet),
    }


def _build_restricted_template_meta(
    exercise: ExerciseDefinition,
    *,
    template_key: str,
    blank_count: int,
) -> dict:
    titles = {
        'fix-the-snippet': 'Correção localizada',
        'fill-in-the-blanks': 'Preenchimento guiado',
    }
    analysis_steps = {
        'fix-the-snippet': [
            'Leia o snippet original para identificar o bug central.',
            'Faça a menor correção que satisfaça os critérios estruturais.',
            'Confirme que a versão editada remove o erro sem reescrever tudo.',
        ],
        'fill-in-the-blanks': [
            'Entenda o papel de cada lacuna antes de preencher.',
            'Valide sintaxe, nomes e ordem das expressões inseridas.',
            'Revise o trecho completo depois de preencher todas as lacunas.',
        ],
    }
    return {
        'key': template_key,
        'title': titles.get(template_key, 'Restricted code'),
        'analysis_steps': analysis_steps.get(template_key, []),
        'response_shape': 'editable_code',
        'blank_count': blank_count,
    }


def _sanitize_restricted_blanks(raw_blanks: list[dict] | None) -> list[dict]:
    sanitized: list[dict] = []
    for index, blank in enumerate(raw_blanks or [], start=1):
        if not isinstance(blank, dict):
            continue
        sanitized.append(
            {
                'key': str(blank.get('key') or blank.get('id') or f'blank-{index}'),
                'label': str(blank.get('label') or blank.get('placeholder') or f'Lacuna {index}'),
                'placeholder': str(blank.get('placeholder') or ''),
                'hint': str(blank.get('hint') or ''),
            }
        )
    return sanitized


def _build_restricted_workspace_spec(exercise: ExerciseDefinition) -> dict:
    family_spec = get_family_spec(exercise.family_key)
    evaluation_plan = exercise.evaluation_plan or {}
    base_workspace_spec = dict(exercise.workspace_spec or {})
    template_key = normalize_restricted_template_key(
        base_workspace_spec.get('template')
        or evaluation_plan.get('template')
        or evaluation_plan.get('kind')
        or 'fix-the-snippet'
    )
    original_code = str(
        base_workspace_spec.get('original_code')
        or base_workspace_spec.get('broken_code')
        or evaluation_plan.get('original_code')
        or evaluation_plan.get('broken_code')
        or exercise.starter_code
        or ''
    )
    editable_code = str(
        base_workspace_spec.get('editable_code')
        or base_workspace_spec.get('starter_code')
        or evaluation_plan.get('editable_code')
        or evaluation_plan.get('starter_code')
        or original_code
    )
    blank_template = str(
        base_workspace_spec.get('blank_template')
        or evaluation_plan.get('blank_template')
        or evaluation_plan.get('template_source')
        or editable_code
    )
    if template_key == 'fill-in-the-blanks' and not editable_code:
        editable_code = render_blank_template(blank_template, {})
    language = str(
        base_workspace_spec.get('language')
        or evaluation_plan.get('language')
        or exercise.language
        or 'python'
    )
    sanitized_blanks = _sanitize_restricted_blanks(
        base_workspace_spec.get('blanks') or evaluation_plan.get('blanks') or []
    )
    template_meta = _build_restricted_template_meta(
        exercise,
        template_key=template_key,
        blank_count=len(sanitized_blanks),
    )

    return {
        **base_workspace_spec,
        'surface_key': (
            base_workspace_spec.get('surface_key')
            or ('restricted_fill_blanks' if template_key == 'fill-in-the-blanks' else family_spec.default_surface_key)
        ),
        'workspace_kind': base_workspace_spec.get('workspace_kind') or 'restricted_code',
        'template': template_key,
        'template_meta': template_meta,
        'language': language,
        'original_code': original_code,
        'editable_code': editable_code,
        'blank_template': blank_template,
        'blanks': sanitized_blanks,
        'instructions': str(
            base_workspace_spec.get('instructions')
            or evaluation_plan.get('instructions')
            or exercise.pedagogical_brief
            or ''
        ),
        'validation_kind': str(evaluation_plan.get('mechanism') or 'structural_checker'),
        'locked_regions': list(base_workspace_spec.get('locked_regions') or evaluation_plan.get('locked_regions') or []),
        'editable_regions': list(base_workspace_spec.get('editable_regions') or evaluation_plan.get('editable_regions') or []),
    }


def _build_contract_behavior_workspace_spec(exercise: ExerciseDefinition) -> dict:
    family_spec = get_family_spec(exercise.family_key)
    base_workspace_spec = dict(exercise.workspace_spec or {})
    evaluation_plan = dict(exercise.evaluation_plan or {})
    template_key = normalize_objective_template_key(
        base_workspace_spec.get('template')
        or evaluation_plan.get('template')
        or evaluation_plan.get('kind')
        or 'http-contract'
    )

    if template_key in {'component-behavior', 'ui-behavior'}:
        entrypoint = str(base_workspace_spec.get('entrypoint') or 'ComponentUnderTest.vue')
        starter_files = _normalize_workspace_files(
            base_workspace_spec.get('files')
            or {
                entrypoint: {
                    'content': base_workspace_spec.get('source_code') or exercise.starter_code or '',
                    'label': 'ComponentUnderTest.vue',
                    'role': 'entrypoint',
                }
            }
        )
        if entrypoint not in starter_files:
            starter_files[entrypoint] = _normalize_workspace_file_entry(
                entrypoint,
                {
                    'content': exercise.starter_code or '',
                    'label': entrypoint,
                    'role': 'entrypoint',
                },
            )
        component_contract = {
            'name': str(base_workspace_spec.get('component_name') or evaluation_plan.get('component_name') or exercise.title),
            'expected_props': _coerce_string_list(base_workspace_spec.get('expected_props') or evaluation_plan.get('required_props')),
            'expected_state': _coerce_string_list(base_workspace_spec.get('expected_state') or evaluation_plan.get('required_state')),
            'expected_events': _coerce_string_list(base_workspace_spec.get('expected_events') or evaluation_plan.get('required_events')),
            'expected_render': _coerce_string_list(base_workspace_spec.get('expected_render') or evaluation_plan.get('required_render')),
            'expected_dom': _coerce_string_list(base_workspace_spec.get('expected_dom') or evaluation_plan.get('required_dom')),
            'forbidden_tokens': _coerce_string_list(base_workspace_spec.get('forbidden_tokens') or evaluation_plan.get('forbidden_tokens')),
            'expected_dom_snapshot': str(base_workspace_spec.get('expected_dom_snapshot') or evaluation_plan.get('expected_dom_snapshot') or ''),
        }
        template_meta = {
            'key': 'component-behavior',
            'title': 'Comportamento de componente',
            'response_shape': 'component_behavior_observation',
            'analysis_steps': [
                'Leia primeiro o contrato visual e os estados esperados.',
                'Compare props, estado, eventos e DOM antes de concluir.',
                'Use a evidência observada para separar divergência de implementação e divergência de comportamento.',
            ],
            'validation_axes': [
                'props',
                'state',
                'events',
                'render',
                'dom',
                'forbidden_tokens',
            ],
        }
        return {
            **base_workspace_spec,
            'surface_key': 'component_behavior_lab',
            'workspace_kind': 'component_behavior',
            'template': template_key,
            'language': str(base_workspace_spec.get('language') or exercise.language or 'vue'),
            'entrypoint': entrypoint,
            'active_file': str(base_workspace_spec.get('active_file') or entrypoint),
            'file_order': list(base_workspace_spec.get('file_order') or starter_files.keys()),
            'files': starter_files,
            'template_meta': _deep_merge_dicts(
                template_meta,
                base_workspace_spec.get('template_meta') if isinstance(base_workspace_spec.get('template_meta'), dict) else {},
            ),
            'component_contract': component_contract,
            'instructions': str(
                base_workspace_spec.get('instructions')
                or evaluation_plan.get('instructions')
                or exercise.pedagogical_brief
                or ''
            ),
        }

    default_contract = {
        'request': {
            'method': 'GET',
            'path': '/health',
            'headers': {},
            'body': None,
        },
        'response': {
            'status_code': 200,
            'headers': {},
            'body': None,
            'body_schema': None,
        },
    }
    contract = _deep_merge_dicts(
        default_contract,
        evaluation_plan.get('contract') if isinstance(evaluation_plan.get('contract'), dict) else {},
    )
    contract = _deep_merge_dicts(
        contract,
        base_workspace_spec.get('contract') if isinstance(base_workspace_spec.get('contract'), dict) else {},
    )
    template_meta = {
        'key': 'http-contract',
        'title': 'Contrato HTTP',
        'response_shape': 'http_contract_observation',
        'analysis_steps': [
            'Valide método e path antes de discutir a resposta.',
            'Compare status, headers e body com o contrato esperado.',
            'Use o schema para separar formato inválido de conteúdo incorreto.',
        ],
        'validation_axes': [
            'request_method',
            'request_path',
            'request_headers',
            'request_body',
            'response_status',
            'response_headers',
            'response_body',
            'response_schema',
        ],
    }
    return {
        **base_workspace_spec,
        'surface_key': base_workspace_spec.get('surface_key') or family_spec.default_surface_key,
        'workspace_kind': base_workspace_spec.get('workspace_kind') or 'http_contract',
        'template': base_workspace_spec.get('template') or evaluation_plan.get('template') or 'http-contract',
        'template_meta': _deep_merge_dicts(
            template_meta,
            base_workspace_spec.get('template_meta') if isinstance(base_workspace_spec.get('template_meta'), dict) else {},
        ),
        'contract': contract,
        'instructions': str(
            base_workspace_spec.get('instructions')
            or evaluation_plan.get('instructions')
            or exercise.pedagogical_brief
            or ''
        ),
        'request_examples': list(base_workspace_spec.get('request_examples') or evaluation_plan.get('request_examples') or []),
        'response_examples': list(base_workspace_spec.get('response_examples') or evaluation_plan.get('response_examples') or []),
    }


def build_default_content_blocks(exercise: ExerciseDefinition) -> list[dict]:
    if exercise.content_blocks:
        return list(exercise.content_blocks)
    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        evaluation_plan = exercise.evaluation_plan or {}
        option_catalog = build_objective_option_catalog(evaluation_plan, exercise.content_blocks or [])
        correct_options = evaluation_plan.get('correct_options') or evaluation_plan.get('correct_answers') or evaluation_plan.get('correct_answer') or evaluation_plan.get('answer_key') or []
        if not isinstance(correct_options, (list, tuple, set)):
            correct_options = [correct_options]
        template_key = normalize_objective_template_key(evaluation_plan.get('template') or evaluation_plan.get('kind') or 'single-choice')
        choice_mode = _resolve_objective_choice_mode(template_key, evaluation_plan, list(correct_options))
        blocks = [
            {
                'kind': 'statement',
                'title': exercise.title,
                'content': exercise.statement,
            }
        ]
        snippet_block = _extract_objective_snippet_block(exercise)
        if snippet_block is not None:
            blocks.append(snippet_block)
        if option_catalog:
            blocks.append(
                {
                    'kind': 'objective-options',
                    'choice_mode': choice_mode,
                    'options': option_catalog,
                }
            )
        return blocks
    if exercise.family_key == ExerciseDefinition.FAMILY_RESTRICTED_CODE:
        workspace_spec = _build_restricted_workspace_spec(exercise)
        blocks: list[dict] = [
            {
                'kind': 'statement',
                'title': exercise.title,
                'content': exercise.statement,
            }
        ]
        if workspace_spec.get('original_code'):
            blocks.append(
                {
                    'kind': 'snippet',
                    'title': 'Snippet original',
                    'language': workspace_spec.get('language') or exercise.language,
                    'read_only': True,
                    'code': workspace_spec.get('original_code'),
                }
            )
        if workspace_spec.get('instructions'):
            blocks.append(
                {
                    'kind': 'instructions',
                    'title': 'Orientações',
                    'content': workspace_spec.get('instructions'),
                }
            )
        return blocks
    if exercise.family_key == ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB:
        workspace_spec = _build_contract_behavior_workspace_spec(exercise)
        if workspace_spec.get('template') in {'component-behavior', 'ui-behavior'}:
            component_contract = (
                workspace_spec.get('component_contract')
                if isinstance(workspace_spec.get('component_contract'), dict)
                else {}
            )
            return [
                {
                    'kind': 'statement',
                    'title': exercise.title,
                    'content': exercise.statement,
                },
                {
                    'kind': 'component-contract',
                    'title': 'Contrato do componente',
                    'component_contract': component_contract,
                    'instructions': workspace_spec.get('instructions') or '',
                },
            ]
        contract = workspace_spec.get('contract') if isinstance(workspace_spec.get('contract'), dict) else {}
        request = contract.get('request') if isinstance(contract.get('request'), dict) else {}
        response = contract.get('response') if isinstance(contract.get('response'), dict) else {}
        return [
            {
                'kind': 'statement',
                'title': exercise.title,
                'content': exercise.statement,
            },
            {
                'kind': 'http-contract',
                'title': 'Contrato esperado',
                'request': request,
                'response': response,
                'instructions': workspace_spec.get('instructions') or '',
            },
        ]
    return [
        {
            'kind': 'statement',
            'title': exercise.title,
            'content': exercise.statement,
        }
    ]


def build_default_workspace_spec(exercise: ExerciseDefinition) -> dict:
    if exercise.workspace_spec and exercise.family_key not in {
        ExerciseDefinition.FAMILY_OBJECTIVE_ITEM,
        ExerciseDefinition.FAMILY_RESTRICTED_CODE,
        ExerciseDefinition.FAMILY_CODE_LAB,
        ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB,
    }:
        return dict(exercise.workspace_spec)

    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        return _build_objective_workspace_spec(exercise)

    if exercise.family_key == ExerciseDefinition.FAMILY_RESTRICTED_CODE:
        return _build_restricted_workspace_spec(exercise)

    if exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        return _build_code_lab_workspace_spec(exercise)

    if exercise.family_key == ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB:
        return _build_contract_behavior_workspace_spec(exercise)

    family_spec = get_family_spec(exercise.family_key)
    return {
        'surface_key': family_spec.default_surface_key,
        'workspace_kind': 'form',
    }


def build_default_evaluation_plan(exercise: ExerciseDefinition) -> dict:
    if exercise.evaluation_plan:
        return dict(exercise.evaluation_plan)

    if exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        return {
            'mechanism': 'runner_tests',
            'language': exercise.language,
            'template': 'implementation',
        }

    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        return {
            'mechanism': 'objective_key',
            'template': 'single-choice',
            'choice_mode': 'single',
        }

    if exercise.family_key == ExerciseDefinition.FAMILY_RESTRICTED_CODE:
        return {
            'mechanism': 'structural_checker',
            'template': 'fix-the-snippet',
            'passing_score': 1.0,
        }

    if exercise.family_key == ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB:
        return {
            'mechanism': 'contract_verifier',
            'template': 'http-contract',
        }

    return {
        'mechanism': 'rubric',
        'template': 'guided-response',
    }


def build_exercise_catalog_meta(exercise: ExerciseDefinition) -> dict:
    exercise_type = exercise.exercise_type.slug if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_SLUG
    return {
        'exercise_type': exercise_type,
        'exercise_type_label': exercise.exercise_type.name if exercise.exercise_type else DEFAULT_EXERCISE_TYPE_LABEL,
        'estimated_time_minutes': exercise.estimated_time_minutes or 15,
        'concept_summary': exercise.concept_summary or exercise.professor_note,
        'pedagogical_brief': exercise.pedagogical_brief or exercise.professor_note,
        'track_position': exercise.track_position or 0,
        'family_key': exercise.family_key or ExerciseDefinition.FAMILY_CODE_LAB,
    }


def serialize_exercise_summary(exercise: ExerciseDefinition) -> dict:
    meta = build_exercise_catalog_meta(exercise)
    return {
        'id': exercise.id,
        'slug': exercise.slug,
        'title': exercise.title,
        'learning_objectives': list(exercise.learning_objectives or []),
        'family_key': meta['family_key'],
        'difficulty': exercise.difficulty,
        'language': exercise.language,
        'professor_note': exercise.professor_note,
        'exercise_type': meta['exercise_type'],
        'exercise_type_label': meta['exercise_type_label'],
        'estimated_time_minutes': meta['estimated_time_minutes'],
        'concept_summary': meta['concept_summary'],
        'track_position': meta['track_position'],
        'module_slug': exercise.track.module.slug if exercise.track and exercise.track.module else None,
        'module_name': exercise.track.module.name if exercise.track and exercise.track.module else None,
        'category_slug': exercise.category.slug if exercise.category else None,
        'category_name': exercise.category.name if exercise.category else None,
        'track_slug': exercise.track.slug if exercise.track else None,
        'track_name': exercise.track.name if exercise.track else None,
    }


def serialize_exercise_detail(exercise: ExerciseDefinition) -> dict:
    return {
        **serialize_exercise_summary(exercise),
        'statement': exercise.statement,
        'version': exercise.version,
        'content_blocks': build_default_content_blocks(exercise),
        'workspace_spec': build_default_workspace_spec(exercise),
        'evaluation_plan': build_default_evaluation_plan(exercise),
        'review_profile': exercise.review_profile,
        'misconception_tags': list(exercise.misconception_tags or []),
        'progression_rules': dict(exercise.progression_rules or {}),
        'starter_code': exercise.starter_code,
        'sample_input': exercise.sample_input,
        'sample_output': exercise.sample_output,
        'test_cases': list(exercise.test_cases.filter(is_hidden=False)),
    }


def serialize_submission_summary(submission: Submission) -> dict:
    return {
        'id': submission.id,
        'exercise_slug': submission.exercise.slug,
        'exercise_title': submission.exercise.title,
        'status': submission.status,
        'passed_tests': submission.passed_tests,
        'total_tests': submission.total_tests,
        'feedback_status': submission.feedback_status,
        'feedback_source': submission.feedback_source,
        'created_at': submission.created_at,
    }


def serialize_submission(submission: Submission) -> dict:
    progress = UserExerciseProgress.objects.filter(user=submission.user, exercise=submission.exercise).first()
    return {
        'id': submission.id,
        'status': submission.status,
        'passed_tests': submission.passed_tests,
        'total_tests': submission.total_tests,
        'source_code': submission.source_code,
        'console_output': submission.console_output,
        'feedback': submission.feedback,
        'feedback_status': submission.feedback_status,
        'feedback_source': submission.feedback_source,
        'feedback_payload': submission.feedback_payload,
        'review_chat_history': submission.review_chat_history,
        'created_at': submission.created_at,
        'results': submission.execution_results,
        'xp_awarded': submission.xp_awarded,
        'unlocked_progress_rewards': submission.unlocked_progress_rewards,
        'exercise_progress': build_exercise_progress_payload(progress)
        if progress
        else {
            'attempts_count': 0,
            'best_passed_tests': 0,
            'best_total_tests': 0,
            'best_ratio': 0,
            'xp_awarded_total': 0,
            'first_passed_at': None,
            'awarded_progress_markers': [],
        },
        'user_progress': build_user_progress_summary(submission.user),
    }


def serialize_attempt_session(session: AttemptSession) -> dict:
    latest_snapshot = session.snapshots.order_by('-created_at', '-id').select_related('legacy_submission').first()
    latest_evaluation = None
    latest_review = None
    if latest_snapshot is not None:
        latest_evaluation = latest_snapshot.evaluation_runs.order_by('-created_at', '-id').first()
        if latest_evaluation is not None:
            latest_review = getattr(latest_evaluation, 'ai_review', None)

    exercise = session.exercise
    assessment = session.assessment
    family_key = exercise.family_key if exercise else None
    surface_key = None
    if exercise is not None:
        surface_key = resolve_surface_key(exercise)
    elif isinstance(session.state, dict):
        surface_key = session.state.get('surface_key')

    serialized_progress = None
    if exercise is not None:
        progress = UserExerciseProgress.objects.filter(user=session.user, exercise=exercise).first()
        if progress is not None:
            unlocked_rewards = []
            if 'passed_once' in (progress.awarded_progress_markers or []):
                unlocked_rewards.append(_build_passed_once_reward_payload(exercise))
            serialized_progress = {
                'xp_awarded': progress.xp_awarded_total,
                'unlocked_progress_rewards': unlocked_rewards,
                'exercise_progress': build_exercise_progress_payload(progress),
                'user_progress': build_user_progress_summary(session.user),
            }
    if serialized_progress is None and latest_snapshot is not None and latest_snapshot.legacy_submission is not None:
        serialized_progress = serialize_submission(latest_snapshot.legacy_submission)

    return {
        'id': session.id,
        'target_type': session.target_type,
        'exercise_slug': exercise.slug if exercise else None,
        'exercise_title': exercise.title if exercise else None,
        'assessment_slug': assessment.slug if assessment else None,
        'assessment_title': assessment.title if assessment else None,
        'family_key': family_key,
        'surface_key': surface_key,
        'mode': session.mode,
        'state': session.state or {},
        'current_workspace_state': session.current_workspace_state or {},
        'answer_state': session.answer_state or {},
        'attempt_status': session.attempt_status,
        'latest_snapshot': serialize_submission_snapshot(latest_snapshot) if latest_snapshot else None,
        'latest_evaluation': serialize_evaluation_run(latest_evaluation) if latest_evaluation else None,
        'latest_review': serialize_ai_review(latest_review) if latest_review else None,
        'xp_awarded': serialized_progress['xp_awarded'] if serialized_progress else 0,
        'unlocked_progress_rewards': serialized_progress['unlocked_progress_rewards'] if serialized_progress else [],
        'exercise_progress': serialized_progress['exercise_progress'] if serialized_progress else None,
        'user_progress': serialized_progress['user_progress'] if serialized_progress else None,
        'created_at': session.created_at,
        'updated_at': session.updated_at,
    }


def serialize_submission_snapshot(snapshot: SubmissionSnapshot) -> dict:
    return {
        'id': snapshot.id,
        'session_id': snapshot.session_id,
        'type': snapshot.type,
        'payload': snapshot.payload or {},
        'files': snapshot.files or {},
        'selected_options': list(snapshot.selected_options or []),
        'created_at': snapshot.created_at,
    }


def serialize_evaluation_run(evaluation_run: EvaluationRun) -> dict:
    return {
        'id': evaluation_run.id,
        'submission_snapshot_id': evaluation_run.submission_id,
        'normalized_score': evaluation_run.normalized_score,
        'verdict': evaluation_run.verdict,
        'evaluator_results': evaluation_run.evaluator_results or {},
        'evidence_bundle': evaluation_run.evidence_bundle or {},
        'misconception_inference': list(evaluation_run.misconception_inference or []),
        'raw_artifacts': evaluation_run.raw_artifacts or {},
        'created_at': evaluation_run.created_at,
    }


def serialize_ai_review(review: AIReview) -> dict:
    return {
        'id': review.id,
        'evaluation_run_id': review.evaluation_run_id,
        'profile_key': review.profile_key,
        'explanation': review.explanation,
        'next_steps': list(review.next_steps or []),
        'conversation_thread': list(review.conversation_thread or []),
        'created_at': review.created_at,
        'updated_at': review.updated_at,
    }


def serialize_assessment_container_part(part: AssessmentContainerPart) -> dict:
    return {
        'id': part.id,
        'title': part.title,
        'sort_order': part.sort_order,
        'exercise_slug': part.exercise.slug if part.exercise else None,
        'scoring_rules': part.scoring_rules or {},
        'timing_rules': part.timing_rules or {},
        'reveal_rules': part.reveal_rules or {},
    }


def serialize_assessment_container(container: AssessmentContainer) -> dict:
    return {
        'id': container.id,
        'slug': container.slug,
        'title': container.title,
        'mode': container.mode,
        'scoring_rules': container.scoring_rules or {},
        'timing_rules': container.timing_rules or {},
        'reveal_rules': container.reveal_rules or {},
        'parts': [serialize_assessment_container_part(part) for part in container.parts.all()],
    }


def build_session_config(exercise: ExerciseDefinition, mode: str = AttemptSession.MODE_PRACTICE) -> dict:
    surface_key = resolve_surface_key(exercise)
    return {
        'exercise': serialize_exercise_detail(exercise),
        'family_key': exercise.family_key,
        'surface_key': surface_key,
        'mode': mode,
        'workspace_spec': build_default_workspace_spec(exercise),
        'review_profile': exercise.review_profile,
    }


def create_attempt_session_for_exercise(user: ArenaUser, exercise: ExerciseDefinition, mode: str = AttemptSession.MODE_PRACTICE) -> AttemptSession:
    workspace_spec = build_default_workspace_spec(exercise)
    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        evaluation_plan = build_default_evaluation_plan(exercise)
        template_key = normalize_objective_template_key(evaluation_plan.get('template', 'single-choice'))
        answer_state = {
            'selected_options': [],
            'selected_labels': [],
            'response_text': '',
            'template': template_key,
            'choice_mode': evaluation_plan.get('choice_mode', 'single'),
        }
    elif exercise.family_key == ExerciseDefinition.FAMILY_RESTRICTED_CODE:
        answer_state = {
            'source_code': str(workspace_spec.get('editable_code') or ''),
            'template': normalize_restricted_template_key(workspace_spec.get('template') or 'fix-the-snippet'),
        }
    elif exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        starter_files = _serialize_workspace_files_for_runner(workspace_spec.get('files'))
        entrypoint = str(workspace_spec.get('entrypoint') or 'main.py')
        answer_state = {
            'source_code': str(starter_files.get(entrypoint) or exercise.starter_code or ''),
            'active_file': str(workspace_spec.get('active_file') or entrypoint),
            'entrypoint': entrypoint,
            'files': starter_files,
        }
    elif exercise.family_key == ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB:
        template = str(workspace_spec.get('template') or 'http-contract')
        if template in {'component-behavior', 'ui-behavior'}:
            starter_files = _serialize_workspace_files_for_runner(workspace_spec.get('files'))
            entrypoint = str(workspace_spec.get('entrypoint') or 'ComponentUnderTest.vue')
            answer_state = {
                'source_code': str(starter_files.get(entrypoint) or exercise.starter_code or ''),
                'active_file': str(workspace_spec.get('active_file') or entrypoint),
                'entrypoint': entrypoint,
                'files': starter_files,
                'response_text': '',
                'template': template,
            }
        else:
            answer_state = {
                'response_text': '',
                'observed_request': {},
                'observed_response': {},
                'template': template,
            }
    else:
        answer_state = {}

    return AttemptSession.objects.create(
        user=user,
        target_type=AttemptSession.TARGET_EXERCISE,
        exercise=exercise,
        mode=mode,
        state={'family_key': exercise.family_key, 'surface_key': resolve_surface_key(exercise)},
        current_workspace_state=workspace_spec,
        answer_state=answer_state,
    )


def create_attempt_session_for_assessment(user: ArenaUser, assessment: AssessmentContainer) -> AttemptSession:
    return AttemptSession.objects.create(
        user=user,
        target_type=AttemptSession.TARGET_ASSESSMENT,
        assessment=assessment,
        mode=assessment.mode,
        state={
            'assessment_slug': assessment.slug,
            'part_ids': list(assessment.parts.order_by('sort_order', 'id').values_list('id', flat=True)),
        },
        current_workspace_state={},
        answer_state={},
    )


def update_attempt_session_state(
    session: AttemptSession,
    state: dict | None = None,
    current_workspace_state: dict | None = None,
    answer_state: dict | None = None,
) -> AttemptSession:
    if state is not None:
        session.state = state
    if current_workspace_state is not None:
        session.current_workspace_state = current_workspace_state
    if answer_state is not None:
        session.answer_state = answer_state
    session.save(update_fields=['state', 'current_workspace_state', 'answer_state', 'updated_at'])
    return session


@dataclass
class ExecutionResult:
    ok: bool
    stdout: str
    stderr: str


def run_python(
    source_code: str,
    stdin: str,
    *,
    files: dict[str, str] | None = None,
    entrypoint: str | None = None,
) -> ExecutionResult:
    payload = json.dumps(
        {
            'language': 'python',
            'source_code': source_code,
            'stdin': stdin,
            'timeout_seconds': 5,
            'files': files or {},
            'entrypoint': entrypoint or 'main.py',
        }
    ).encode()
    request = Request(
        f'{settings.RUNNER_URL}/execute/python',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urlopen(request, timeout=8) as response:
            parsed = json.loads(response.read().decode())
            return ExecutionResult(
                ok=bool(parsed.get('ok')),
                stdout=str(parsed.get('stdout', '')),
                stderr=str(parsed.get('stderr', '')),
            )
    except URLError as error:
        return ExecutionResult(ok=False, stdout='', stderr=f'Runner indisponível: {error}')
    except Exception as error:  # pragma: no cover
        return ExecutionResult(ok=False, stdout='', stderr=str(error))


def execute_code_lab(
    exercise: ExerciseDefinition,
    source_code: str,
    *,
    files: dict[str, str] | None = None,
    entrypoint: str | None = None,
) -> tuple[list[dict], int, int, str, str]:
    results: list[dict] = []

    for index, test_case in enumerate(exercise.test_cases.all(), start=1):
        try:
            execution = run_python(
                source_code,
                test_case.input_data,
                files=files,
                entrypoint=entrypoint,
            )
        except TypeError:
            execution = run_python(source_code, test_case.input_data)
        actual_output = normalize_text(execution.stdout)
        expected_output = normalize_text(test_case.expected_output)
        passed = execution.ok and outputs_match_robust(expected_output, actual_output)
        results.append(
            {
                'index': index,
                'input_data': test_case.input_data,
                'expected_output': expected_output,
                'actual_output': actual_output,
                'passed': passed,
                'stderr': normalize_text(execution.stderr),
            }
        )

    passed_tests = sum(1 for result in results if result['passed'])
    total_tests = len(results)
    status = Submission.STATUS_PASSED if total_tests > 0 and passed_tests == total_tests else Submission.STATUS_FAILED
    console_output = format_execution_results_console(results)
    return results, passed_tests, total_tests, status, console_output


def create_legacy_submission(
    user: ArenaUser,
    exercise: ExerciseDefinition,
    source_code: str,
    results: list[dict],
    passed_tests: int,
    total_tests: int,
    status: str,
    console_output: str,
) -> Submission:
    submission = Submission.objects.create(
        user=user,
        exercise=exercise,
        source_code=source_code,
        status=status,
        passed_tests=passed_tests,
        total_tests=total_tests,
        console_output=console_output,
        feedback='Revisão com IA em processamento...',
        feedback_status=Submission.FEEDBACK_PENDING,
        feedback_source='agno-gemini',
        feedback_payload={
            'summary': 'Revisão com IA em processamento...',
            'strengths': [],
            'issues': [],
            'next_steps': [],
            'source': 'agno-gemini',
        },
        execution_results=results,
        review_chat_history=[],
        xp_awarded=0,
        unlocked_progress_rewards=[],
    )
    apply_submission_progress(user, exercise, submission)
    return submission


def build_code_lab_evaluation(
    session: AttemptSession,
    source_code: str,
    files: dict | None,
    snapshot_type: str,
) -> tuple[SubmissionSnapshot, EvaluationRun, Submission | None]:
    exercise = session.exercise
    if exercise is None:
        raise ValueError('Sessão sem exercício associado.')

    workspace_spec = build_default_workspace_spec(exercise)
    current_workspace_state = dict(session.current_workspace_state or {})
    entrypoint = str(
        current_workspace_state.get('entrypoint')
        or workspace_spec.get('entrypoint')
        or 'main.py'
    )
    base_runner_files = _serialize_workspace_files_for_runner(
        current_workspace_state.get('files') or workspace_spec.get('files')
    )
    submitted_files = _serialize_workspace_files_for_runner(files)
    merged_files = {
        **base_runner_files,
        **submitted_files,
    }
    if not merged_files:
        merged_files[entrypoint] = source_code
    else:
        merged_files[entrypoint] = source_code or merged_files.get(entrypoint, '')

    results, passed_tests, total_tests, status, console_output = execute_code_lab(
        exercise,
        source_code,
        files=merged_files,
        entrypoint=entrypoint,
    )
    normalized_score = (passed_tests / total_tests) if total_tests else 0
    verdict = EvaluationRun.VERDICT_PASSED if status == Submission.STATUS_PASSED else EvaluationRun.VERDICT_FAILED
    legacy_submission = None

    if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT:
        legacy_submission = create_legacy_submission(
            user=session.user,
            exercise=exercise,
            source_code=source_code,
            results=results,
            passed_tests=passed_tests,
            total_tests=total_tests,
            status=status,
            console_output=console_output,
        )

    snapshot = SubmissionSnapshot.objects.create(
        session=session,
        type=snapshot_type,
        payload={
            'source_code': source_code,
            'entrypoint': entrypoint,
        },
        files=merged_files,
        selected_options=[],
        legacy_submission=legacy_submission,
    )
    evaluation_run = EvaluationRun.objects.create(
        submission=snapshot,
        evaluator_results={
            'family_key': exercise.family_key,
            'mechanism': 'runner_tests',
            'passed_tests': passed_tests,
            'total_tests': total_tests,
        },
        normalized_score=normalized_score,
        verdict=verdict,
        evidence_bundle={
            'console_output': console_output,
            'results': results,
            'workspace_spec': workspace_spec,
            'entrypoint': entrypoint,
            'files': merged_files,
        },
        misconception_inference=[],
        raw_artifacts={
            'status': status,
            'source_code': source_code,
            'entrypoint': entrypoint,
            'files': merged_files,
        },
        legacy_submission=legacy_submission,
    )

    if legacy_submission is not None:
        AIReview.objects.create(
            evaluation_run=evaluation_run,
            profile_key=exercise.review_profile,
            explanation='Revisão com IA em processamento...',
            next_steps=[],
            conversation_thread=[],
        )
        schedule_submission_feedback(
            legacy_submission.id,
            exercise.title,
            exercise.statement,
            source_code,
            merged_files,
            passed_tests,
            total_tests,
            results,
            evaluation_run_id=evaluation_run.id,
        )

    session.answer_state = {'source_code': source_code}
    session.current_workspace_state = {
        **current_workspace_state,
        'entrypoint': entrypoint,
        'active_file': current_workspace_state.get('active_file') or entrypoint,
        'files': {
            file_name: _normalize_workspace_file_entry(
                file_name,
                {
                    'content': file_content,
                    'path': (
                        (current_workspace_state.get('files') or {}).get(file_name, {}).get('path')
                        if isinstance((current_workspace_state.get('files') or {}).get(file_name), dict)
                        else file_name
                    ),
                    'label': (
                        (current_workspace_state.get('files') or {}).get(file_name, {}).get('label')
                        if isinstance((current_workspace_state.get('files') or {}).get(file_name), dict)
                        else file_name
                    ),
                    'read_only': bool(
                        isinstance((current_workspace_state.get('files') or {}).get(file_name), dict)
                        and (current_workspace_state.get('files') or {}).get(file_name, {}).get('read_only')
                    ),
                    'role': (
                        'entrypoint'
                        if file_name == entrypoint
                        else (
                            (current_workspace_state.get('files') or {}).get(file_name, {}).get('role')
                            if isinstance((current_workspace_state.get('files') or {}).get(file_name), dict)
                            else ''
                        )
                    ),
                },
            )
            for file_name, file_content in merged_files.items()
        },
    }
    session.answer_state = {
        'source_code': source_code,
        'entrypoint': entrypoint,
        'active_file': current_workspace_state.get('active_file') or entrypoint,
        'files': merged_files,
    }
    session.attempt_status = (
        AttemptSession.STATUS_COMPLETED if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT else AttemptSession.STATUS_ACTIVE
    )
    session.save(update_fields=['answer_state', 'current_workspace_state', 'attempt_status', 'updated_at'])

    return snapshot, evaluation_run, legacy_submission


def evaluate_attempt_session(
    session: AttemptSession,
    *,
    snapshot_type: str,
    source_code: str = '',
    selected_options: list[str] | None = None,
    response_text: str = '',
    files: dict | None = None,
) -> tuple[SubmissionSnapshot, EvaluationRun, AIReview | None, Submission | None]:
    exercise = session.exercise
    if exercise is None:
        raise ValueError('Sessão sem exercício associado.')

    family_spec = get_family_spec(exercise.family_key)
    if snapshot_type not in family_spec.supported_snapshot_types:
        raise ValueError(f'Tipo de snapshot "{snapshot_type}" não suportado para {exercise.family_key}.')

    if exercise.family_key == ExerciseDefinition.FAMILY_CODE_LAB:
        workspace_spec = build_default_workspace_spec(exercise)
        effective_entrypoint = str(
            (session.current_workspace_state or {}).get('entrypoint')
            or workspace_spec.get('entrypoint')
            or 'main.py'
        )
        runner_files = _serialize_workspace_files_for_runner(files)
        effective_source_code = source_code or runner_files.get(effective_entrypoint, '')
        snapshot, evaluation_run, legacy_submission = build_code_lab_evaluation(
            session=session,
            source_code=effective_source_code,
            files=files,
            snapshot_type=snapshot_type,
        )
        review = AIReview.objects.filter(evaluation_run=evaluation_run).first()
        return snapshot, evaluation_run, review, legacy_submission

    if exercise.family_key == ExerciseDefinition.FAMILY_OBJECTIVE_ITEM:
        evaluation_plan = build_default_evaluation_plan(exercise)
        content_blocks = build_default_content_blocks(exercise)
        objective_result = evaluate_objective_selection(
            evaluation_plan=evaluation_plan,
            content_blocks=content_blocks,
            selected_options=selected_options,
            response_text=response_text,
            attempt_mode=session.mode,
        )
        snapshot = SubmissionSnapshot.objects.create(
            session=session,
            type=snapshot_type,
            payload={
                'selected_options': objective_result['selected_options'],
                'selected_labels': objective_result['selected_labels'],
                'response_text': response_text,
                'template': objective_result['template'],
                'choice_mode': objective_result['choice_mode'],
                'score_rule': objective_result['score_rule'],
            },
            files=files or {},
            selected_options=objective_result['selected_options'],
        )
        explanation_lines = [
            '### Revisão objetiva',
            f"Template avaliado: {objective_result['template']}",
            f"Você selecionou: {', '.join(objective_result['selected_labels']) if objective_result['selected_labels'] else '(nenhuma opção)'}",
            f"Gabarito esperado: {', '.join(objective_result['correct_labels']) if objective_result['correct_labels'] else '(sem gabarito definido)'}",
            '',
        ]
        if objective_result['template'] == 'compile-runtime-output':
            explanation_lines.append('A análise foi feita separando compilação, runtime e saída observável.')
            if objective_result['requires_output_text']:
                explanation_lines.append(f"Saída esperada: {objective_result['expected_output_text'] or '(sem saída configurada)'}")
                explanation_lines.append(f"Saída informada: {objective_result['response_text'] or '(nenhuma saída informada)'}")
                if objective_result['output_text_matches'] is False:
                    explanation_lines.append('A classificação apontou para output, mas o texto de saída ainda não bate com o esperado.')
        elif objective_result['template'] == 'behavior-classification':
            explanation_lines.append('O veredito depende do comportamento real do trecho, não apenas da leitura superficial do snippet.')
        elif objective_result['template'] == 'output-prediction':
            explanation_lines.append('A resposta foi avaliada como previsão de saída, com foco na execução linha a linha.')
        if objective_result['passed']:
            explanation_lines.append('Você acertou a leitura conceitual principal dessa questão.')
        else:
            explanation_lines.append('A resposta ainda não bate com o gabarito esperado.')
            if objective_result['correct_labels']:
                explanation_lines.append(
                    'Conceitos a revisar: ' + ', '.join(objective_result['correct_labels'])
                )
            wrong_explanations = [
                option.get('explanation')
                for option in objective_result['option_results']
                if option.get('selected') and not option.get('correct') and option.get('explanation')
            ]
            if wrong_explanations:
                explanation_lines.append('Explicações dos distratores escolhidos: ' + ' | '.join(dict.fromkeys(wrong_explanations)))
            if objective_result['misconception_inference']:
                explanation_lines.append(
                    'Conceitos a revisar: ' + ', '.join(objective_result['misconception_inference'])
                )
        correct_explanations = [
            option.get('explanation')
            for option in objective_result['option_results']
            if option.get('correct') and option.get('explanation')
        ]
        if correct_explanations:
            explanation_lines.append('Explicação da alternativa correta: ' + ' | '.join(dict.fromkeys(correct_explanations)))
        explanation_lines.extend(
            [
                '',
                'Pense na regra que diferencia a alternativa correta das distratoras e revise o enunciado com foco no ponto de decisão central.',
            ]
        )
        next_steps = [
            'Releia o enunciado e destaque a regra que decide a resposta correta.',
            'Compare as alternativas escolhidas com o gabarito e identifique a diferença conceitual principal.',
        ]
        if objective_result['misconception_inference']:
            next_steps.append(f"Revise os conceitos: {', '.join(objective_result['misconception_inference'])}.")

        evaluation_run = EvaluationRun.objects.create(
            submission=snapshot,
            evaluator_results={
                'family_key': exercise.family_key,
                'mechanism': objective_result['template'],
                'choice_mode': objective_result['choice_mode'],
                'selected_options': objective_result['selected_options'],
                'selected_labels': objective_result['selected_labels'],
                'correct_options': objective_result['correct_options'],
                'correct_labels': objective_result['correct_labels'],
                'passed': objective_result['passed'],
                'exact_match': objective_result['exact_match'],
                'score': objective_result['normalized_score'],
                'passing_score': objective_result['passing_score'],
                'option_results': objective_result['option_results'],
                'requires_output_text': objective_result['requires_output_text'],
                'expected_output_text': objective_result['expected_output_text'],
                'output_text_matches': objective_result['output_text_matches'],
                'response_text': objective_result['response_text'],
            },
            normalized_score=objective_result['normalized_score'],
            verdict=objective_result['verdict'],
            evidence_bundle={
                'statement': exercise.statement,
                'content_blocks': content_blocks,
                'workspace_spec': build_default_workspace_spec(exercise),
                'evaluation_plan': evaluation_plan,
                'template_meta': build_default_workspace_spec(exercise).get('template_meta', {}),
                'selected_options': objective_result['selected_options'],
                'selected_labels': objective_result['selected_labels'],
                'correct_options': objective_result['correct_options'],
                'correct_labels': objective_result['correct_labels'],
                'score_rule': objective_result['score_rule'],
                'option_results': objective_result['option_results'],
                'requires_output_text': objective_result['requires_output_text'],
                'expected_output_text': objective_result['expected_output_text'],
                'output_text_matches': objective_result['output_text_matches'],
                'response_text': objective_result['response_text'],
            },
            misconception_inference=objective_result['misconception_inference'],
            raw_artifacts={
                'response_text': response_text,
                'payload_selected_options': list(selected_options or []),
                'payload_files': files or {},
                'template': objective_result['template'],
                'choice_mode': objective_result['choice_mode'],
                'score_rule': objective_result['score_rule'],
            },
        )
        review = AIReview.objects.create(
            evaluation_run=evaluation_run,
            profile_key=exercise.review_profile,
            explanation='\n'.join(explanation_lines).strip(),
            next_steps=next_steps,
            conversation_thread=[
                {
                    'role': 'assistant',
                    'content': '\n'.join(explanation_lines).strip(),
                }
            ],
        )

        session.answer_state = {
            'selected_options': objective_result['selected_options'],
            'selected_labels': objective_result['selected_labels'],
            'response_text': response_text,
            'normalized_score': objective_result['normalized_score'],
            'verdict': objective_result['verdict'],
        }
        session.current_workspace_state = {
            **(session.current_workspace_state or {}),
            'selected_options': objective_result['selected_options'],
            'selected_labels': objective_result['selected_labels'],
            'response_text': response_text,
        }
        session.attempt_status = (
            AttemptSession.STATUS_COMPLETED if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT else AttemptSession.STATUS_ACTIVE
        )
        session.save(update_fields=['answer_state', 'current_workspace_state', 'attempt_status', 'updated_at'])
        update_objective_item_progress(session.user, exercise, objective_result)
        return snapshot, evaluation_run, review, None

    if exercise.family_key == ExerciseDefinition.FAMILY_RESTRICTED_CODE:
        evaluation_plan = build_default_evaluation_plan(exercise)
        workspace_spec = build_default_workspace_spec(exercise)
        restricted_result = evaluate_restricted_code_submission(
            evaluation_plan=evaluation_plan,
            workspace_spec=workspace_spec,
            source_code=source_code,
            attempt_mode=session.mode,
        )
        snapshot = SubmissionSnapshot.objects.create(
            session=session,
            type=snapshot_type,
            payload={
                'source_code': source_code,
                'template': restricted_result['template'],
                'matched_criteria': restricted_result['matched_criteria'],
                'total_criteria': restricted_result['total_criteria'],
            },
            files=files or {},
            selected_options=[],
        )
        explanation_lines = [
            '### Revisão estrutural',
            f"Template avaliado: {restricted_result['template']}",
            f"Critérios atendidos: {restricted_result['matched_criteria']}/{restricted_result['total_criteria']}",
            '',
        ]
        if restricted_result['passed']:
            explanation_lines.append('A correção respeitou os critérios estruturais configurados para este exercício.')
        else:
            explanation_lines.append('A solução ainda não fecha com todos os critérios estruturais esperados.')
            if restricted_result['failed_criteria']:
                explanation_lines.append('O que ainda falta: ' + ' | '.join(restricted_result['failed_criteria']))
        if restricted_result['passed_criteria']:
            explanation_lines.append('O que já foi atendido: ' + ' | '.join(restricted_result['passed_criteria']))
        if restricted_result['blank_results']:
            missing_blanks = [
                blank['label']
                for blank in restricted_result['blank_results']
                if not blank['passed']
            ]
            if missing_blanks:
                explanation_lines.append('Lacunas que ainda precisam de ajuste: ' + ', '.join(missing_blanks))
        explanation_lines.extend(
            [
                '',
                'Procure a menor alteração capaz de satisfazer os critérios que ainda falharam antes de reescrever o trecho inteiro.',
            ]
        )
        next_steps = [
            'Compare o código editado com o snippet original e identifique a menor correção possível.',
            'Revise apenas os critérios que ainda falharam antes de tentar novamente.',
        ]

        evaluation_run = EvaluationRun.objects.create(
            submission=snapshot,
            evaluator_results={
                'family_key': exercise.family_key,
                'mechanism': evaluation_plan.get('mechanism') or 'structural_checker',
                'template': restricted_result['template'],
                'matched_criteria': restricted_result['matched_criteria'],
                'total_criteria': restricted_result['total_criteria'],
                'passed_tests': restricted_result['matched_criteria'],
                'total_tests': restricted_result['total_criteria'],
                'criteria_results': restricted_result['criteria_results'],
                'exact_match': restricted_result['exact_match'],
            },
            normalized_score=restricted_result['normalized_score'],
            verdict=restricted_result['verdict'],
            evidence_bundle={
                'workspace_spec': workspace_spec,
                'evaluation_plan': evaluation_plan,
                'criteria_results': restricted_result['criteria_results'],
                'passed_criteria': restricted_result['passed_criteria'],
                'failed_criteria': restricted_result['failed_criteria'],
                'blank_answers': restricted_result['blank_answers'],
                'submitted_source_code': source_code,
            },
            misconception_inference=[] if restricted_result['passed'] else list(exercise.misconception_tags or []),
            raw_artifacts={
                'source_code': source_code,
                'normalized_source': restricted_result['normalized_source'],
                'expected_code': restricted_result['expected_code'],
                'files': files or {},
            },
        )
        review = AIReview.objects.create(
            evaluation_run=evaluation_run,
            profile_key=exercise.review_profile,
            explanation='\n'.join(explanation_lines).strip(),
            next_steps=next_steps,
            conversation_thread=[
                {
                    'role': 'assistant',
                    'content': '\n'.join(explanation_lines).strip(),
                }
            ],
        )

        session.answer_state = {
            'source_code': source_code,
            'template': restricted_result['template'],
            'normalized_score': restricted_result['normalized_score'],
            'verdict': restricted_result['verdict'],
        }
        session.current_workspace_state = {
            **(session.current_workspace_state or {}),
            'editable_code': source_code,
            'last_matched_criteria': restricted_result['matched_criteria'],
            'last_total_criteria': restricted_result['total_criteria'],
        }
        session.attempt_status = (
            AttemptSession.STATUS_COMPLETED if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT else AttemptSession.STATUS_ACTIVE
        )
        session.save(update_fields=['answer_state', 'current_workspace_state', 'attempt_status', 'updated_at'])
        update_restricted_code_progress(session.user, exercise, restricted_result)
        return snapshot, evaluation_run, review, None

    if exercise.family_key == ExerciseDefinition.FAMILY_CONTRACT_BEHAVIOR_LAB:
        evaluation_plan = build_default_evaluation_plan(exercise)
        workspace_spec = build_default_workspace_spec(exercise)
        template = str(workspace_spec.get('template') or evaluation_plan.get('template') or 'http-contract')
        if template in {'component-behavior', 'ui-behavior'}:
            component_result = evaluate_component_behavior_submission(
                workspace_spec=workspace_spec,
                evaluation_plan=evaluation_plan,
                source_code=source_code,
                response_text=response_text,
            )
            snapshot = SubmissionSnapshot.objects.create(
                session=session,
                type=snapshot_type,
                payload={
                    'source_code': source_code,
                    'response_text': response_text,
                    'template': component_result['template'],
                },
                files=files or {},
                selected_options=[],
            )
            explanation_lines = [
                '### Revisão de comportamento de componente',
                f"Checks atendidos: {component_result['passed_tests']}/{component_result['total_tests']}",
            ]
            if component_result['passed']:
                explanation_lines.append('O componente atende ao contrato observável de props, estado, eventos e DOM.')
            else:
                explanation_lines.append('Ainda existem divergências entre o contrato esperado do componente e a evidência observada.')
                if component_result['divergences']:
                    explanation_lines.append('Divergências: ' + ' | '.join(component_result['divergences']))
            explanation_lines.extend(
                [
                    '',
                    'Leia o componente como contrato observável: primeiro sinais de props e estado, depois eventos, renderização e DOM.',
                ]
            )
            next_steps = [
                'Confirme se os sinais obrigatórios de props e estado aparecem no componente.',
                'Revise eventos emitidos e a renderização observável antes de submeter novamente.',
            ]
            evaluation_run = EvaluationRun.objects.create(
                submission=snapshot,
                evaluator_results={
                    'family_key': exercise.family_key,
                    'mechanism': evaluation_plan.get('mechanism') or 'component_behavior_verifier',
                    'template': component_result['template'],
                    'passed': component_result['passed'],
                    'passed_tests': component_result['passed_tests'],
                    'total_tests': component_result['total_tests'],
                    'checks': component_result['checks'],
                },
                normalized_score=component_result['normalized_score'],
                verdict=component_result['verdict'],
                evidence_bundle={
                    'workspace_spec': workspace_spec,
                    'evaluation_plan': evaluation_plan,
                    'component_contract': component_result['component_contract'],
                    'source_summary': component_result['source_summary'],
                    'observation': component_result['observation'],
                    'checks': component_result['checks'],
                    'results': component_result['results'],
                    'divergences': component_result['divergences'],
                    'console_output': component_result['console_output'],
                },
                misconception_inference=[] if component_result['passed'] else list(exercise.misconception_tags or []),
                raw_artifacts={
                    'source_code': source_code,
                    'response_text': response_text,
                    'files': files or {},
                },
            )
            review = AIReview.objects.create(
                evaluation_run=evaluation_run,
                profile_key=exercise.review_profile,
                explanation='\n'.join(explanation_lines).strip(),
                next_steps=next_steps,
                conversation_thread=[
                    {
                        'role': 'assistant',
                        'content': '\n'.join(explanation_lines).strip(),
                    }
                ],
            )
            session.answer_state = {
                'source_code': source_code,
                'response_text': response_text,
                'normalized_score': component_result['normalized_score'],
                'verdict': component_result['verdict'],
                'template': component_result['template'],
                'files': files or {},
                'active_file': str(workspace_spec.get('active_file') or workspace_spec.get('entrypoint') or ''),
                'entrypoint': str(workspace_spec.get('entrypoint') or ''),
            }
            session.current_workspace_state = {
                **(session.current_workspace_state or {}),
                'files': workspace_spec.get('files') or {},
                'last_component_checks': component_result['checks'],
                'last_component_observation': component_result['observation'],
            }
            session.attempt_status = (
                AttemptSession.STATUS_COMPLETED if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT else AttemptSession.STATUS_ACTIVE
            )
            session.save(update_fields=['answer_state', 'current_workspace_state', 'attempt_status', 'updated_at'])
            update_contract_behavior_progress(session.user, exercise, component_result)
            return snapshot, evaluation_run, review, None

        contract_result = evaluate_http_contract_submission(
            workspace_spec=workspace_spec,
            evaluation_plan=evaluation_plan,
            response_text=response_text,
        )
        snapshot = SubmissionSnapshot.objects.create(
            session=session,
            type=snapshot_type,
            payload={
                'response_text': response_text,
                'template': contract_result['template'],
                'observed_request': contract_result['observed_request'],
                'observed_response': contract_result['observed_response'],
            },
            files=files or {},
            selected_options=[],
        )
        explanation_lines = [
            '### Revisão de contrato HTTP',
            f"Checks atendidos: {contract_result['passed_tests']}/{contract_result['total_tests']}",
        ]
        if contract_result['passed']:
            explanation_lines.append('A requisição observada e a resposta retornada respeitam o contrato configurado.')
        else:
            explanation_lines.append('O contrato ainda não fecha completamente entre o esperado e o observado.')
            if contract_result['divergences']:
                explanation_lines.append('Divergências: ' + ' | '.join(contract_result['divergences']))
        explanation_lines.extend(
            [
                '',
                'Leia o contrato como acordo entre cliente e servidor: primeiro request, depois status, headers, body e schema.',
            ]
        )
        next_steps = [
            'Compare método e path enviados com o contrato esperado.',
            'Revise status, headers e body observados antes de reenviar a tentativa.',
        ]
        if contract_result['divergences']:
            next_steps.append('Corrija primeiro a divergência mais estrutural antes de ajustar detalhes de payload.')

        evaluation_run = EvaluationRun.objects.create(
            submission=snapshot,
            evaluator_results={
                'family_key': exercise.family_key,
                'mechanism': evaluation_plan.get('mechanism') or 'contract_verifier',
                'template': contract_result['template'],
                'passed': contract_result['passed'],
                'passed_tests': contract_result['passed_tests'],
                'total_tests': contract_result['total_tests'],
                'checks': contract_result['checks'],
            },
            normalized_score=contract_result['normalized_score'],
            verdict=contract_result['verdict'],
            evidence_bundle={
                'workspace_spec': workspace_spec,
                'evaluation_plan': evaluation_plan,
                'request': contract_result['request'],
                'expected_response': contract_result['expected_response'],
                'observed_request': contract_result['observed_request'],
                'observed_response': contract_result['observed_response'],
                'checks': contract_result['checks'],
                'results': contract_result['results'],
                'divergences': contract_result['divergences'],
                'console_output': contract_result['console_output'],
            },
            misconception_inference=[] if contract_result['passed'] else list(exercise.misconception_tags or []),
            raw_artifacts={
                'response_text': response_text,
                'payload': contract_result['payload'],
                'files': files or {},
            },
        )
        review = AIReview.objects.create(
            evaluation_run=evaluation_run,
            profile_key=exercise.review_profile,
            explanation='\n'.join(explanation_lines).strip(),
            next_steps=next_steps,
            conversation_thread=[
                {
                    'role': 'assistant',
                    'content': '\n'.join(explanation_lines).strip(),
                }
            ],
        )
        session.answer_state = {
            'response_text': response_text,
            'observed_request': contract_result['observed_request'],
            'observed_response': contract_result['observed_response'],
            'normalized_score': contract_result['normalized_score'],
            'verdict': contract_result['verdict'],
            'template': contract_result['template'],
        }
        session.current_workspace_state = {
            **(session.current_workspace_state or {}),
            'last_contract_checks': contract_result['checks'],
            'last_observed_request': contract_result['observed_request'],
            'last_observed_response': contract_result['observed_response'],
        }
        session.attempt_status = (
            AttemptSession.STATUS_COMPLETED if snapshot_type == SubmissionSnapshot.TYPE_SUBMIT else AttemptSession.STATUS_ACTIVE
        )
        session.save(update_fields=['answer_state', 'current_workspace_state', 'attempt_status', 'updated_at'])
        update_contract_behavior_progress(session.user, exercise, contract_result)
        return snapshot, evaluation_run, review, None

    snapshot = SubmissionSnapshot.objects.create(
        session=session,
        type=snapshot_type,
        payload={
            'source_code': source_code,
            'response_text': response_text,
        },
        files=files or {},
        selected_options=selected_options or [],
    )
    evaluation_run = EvaluationRun.objects.create(
        submission=snapshot,
        evaluator_results={
            'family_key': exercise.family_key,
            'mechanism': build_default_evaluation_plan(exercise).get('mechanism'),
        },
        normalized_score=0,
        verdict=EvaluationRun.VERDICT_ERROR,
        evidence_bundle={},
        misconception_inference=[],
        raw_artifacts={'status': 'not_implemented'},
    )
    review = AIReview.objects.create(
        evaluation_run=evaluation_run,
        profile_key=exercise.review_profile,
        explanation='Esta família ainda está em implementação na plataforma.',
        next_steps=['Volte a este exercício quando a família estiver habilitada.'],
        conversation_thread=[],
    )
    return snapshot, evaluation_run, review, None


def update_objective_item_progress(
    user: ArenaUser,
    exercise: ExerciseDefinition,
    objective_result: dict,
) -> tuple[UserExerciseProgress, list, int]:
    with transaction.atomic():
        locked_user = ArenaUser.objects.select_for_update().get(pk=user.pk)
        progress, _ = UserExerciseProgress.objects.select_for_update().get_or_create(
            user=locked_user,
            exercise=exercise,
        )

        progress.attempts_count += 1
        current_ratio = float(objective_result.get('normalized_score', 0) or 0)
        best_ratio = progress.best_ratio or 0
        improved = (
            current_ratio > best_ratio
            or (current_ratio == best_ratio and objective_result.get('passed') and progress.best_total_tests == 0)
        )

        if improved:
            progress.best_passed_tests = 1 if objective_result.get('passed') else 0
            progress.best_total_tests = 1
            progress.best_ratio = current_ratio

        awarded_progress_markers = list(progress.awarded_progress_markers or [])
        unlocked_rewards = []
        xp_awarded = 0

        if objective_result.get('passed') and 'passed_once' not in awarded_progress_markers:
            awarded_progress_markers.append('passed_once')
            unlocked_rewards.append(_build_passed_once_reward_payload(exercise))
            xp_awarded += DEFAULT_OBJECTIVE_ITEM_XP
            progress.first_passed_at = progress.first_passed_at or timezone.now()

        progress.awarded_progress_markers = awarded_progress_markers
        progress.xp_awarded_total += xp_awarded
        progress.save()

        if xp_awarded:
            locked_user.xp_total += xp_awarded
            locked_user.save(update_fields=['xp_total', 'updated_at'])

        user.xp_total = locked_user.xp_total
        return progress, unlocked_rewards, xp_awarded


def update_restricted_code_progress(
    user: ArenaUser,
    exercise: ExerciseDefinition,
    restricted_result: dict,
) -> tuple[UserExerciseProgress, list, int]:
    with transaction.atomic():
        locked_user = ArenaUser.objects.select_for_update().get(pk=user.pk)
        progress, _ = UserExerciseProgress.objects.select_for_update().get_or_create(
            user=locked_user,
            exercise=exercise,
        )

        progress.attempts_count += 1
        current_ratio = float(restricted_result.get('normalized_score', 0) or 0)
        best_ratio = progress.best_ratio or 0
        improved = (
            current_ratio > best_ratio
            or (
                current_ratio == best_ratio
                and restricted_result.get('passed')
                and (progress.best_total_tests or 0) == 0
            )
        )

        if improved:
            progress.best_passed_tests = int(restricted_result.get('matched_criteria', 0) or 0)
            progress.best_total_tests = int(restricted_result.get('total_criteria', 0) or 0)
            progress.best_ratio = current_ratio

        awarded_progress_markers = list(progress.awarded_progress_markers or [])
        unlocked_rewards = []
        xp_awarded = 0

        if restricted_result.get('passed') and 'passed_once' not in awarded_progress_markers:
            awarded_progress_markers.append('passed_once')
            unlocked_rewards.append(_build_passed_once_reward_payload(exercise))
            xp_awarded += DEFAULT_RESTRICTED_CODE_XP
            progress.first_passed_at = progress.first_passed_at or timezone.now()

        progress.awarded_progress_markers = awarded_progress_markers
        progress.xp_awarded_total += xp_awarded
        progress.save()

        if xp_awarded:
            locked_user.xp_total += xp_awarded
            locked_user.save(update_fields=['xp_total', 'updated_at'])

        user.xp_total = locked_user.xp_total
        return progress, unlocked_rewards, xp_awarded


def update_contract_behavior_progress(
    user: ArenaUser,
    exercise: ExerciseDefinition,
    contract_result: dict,
) -> tuple[UserExerciseProgress, list, int]:
    with transaction.atomic():
        locked_user = ArenaUser.objects.select_for_update().get(pk=user.pk)
        progress, _ = UserExerciseProgress.objects.select_for_update().get_or_create(
            user=locked_user,
            exercise=exercise,
        )

        progress.attempts_count += 1
        current_ratio = float(contract_result.get('normalized_score', 0) or 0)
        best_ratio = progress.best_ratio or 0
        improved = (
            current_ratio > best_ratio
            or (current_ratio == best_ratio and contract_result.get('passed') and (progress.best_total_tests or 0) == 0)
        )

        if improved:
            progress.best_passed_tests = int(contract_result.get('passed_tests', 0) or 0)
            progress.best_total_tests = int(contract_result.get('total_tests', 0) or 0)
            progress.best_ratio = current_ratio

        awarded_progress_markers = list(progress.awarded_progress_markers or [])
        unlocked_rewards = []
        xp_awarded = 0

        if contract_result.get('passed') and 'passed_once' not in awarded_progress_markers:
            awarded_progress_markers.append('passed_once')
            unlocked_rewards.append(
                {
                    'milestone_key': 'passed_once',
                    'label': 'Contrato validado',
                    'xp_awarded': DEFAULT_CONTRACT_BEHAVIOR_XP,
                }
            )
            xp_awarded += DEFAULT_CONTRACT_BEHAVIOR_XP
            progress.first_passed_at = progress.first_passed_at or timezone.now()

        progress.awarded_progress_markers = awarded_progress_markers
        progress.xp_awarded_total += xp_awarded
        progress.save()

        if xp_awarded:
            locked_user.xp_total += xp_awarded
            locked_user.save(update_fields=['xp_total', 'updated_at'])

        user.xp_total = locked_user.xp_total
        return progress, unlocked_rewards, xp_awarded


def evaluate_submission(user: ArenaUser, exercise: ExerciseDefinition, source_code: str) -> tuple[Submission, list[dict]]:
    session = create_attempt_session_for_exercise(user, exercise, mode=AttemptSession.MODE_PRACTICE)
    _, evaluation_run, _, legacy_submission = evaluate_attempt_session(
        session,
        snapshot_type=SubmissionSnapshot.TYPE_SUBMIT,
        source_code=source_code,
    )
    if legacy_submission is None:
        raise ValueError('Submissão legada não foi criada para code_lab.')
    return legacy_submission, list(evaluation_run.evidence_bundle.get('results') or [])
