"""补齐 app.utils.api_error 覆盖率缺口。

目标行：
- 96：safe_api_call 同步包装器对 HTTPException 直接 re-raise
- 122：APIErrorHandler.__exit__ 处理异常后返回 True（抑制异常）
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.utils.api_error import APIErrorHandler, safe_api_call


class TestSafeApiCallSyncHttpException:
    def test_http_exception_reraised(self):
        @safe_api_call("测试操作")
        def boom():
            raise HTTPException(status_code=400, detail="bad request")

        with pytest.raises(HTTPException):
            boom()


class TestAPIErrorHandlerExit:
    def test_exception_suppressed_after_handle(self):
        with patch("app.utils.api_error.handle_service_error") as mock_handle:
            with APIErrorHandler("测试操作"):
                raise ValueError("boom")

        mock_handle.assert_called_once()
