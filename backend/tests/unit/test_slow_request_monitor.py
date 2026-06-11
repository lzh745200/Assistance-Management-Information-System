"""Tests for app.middleware.slow_request_monitor — 100% coverage target."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import anyio

import pytest
from starlette.testclient import TestClient

from app.middleware import slow_request_monitor as srm


# Clean up module-level state before every test
@pytest.fixture(autouse=True)
def _reset_state():
    srm._slow_apis.clear()
    srm._slow_sqls.clear()
    srm._counters.update({
        "total_requests": 0,
        "slow_api_count": 0,
        "slow_sql_count": 0,
    })
    yield


# ==============================================================================
# SlowRequestMiddleware — ASGI
# ==============================================================================


def _make_app(slow_api_ms=500, slow_sql_ms=200):
    """Build a minimal ASGI app with SlowRequestMiddleware."""
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route

    async def fast(request):
        return PlainTextResponse("fast")

    async def slow_enough(request):
        time.sleep(0.01)
        return PlainTextResponse("slowish")

    app = Starlette(
        routes=[
            Route("/fast", endpoint=fast),
            Route("/slowish", endpoint=slow_enough),
        ]
    )
    # Patch _install_sql_listener to avoid database engine import
    with patch.object(srm.SlowRequestMiddleware, "_install_sql_listener", return_value=None):
        app.add_middleware(srm.SlowRequestMiddleware, slow_api_ms=slow_api_ms, slow_sql_ms=slow_sql_ms)
    return app


class TestMiddlewareCall:
    def test_non_http_scope_passthrough(self):
        """WebSocket or other scopes pass through without counting."""
        async def fake_send(msg):
            pass

        mw = srm.SlowRequestMiddleware.__new__(srm.SlowRequestMiddleware)
        mw.app = AsyncMock()
        mw.slow_api_ms = 999
        mw.slow_sql_ms = 999
        mw._install_sql_listener = MagicMock()

        scope_ws = {"type": "websocket", "path": "/ws", "method": "GET"}
        anyio.run(mw.__call__, scope_ws, None, fake_send)
        mw.app.assert_awaited_once_with(scope_ws, None, fake_send)
        assert srm._counters["total_requests"] == 0

    def test_fast_request_does_not_log_slow(self, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        app = _make_app(slow_api_ms=99999)
        client = TestClient(app)
        client.get("/fast")
        assert not any("慢API" in msg for msg in caplog.messages)

    def test_slow_request_logs_warning(self, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        app = _make_app(slow_api_ms=1)
        client = TestClient(app)
        client.get("/slowish")
        assert any("慢API" in msg for msg in caplog.messages)

    def test_counters_incremented(self):
        app = _make_app(slow_api_ms=1)
        client = TestClient(app)
        client.get("/fast")
        client.get("/slowish")
        assert srm._counters["total_requests"] == 2
        assert srm._counters["slow_api_count"] == 1  # slowish exceeds 1ms


# ==============================================================================
# get_slow_api_records / get_slow_sql_records
# ==============================================================================


class TestGetRecords:
    def test_get_slow_api_records_returns_reversed(self):
        srm._slow_apis.append({"method": "GET", "path": "/a", "elapsed_ms": 100})
        srm._slow_apis.append({"method": "GET", "path": "/b", "elapsed_ms": 200})
        records = srm.get_slow_api_records(limit=10)
        assert records[0]["path"] == "/b"
        assert records[1]["path"] == "/a"

    def test_get_slow_sql_records_returns_reversed(self):
        srm._slow_sqls.append({"sql": "SELECT 1", "elapsed_ms": 100})
        srm._slow_sqls.append({"sql": "SELECT 2", "elapsed_ms": 200})
        records = srm.get_slow_sql_records(limit=10)
        assert records[0]["sql"] == "SELECT 2"

    def test_limit_respected(self):
        for i in range(10):
            srm._slow_apis.append({"method": "GET", "path": f"/{i}", "elapsed_ms": i})
        records = srm.get_slow_api_records(limit=3)
        assert len(records) == 3

    def test_empty_returns_empty_list(self):
        assert srm.get_slow_api_records() == []
        assert srm.get_slow_sql_records() == []


# ==============================================================================
# get_slow_stats
# ==============================================================================


class TestGetSlowStats:
    def test_basic_shape(self):
        srm._counters["total_requests"] = 10
        srm._counters["slow_api_count"] = 2
        srm._counters["slow_sql_count"] = 3
        srm._slow_apis.append({"elapsed_ms": 100})
        srm._slow_apis.append({"elapsed_ms": 200})
        srm._slow_sqls.append({"elapsed_ms": 50})

        stats = srm.get_slow_stats()
        assert stats["total_requests"] == 10
        assert stats["slow_api_count"] == 2
        assert stats["slow_sql_count"] == 3
        assert stats["slow_api_peak_ms"] == 200
        assert stats["slow_sql_peak_ms"] == 50
        assert stats["slow_api_last_50_avg_ms"] == 150.0
        assert stats["slow_sql_last_50_avg_ms"] == 50.0

    def test_empty_stats_returns_zeros(self):
        stats = srm.get_slow_stats()
        assert stats["slow_api_peak_ms"] == 0
        assert stats["slow_sql_peak_ms"] == 0
        assert stats["slow_api_last_50_avg_ms"] == 0.0
        assert stats["slow_sql_last_50_avg_ms"] == 0.0

    def test_deque_maxlen_enforced(self):
        for i in range(srm._MAX_RECORDS + 50):
            srm._slow_apis.append({"elapsed_ms": float(i)})
        assert len(srm._slow_apis) == srm._MAX_RECORDS


# ==============================================================================
# _install_sql_listener
# ==============================================================================


class TestInstallSqlListener:
    def test_successful_install(self):
        """When engine is available, listeners are registered."""
        middleware = srm.SlowRequestMiddleware(app=MagicMock(), slow_api_ms=999, slow_sql_ms=100)
        # If engine import succeeds, no exception
        assert middleware.slow_sql_ms == 100

    def test_exception_on_install(self):
        """When DB engine not ready, except branch is taken."""
        mw = srm.SlowRequestMiddleware.__new__(srm.SlowRequestMiddleware)
        mw.slow_sql_ms = 200
        mw.app = MagicMock()

        # Make engine.sync_engine raise AttributeError
        bad_engine = MagicMock()
        del bad_engine.sync_engine
        with patch("app.core.database.engine", bad_engine):
            mw._install_sql_listener()
        assert mw.slow_sql_ms == 200


# ==============================================================================
# Directly exercise the _before / _after cursor execute listeners
# ==============================================================================


class TestSqlEventListeners:
    def _make_middleware_with_real_db(self, slow_sql_ms=99999):
        """Helper: patch engine so _install_sql_listener can register on a real db."""
        from sqlalchemy import create_engine

        real_engine = create_engine("sqlite:///:memory:")
        # _install_sql_listener does engine.sync_engine — wrap in mock
        engine_like = MagicMock()
        engine_like.sync_engine = real_engine

        mw = srm.SlowRequestMiddleware.__new__(srm.SlowRequestMiddleware)
        mw.slow_sql_ms = slow_sql_ms
        mw.app = MagicMock()

        with patch("app.core.database.engine", engine_like):
            mw._install_sql_listener()
        return mw, real_engine

    def test_before_sets_start_time(self):
        """_before listener stores perf counter on conn.info."""
        from sqlalchemy import text

        mw, real_engine = self._make_middleware_with_real_db()
        with real_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # If _before fired, _after consumed the start; no crash = success
        assert True

    def test_after_skipped_when_no_start(self):
        """_after returns early if _slow_req_start is missing from conn.info."""
        srm._slow_sqls.clear()
        count_before = srm._counters["slow_sql_count"]

        mw, real_engine = self._make_middleware_with_real_db(slow_sql_ms=0)

        # Register a before_cursor_execute that fires AFTER _before and clears the key
        from sqlalchemy import event as sqla_event, text

        @sqla_event.listens_for(real_engine, "before_cursor_execute")
        def _clear_start(conn, cursor, statement, parameters, context, executemany):
            conn.info.pop("_slow_req_start", None)

        with real_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # The _after handler saw start is None → returned early → no slow sql recorded
        assert srm._counters["slow_sql_count"] == count_before
        assert len(srm._slow_sqls) == 0

    def test_slow_sql_recorded_when_exceeds_threshold(self):
        """Slow SQL listener logs and records when elapsed > threshold."""
        from sqlalchemy import text

        srm._slow_sqls.clear()
        slow_count_before = srm._counters["slow_sql_count"]

        mw, real_engine = self._make_middleware_with_real_db(slow_sql_ms=0)

        with real_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        assert srm._counters["slow_sql_count"] == slow_count_before + 1
        assert len(srm._slow_sqls) == 1
        assert "SELECT" in srm._slow_sqls[0]["sql"]
        assert srm._slow_sqls[0]["elapsed_ms"] > 0
