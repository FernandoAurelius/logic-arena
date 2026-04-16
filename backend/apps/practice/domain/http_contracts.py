from __future__ import annotations

import json
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
    if expected_type == 'object' or (expected_type is None and any(key in schema for key in ('properties', 'required'))):
        if not isinstance(value, dict):
            return [f'{path}: esperado objeto, obtido {type(value).__name__}']
        for field in schema.get('required', []):
            if field not in value:
                issues.append(f'{path}: campo obrigatório ausente: {field}')
        for field, field_schema in (schema.get('properties') or {}).items():
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


def _normalize_contract_payload(response_text: str) -> dict[str, Any]:
    parsed = try_parse_json(response_text)
    if isinstance(parsed, dict):
        return parsed
    return {}


def evaluate_http_contract_submission(
    *,
    workspace_spec: dict[str, Any] | None,
    evaluation_plan: dict[str, Any] | None,
    response_text: str,
) -> dict[str, Any]:
    workspace_spec = workspace_spec or {}
    evaluation_plan = evaluation_plan or {}
    contract = workspace_spec.get('contract') if isinstance(workspace_spec.get('contract'), dict) else {}
    request_spec = contract.get('request') if isinstance(contract.get('request'), dict) else {}
    response_spec = contract.get('response') if isinstance(contract.get('response'), dict) else {}
    payload = _normalize_contract_payload(response_text)

    request_payload = payload.get('request') if isinstance(payload.get('request'), dict) else payload
    observed_payload = payload.get('observed_response') if isinstance(payload.get('observed_response'), dict) else payload

    actual_method = str(request_payload.get('request_method') or request_payload.get('method') or '').upper()
    actual_path = str(request_payload.get('request_path') or request_payload.get('path') or '')
    actual_request_headers = normalize_headers(request_payload.get('request_headers') or request_payload.get('headers'))
    actual_request_body = try_parse_json(request_payload.get('request_body') or request_payload.get('body'))

    actual_status = observed_payload.get('response_status') or observed_payload.get('status')
    actual_headers = normalize_headers(observed_payload.get('response_headers') or observed_payload.get('headers'))
    actual_body = try_parse_json(observed_payload.get('response_body') or observed_payload.get('body'))

    expected_method = str(request_spec.get('method') or 'GET').upper()
    expected_path = str(request_spec.get('path') or '/')
    expected_request_headers = normalize_headers(request_spec.get('headers'))
    expected_request_body = request_spec.get('body')
    expected_status = response_spec.get('status_code', response_spec.get('status'))
    expected_headers = normalize_headers(response_spec.get('headers'))
    expected_body = response_spec.get('body')
    expected_schema = response_spec.get('body_schema') or response_spec.get('schema')

    checks: list[dict[str, Any]] = []
    divergences: list[str] = []

    def add_check(name: str, expected: Any, actual: Any, passed: bool, detail: str | None = None) -> None:
        checks.append(
            {
                'check': name,
                'expected': expected,
                'actual': actual,
                'passed': passed,
                'detail': detail or '',
            }
        )
        if not passed:
            divergences.append(detail or f'{name}: esperado {expected!r}, obtido {actual!r}')

    add_check(
        'request_method',
        expected_method,
        actual_method,
        actual_method == expected_method,
        None if actual_method == expected_method else f'método esperado {expected_method}, obtido {actual_method or "(vazio)"}',
    )
    add_check(
        'request_path',
        expected_path,
        actual_path,
        actual_path == expected_path,
        None if actual_path == expected_path else f'path esperado {expected_path}, obtido {actual_path or "(vazio)"}',
    )

    if expected_request_headers:
        header_issues = []
        for key, expected_value in expected_request_headers.items():
            actual_value = actual_request_headers.get(key)
            if actual_value != expected_value:
                header_issues.append(f'{key}: esperado {expected_value!r}, obtido {actual_value!r}')
        add_check('request_headers', expected_request_headers, actual_request_headers, not header_issues, '; '.join(header_issues) if header_issues else None)

    if expected_request_body is not None:
        request_body_passed = canonicalize_json(actual_request_body) == canonicalize_json(expected_request_body)
        add_check(
            'request_body',
            expected_request_body,
            actual_request_body,
            request_body_passed,
            None if request_body_passed else 'corpo da request diferente do contrato',
        )

    if expected_status is not None:
        add_check(
            'response_status',
            expected_status,
            actual_status,
            actual_status == expected_status,
            None if actual_status == expected_status else f'status esperado {expected_status}, obtido {actual_status!r}',
        )

    if expected_headers:
        header_issues = []
        for key, expected_value in expected_headers.items():
            actual_value = actual_headers.get(key)
            if actual_value != expected_value:
                header_issues.append(f'{key}: esperado {expected_value!r}, obtido {actual_value!r}')
        add_check('response_headers', expected_headers, actual_headers, not header_issues, '; '.join(header_issues) if header_issues else None)

    if expected_body is not None:
        body_passed = canonicalize_json(actual_body) == canonicalize_json(expected_body)
        add_check(
            'response_body',
            expected_body,
            actual_body,
            body_passed,
            None if body_passed else 'corpo da response diferente do contrato',
        )

    if expected_schema is not None:
        schema_issues = validate_json_schema(expected_schema, actual_body)
        add_check(
            'response_schema',
            expected_schema,
            actual_body,
            not schema_issues,
            '; '.join(schema_issues) if schema_issues else None,
        )

    passed_tests = sum(1 for check in checks if check['passed'])
    total_tests = len(checks)
    normalized_score = (passed_tests / total_tests) if total_tests else 0.0
    verdict = 'passed' if total_tests and passed_tests == total_tests else ('partial' if passed_tests > 0 else 'failed')

    console_lines = [
        f"Contrato HTTP: {'PASSOU' if verdict == 'passed' else 'FALHOU'} ({passed_tests}/{total_tests})",
        f'Request observada: {actual_method or "(vazio)"} {actual_path or "(vazio)"}',
    ]
    if divergences:
        console_lines.append('Divergências:')
        console_lines.extend(f'- {item}' for item in divergences)

    return {
        'template': 'http-contract',
        'passed': verdict == 'passed',
        'normalized_score': normalized_score,
        'verdict': verdict,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'checks': checks,
        'results': checks,
        'divergences': divergences,
        'console_output': '\n'.join(console_lines),
        'request': {
            'method': expected_method,
            'path': expected_path,
            'headers': expected_request_headers,
            'body': expected_request_body,
        },
        'expected_response': {
            'status_code': expected_status,
            'headers': expected_headers,
            'body': expected_body,
            'body_schema': expected_schema,
        },
        'observed_request': {
            'method': actual_method,
            'path': actual_path,
            'headers': actual_request_headers,
            'body': actual_request_body,
        },
        'observed_response': {
            'status_code': actual_status,
            'headers': actual_headers,
            'body': actual_body,
        },
        'payload': payload,
    }
