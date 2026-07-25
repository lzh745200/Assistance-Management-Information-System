# -*- coding: utf-8 -*-
"""request_id 中间件覆盖率测试：合法客户端ID/断流/异常/慢请求/DEBUG分支"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import anyio
import pytest

import app.middleware.request_id as mod


def _mw():
    return mod.RequestIDMiddleware(app=MagicMock())


def _req(headers=None):
    r = MagicMock()
    r.headers = headers or {}
    r.method = "GET"
    r.url.path = "/x"
    r.state = MagicMock()
    return r


def _resp():
    resp = MagicMock()
    resp.headers = {}
    resp.status_code = 200
    return resp


@pytest.mark.asyncio
async def test_dispatch_uses_valid_client_request_id():
    resp = _resp()
    out = await _mw().dispatch(_req({"X-Request-ID": "abc-123_X"}), AsyncMock(return_value=resp))
    assert out.headers["X-Request-ID"] == "abc-123_X"


@pytest.mark.asyncio
async def test_dispatch_invalid_client_id_generates_uuid():
    resp = _resp()
    out = await _mw().dispatch(_req({"X-Request-ID": "bad id!"}), AsyncMock(return_value=resp))
    assert len(out.headers["X-Request-ID"]) == 16


@pytest.mark.asyncio
async def test_dispatch_end_of_stream_returns_499():
    out = await _mw().dispatch(_req(), AsyncMock(side_effect=anyio.EndOfStream()))
    assert out.status_code == mod.HTTP_CLIENT_CLOSED_REQUEST


@pytest.mark.asyncio
async def test_dispatch_exception_reraises():
    with pytest.raises(ValueError):
        await _mw().dispatch(_req(), AsyncMock(side_effect=ValueError("boom")))


@pytest.mark.asyncio
async def test_dispatch_slow_request_warning():
    resp = _resp()
    with patch.object(mod.time, "time", side_effect=[1000.0] + [1003.0] * 20):
        out = await _mw().dispatch(_req(), AsyncMock(return_value=resp))
    assert out.status_code == 200


@pytest.mark.asyncio
async def test_dispatch_debug_enabled_logs_completion():
    resp = _resp()
    with patch.object(mod.logger, "isEnabledFor", return_value=True), patch.object(
        mod.logger, "debug"
    ) as dbg:
        await _mw().dispatch(_req(), AsyncMock(return_value=resp))
    assert any("请求完成" in str(c.args[0]) for c in dbg.call_args_list)


def test_log_filter_injects_request_id():
    token = mod.request_id_var.set("rid-1")
    try:
        rec = logging.LogRecord("n", logging.INFO, "p", 1, "m", (), None)
        assert mod.RequestIDLogFilter().filter(rec) is True
        assert rec.request_id == "rid-1"
    finally:
        mod.request_id_var.reset(token)
