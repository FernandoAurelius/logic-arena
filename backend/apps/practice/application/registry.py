from dataclasses import dataclass

from apps.practice.domain import normalize_objective_template_key


@dataclass(frozen=True)
class ExerciseFamilySpec:
    family_key: str
    default_surface_key: str
    default_review_profile: str
    supported_snapshot_types: tuple[str, ...]


FAMILY_REGISTRY: dict[str, ExerciseFamilySpec] = {
    'code_lab': ExerciseFamilySpec(
        family_key='code_lab',
        default_surface_key='code_editor_single',
        default_review_profile='code_lab_default',
        supported_snapshot_types=('run', 'check', 'submit'),
    ),
    'objective_item': ExerciseFamilySpec(
        family_key='objective_item',
        default_surface_key='objective_choices',
        default_review_profile='objective_item_default',
        supported_snapshot_types=('check', 'submit'),
    ),
    'restricted_code': ExerciseFamilySpec(
        family_key='restricted_code',
        default_surface_key='restricted_diff',
        default_review_profile='restricted_code_default',
        supported_snapshot_types=('run', 'check', 'submit'),
    ),
    'contract_behavior_lab': ExerciseFamilySpec(
        family_key='contract_behavior_lab',
        default_surface_key='http_contract_lab',
        default_review_profile='contract_behavior_default',
        supported_snapshot_types=('run', 'check', 'submit'),
    ),
    'guided_response': ExerciseFamilySpec(
        family_key='guided_response',
        default_surface_key='guided_text_response',
        default_review_profile='guided_response_default',
        supported_snapshot_types=('submit',),
    ),
}


OBJECTIVE_CLASSIFIER_TEMPLATES = {
    'compile-runtime-output',
    'behavior-classification',
}


OBJECTIVE_SNIPPET_TEMPLATES = {
    'snippet-read-only',
    'read-only-snippet',
    'snippet-analysis',
    'code-snippet',
    'output-prediction',
}


RESTRICTED_FILL_TEMPLATES = {
    'fill-in-the-blanks',
}


CONTRACT_COMPONENT_TEMPLATES = {
    'component-behavior',
    'ui-behavior',
}


def get_family_spec(family_key: str) -> ExerciseFamilySpec:
    try:
        return FAMILY_REGISTRY[family_key]
    except KeyError as error:
        raise ValueError(f'Família de exercício não registrada: {family_key}') from error


def resolve_surface_key(exercise) -> str:
    family_spec = get_family_spec(exercise.family_key)
    workspace_spec = exercise.workspace_spec or {}
    evaluation_plan = exercise.evaluation_plan or {}
    template = normalize_objective_template_key(
        workspace_spec.get('template')
        or evaluation_plan.get('template')
        or evaluation_plan.get('kind')
        or ''
    )

    if exercise.family_key == 'code_lab':
        if workspace_spec.get('workspace_kind') == 'multifile':
            return 'code_editor_multifile'
        return family_spec.default_surface_key

    if exercise.family_key == 'objective_item':
        if template in OBJECTIVE_CLASSIFIER_TEMPLATES:
            return 'objective_classifier'
        return family_spec.default_surface_key

    if exercise.family_key == 'restricted_code':
        if template in RESTRICTED_FILL_TEMPLATES:
            return 'restricted_fill_blanks'
        return family_spec.default_surface_key

    if exercise.family_key == 'contract_behavior_lab':
        if template in CONTRACT_COMPONENT_TEMPLATES:
            return 'component_behavior_lab'
        return family_spec.default_surface_key

    return family_spec.default_surface_key
