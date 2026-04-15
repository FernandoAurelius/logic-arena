import re

NUMERIC_TOLERANCE = 1e-9

APPROVAL_PATTERNS = {
    'approved': [
        'aluno aprovado',
        'aprovado',
        'aluno passou',
        'passou',
    ],
    'failed': [
        'aluno reprovado',
        'reprovado',
        'aluno reprovou',
        'reprovou',
    ],
}

OBJECTIVE_TEMPLATE_ALIASES = {
    'single_choice': 'single-choice',
    'multi_select': 'multi-select',
    'read-only-snippet': 'snippet-read-only',
    'snippet-analysis': 'snippet-read-only',
    'code-snippet': 'snippet-read-only',
    'output_prediction': 'output-prediction',
}

OBJECTIVE_SCORE_RULE_KEYS = (
    'scoring_rules',
    'mode_scoring',
    'scoring_by_mode',
)


def normalize_text(text: str) -> str:
    return str(text).replace('\r', '').strip()


def canonical_text(text: str) -> str:
    return re.sub(r'\s+', ' ', normalize_text(text).lower())


def detect_status_intent(text: str) -> str | None:
    canonical = canonical_text(text)
    for status, patterns in APPROVAL_PATTERNS.items():
        if any(pattern in canonical for pattern in patterns):
            return status
    return None


def extract_numeric_tokens(text: str) -> list[float]:
    return [float(token) for token in re.findall(r'-?\d+(?:\.\d+)?', normalize_text(text))]


def line_matches(expected_line: str, actual_output: str) -> bool:
    try:
        expected_number = float(expected_line)
        return any(abs(number - expected_number) < NUMERIC_TOLERANCE for number in extract_numeric_tokens(actual_output))
    except ValueError:
        expected_status = detect_status_intent(expected_line)
        actual_status = detect_status_intent(actual_output)
        if expected_status is not None and actual_status is not None:
            return expected_status == actual_status
        return canonical_text(expected_line) in canonical_text(actual_output)


def outputs_match_robust(expected: str, actual: str) -> bool:
    expected_normalized = normalize_text(expected)
    actual_normalized = normalize_text(actual)

    if expected_normalized == actual_normalized:
        return True

    return all(line_matches(expected_line, actual_normalized) for expected_line in expected_normalized.split('\n'))


def normalize_choice_key(value: object) -> str:
    return re.sub(r'[^a-z0-9]+', '-', normalize_text(str(value)).lower()).strip('-')


def normalize_objective_template_key(value: object) -> str:
    normalized = normalize_choice_key(value or 'single-choice')
    return OBJECTIVE_TEMPLATE_ALIASES.get(normalized, normalized or 'single-choice')


def _coerce_objective_raw_options(evaluation_plan: dict | None, content_blocks: list[dict] | None) -> list[dict | str]:
    evaluation_plan = evaluation_plan or {}
    candidate_options = evaluation_plan.get('options') or evaluation_plan.get('choices') or evaluation_plan.get('alternatives')
    if candidate_options:
        return list(candidate_options)

    content_blocks = content_blocks or []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        kind = normalize_choice_key(block.get('kind') or block.get('type') or '')
        if kind in {'objective-options', 'objective-options-block', 'options', 'choices', 'alternatives'}:
            block_options = block.get('options') or block.get('choices') or block.get('alternatives') or block.get('items')
            if block_options:
                return list(block_options)
    return []


def _coerce_mode_alias(value: str | None) -> str:
    return normalize_choice_key(value or '')


def _coerce_objective_score_rule(rule: object, evaluation_plan: dict | None) -> dict:
    evaluation_plan = evaluation_plan or {}
    if isinstance(rule, dict):
        result = dict(rule)
    elif rule in (None, ''):
        result = {}
    else:
        result = {'passing_score': rule}

    if 'passing_score' not in result:
        result['passing_score'] = evaluation_plan.get('passing_score', 1.0)
    return result


def _resolve_objective_score_rule(evaluation_plan: dict | None, attempt_mode: str | None) -> dict:
    evaluation_plan = evaluation_plan or {}
    mode_alias = _coerce_mode_alias(attempt_mode)

    for key in OBJECTIVE_SCORE_RULE_KEYS:
        raw_rules = evaluation_plan.get(key)
        if not isinstance(raw_rules, dict):
            continue

        for candidate_key in (attempt_mode, mode_alias, 'default'):
            if candidate_key and candidate_key in raw_rules:
                return _coerce_objective_score_rule(raw_rules[candidate_key], evaluation_plan)

    for key in ('passing_scores', 'passing_score_by_mode', 'mode_passing_scores'):
        raw_scores = evaluation_plan.get(key)
        if not isinstance(raw_scores, dict):
            continue

        for candidate_key in (attempt_mode, mode_alias, 'default'):
            if candidate_key and candidate_key in raw_scores:
                return _coerce_objective_score_rule({'passing_score': raw_scores[candidate_key]}, evaluation_plan)

    return _coerce_objective_score_rule(evaluation_plan.get('passing_score', 1.0), evaluation_plan)


