"""补齐 app.api.v1.batch_operations 覆盖率缺口（a23）。

缺口：
- 校验器被 Field(min_length/max_length) 拦截、无法经模型构造触发的分支，直接调用校验器类方法：
  BatchUpdateRequest.validate_ids 空列表(37)/超1000(39)、validate_updates 空dict(49)、
  BatchDeleteRequest.validate_ids (77/79/81)、BatchExportRequest.validate_table_name (94)、
  validate_ids (101/103/105)。
- 端点异常重抛分支：batch_export 的 ValidationError(175)/DatabaseError(177)、
  validate_batch 的 ValidationError(194)/DatabaseError(196)——端点直接 async 调用。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.api.v1.batch_operations as mod
from app.api.v1.batch_operations import (
    BatchDeleteRequest,
    BatchExportRequest,
    BatchUpdateRequest,
)
from app.core.exceptions import DatabaseError, ValidationError


def _admin_user():
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.is_superuser = True
    user.role = "admin"
    return user


class TestBatchUpdateRequestValidators:
    def test_validate_ids_empty(self):
        with pytest.raises(ValueError, match="ID列表不能为空"):
            BatchUpdateRequest.validate_ids([])

    def test_validate_ids_too_many(self):
        with pytest.raises(ValueError, match="最多支持1000条"):
            BatchUpdateRequest.validate_ids(list(range(1, 1002)))

    def test_validate_updates_empty(self):
        with pytest.raises(ValueError, match="更新字段不能为空"):
            BatchUpdateRequest.validate_updates({})


class TestBatchDeleteRequestValidators:
    def test_validate_ids_empty(self):
        with pytest.raises(ValueError, match="ID列表不能为空"):
            BatchDeleteRequest.validate_ids([])

    def test_validate_ids_too_many(self):
        with pytest.raises(ValueError, match="最多支持1000条"):
            BatchDeleteRequest.validate_ids(list(range(1, 1002)))

    def test_validate_ids_not_positive(self):
        with pytest.raises(ValueError, match="ID必须为正整数"):
            BatchDeleteRequest.validate_ids([0])


class TestBatchExportRequestValidators:
    def test_validate_table_name_not_in_whitelist(self):
        with pytest.raises(ValueError, match="不允许的表名"):
            BatchExportRequest.validate_table_name("no_such_table")

    def test_validate_ids_empty(self):
        with pytest.raises(ValueError, match="ID列表不能为空"):
            BatchExportRequest.validate_ids([])

    def test_validate_ids_too_many(self):
        with pytest.raises(ValueError, match="最多支持5000条"):
            BatchExportRequest.validate_ids(list(range(1, 5002)))

    def test_validate_ids_not_positive(self):
        with pytest.raises(ValueError, match="ID必须为正整数"):
            BatchExportRequest.validate_ids([-1])


class TestBatchExportEndpointErrors:
    @pytest.mark.asyncio
    async def test_validation_error_reraised(self):
        req = BatchExportRequest(table_name="villages", ids=[1], format="xlsx")
        with patch.object(mod, "batch_service") as svc:
            svc.batch_export = AsyncMock(side_effect=ValidationError("bad data"))
            with pytest.raises(ValidationError):
                await mod.batch_export(req, current_user=_admin_user())

    @pytest.mark.asyncio
    async def test_database_error_reraised(self):
        req = BatchExportRequest(table_name="villages", ids=[1], format="xlsx")
        with patch.object(mod, "batch_service") as svc:
            svc.batch_export = AsyncMock(side_effect=DatabaseError("db error"))
            with pytest.raises(DatabaseError):
                await mod.batch_export(req, current_user=_admin_user())


class TestValidateBatchEndpointErrors:
    @pytest.mark.asyncio
    async def test_validation_error_reraised(self):
        with patch.object(mod, "batch_service") as svc:
            svc.validate_batch = AsyncMock(side_effect=ValidationError("bad data"))
            with pytest.raises(ValidationError):
                await mod.validate_batch(
                    table_name="villages", ids=[1], current_user=_admin_user()
                )

    @pytest.mark.asyncio
    async def test_database_error_reraised(self):
        with patch.object(mod, "batch_service") as svc:
            svc.validate_batch = AsyncMock(side_effect=DatabaseError("db error"))
            with pytest.raises(DatabaseError):
                await mod.validate_batch(
                    table_name="villages", ids=[1], current_user=_admin_user()
                )
