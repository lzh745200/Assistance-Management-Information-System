"""补齐 app.services.work_log_service 覆盖率缺口（28-34 行 create_work_log、83-88 行 user_id 为空跳过）."""
from datetime import date
from unittest.mock import MagicMock

from app.services.work_log_service import WorkLogService, write_work_log


class TestCreateWorkLog:
    def test_create_persists_log(self):
        db = MagicMock()
        svc = WorkLogService(db)
        log = svc.create_work_log(
            {"user_id": 1, "content": "走访记录", "log_date": date.today()}
        )
        db.add.assert_called_once_with(log)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(log)
        assert log.content == "走访记录"


class TestWriteWorkLogNoneUser:
    def test_skips_when_user_id_is_none(self):
        db = MagicMock()
        result = write_work_log(db, "project", "create", 1, "产业项目", user_id=None)
        assert result is None
        db.add.assert_not_called()
        db.commit.assert_not_called()