def build_objective_option_catalog(
    evaluation_plan: dict | None,
    content_blocks: list[dict] | None,
) -> list[dict]:
    raw_options = _coerce_objective_raw_options(evaluation_plan, content_blocks)
    catalog: list[dict] = []

    for index, raw_option in enumerate(raw_options, start=1):
        if isinstance(raw_option, str):
            raw_option = {'label': raw_option}
        elif not isinstance(raw_option, dict):
            raw_option = {'label': str(raw_option)}

        raw_key = raw_option.get('key') or raw_option.get('id') or raw_option.get('value') or raw_option.get('slug')
        label = raw_option.get('label') or raw_option.get('title') or raw_option.get('text') or raw_option.get('description')
        if raw_key is None and label is None:
            raw_key = f'option-{index}'
        if raw_key is None:
            raw_key = label
        if label is None:
            label = str(raw_key)

        aliases = []
        for alias in (
            raw_option.get('aliases'),
            raw_option.get('short_label'),
            raw_option.get('shortcut'),
        ):
            if isinstance(alias, (list, tuple)):
                aliases.extend(alias)
            elif alias is not None:
                aliases.append(alias)

        catalog.append(
            {
                'index': index,
                'key': str(raw_key),
                'canonical_key': normalize_choice_key(raw_key),
                'label': str(label),
                'is_correct': bool(raw_option.get('is_correct', False)),
                'explanation': str(raw_option.get('explanation') or raw_option.get('rationale') or ''),
                'misconception_tag': str(raw_option.get('misconception_tag') or raw_option.get('misconception') or raw_option.get('tag') or ''),
                'semantic': str(raw_option.get('semantic') or raw_option.get('option_kind') or raw_option.get('verdict_kind') or ''),
                'aliases': [str(alias) for alias in aliases if alias not in (None, '')],
            }
        )

    return catalog


def extract_objective_correct_options(
    evaluation_plan: dict | None,
    option_catalog: list[dict],
) -> list[str]:
    evaluation_plan = evaluation_plan or {}
    raw_correct = (
        evaluation_plan.get('correct_options')
        or evaluation_plan.get('correct_answers')
        or evaluation_plan.get('correct_answer')
        or evaluation_plan.get('answer_key')
    )

    correct_options: list[str] = []
    if raw_correct is not None:
        if isinstance(raw_correct, (list, tuple, set)):
            raw_values = list(raw_correct)
        else:
            raw_values = [raw_correct]
        for raw_value in raw_values:
            if raw_value in (None, ''):
                continue
            correct_options.append(normalize_choice_key(raw_value))

    if correct_options:
        return list(dict.fromkeys(correct_options))

    fallback = [
        option['canonical_key']
        for option in option_catalog
        if option.get('is_correct')
    ]
    return list(dict.fromkeys(fallback))


def normalize_objective_selections(
    selected_options: list[str] | None,
    response_text: str,
    option_catalog: list[dict],
) -> list[str]:
    alias_to_key: dict[str, str] = {}
    for option in option_catalog:
        for alias in (option['key'], option['label'], *option.get('aliases', [])):
            alias_to_key[normalize_choice_key(alias)] = option['canonical_key']

    raw_selections = [item for item in (selected_options or []) if item not in (None, '')]
    if not raw_selections and response_text.strip():
        raw_selections = [response_text]

    normalized: list[str] = []
    for raw_selection in raw_selections:
        key = alias_to_key.get(normalize_choice_key(raw_selection), normalize_choice_key(raw_selection))
        if key not in normalized:
            normalized.append(key)

    return normalized


def _resolve_expected_output_text(evaluation_plan: dict | None) -> str:
    evaluation_plan = evaluation_plan or {}
    for key in ('expected_output_text', 'expected_output', 'correct_output_text', 'output_text'):
        value = evaluation_plan.get(key)
        if value not in (None, ''):
            return normalize_text(str(value))
    return ''


def _resolve_output_option_keys(
    evaluation_plan: dict | None,
    option_catalog: list[dict],
    correct_options: list[str],
) -> set[str]:
    evaluation_plan = evaluation_plan or {}
    explicit_output_options = (
        evaluation_plan.get('output_option_keys')
        or evaluation_plan.get('output_options')
        or evaluation_plan.get('output_verdict_keys')
        or []
    )
    if not isinstance(explicit_output_options, (list, tuple, set)):
        explicit_output_options = [explicit_output_options]

    resolved_keys = {
        normalize_choice_key(value)
        for value in explicit_output_options
        if value not in (None, '')
    }
    if resolved_keys:
        return resolved_keys

    semantic_keys = {
        option['canonical_key']
        for option in option_catalog
        if normalize_choice_key(option.get('semantic') or '') == 'output'
    }
    if semantic_keys:
        return semantic_keys

    expected_output_text = _resolve_expected_output_text(evaluation_plan)
    if expected_output_text:
        return set(correct_options)

    return set()


