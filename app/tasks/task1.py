from app.models import APICall


TASK1 = {
    "name": "User Service — Field & Path Migration",
    "description": (
        "Rewrite user-service v1 calls into v2 by moving IDs into URL paths, "
        "renaming endpoints, and updating request body field names."
    ),
    "migration_guide": (
        "User Service migration rules:\n"
        "- IDs move from query params to URL path (?user_id=42 -> /v2/users/42)\n"
        "- Prefix changes from /v1 to /v2\n"
        "- Endpoint names simplify:\n"
        "  * /v1/users?user_id=X -> /v2/users/X\n"
        "  * /v1/create_user -> /v2/users\n"
        "  * /v1/remove_user?user_id=X -> /v2/users/X\n"
        "- Body field renames: name->full_name, email->email_address, phone->phone_number\n"
        "- Auth unchanged: X-API-Key header stays the same"
    ),
    "v1_calls": [
        APICall(
            method="GET",
            endpoint="/v1/users",
            headers={"X-API-Key": "key_abc123"},
            params={"user_id": "42"},
            body={},
        ),
        APICall(
            method="POST",
            endpoint="/v1/create_user",
            headers={
                "X-API-Key": "key_abc123",
                "Content-Type": "application/json",
            },
            params={},
            body={
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "phone": "555-1234",
            },
        ),
        APICall(
            method="DELETE",
            endpoint="/v1/remove_user",
            headers={"X-API-Key": "key_abc123"},
            params={"user_id": "42"},
            body={},
        ),
    ],
    "expected_calls": [
        APICall(
            method="GET",
            endpoint="/v2/users/42",
            headers={"X-API-Key": "key_abc123"},
            params={},
            body={},
        ),
        APICall(
            method="POST",
            endpoint="/v2/users",
            headers={
                "X-API-Key": "key_abc123",
                "Content-Type": "application/json",
            },
            params={},
            body={
                "full_name": "Alice Johnson",
                "email_address": "alice@example.com",
                "phone_number": "555-1234",
            },
        ),
        APICall(
            method="DELETE",
            endpoint="/v2/users/42",
            headers={"X-API-Key": "key_abc123"},
            params={},
            body={},
        ),
    ],
    "grading_config": {
        "method_weight": 0.20,
        "endpoint_weight": 0.35,
        "headers_weight": 0.20,
        "payload_weight": 0.25,
        "required_headers": {"X-API-Key": "key_abc123"},
        "forbidden_headers": [],
        "forbidden_body_fields": ["name", "email", "phone"],
        "forbidden_params": [],
    },
    "max_steps": 10,
}
