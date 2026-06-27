"""Custom assertion helpers for comprehensive API response validation.

Covers both response formats (Bare and Envelope) used in the system.
"""

from typing import Any, List, Optional, Union


def assert_envelope_response(
    resp_data: dict,
    expected_code: int = 200,
    expected_message: Optional[str] = None,
    has_data: bool = True,
) -> dict:
    """Assert response follows Envelope format: {code, message, data?, ...}

    Used by: /auth/login, /users, /rbac
    """
    assert isinstance(resp_data, dict), f"Response should be dict, got {type(resp_data)}"
    assert "code" in resp_data, f"Envelope response missing 'code' field: {resp_data}"
    assert "message" in resp_data, f"Envelope response missing 'message' field: {resp_data}"
    assert resp_data["code"] == expected_code, (
        f"Expected code={expected_code}, got {resp_data['code']}: {resp_data.get('message')}"
    )
    if expected_message:
        assert resp_data["message"] == expected_message, (
            f"Expected message='{expected_message}', got '{resp_data['message']}'"
        )
    if has_data:
        assert "data" in resp_data, f"Envelope response missing 'data' field: {resp_data}"
    return resp_data.get("data")


def assert_bare_response(
    resp_data: dict,
    expected_total: Optional[int] = None,
    expected_page: Optional[int] = None,
    expected_page_size: Optional[int] = None,
    min_items: int = 0,
) -> List[Any]:
    """Assert response follows Bare list format: {total, page, page_size, items}

    Used by: /supported-villages, /funds, /work-logs
    """
    assert isinstance(resp_data, dict), f"Bare response should be dict, got {type(resp_data)}"
    assert "total" in resp_data, f"Bare response missing 'total': {resp_data}"
    assert "page" in resp_data, f"Bare response missing 'page': {resp_data}"
    assert "page_size" in resp_data, f"Bare response missing 'page_size': {resp_data}"
    assert "items" in resp_data, f"Bare response missing 'items': {resp_data}"
    assert isinstance(resp_data["items"], list), f"items should be list, got {type(resp_data['items'])}"

    if expected_total is not None:
        assert resp_data["total"] == expected_total, (
            f"Expected total={expected_total}, got {resp_data['total']}"
        )
    if expected_page is not None:
        assert resp_data["page"] == expected_page, (
            f"Expected page={expected_page}, got {resp_data['page']}"
        )
    if expected_page_size is not None:
        assert resp_data["page_size"] == expected_page_size, (
            f"Expected page_size={expected_page_size}, got {resp_data['page_size']}"
        )
    assert len(resp_data["items"]) >= min_items, (
        f"Expected at least {min_items} items, got {len(resp_data['items'])}"
    )
    return resp_data["items"]


def assert_pagination(
    resp_data: dict,
    page: int = 1,
    page_size: int = 10,
    total: Optional[int] = None,
):
    """Shorthand: assert paginated response with expected params."""
    assert "meta" in resp_data, f"Response missing 'meta': {resp_data}"
    pagination = resp_data["meta"].get("pagination", {})
    assert pagination.get("page") == page, f"Expected page={page}, got {pagination.get('page')}"
    assert pagination.get("page_size") == page_size, f"Expected page_size={page_size}, got {pagination.get('page_size')}"
    if total is not None:
        assert pagination.get("total") == total, f"Expected total={total}, got {pagination.get('total')}"


def assert_data_isolation(items: List[Any], allowed_org_ids: Union[int, List[int]]):
    """Assert all items belong to allowed organization(s)."""
    if isinstance(allowed_org_ids, int):
        allowed_org_ids = [allowed_org_ids]
    for item in items:
        org_id = getattr(item, "organization_id", None) or item.get("organization_id")
        if org_id is not None:
            assert org_id in allowed_org_ids, (
                f"Data isolation breach: item org_id={org_id} not in allowed {allowed_org_ids}"
            )


def assert_permission_denied(response, status_code: int = 403):
    """Assert 403 Forbidden or 401 Unauthorized response."""
    assert response.status_code == status_code, (
        f"Expected status {status_code}, got {response.status_code}: {response.text[:200]}"
    )
    data = response.json()
    assert "message" in data or "detail" in data


def assert_not_found(response):
    """Assert 404 Not Found response."""
    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}: {response.text[:200]}"
    )


def assert_validation_error(response, expected_errors: Optional[int] = None):
    """Assert 422 Validation Error response."""
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}: {response.text[:200]}"
    )
    data = response.json()
    if expected_errors is not None:
        errors = data.get("errors") or data.get("detail") or []
        assert len(errors) >= expected_errors, f"Expected {expected_errors} errors, got {len(errors)}"


def assert_audit_logged(
    audit_service_or_db,
    user_id: int,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
):
    """Assert audit log entry exists matching given criteria."""
    from unittest.mock import MagicMock
    if isinstance(audit_service_or_db, MagicMock):
        calls = audit_service_or_db.log.call_args_list
        assert any(
            call[0][0] == action for call in calls
        ), f"Action '{action}' not logged. Calls: {calls}"
    else:
        from app.models.audit import AuditLog
        query = audit_service_or_db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.action == action,
        )
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        assert query.first() is not None, (
            f"AuditLog not found for user_id={user_id}, action='{action}'"
        )


def assert_fields_encrypted(obj, fields: List[str]):
    """Assert specified fields are encrypted (ciphertext != plaintext)."""
    for field in fields:
        value = getattr(obj, field, None)
        if value is not None:
            assert value.startswith("gAAAA") or "encrypted" in str(value).lower()[:20] or len(value) > 20, (
                f"Field '{field}' does not appear encrypted: {value[:50]}"
            )


def assert_sync_version_bumped(
    old_obj, new_obj, old_ver_field: str = "sync_version", new_ver_field: str = "sync_version"
):
    """Assert sync_version has incremented."""
    old_ver = getattr(old_obj, old_ver_field, 0)
    new_ver = getattr(new_obj, new_ver_field, 0)
    assert new_ver > old_ver, (
        f"sync_version not bumped: {old_ver} -> {new_ver}"
    )


def assert_response_code(response, expected_code: int = 200):
    """Assert HTTP response status code."""
    assert response.status_code == expected_code, (
        f"Expected status {expected_code}, got {response.status_code}: {response.text[:300]}"
    )


def assert_created_response(response):
    """Assert 201 Created."""
    assert_response_code(response, 201)


def assert_ok_response(response):
    """Assert 200 OK and parse JSON body."""
    assert_response_code(response, 200)
    return response.json()
