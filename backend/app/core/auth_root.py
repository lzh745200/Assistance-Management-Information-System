"""Auth-root configuration.

Provides FastAPI router aliases for authentication endpoints so that
the root-level auth routes (e.g. /auth/login) can be composed with the
main API prefix.
"""

from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["认证"])


def get_auth_router() -> APIRouter:
    """Return the auth router instance.

    The router is used by the main application factory to register
    authentication-related endpoints.
    """
    return auth_router
