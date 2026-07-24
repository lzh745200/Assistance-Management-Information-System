"""Tests for app.middleware.audit_middleware — 100% coverage target."""

import logging
from unittest.mock import patch

import anyio
import pytest
from starlette.testclient import TestClient

from app.middleware.audit_middleware import AuditMiddleware

_AUDIT_LOGGER_NAME = "app.middleware.audit_middleware"


@pytest.fixture()
def audit_messages():
    """Capture audit-middleware log messages by patching the module logger.

    Using mock.patch on the logger object itself (instead of caplog or a
    handler attached to the real logger) makes capture fully immune to
    init_logging() / configure_logging() reconfiguration that other test
    files trigger in parallel xdist workers.
    """
    messages: list[str] = []

    class _FakeLogger:
        def info(self, msg, *args, **kwargs):
            messages.append(str(msg) % args if args else str(msg))

        def warning(self, msg, *args, **kwargs):
            messages.append(str(msg) % args if args else str(msg))

        def error(self, msg, *args, **kwargs):
            messages.append(str(msg) % args if args else str(msg))

        def debug(self, msg, *args, **kwargs):
            messages.append(str(msg) % args if args else str(msg))

        def __getattr__(self, name):
            return lambda *a, **kw: None

    with patch("app.middleware.audit_middleware.logger", _FakeLogger()):
        yield messages


def _make_app(exclude_paths=None):
    """Build a minimal ASGI app wrapped with AuditMiddleware."""
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok(request):
        return PlainTextResponse("ok")

    async def slow(request):
        await anyio.sleep(0.01)
        return PlainTextResponse("slow")

    app = Starlette(
        routes=[
            Route("/health", endpoint=ok),
            Route("/api/data", endpoint=ok),
            Route("/slow", endpoint=slow),
        ]
    )
    app.add_middleware(AuditMiddleware, exclude_paths=exclude_paths)
    return app


class TestAuditMiddleware:
    def test_excluded_path_skips_audit(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "ok"

    def test_normal_path_logs_audit(self, audit_messages):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/api/data")
        assert resp.status_code == 200
        assert any("Audit:" in msg for msg in audit_messages)

    def test_custom_exclude_paths(self, audit_messages):
        app = _make_app(exclude_paths=["/api/data"])
        client = TestClient(app)
        resp = client.get("/api/data")
        assert resp.status_code == 200
        assert not any("Audit:" in msg for msg in audit_messages)

    def test_response_includes_status(self, audit_messages):
        app = _make_app()
        client = TestClient(app)
        client.get("/api/data")
        assert any("200" in msg for msg in audit_messages)

    def test_eos_exception_returns_499(self, audit_messages):
        """Force EndOfStream by making call_next raise it."""
        from unittest.mock import MagicMock
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        async def call_next(_request):
            raise anyio.EndOfStream()

        mw = AuditMiddleware(app=MagicMock())
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
        }
        request = Request(scope)
        response = anyio.run(mw.dispatch, request, call_next)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 499
        assert any("499" in msg for msg in audit_messages)
