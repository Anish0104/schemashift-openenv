from app.models import APICall


TASK2 = {
    "name": "Order Service — Auth & Payload Restructuring",
    "description": (
        "Rewrite order-service v1 calls into v2 by converting API-key auth to "
        "Bearer auth, moving identifiers into paths, and nesting create-order payloads."
    ),
    "migration_guide": (
        "Order Service migration rules:\n"
        "- Auth changes: X-API-Key: {key} -> Authorization: Bearer {same key value}\n"
        "- Sending X-API-Key in v2 is forbidden and penalized\n"
        "- IDs move from query params to URL path\n"
        "- Endpoint mapping:\n"
        "  * GET /v1/orders?order_id=X -> GET /v2/orders/X\n"
        "  * POST /v1/create_order -> POST /v2/orders\n"
        "  * PUT /v1/update_order?order_id=X -> PUT /v2/orders/X\n"
        "  * GET /v1/customer_orders?customer_id=X -> GET /v2/customers/X/orders\n"
        "  * DELETE /v1/cancel_order?order_id=X -> DELETE /v2/orders/X\n"
        "- POST body restructures flat -> nested:\n"
        "  * v1: {product_id, quantity, customer_id, address}\n"
        "  * v2: {item: {product_id, quantity}, customer: {id, shipping_address}}\n"
        "- customer_id becomes customer.id\n"
        "- address becomes customer.shipping_address\n"
        "- Status update body stays flat: {status: \"processing\"}"
    ),
    "v1_calls": [
        APICall(
            method="GET",
            endpoint="/v1/orders",
            headers={"X-API-Key": "shop_key_xyz"},
            params={"order_id": "101"},
            body={},
        ),
        APICall(
            method="POST",
            endpoint="/v1/create_order",
            headers={
                "X-API-Key": "shop_key_xyz",
                "Content-Type": "application/json",
            },
            params={},
            body={
                "product_id": 7,
                "quantity": 3,
                "customer_id": 5,
                "address": "123 Main St",
            },
        ),
        APICall(
            method="PUT",
            endpoint="/v1/update_order",
            headers={
                "X-API-Key": "shop_key_xyz",
                "Content-Type": "application/json",
            },
            params={"order_id": "101"},
            body={"status": "processing"},
        ),
        APICall(
            method="GET",
            endpoint="/v1/customer_orders",
            headers={"X-API-Key": "shop_key_xyz"},
            params={"customer_id": "5"},
            body={},
        ),
        APICall(
            method="DELETE",
            endpoint="/v1/cancel_order",
            headers={"X-API-Key": "shop_key_xyz"},
            params={"order_id": "101"},
            body={},
        ),
    ],
    "expected_calls": [
        APICall(
            method="GET",
            endpoint="/v2/orders/101",
            headers={"Authorization": "Bearer shop_key_xyz"},
            params={},
            body={},
        ),
        APICall(
            method="POST",
            endpoint="/v2/orders",
            headers={
                "Authorization": "Bearer shop_key_xyz",
                "Content-Type": "application/json",
            },
            params={},
            body={
                "item": {"product_id": 7, "quantity": 3},
                "customer": {"id": 5, "shipping_address": "123 Main St"},
            },
        ),
        APICall(
            method="PUT",
            endpoint="/v2/orders/101",
            headers={
                "Authorization": "Bearer shop_key_xyz",
                "Content-Type": "application/json",
            },
            params={},
            body={"status": "processing"},
        ),
        APICall(
            method="GET",
            endpoint="/v2/customers/5/orders",
            headers={"Authorization": "Bearer shop_key_xyz"},
            params={},
            body={},
        ),
        APICall(
            method="DELETE",
            endpoint="/v2/orders/101",
            headers={"Authorization": "Bearer shop_key_xyz"},
            params={},
            body={},
        ),
    ],
    "grading_config": {
        "method_weight": 0.20,
        "endpoint_weight": 0.35,
        "headers_weight": 0.20,
        "payload_weight": 0.25,
        "required_headers": {"Authorization": "Bearer shop_key_xyz"},
        "forbidden_headers": ["X-API-Key"],
        "forbidden_body_fields": ["customer_id", "address"],
        "forbidden_params": [],
    },
    "max_steps": 15,
}
