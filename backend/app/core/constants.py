"""全局常量定义。

消除跨层导入：调度层不应依赖 HTTP API 层的模块级常量。
所有跨层共享的常量定义在此。
"""

# ── 数据分析 ──
# 数据分析缓存前缀（原在 app.api.v1.data.data.analytics 中定义）
ANALYTICS_CACHE_PREFIX = "analytics:"

# ── 分页 ──
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ── HTTP ──
# Nginx 非标准状态码：客户端在服务器完成响应前关闭了连接
HTTP_CLIENT_CLOSED_REQUEST = 499

# ── 角色常量 ──
ROLE_SUPER_ADMIN = "super_admin"
ROLE_ADMIN = "admin"
ROLE_APPROVAL_LEADER = "approval_leader"
ROLE_MANAGER = "manager"
ROLE_OPERATOR = "operator"
ROLE_VIEWER = "viewer"

ADMIN_ROLES = {ROLE_SUPER_ADMIN, ROLE_ADMIN}

ALL_ROLES = [
    ROLE_SUPER_ADMIN,
    ROLE_ADMIN,
    ROLE_APPROVAL_LEADER,
    ROLE_MANAGER,
    ROLE_OPERATOR,
    ROLE_VIEWER,
]


class UserRole:
    """用户角色枚举（字符串常量）"""
    SUPER_ADMIN = ROLE_SUPER_ADMIN
    ADMIN = ROLE_ADMIN
    APPROVAL_LEADER = ROLE_APPROVAL_LEADER
    MANAGER = ROLE_MANAGER
    OPERATOR = ROLE_OPERATOR
    VIEWER = ROLE_VIEWER
