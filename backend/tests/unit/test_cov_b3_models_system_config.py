"""b3 攻坚：覆盖 app.models.system_config 的 SystemUpdateLog.to_dict"""
from datetime import datetime

from app.models.system_config import SystemConfig, SystemUpdateLog


class TestSystemConfigModel:
    def test_repr(self):
        cfg = SystemConfig(key="site_name", value="test")
        assert "site_name" in repr(cfg)


class TestSystemUpdateLogToDict:
    def test_to_dict_with_created_at(self):
        log = SystemUpdateLog(
            id="log1",
            version="1.2.3",
            description="升级",
            updated_by="admin",
            created_at=datetime(2024, 1, 2, 3, 4, 5),
        )
        d = log.to_dict()
        assert d["id"] == "log1"
        assert d["version"] == "1.2.3"
        assert d["description"] == "升级"
        assert d["updated_by"] == "admin"
        assert d["created_at"] == "2024-01-02T03:04:05"

    def test_to_dict_without_created_at(self):
        log = SystemUpdateLog(id="log2", version="1.0.0")
        assert log.to_dict()["created_at"] is None
