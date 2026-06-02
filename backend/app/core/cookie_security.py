"""Cookie security helpers.

Provides utilities for setting secure HTTP cookies with sensible
defaults and validating incoming cookies against common attacks.
"""

import logging
from typing import Optional

from fastapi import Response

logger = logging.getLogger(__name__)


def set_secure_cookie(
    response: Response,
    key: str,
    value: str,
    *,
    max_age: int = 24 * 3600,
    path: str = "/",
    domain: Optional[str] = None,
    secure: bool = True,
    httponly: bool = True,
    samesite: str = "lax",
) -> None:
    """Set a cookie with security-best-practice defaults.

    Args:
        response: FastAPI/Starlette Response object.
        key: Cookie name.
        value: Cookie value.
        max_age: Max age in seconds.
        path: Cookie path.
        domain: Cookie domain.
        secure: Require HTTPS.
        httponly: Prevent JavaScript access.
        samesite: SameSite attribute (``"lax"``, ``"strict"``, or ``"none"``).
    """
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        path=path,
        domain=domain,
        secure=secure,
        httponly=httponly,
        samesite=samesite,
    )


def delete_cookie(
    response: Response,
    key: str,
    *,
    path: str = "/",
    domain: Optional[str] = None,
) -> None:
    """Remove a cookie by setting its max_age to 0.

    Args:
        response: FastAPI/Starlette Response object.
        key: Cookie name to delete.
        path: Must match the path used when the cookie was set.
        domain: Must match the domain used when the cookie was set.
    """
    response.delete_cookie(key=key, path=path, domain=domain)


def get_cookie_domain(request_host: str) -> Optional[str]:
    """Derive a safe cookie domain from the request host.

    Returns *None* (browser default – no domain attribute) for localhost/IP
    addresses, and the stripped host otherwise.

    Args:
        request_host: Value of ``request.headers["host"]``.

    Returns:
        A domain string or *None*.
    """
    if not request_host:
        return None
    # Strip port
    host = request_host.split(":")[0]
    # Do not set domain for localhost / IP addresses
    if host in ("localhost", "127.0.0.1", "::1"):
        return None
    # Check if it looks like an IP address
    import ipaddress

    try:
        ipaddress.ip_address(host)
        return None  # bare IP
    except ValueError:
        pass
    return host
