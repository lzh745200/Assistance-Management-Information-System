"""补齐 app.schemas.data_package_encrypted 覆盖率缺口（a23）。

缺口：DataPackageExportEncryptedRequest.validate_data_types (22-26)、
validate_password (32-34)、DataPackageImportEncryptedRequest.validate_strategy (48-51)、
ImportConfirmRequest.validate_strategy (94-97)。
"""

import pytest
from pydantic import ValidationError

from app.schemas.data_package_encrypted import (
    DataPackageExportEncryptedRequest,
    DataPackageImportEncryptedRequest,
    ImportConfirmRequest,
)


class TestExportRequestDataTypes:
    def test_all_allowed_types(self):
        req = DataPackageExportEncryptedRequest(
            data_types=["villages", "projects", "funds", "schools"]
        )
        assert req.data_types == ["villages", "projects", "funds", "schools"]

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError, match="不支持的数据类型"):
            DataPackageExportEncryptedRequest(data_types=["users"])

    def test_mixed_valid_invalid_rejected(self):
        with pytest.raises(ValidationError, match="不支持的数据类型"):
            DataPackageExportEncryptedRequest(data_types=["villages", "bad_type"])


class TestExportRequestPassword:
    def test_none_password_allowed(self):
        req = DataPackageExportEncryptedRequest(data_types=["villages"], password=None)
        assert req.password is None

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError, match="密码长度至少8位"):
            DataPackageExportEncryptedRequest(data_types=["villages"], password="short")

    def test_valid_password(self):
        req = DataPackageExportEncryptedRequest(data_types=["villages"], password="12345678")
        assert req.password == "12345678"


class TestImportRequestStrategy:
    @pytest.mark.parametrize("strategy", ["SKIP", "OVERWRITE", "KEEP_BOTH", "MERGE"])
    def test_allowed_strategies(self, strategy):
        req = DataPackageImportEncryptedRequest(conflict_strategy=strategy)
        assert req.conflict_strategy == strategy

    def test_default_strategy(self):
        req = DataPackageImportEncryptedRequest()
        assert req.conflict_strategy == "KEEP_BOTH"

    def test_invalid_strategy_rejected(self):
        with pytest.raises(ValidationError, match="不支持的冲突策略"):
            DataPackageImportEncryptedRequest(conflict_strategy="DELETE_ALL")


class TestConfirmRequestStrategy:
    @pytest.mark.parametrize("strategy", ["SKIP", "OVERWRITE", "KEEP_BOTH", "MERGE"])
    def test_allowed_strategies(self, strategy):
        req = ImportConfirmRequest(package_id=1, conflict_strategy=strategy)
        assert req.conflict_strategy == strategy

    def test_default_strategy(self):
        req = ImportConfirmRequest(package_id=1)
        assert req.conflict_strategy == "KEEP_BOTH"

    def test_invalid_strategy_rejected(self):
        with pytest.raises(ValidationError, match="不支持的冲突策略"):
            ImportConfirmRequest(package_id=1, conflict_strategy="REPLACE")
