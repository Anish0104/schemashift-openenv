from app.models import APICall


TASK3 = {
    "name": "Analytics Service — Pagination, Enums & Timestamps",
    "description": (
        "Rewrite analytics-service v1 calls into v2 by converting auth, replacing "
        "page-based pagination, renaming enum values, and transforming timestamps."
    ),
    "migration_guide": (
        "Analytics Service migration rules:\n"
        "- Auth changes: X-Token: {key} -> Authorization: Bearer {same key value}\n"
        "- Sending X-Token in v2 is forbidden and penalized\n"
        "- Pagination changes completely:\n"
        "  * v1: ?page=1&per_page=10\n"
        "  * v2: ?cursor=null&limit=10\n"
        "  * page and per_page are forbidden params in v2\n"
        "- Status enum renames:\n"
        "  * active -> enabled\n"
        "  * inactive -> disabled\n"
        "  * pending -> queued\n"
        "  * archived -> retired\n"
        "- Timestamp format: Unix integer -> ISO 8601 date string\n"
        "  * start_ts -> start_date\n"
        "  * end_ts -> end_date\n"
        "  * 1704067200 = 2024-01-01\n"
        "  * 1706745600 = 2024-02-01\n"
        "- Status moves from query param -> request body\n"
        "- Query param metric renames to type\n"
        "- Query param report_id moves to URL path as /v2/reports/{id}/export\n"
        "- Endpoint mapping:\n"
        "  * GET /v1/reports?page=N&per_page=N -> GET /v2/reports?cursor=null&limit=N\n"
        "  * POST /v1/reports -> POST /v2/reports\n"
        "  * PUT /v1/reports/{id}?status=S -> PUT /v2/reports/{id} with status in body\n"
        "  * GET /v1/metrics?metric=M&page=N&per_page=N -> GET /v2/metrics?type=M&cursor=null&limit=N\n"
        "  * DELETE /v1/reports/{id} -> DELETE /v2/reports/{id}\n"
        "  * GET /v1/export?report_id=X -> GET /v2/reports/X/export"
    ),
    "v1_calls": [
        APICall(
            method="GET",
            endpoint="/v1/reports",
            headers={"X-Token": "analytics_token_99"},
            params={"page": "1", "per_page": "10"},
            body={},
        ),
        APICall(
            method="POST",
            endpoint="/v1/reports",
            headers={
                "X-Token": "analytics_token_99",
                "Content-Type": "application/json",
            },
            params={},
            body={
                "title": "Q1 Revenue",
                "start_ts": 1704067200,
                "end_ts": 1706745600,
                "status": "active",
            },
        ),
        APICall(
            method="PUT",
            endpoint="/v1/reports/5",
            headers={"X-Token": "analytics_token_99"},
            params={"status": "inactive"},
            body={},
        ),
        APICall(
            method="GET",
            endpoint="/v1/metrics",
            headers={"X-Token": "analytics_token_99"},
            params={"metric": "revenue", "page": "1", "per_page": "5"},
            body={},
        ),
        APICall(
            method="DELETE",
            endpoint="/v1/reports/5",
            headers={"X-Token": "analytics_token_99"},
            params={},
            body={},
        ),
        APICall(
            method="GET",
            endpoint="/v1/export",
            headers={"X-Token": "analytics_token_99"},
            params={"report_id": "5"},
            body={},
        ),
    ],
    "expected_calls": [
        APICall(
            method="GET",
            endpoint="/v2/reports",
            headers={"Authorization": "Bearer analytics_token_99"},
            params={"cursor": "null", "limit": "10"},
            body={},
        ),
        APICall(
            method="POST",
            endpoint="/v2/reports",
            headers={
                "Authorization": "Bearer analytics_token_99",
                "Content-Type": "application/json",
            },
            params={},
            body={
                "title": "Q1 Revenue",
                "start_date": "2024-01-01",
                "end_date": "2024-02-01",
                "status": "enabled",
            },
        ),
        APICall(
            method="PUT",
            endpoint="/v2/reports/5",
            headers={"Authorization": "Bearer analytics_token_99"},
            params={},
            body={"status": "disabled"},
        ),
        APICall(
            method="GET",
            endpoint="/v2/metrics",
            headers={"Authorization": "Bearer analytics_token_99"},
            params={"type": "revenue", "cursor": "null", "limit": "5"},
            body={},
        ),
        APICall(
            method="DELETE",
            endpoint="/v2/reports/5",
            headers={"Authorization": "Bearer analytics_token_99"},
            params={},
            body={},
        ),
        APICall(
            method="GET",
            endpoint="/v2/reports/5/export",
            headers={"Authorization": "Bearer analytics_token_99"},
            params={},
            body={},
        ),
    ],
    "grading_config": {
        "method_weight": 0.20,
        "endpoint_weight": 0.35,
        "headers_weight": 0.20,
        "payload_weight": 0.25,
        "required_headers": {"Authorization": "Bearer analytics_token_99"},
        "forbidden_headers": ["X-Token"],
        "forbidden_body_fields": ["start_ts", "end_ts"],
        "forbidden_params": ["page", "per_page", "metric", "report_id"],
    },
    "max_steps": 20,
}