def evaluate_objective_selection(
    *,
    evaluation_plan: dict | None,
    content_blocks: list[dict] | None,
    selected_options: list[str] | None,
    response_text: str,
    attempt_mode: str | None = None,
) -> dict:
    evaluation_plan = evaluation_plan or {}
    option_catalog = build_objective_option_catalog(evaluation_plan, content_blocks)
    correct_options = extract_objective_correct_options(evaluation_plan, option_catalog)
    normalized_selected = normalize_objective_selections(selected_options, response_text, option_catalog)
    selected_set = set(normalized_selected)
    correct_set = set(correct_options)
    score_rule = _resolve_objective_score_rule(evaluation_plan, attempt_mode)

    template = normalize_objective_template_key(evaluation_plan.get('template') or evaluation_plan.get('kind') or 'single-choice')
    choice_mode = normalize_choice_key(
        evaluation_plan.get('choice_mode')
        or evaluation_plan.get('selection_mode')
        or ('multiple' if template == 'multi-select' or len(correct_options) > 1 else 'single')
    )
    if choice_mode not in {'single', 'multiple'}:
        choice_mode = 'single'

    option_index = {option['canonical_key']: option for option in option_catalog}
    selected_labels = [option_index[key]['label'] for key in normalized_selected if key in option_index]
    correct_labels = [option_index[key]['label'] for key in correct_options if key in option_index]

    exact_match = bool(selected_set) and selected_set == correct_set and len(selected_set) == len(correct_set)
    if choice_mode == 'single':
        normalized_score = 1.0 if exact_match else 0.0
    else:
        if not correct_set:
            normalized_score = 0.0
        else:
            hits = len(selected_set & correct_set)
            wrong = len(selected_set - correct_set)
            misses = len(correct_set - selected_set)
            raw_score = (hits / len(correct_set)) - (wrong * 0.25) - (misses * 0.0)
            normalized_score = max(0.0, min(1.0, raw_score))

    raw_passing_score = score_rule.get('passing_score', evaluation_plan.get('passing_score', 1.0))
    if raw_passing_score is None:
        raw_passing_score = 1.0
    passing_score = float(raw_passing_score)

    expected_output_text = _resolve_expected_output_text(evaluation_plan)
    output_option_keys = _resolve_output_option_keys(evaluation_plan, option_catalog, correct_options)
    requires_output_text = bool(expected_output_text) and bool(correct_set & output_option_keys) and template == 'compile-runtime-output'
    output_text_matches = None
    if requires_output_text and bool(selected_set & output_option_keys):
        output_text_matches = outputs_match_robust(expected_output_text, response_text)
        if selected_set == correct_set and output_text_matches is False:
            normalized_score = 0.5

    passed = normalized_score >= passing_score and bool(correct_set)
    verdict = 'passed' if passed else ('partial' if normalized_score > 0 else 'failed')
    if not correct_set:
        verdict = 'error'

    option_results = []
    misconception_inference: list[str] = []
    for option in option_catalog:
        selected = option['canonical_key'] in selected_set
        correct = option['canonical_key'] in correct_set
        if selected and not correct:
            tag = option.get('misconception_tag')
            if tag:
                misconception_inference.append(tag)
        option_results.append(
            {
                **option,
                'selected': selected,
                'correct': correct,
            }
        )

    misconception_inference.extend(
        [
            str(tag)
            for tag in (evaluation_plan.get('misconception_tags') or [])
            if tag not in misconception_inference
        ]
    )

    misconception_inference = [tag for tag in dict.fromkeys(misconception_inference) if tag]

    return {
        'template': template,
        'choice_mode': choice_mode,
        'option_catalog': option_catalog,
        'correct_options': correct_options,
        'correct_labels': correct_labels,
        'selected_options': normalized_selected,
        'selected_labels': selected_labels,
        'selected_set': sorted(selected_set),
        'correct_set': sorted(correct_set),
        'score_rule': score_rule,
        'exact_match': exact_match,
        'normalized_score': normalized_score,
        'passing_score': passing_score,
        'passed': passed,
        'verdict': verdict,
        'option_results': option_results,
        'misconception_inference': misconception_inference,
        'requires_output_text': requires_output_text,
        'expected_output_text': expected_output_text,
        'output_text_matches': output_text_matches,
        'response_text': response_text,
    }


def format_execution_results_console(results: list[dict]) -> str:
    return '\n\n'.join(
        [
            '\n'.join(
                [
                    f"Teste {result['index']}: {'PASSOU' if result['passed'] else 'FALHOU'}",
                    f"Entrada: {result['input_data']!r}",
                    f"Esperado: {result['expected_output']}",
                    f"Obtido: {result['actual_output'] or '(sem saída)'}",
                    *([f"Erro: {result['stderr']}"] if result['stderr'] else []),
                ]
            )
            for result in results
        ]
    )
