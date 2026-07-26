"""b3 攻坚：覆盖 app.schemas.data_package 的 data_types 非空校验分支"""
import pytest
from pydantic import ValidationError

from app.schemas.data_package import DataPackageExportRequest


class TestDataPackageExportRequestValidator:
    def test_empty_data_types_raises(self):
        with pytest.raises(ValidationError, match="至少需要选择一种数据类型"):
            DataPackageExportRequest(data_types=[])

    def test_valid_data_types(self):
        req = DataPackageExportRequest(data_types=["fund", "village"])
        assert req.data_types == ["fund", "village"]
