"""app.api.v1.work_logs 覆盖补全 — log_date 字符串转 date 对象分支 (line 203).

WorkLogCreate schema 将 log_date 声明为 date 类型，HTTP 层总是已解析对象，
因此直接调用端点函数并构造字符串 log_date。
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.api.v1.work_logs import create_work_log


class TestCreateWorkLog:
    async def test_string_log_date_converted(self):
        data = MagicMock(name="data")
        data.model_dump.return_value = {
            "log_date": "2026-07-21",
            "content": "  走访帮扶村  ",
            "category": "daily",
        }

        db = MagicMock(name="db")
        user = SimpleNamespace(id=1, username="zhang", role="user", is_superuser=False)

        with patch("app.api.v1.work_logs.safe_commit"):
            result = await create_work_log(data=data, current_user=user, db=db)

        # line 203: 字符串日期被转为 date 对象
        log = db.add.call_args[0][0]
        assert log.log_date == date(2026, 7, 21)
        assert log.content == "走访帮扶村"
        assert result.work_date == "2026-07-21"
