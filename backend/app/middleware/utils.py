"""
中间件共享工具

提供中间件常用的辅助函数和常量
"""

from typing import Collection


def should_skip_middleware(path: str, exclude_paths: Collection[str]) -> bool:
    """
    检查请求路径是否应跳过中间件处理

    Args:
        path: 请求路径
        exclude_paths: 排除路径集合

    Returns:
        bool: 是否应该跳过
    """
    return any(path.startswith(ep) for ep in exclude_paths)
