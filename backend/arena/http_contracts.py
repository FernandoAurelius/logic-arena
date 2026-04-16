from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


def normalize_headers(headers: dict[str, Any] | None) -> dict[str, str]:
    if not headers:
        return {}
    return {str(key).strip().lower(): str(value).strip() for key, value in headers.items()}


def try_parse_json(value: str | dict[str, Any] | list[Any] | None) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value

    candidate = value.strip()
    if not candidate:
        return None

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return value


def canonicalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): canonicalize_json(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [canonicalize_json(item) for item in value]
    return value


def schema_type_name(schema: dict[str, Any]) -> str | None:
    raw_type = schema.get('type')
    if isinstance(raw_type, str):
        return raw_type
    if isinstance(raw_type, list):
        return raw_type[0] if raw_type else None
    return None


def validate_json_schema(schema: Any, value: Any, path: str = '$') -> list[str]:
    issues: list[str] = []

    if schema is None:
        return issues

    if isinstance(schema, list):
        if not isinstance(value, list):
            return [f'{path}: esperado array, obtido {type(value).__name__}']
        if schema:
            for index, item in enumerate(value):
                issues.extend(validate_json_schema(schema[0], item, f'{path}[{index}]'))
        return issues

    if not isinstance(schema, dict):
        return issues

    expected_type = schema_type_name(schema)
    if expected_type == 'object' or (expected_type is None and any(key in schema for key in ('properties', 'required', 'additionalProperties'))):
        if not isinstance(value, dict):
            return [f'{path}: esperado objeto, obtido {type(value).__name__}']
        required = schema.get('required', [])
        for field in required:
            if field not in value:
                issues.append(f'{path}: campo obrigatório ausente: {field}')
        properties = schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in value:
                issues.extend(validate_json_schema(field_schema, value[field], f'{path}.{field}'))
        return issues

    if expected_type == 'array':
        if not isinstance(value, list):
            return [f'{path}: esperado array, obtido {type(value).__name__}']
        item_schema = schema.get('items')
        if item_schema is not None:
            for index, item in enumerate(value):
                issues.extend(validate_json_schema(item_schema, item, f'{path}[{index}]'))
        return issues

    if expected_type == 'string':
        if not isinstance(value, str):
            return [f'{path}: esperado string, obtido {type(value).__name__}']
        return issues

    if expected_type == 'integer':
        if not isinstance(value, int) or isinstance(value, bool):
            return [f'{path}: esperado integer, obtido {type(value).__name__}']
        return issues

    if expected_type == 'number':
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return [f'{path}: esperado number, obtido {type(value).__name__}']
        return issues

    if expected_type == 'boolean':
        if not isinstance(value, bool):
            return [f'{path}: esperado boolean, obtido {type(value).__name__}']
        return issues

    if expected_type == 'null':
        if value is not None:
            return [f'{path}: esperado null, obtido {type(value).__name__}']
        return issues

    enum_values = schema.get('enum')
    if enum_values is not None and value not in enum_values:
        issues.append(f'{path}: valor {value!r} fora do enum esperado {enum_values!r}')

    return issues


@dataclass(frozen=True)
class HttpContractEvaluation:
    results: list[dict[str, Any]]
    evidence_bundle: dict[str, Any]
    console_output: str
    passed_tests: int
    total_tests: int
    status: str


def evaluate_http_contract(
    *,
    family_key: str,
    surface_key: str,
    request_spec: dict[str, Any],
    response_spec: dict[str, Any],
    submission_payload: dict[str, Any],
) -> HttpContractEvaluation:
    expected_request = request_spec or {}
    expected_response = response_spec or {}
    actual_status = submission_payload.get('response_status')
    actual_headers = normalize_headers(submission_payload.get('response_headers'))
    actual_body_raw = submission_payload.get('response_body', '')
    actual_body = try_parse_json(actual_body_raw)

    expected_status = expected_response.get('status_code')
    if expected_status is None:
        expected_status = expected_response.get('status')

    expected_headers = normalize_headers(expected_response.get('headers'))
    expected_body = expected_response.get('body')
    expected_schema = expected_response.get('body_schema')

    checks: list[dict[str, Any]] = []
    divergences: list[str] = []

    def add_check(name: str, expected: Any, actual: Any, passed: bool, detail: str | None = None) -> None:
        item = {
            'check': name,
            'expected': expected,
            'actual': actual,
            'passed': passed,
        }
        if detail:
            item['detail'] = detail
        checks.append(item)
        if not passed:
            if detail:
                divergences.append(f'{name}: {detail}')
            else:
                divergences.append(f'{name}: esperado {expected!r}, obtido {actual!r}')

    if expected_status is not None:
        add_check(
            'status',
            expected_status,
            actual_status,
            actual_status == expected_status,
            None if actual_status == expected_status else f'esperado {expected_status}, obtido {actual_status!r}',
        )

    if expected_headers:
        header_issues: list[str] = []
        for key, expected_value in expected_headers.items():
            actual_value = actual_headers.get(key)
            if actual_value != expected_value:
                header_issues.append(f'{key}: esperado {expected_value!r}, obtido {actual_value!r}')
        add_check(
            'headers',
            expected_headers,
            actual_headers,
            not header_issues,
            None if not header_issues else '; '.join(header_issues),
        )

    if expected_body is not None:
        if isinstance(expected_body, (dict, list)):
            body_passed = canonicalize_json(actual_body) == canonicalize_json(expected_body)
            add_check(
                'body',
                expected_body,
                actual_body,
                body_passed,
                None if body_passed else 'corpo JSON diferente do esperado',
            )
        else:
            actual_text = actual_body_raw if isinstance(actual_body_raw, str) else json.dumps(actual_body_raw, ensure_ascii=False)
            expected_text = str(expected_body)
            body_passed = str(actual_text).strip() == expected_text.strip()
            add_check(
                'body',
                expected_text,
                actual_text,
                body_passed,
                None if body_passed else 'corpo textual diferente do esperado',
            )

    if expected_schema is not None:
        schema_issues = validate_json_schema(expected_schema, actual_body)
        add_check(
            'body_schema',
            expected_schema,
            actual_body,
            not schema_issues,
            None if not schema_issues else '; '.join(schema_issues),
        )

    passed_tests = sum(1 for result in checks if result['passed'])
    total_tests = len(checks)
    passed = total_tests > 0 and passed_tests == total_tests
    status = 'passed' if passed else 'failed'
    console_lines = [
        f"Contrato HTTP: {'PASSOU' if passed else 'FALHOU'} ({passed_tests}/{total_tests})",
    ]
    if expected_request:
        console_lines.append(f"Request esperada: {json.dumps(expected_request, ensure_ascii=False, default=str)}")
    if expected_response:
        console_lines.append(f"Response esperada: {json.dumps(expected_response, ensure_ascii=False, default=str)}")
    console_lines.append(f"Response obtida: {json.dumps({'status': actual_status, 'headers': actual_headers, 'body': actual_body}, ensure_ascii=False, default=str)}")
    if divergences:
        console_lines.append('Divergências:')
        console_lines.extend(f'- {item}' for item in divergences)

    evidence_bundle = {
        'family_key': family_key,
        'surface_key': surface_key,
        'request': expected_request,
        'expected_response': expected_response,
        'observed_response': {
            'status': actual_status,
            'headers': actual_headers,
            'body': actual_body,
        },
        'checks': checks,
        'divergences': divergences,
        'passed_checks': passed_tests,
        'total_checks': total_tests,
    }

    return HttpContractEvaluation(
        results=checks,
        evidence_bundle=evidence_bundle,
        console_output='\n'.join(console_lines).strip(),
        passed_tests=passed_tests,
        total_tests=total_tests,
        status=status,
    )
