"""app.api.v1.system.metrics 覆盖补全 —
- get_system_metrics: 数据库连接池指标采集失败的降级分支 (lines 135-136)
- get_database_metrics: 表名超过 20 个截断标记 (line 240) 与行数统计外层异常分支 (lines 263-264)
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app.api.v1.system.metrics as metrics_mod
from app.api.v1.system.metrics import get_database_metrics, get_system_metrics


class _BadEngine:
    @property
    def pool(self):
        raise RuntimeError("pool unavailable")


class TestGetSystemMetrics:
    async def test_database_pool_failure_degrades(self, monkeypatch):
        monkeypatch.setattr(metrics_mod, "engine", _BadEngine())
        user = SimpleNamespace(id=1, username="admin", role="admin", is_superuser=True)
        resp = await get_system_metrics(current_user=user)
        assert resp["success"] is True
        assert resp["data"]["database"]["status"] == "unavailable"


class TestGetDatabaseMetrics:
    def _db(self):
        db = MagicMock(name="db")
        result = MagicMock(name="result")
        result.scalar.return_value = 7
        db.execute.return_value = result
        return db

    async def test_table_names_truncated_over_20(self, monkeypatch):
        inspector = SimpleNamespace(get_table_names=lambda: [f"t{i}" for i in range(25)])
        monkeypatch.setattr("sqlalchemy.inspect", lambda bind: inspector)
        resp = await get_database_metrics(db=self._db(), current_user=MagicMock())
        metrics = resp["data"]["metrics"]
        assert metrics["table_count"] == 25
        assert len(metrics["table_names"]) == 20
        assert metrics["table_names_truncated"] is True

    async def test_row_count_outer_exception(self, monkeypatch):
        """内层 db.execute 失败 → logger.debug 再抛异常 → 外层兜底 (lines 263-264)"""
        inspector = SimpleNamespace(get_table_names=lambda: [])
        monkeypatch.setattr("sqlalchemy.inspect", lambda bind: inspector)
        db = self._db()
        db.execute.side_effect = RuntimeError("db fail")
        with patch.object(metrics_mod, "logger") as mock_log:
            mock_log.debug.side_effect = RuntimeError("log fail")
            resp = await get_database_metrics(db=db, current_user=MagicMock())
        assert "row_count_error" in resp["data"]["metrics"]
