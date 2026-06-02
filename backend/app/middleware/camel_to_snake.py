"""
请求体键名转换中间件

将前端发送的 camelCase JSON 键名自动转换为 snake_case，
确保与后端 Pydantic Schema 的字段名一致。

使用 starlette BaseHTTPMiddleware 实现，通过修改 Request._body 来转换键名。
"""

import json
from typing import Any, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils.common import StringHelper  # noqa: E402


def _convert_keys(obj: Any, converter) -> Any:
    """递归转换对象中所有的字符串键名；返回 (converted_obj, changed)"""
    if isinstance(obj, dict):
        new: Dict[str, Any] = {}
        changed = False
        for k, v in obj.items():
            if isinstance(k, str):
                new_key = converter(k)
                if new_key != k:
                    changed = True
            else:
                new_key = k
            inner, inner_changed = _convert_keys(v, converter)
            new[new_key] = inner
            if inner_changed:
                changed = True
        return new, changed
    if isinstance(obj, list):
        items = [_convert_keys(item, converter) for item in obj]
        return [i[0] for i in items], any(i[1] for i in items)
    return obj, False


class CamelToSnakeMiddleware(BaseHTTPMiddleware):
    """
    HTTP 中间件：自动将 JSON 请求体中的 camelCase 键转换为 snake_case。

    仅在 Content-Type 为 application/json 时生效。
    不影响响应体。
    """

    async def dispatch(self, request: Request, call_next):
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    converted, changed = _convert_keys(data, StringHelper.to_snake_case)
                    if changed:
                        request._body = json.dumps(
                            converted, ensure_ascii=False
                        ).encode("utf-8")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass  # 非 JSON 体保持原样
        response = await call_next(request)
        return response
