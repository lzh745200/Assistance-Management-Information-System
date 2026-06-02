"""
UserInfo - 用户信息对象

支持属性访问（user.id）和字典风格访问（user.get("id")、user["id"]），
兼容 SimpleNamespace 的所有用法，同时解决 .get() 不可用的问题。
"""

from types import SimpleNamespace
from typing import Any


class UserInfo(SimpleNamespace):
    """用户信息对象，兼容 dict 和 SimpleNamespace 两种访问方式。"""

    def get(self, key: str, default: Any = None) -> Any:
        """字典风格的 get 方法。"""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def __repr__(self) -> str:
        items = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"UserInfo({items})"

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()
