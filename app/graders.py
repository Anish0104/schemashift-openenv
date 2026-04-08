from __future__ import annotations

from typing import Any, Dict, List

from app.models import APICall, CallResult


SCORE_EPSILON = 0.0001


def _round_score(value: float) -> float:
    return round(float(value), 4)


def _normalize_score(value: float) -> float:
    bounded = min(max(float(value), SCORE_EPSILON), 1.0 - SCORE_EPSILON)
    return _round_score(bounded)


def _extract_version_prefix(path: str) -> str:
    parts = path.split("/")
    if len(parts) > 1 and parts[1] in {"v1", "v2"}:
        return parts[1]
    return ""


def _strip_version_prefix(path: str) -> str:
    parts = path.split("/")
    if len(parts) > 1 and parts[1] in {"v1", "v2"}:
        stripped = "/" + "/".join(parts[2:])
        return stripped if stripped != "/" else "/"
    return path


def _endpoint_score(submitted: str, expected: str) -> float:
    if submitted == expected:
        return 1.0

    if (
        _strip_version_prefix(submitted) == _strip_version_prefix(expected)
        and _extract_version_prefix(submitted) != _extract_version_prefix(expected)
    ):
        return 0.3

    expected_prefix = expected.rsplit("/", 1)[0] if "/" in expected[1:] else expected
    if expected_prefix and submitted.startswith(expected_prefix):
        return 0.5

    return 0.0


def _recursive_value_score(expected: Any, submitted: Any) -> float:
    if expected == submitted:
        return 1.0

    if isinstance(expected, dict) and isinstance(submitted, dict):
        if not expected:
            return 1.0
        matched = 0.0
        for key, expected_value in expected.items():
            if key not in submitted:
                continue
            matched += _recursive_value_score(expected_value, submitted[key])
        return matched / len(expected)

    return 0.0


def _collect_expected_issues(
    expected: Dict[str, Any],
    submitted: Dict[str, Any],
    label: str,
    prefix: str = "",
) -> List[str]:
    issues: List[str] = []
    for key, expected_value in expected.items():
        dotted_key = f"{prefix}.{key}" if prefix else key
        if key not in submitted:
            issues.append(f"{label} missing field {dotted_key}.")
            continue

        submitted_value = submitted[key]
        if isinstance(expected_value, dict) and isinstance(submitted_value, dict):
            issues.extend(
                _collect_expected_issues(
                    expected=expected_value,
                    submitted=submitted_value,
                    label=label,
                    prefix=dotted_key,
                )
            )
            continue

        if expected_value != submitted_value:
            issues.append(
                f"{label} field {dotted_key} incorrect "
                f"(got {submitted_value!r}, expected {expected_value!r})."
            )
    return issues


def grade_call(submitted: APICall, expected: APICall, config: dict) -> dict:
    method_score = 1.0 if submitted.method.upper() == expected.method.upper() else 0.0
    endpoint_score = _endpoint_score(submitted.endpoint, expected.endpoint)

    required_headers = config.get("required_headers", {})
    forbidden_headers = config.get("forbidden_headers", [])
    if required_headers:
        matched_required = sum(
            1
            for key, value in required_headers.items()
            if submitted.headers.get(key) == value
        )
        headers_score = matched_required / len(required_headers)
    else:
        headers_score = 1.0

    for header_name in forbidden_headers:
        if header_name in submitted.headers:
            headers_score = max(0.0, headers_score - 0.3)

    expected_payload = {**expected.body, **expected.params}
    submitted_payload = {**submitted.body, **submitted.params}
    if expected_payload:
        matched_payload = 0.0
        for key, expected_value in expected_payload.items():
            if key not in submitted_payload:
                continue
            matched_payload += _recursive_value_score(expected_value, submitted_payload[key])
        payload_score = matched_payload / len(expected_payload)
    else:
        payload_score = 1.0

    for field_name in config.get("forbidden_body_fields", []):
        if field_name in submitted.body:
            payload_score = max(0.0, payload_score - 0.2)

    for param_name in config.get("forbidden_params", []):
        if param_name in submitted.params:
            payload_score = max(0.0, payload_score - 0.15)

    total = (
        config["method_weight"] * method_score
        + config["endpoint_weight"] * endpoint_score
        + config["headers_weight"] * headers_score
        + config["payload_weight"] * payload_score
    )
    total = min(max(total, 0.0), 1.0)

    feedback_parts: List[str] = []

    if method_score == 1.0:
        feedback_parts.append("Method correct.")
    else:
        feedback_parts.append(
            f"Method wrong (got {submitted.method}, expected {expected.method})."
        )

    if endpoint_score == 1.0:
        feedback_parts.append("Endpoint correct.")
    elif endpoint_score == 0.3:
        feedback_parts.append(
            f"Endpoint has wrong version prefix (got {submitted.endpoint}, "
            f"expected {expected.endpoint})."
        )
    elif endpoint_score == 0.5:
        feedback_parts.append(
            f"Endpoint partially correct (got {submitted.endpoint}, "
            f"expected {expected.endpoint})."
        )
    else:
        feedback_parts.append(
            f"Endpoint wrong (got {submitted.endpoint}, expected {expected.endpoint})."
        )

    header_issues: List[str] = []
    for key, expected_value in required_headers.items():
        submitted_value = submitted.headers.get(key)
        if submitted_value is None:
            header_issues.append(f"Missing required header {key}.")
        elif submitted_value != expected_value:
            header_issues.append(
                f"Header {key} incorrect (got {submitted_value!r}, expected {expected_value!r})."
            )
    for key in forbidden_headers:
        if key in submitted.headers:
            header_issues.append(f"Forbidden header {key} present.")

    if header_issues:
        feedback_parts.append(" ".join(header_issues))
    else:
        feedback_parts.append("Headers correct.")

    payload_issues: List[str] = []
    payload_issues.extend(
        _collect_expected_issues(expected_payload, submitted_payload, "Payload")
    )

    for field_name in config.get("forbidden_body_fields", []):
        if field_name in submitted.body:
            payload_issues.append(f"Body contains forbidden field {field_name}.")

    for param_name in config.get("forbidden_params", []):
        if param_name in submitted.params:
            payload_issues.append(f"Params contains forbidden parameter {param_name}.")

    if payload_issues:
        feedback_parts.append(" ".join(payload_issues))
    else:
        feedback_parts.append("Payload correct.")

    return {
        "method": _normalize_score(method_score),
        "endpoint": _normalize_score(endpoint_score),
        "headers": _normalize_score(headers_score),
        "payload": _normalize_score(payload_score),
        "total": _normalize_score(total),
        "feedback": " ".join(feedback_parts),
    }


def grade_episode(call_results: List[CallResult]) -> float:
    completed = [result for result in call_results if result.completed]
    if not completed:
        return _normalize_score(0.0)
    return _normalize_score(sum(result.score for result in completed) / len(call_results))
