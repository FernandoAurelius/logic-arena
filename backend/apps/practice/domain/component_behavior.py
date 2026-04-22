from __future__ import annotations

import json
import re
from typing import Any


def _normalize_text(value: Any) -> str:
    return re.sub(r'\s+', ' ', str(value or '').strip().lower())


def _normalize_identifier(value: Any) -> str:
    return re.sub(r'[^a-z0-9]+', '', _normalize_text(value))


def _extract_section(source_code: str, tag: str) -> str:
    pattern = rf'<{tag}\b[^>]*>(.*?)</{tag}>'
    match = re.search(pattern, source_code, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else ''


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if isinstance(value, dict):
        return [str(key) for key in value.keys() if str(key).strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _parse_observation_payload(response_text: str) -> dict[str, Any]:
    if not response_text.strip():
        return {}
    try:
        parsed = json.loads(response_text)
        return parsed if isinstance(parsed, dict) else {'observed_snapshot': parsed}
    except json.JSONDecodeError:
        return {'raw_response_text': response_text}


def _build_source_signals(source_code: str) -> dict[str, list[str]]:
    script = _extract_section(source_code, 'script') or source_code
    template = _extract_section(source_code, 'template') or source_code

    props = re.findall(r'defineProps\s*\(\s*\{([^}]*)\}', script, flags=re.IGNORECASE | re.DOTALL)
    props.extend(re.findall(r'props\s*:\s*\{([^}]*)\}', script, flags=re.IGNORECASE | re.DOTALL))

    state = re.findall(
        r'(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:ref|reactive|computed|shallowRef)\(',
        script,
    )
    state.extend(
        re.findall(r'data\s*\(\s*\)\s*\{.*?return\s*\{\s*([^}]*)\}', script, flags=re.IGNORECASE | re.DOTALL)
    )

    events = re.findall(r'defineEmits\s*\(\s*\[([^\]]*)\]', script, flags=re.IGNORECASE | re.DOTALL)
    events.extend(re.findall(r'emit\s*\(\s*[\'"]([^\'"]+)[\'"]', script, flags=re.IGNORECASE))
    events.extend(re.findall(r'@([a-zA-Z0-9:_-]+)=', template, flags=re.IGNORECASE))

    render = re.findall(r'v-(?:if|show|for)\s*=\s*[\'"]([^\'"]+)[\'"]', template, flags=re.IGNORECASE)
    render.extend(re.findall(r'>\s*([^<>{}][^<>{}]*)\s*<', template, flags=re.DOTALL))
    render.extend(re.findall(r'(?:aria-label|role|class|data-test)\s*=\s*[\'"]([^\'"]+)[\'"]', template, flags=re.IGNORECASE))

    dom = re.findall(r'(?:aria-label|role|class|data-test)\s*=\s*[\'"]([^\'"]+)[\'"]', template, flags=re.IGNORECASE)
    dom.extend(re.findall(r'<([A-Za-z][A-Za-z0-9-]*)\b', template))

    forbidden = []
    source_lower = _normalize_text(source_code)
    if 'console.log' in source_lower:
        forbidden.append('console.log')
    if 'alert(' in source_lower:
        forbidden.append('alert(')

    return {
        'props': sorted({item.strip() for item in props if item.strip()}),
        'state': sorted({item.strip() for item in state if item.strip()}),
        'events': sorted({item.strip() for item in events if item.strip()}),
        'render': sorted({item.strip() for item in render if item.strip()}),
        'dom': sorted({item.strip() for item in dom if item.strip()}),
        'forbidden': sorted({item.strip() for item in forbidden if item.strip()}),
    }


def _observation_text_bundle(observation: dict[str, Any]) -> str:
    chunks: list[str] = []
    for key, value in observation.items():
        if isinstance(value, (dict, list)):
            chunks.append(json.dumps(value, ensure_ascii=False))
        else:
            chunks.append(str(value))
    return '\n'.join(chunks)


def _match_token(token: str, source_code: str, observation: dict[str, Any]) -> bool:
    cleaned = str(token).strip()
    if not cleaned:
        return False
    corpus = '\n'.join([source_code, _observation_text_bundle(observation)])
    normalized_token = _normalize_identifier(cleaned)
    normalized_corpus = _normalize_identifier(corpus)
    return normalized_token in normalized_corpus or _normalize_text(cleaned) in _normalize_text(corpus)


def _check_requirement(category: str, token: str, source_code: str, observation: dict[str, Any]) -> dict[str, Any]:
    matched = _match_token(token, source_code, observation)
    return {
        'check': f'{category}:{token}',
        'expected': token,
        'actual': 'presente' if matched else 'ausente',
        'passed': matched,
        'detail': '' if matched else f'{category} esperado não observado: {token}',
    }


def evaluate_component_behavior_submission(
    *,
    workspace_spec: dict[str, Any] | None,
    evaluation_plan: dict[str, Any] | None,
    source_code: str,
    response_text: str,
) -> dict[str, Any]:
    workspace_spec = workspace_spec or {}
    evaluation_plan = evaluation_plan or {}
    component_contract = (
        workspace_spec.get('component_contract')
        if isinstance(workspace_spec.get('component_contract'), dict)
        else {}
    )
    observation = _parse_observation_payload(response_text)
    signals = _build_source_signals(source_code)

    required_props = _coerce_string_list(component_contract.get('expected_props') or evaluation_plan.get('required_props'))
    required_state = _coerce_string_list(component_contract.get('expected_state') or evaluation_plan.get('required_state'))
    required_events = _coerce_string_list(component_contract.get('expected_events') or evaluation_plan.get('required_events'))
    required_render = _coerce_string_list(component_contract.get('expected_render') or evaluation_plan.get('required_render'))
    required_dom = _coerce_string_list(component_contract.get('expected_dom') or evaluation_plan.get('required_dom'))
    forbidden_tokens = _coerce_string_list(component_contract.get('forbidden_tokens') or evaluation_plan.get('forbidden_tokens'))

    checks: list[dict[str, Any]] = []
    for token in required_props:
        checks.append(_check_requirement('props', token, source_code, observation))
    for token in required_state:
        checks.append(_check_requirement('state', token, source_code, observation))
    for token in required_events:
        checks.append(_check_requirement('events', token, source_code, observation))
    for token in required_render:
        checks.append(_check_requirement('render', token, source_code, observation))
    for token in required_dom:
        checks.append(_check_requirement('dom', token, source_code, observation))

    for token in forbidden_tokens:
        hit = _match_token(token, source_code, observation)
        checks.append(
            {
                'check': f'forbidden:{token}',
                'expected': 'não utilizar',
                'actual': 'presente' if hit else 'ausente',
                'passed': not hit,
                'detail': '' if not hit else f'token proibido encontrado: {token}',
            }
        )

    passed_tests = sum(1 for check in checks if check['passed'])
    total_tests = len(checks)
    normalized_score = (passed_tests / total_tests) if total_tests else 0.0
    verdict = 'passed' if total_tests and passed_tests == total_tests else ('partial' if passed_tests > 0 else 'failed')
    divergences = [check['detail'] for check in checks if not check['passed'] and check.get('detail')]

    console_lines = [
        f"Comportamento de componente: {'PASSOU' if verdict == 'passed' else 'FALHOU'} ({passed_tests}/{total_tests})",
    ]
    if divergences:
        console_lines.append('Divergências:')
        console_lines.extend(f'- {item}' for item in divergences)

    return {
        'template': 'component-behavior',
        'passed': verdict == 'passed',
        'normalized_score': normalized_score,
        'verdict': verdict,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'checks': checks,
        'results': checks,
        'divergences': divergences,
        'console_output': '\n'.join(console_lines),
        'component_contract': component_contract,
        'source_summary': signals,
        'observation': observation,
        'payload': observation,
    }
