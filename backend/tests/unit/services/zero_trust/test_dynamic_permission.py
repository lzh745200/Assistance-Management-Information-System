"""
零信任动态权限评估器（stub）测试

测试 app/services/zero_trust/dynamic_permission.py 模块
"""
import pytest
from app.services.zero_trust.dynamic_permission import PermissionEvaluator, permission_evaluator


class TestPermissionEvaluator:
    @pytest.mark.asyncio
    async def test_evaluate_raises_not_implemented(self):
        evaluator = PermissionEvaluator()
        with pytest.raises(NotImplementedError):
            await evaluator.evaluate({"id": "user1"}, "resource:data", "read")

    @pytest.mark.asyncio
    async def test_global_instance_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await permission_evaluator.evaluate({"id": "user1"}, "resource:data", "write")
