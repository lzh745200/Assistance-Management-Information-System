"""Shared test utilities."""

from typing import Any, Dict, Tuple

# Acceptable HTTP status codes for success/error responses in tests
HTTP_SUCCESS_OR_ERROR: Tuple[int, ...] = (200, 201, 400, 401, 403, 404, 422, 500)


def assert_create_or_error(status_code: int):
    """Assert the HTTP status is acceptable for a create/update operation.

    Args:
        status_code: The response status code to check.
    """
    assert status_code in HTTP_SUCCESS_OR_ERROR, (
        f"Unexpected status {status_code}"
    )
