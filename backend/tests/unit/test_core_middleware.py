from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
    TimingMiddleware,
    setup_cors,
    setup_default_middleware,
)


def _make_app():
    app = FastAPI()

    @app.get("/test")
    async def test_route():
        return {"ok": True}

    @app.get("/slow")
    async def slow_route():
        import asyncio

        await asyncio.sleep(0.25)
        return {"slow": True}

    return app


class TestTimingMiddleware:
    def test_adds_process_time_header(self):
        app = _make_app()
        app.add_middleware(TimingMiddleware)
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "X-Process-Time" in resp.headers

    def test_logs_slow_request(self):
        app = _make_app()
        app.add_middleware(TimingMiddleware)
        client = TestClient(app)
        with patch("app.core.middleware.logger.warning") as mock_warn:
            resp = client.get("/slow")
            assert resp.status_code == 200
            mock_warn.assert_called_once()

    def test_custom_slow_threshold(self):
        app = _make_app()
        app.add_middleware(TimingMiddleware, slow_threshold_ms=999999)
        client = TestClient(app)
        with patch("app.core.middleware.logger.warning") as mock_warn:
            resp = client.get("/slow")
            assert resp.status_code == 200
            mock_warn.assert_not_called()

    def test_settings_threshold_fallback(self):
        with patch("app.core.middleware.logger") as mock_logger:
            middleware = TimingMiddleware.__new__(TimingMiddleware)
            middleware.__init__(MagicMock(), slow_threshold_ms=None)
            assert middleware._slow_threshold == 200.0

    def test_init_without_settings(self):
        import sys

        with (
            patch.dict(sys.modules, {"app.core.config": None}),
            patch(
                "app.core.middleware.logger.warning"
            ) as mock_warn,
        ):
            app = _make_app()
            app.add_middleware(TimingMiddleware)
            client = TestClient(app)
            resp = client.get("/test")
            assert resp.status_code == 200

    def test_init_exception(self):
        app = _make_app()
        app.add_middleware(TimingMiddleware)
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "X-Process-Time" in resp.headers


class TestRequestIDMiddleware:
    def test_sets_request_id_from_header(self):
        app = _make_app()
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)
        resp = client.get("/test", headers={"X-Request-ID": "my-id-123"})
        assert resp.headers.get("X-Request-ID") == "my-id-123"

    def test_generates_request_id(self):
        app = _make_app()
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)
        resp = client.get("/test")
        rid = resp.headers.get("X-Request-ID")
        assert rid is not None
        assert len(rid) == 16


class TestLoggingMiddleware:
    def test_logs_request(self):
        app = _make_app()
        app.add_middleware(LoggingMiddleware)
        client = TestClient(app)
        with patch("app.core.middleware.logger.info") as mock_info:
            resp = client.get("/test")
            assert resp.status_code == 200
            mock_info.assert_called_once()


class TestSetupCORS:
    def test_with_settings(self):
        app = FastAPI()
        settings = MagicMock()
        settings.cors_origins_list = ["http://example.com"]
        settings.CORS_ALLOW_CREDENTIALS = True
        settings.cors_allow_methods_list = ["GET", "POST"]
        settings.cors_allow_headers_list = ["Content-Type"]
        setup_cors(app, settings)
        client = TestClient(app)
        resp = client.options(
            "/test",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200

    def test_without_settings(self):
        app = FastAPI()
        setup_cors(app, None)
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 404

    def test_with_import_error(self):
        app = FastAPI()
        orig_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "app.core.config":
                raise ImportError("mocked")
            return orig_import(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=mock_import),
            patch("app.core.middleware.logger.warning") as mock_warn,
        ):
            setup_cors(app, None)
            mock_warn.assert_called_once_with("无法加载 CORS 配置，使用默认值")
            client = TestClient(app)
            resp = client.get("/test")
            assert resp.status_code == 404


class TestSetupDefaultMiddleware:
    def test_sets_up_all_middleware(self):
        app = _make_app()
        setup_default_middleware(app)
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert "X-Process-Time" in resp.headers

    def test_with_settings_object(self):
        app = _make_app()
        settings = MagicMock()
        settings.cors_origins_list = ["*"]
        settings.CORS_ALLOW_CREDENTIALS = True
        settings.cors_allow_methods_list = ["*"]
        settings.cors_allow_headers_list = ["*"]
        setup_default_middleware(app, settings)
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200

    def test_security_headers_import_error(self):
        app = _make_app()
        orig_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "app.core.security":
                raise ImportError("Mocked import error")
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            setup_default_middleware(app)
            client = TestClient(app)
            resp = client.get("/test")
            assert resp.status_code == 200
