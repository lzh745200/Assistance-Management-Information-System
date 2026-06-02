"""将 dict 的 snake_case 键递归转换为 camelCase。"""
from app.utils.common import StringHelper


def _convert(obj):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if isinstance(k, str):
                result[StringHelper.to_camel_case(k)] = _convert(v)
            else:
                result[k] = _convert(v)
        return result
    if isinstance(obj, list):
        return [_convert(item) for item in obj]
    return obj


def to_camel(obj):
    """顶层入口：将响应 dict 的键从 snake_case 转为 camelCase。"""
    return _convert(obj) if obj is not None else None
