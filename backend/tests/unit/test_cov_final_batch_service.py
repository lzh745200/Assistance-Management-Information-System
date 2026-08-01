"""补齐 app.services.batch_service 覆盖率缺口。

目标行：
- 39-40：_reject_protected_table 命中高权限表（users/organizations）抛出 BusinessLogicError
- 70：_resolve_model 表名在白名单但缺少模型映射 → ValueError
- 158-161：batch_update 非超管跨组织记录跳过（skipped 计数）
- 184-187：batch_delete 非超管跨组织记录跳过
- 191：batch_delete 软删除优先走 is_active 列
- 234-236：validate_batch 非超管跨组织记录不计数

db 使用 MagicMock（db.query().filter() 批量查询链）；异步用例依赖 pytest.ini asyncio_mode=auto。
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.services.batch_service as batch_mod
from app.core.error_handler import BusinessLogicError
from app.services.batch_service import BatchService, _reject_protected_table, _resolve_model


class TestRejectProtectedTable:
    def test_protected_table_raises_business_logic_error(self):
        with pytest.raises(BusinessLogicError, match="不允许通过批量接口操作"):
            _reject_protected_table("users")


class TestResolveModelMissingMapping:
    def test_whitelisted_table_without_model_mapping_raises(self, monkeypatch):
        # 表名在 ALLOWED_TABLES 白名单内但无模型映射 → 70 行 ValueError
        monkeypatch.setitem(batch_mod.TABLE_MODEL_MAP, "ghost_table", None)
        monkeypatch.setattr(batch_mod, "ALLOWED_TABLES", frozenset({"ghost_table"}))

        with pytest.raises(ValueError, match="Unknown table: ghost_table"):
            _resolve_model("ghost_table")


class TestBatchUpdateDataIsolation:
    async def test_cross_org_record_skipped(self):
        db = MagicMock()
        own = SimpleNamespace(organization_id=1, name="old1")
        # 批量查询链：base_query.count()=总数 2，组织过滤后只剩本组织 1 条
        base_query = db.query.return_value.filter.return_value
        base_query.count.return_value = 2
        base_query.filter.return_value.all.return_value = [own]

        svc = BatchService(db)
        result = await svc.batch_update("funds", [1, 2], {"name": "new"}, organization_id=1)

        assert result == {"success": True, "success_count": 1, "skipped": 1}
        assert own.name == "new"


class TestBatchDeleteDataIsolation:
    async def test_soft_delete_is_active_and_cross_org_skip(self):
        db = MagicMock()
        own = SimpleNamespace(organization_id=1, is_active=True)
        base_query = db.query.return_value.filter.return_value
        base_query.count.return_value = 2
        base_query.filter.return_value.all.return_value = [own]

        svc = BatchService(db)
        result = await svc.batch_delete("funds", [1, 2], soft_delete=True, organization_id=1)

        assert result == {"success": True, "success_count": 1, "skipped": 1}
        assert own.is_active is False  # 软删除走 is_active 列（191 行）
        db.delete.assert_not_called()


class TestValidateBatchDataIsolation:
    async def test_cross_org_record_not_counted(self):
        db = MagicMock()
        base_query = db.query.return_value.filter.return_value
        # 组织过滤后的 query.count() 只计本组织记录
        base_query.filter.return_value.count.return_value = 1

        svc = BatchService(db)
        result = await svc.validate_batch("funds", [1, 2], organization_id=1)

        assert result == {"success": True, "existing_count": 1}
