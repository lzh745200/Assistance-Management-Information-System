"""Tests for app.middleware.audit_middleware — 100% coverage target."""

import anyio
import pytest
from starlette.testclient import TestClient

from app.middleware.audit_middleware import AuditMiddleware


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

    def test_normal_path_logs_audit(self, caplog):
        import logging
        caplog.set_level(logging.INFO)
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/api/data")
        assert resp.status_code == 200
        assert any("Audit:" in msg for msg in caplog.messages)

    def test_custom_exclude_paths(self, caplog):
        import logging
        caplog.set_level(logging.INFO)
        app = _make_app(exclude_paths=["/api/data"])
        client = TestClient(app)
        resp = client.get("/api/data")
        assert resp.status_code == 200
        assert not any("Audit:" in msg for msg in caplog.messages)

    def test_response_includes_status(self, caplog):
        import logging
        caplog.set_level(logging.INFO)
        app = _make_app()
        client = TestClient(app)
        client.get("/api/data")
        assert any("200" in msg for msg in caplog.messages)

    def test_eos_exception_returns_499(self, caplog):
        """Force EndOfStream by making call_next raise it."""
        import logging
        caplog.set_level(logging.INFO)

        from unittest.mock import AsyncMock, MagicMock
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
        assert any("499" in msg for msg in caplog.messages)
