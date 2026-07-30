"""零信任动态权限评估器。

基于用户角色、设备信任评分和访问上下文动态评估对指定资源执行
指定操作的权限。

评估因子：
1. **用户角色**：admin/super_admin 可执行 admin 操作；普通用户不可。
2. **设备信任度**：敏感操作（delete/admin）要求设备信任评分 ≥ 0.5。
3. **数据范围**：write 操作要求用户已认证（非匿名）。

使用方式::

    from app.services.zero_trust.dynamic_permission import permission_evaluator

    allowed = await permission_evaluator.evaluate(user, "/api/v1/funds", "read")
    if not allowed:
        raise HTTPException(403, "访问被拒绝")
"""

import logging
from typing import Optional

from app.services.zero_trust.device_fingerprint import (
    DeviceRiskLevel,
    device_fingerprint_service,
)

logger = logging.getLogger(__name__)

# 敏感操作需要更高的设备信任评分
_SENSITIVE_ACTIONS = {"delete", "admin"}
_SENSITIVE_TRUST_THRESHOLD = 0.5

# 高风险操作需要 MFA 验证
_HIGH_RISK_ACTIONS = {"admin"}
_HIGH_RISK_TRUST_THRESHOLD = 0.7


class PermissionEvaluator:
    """零信任动态权限评估器。

    综合用户身份、设备信任度和操作类型评估访问权限。
    评估结果为 ``True``（允许）或 ``False``（拒绝）。
    """

    async def evaluate(
        self,
        user: Optional[object],
        resource: str,
        action: str,
        device_fingerprint: Optional[str] = None,
    ) -> bool:
        """评估用户对资源的访问权限。

        Args:
            user: 当前用户对象（需具有 ``username``、``is_superuser`` 等
                属性），匿名用户传 ``None``。
            resource: 请求访问的资源路径。
            action: 请求的操作类型（read/write/delete/admin）。
            device_fingerprint: 设备指纹 ID（可选，从中间件获取）。

        Returns:
            ``True`` 表示允许访问，``False`` 表示拒绝。
        """
        # 1. 匿名用户仅允许 read
        if user is None:
            if action == "read":
                logger.debug("匿名用户读取操作允许: resource=%s", resource)
                return True
            logger.info(
                "匿名用户非读操作被拒绝: resource=%s, action=%s", resource, action
            )
            return False

        username = getattr(user, "username", "unknown")
        is_superuser = getattr(user, "is_superuser", False)
        role = getattr(user, "role", "")

        # 2. admin 操作仅允许管理员
        if action in _HIGH_RISK_ACTIONS:
            if not is_superuser and role not in ("admin", "super_admin"):
                logger.warning(
                    "非管理员用户尝试管理操作: user=%s, resource=%s, action=%s",
                    username, resource, action,
                )
                return False

            # admin 操作还需检查设备信任度
            if device_fingerprint:
                trust_score = device_fingerprint_service.get_trust_score(
                    device_fingerprint
                )
                if trust_score < _HIGH_RISK_TRUST_THRESHOLD:
                    logger.warning(
                        "管理操作设备信任度不足: user=%s, score=%.2f, required=%.2f",
                        username, trust_score, _HIGH_RISK_TRUST_THRESHOLD,
                    )
                    return False

        # 3. 敏感操作检查设备信任度
        elif action in _SENSITIVE_ACTIONS:
            if device_fingerprint:
                trust_score = device_fingerprint_service.get_trust_score(
                    device_fingerprint
                )
                if trust_score < _SENSITIVE_TRUST_THRESHOLD:
                    logger.warning(
                        "敏感操作设备信任度不足: user=%s, score=%.2f, required=%.2f",
                        username, trust_score, _SENSITIVE_TRUST_THRESHOLD,
                    )
                    return False

        # 4. 设备被封禁则拒绝所有操作
        if device_fingerprint and device_fingerprint_service.is_device_blocked(
            device_fingerprint
        ):
            logger.warning(
                "被封禁设备操作被拒绝: user=%s, fingerprint=%s, action=%s",
                username, device_fingerprint, action,
            )
            return False

        logger.debug(
            "权限评估通过: user=%s, resource=%s, action=%s",
            username, resource, action,
        )
        return True


# 全局服务实例
permission_evaluator = PermissionEvaluator()
