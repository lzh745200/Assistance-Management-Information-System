"""Tests for app.middleware.query_counter — 100% coverage target."""

from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from app.middleware.query_counter import QueryCounterMiddleware, increment_query_count


def _make_app():
    """Build a minimal ASGI app wrapped with QueryCounterMiddleware."""
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def ok(request):
        # Simulate a few queries
        increment_query_count(request)
        increment_query_count(request)
        return PlainTextResponse("ok")

    async def many_queries(request):
        for _ in range(55):
            increment_query_count(request)
        return PlainTextResponse("many")

    app = Starlette(
        routes=[
            Route("/ok", endpoint=ok),
            Route("/many", endpoint=many_queries),
        ]
    )
    app.add_middleware(QueryCounterMiddleware)
    return app


class TestQueryCounterMiddleware:
    def test_headers_present(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/ok")
        assert "X-Query-Count" in resp.headers
        assert "X-Response-Time" in resp.headers

    def test_query_count_correct(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/ok")
        assert resp.headers["X-Query-Count"] == "2"

    def test_no_warning_below_threshold(self, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        app = _make_app()
        client = TestClient(app)
        client.get("/ok")
        assert not any("慢查询警告" in msg for msg in caplog.messages)

    def test_warning_above_threshold(self, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        app = _make_app()
        client = TestClient(app)
        client.get("/many")
        assert any("慢查询警告" in msg for msg in caplog.messages)
        assert any("55" in msg for msg in caplog.messages)


class TestIncrementQueryCount:
    def test_without_state_does_not_raise(self):
        request = MagicMock()
        del request.state  # ensure no state attr
        increment_query_count(request)  # should not raise

    def test_without_query_count_does_not_raise(self):
        request = MagicMock()
        # state exists but has no query_count
        increment_query_count(request)  # should not raise

    def test_increments(self):
        request = MagicMock()
        request.state.query_count = 0
        increment_query_count(request)
        assert request.state.query_count == 1
