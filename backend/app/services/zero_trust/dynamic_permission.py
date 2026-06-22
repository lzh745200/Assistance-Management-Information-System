"""零信任动态权限评估器（stub）。

.. warning::
    本模块为自动生成的占位实现，**尚未接入鉴权链**（无任何路由/中间件引用
    ``permission_evaluator``）。``evaluate`` 此前恒返回 ``True``，存在绕过
    权限校验的风险。为避免被误用为"已实现"，此处显式抛出
    :class:`NotImplementedError` 暴露问题。

    完整的零信任动态权限评估实现超出了本次 BugFix 的范围，需后续专项实现：
    结合 RBAC 角色、数据范围、设备信任分、会话风险等因子进行综合评估。
"""

import logging

logger = logging.getLogger(__name__)


class PermissionEvaluator:
    """零信任动态权限评估器（未实现）。

    真正的实现应基于用户身份、设备信任度、访问上下文、数据范围等因子
    动态评估对指定 ``resource`` 执行 ``action`` 的权限，而非恒返回 ``True``。
    """

    async def evaluate(self, user, resource: str, action: str) -> bool:
        """评估用户对资源的访问权限。

        Raises:
            NotImplementedError: 本评估器尚未实现，调用方不应依赖其结果。
        """
        raise NotImplementedError(
            "PermissionEvaluator.evaluate 尚未实现（零信任动态权限评估为占位 "
            "stub，未接入鉴权链）。请勿在此实现就绪前将其用于权限决策。"
        )


permission_evaluator = PermissionEvaluator()
