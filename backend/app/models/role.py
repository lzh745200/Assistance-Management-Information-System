"""Role model — 向后兼容桥接。

实际模型定义在 models/rbac.py (RbacRole)，
本模块导出 BasicRole / Role 别名，保持已有导入不中断。
"""

from app.models.rbac import RbacRole as BasicRole  # noqa: F401
from app.models.rbac import RbacRole as Role

__all__ = ["BasicRole", "Role"]
