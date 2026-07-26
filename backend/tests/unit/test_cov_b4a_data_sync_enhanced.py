"""覆盖率攻坚: app/services/data_sync_enhanced.py 缺口行 265/270（sync_version 过滤与排序分支）."""
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy import BigInteger, Column, DateTime, Integer, MetaData, Table


def _fake_table():
    meta = MetaData()
    return Table(
        "fake_sync_table",
        meta,
        Column("id", Integer, primary_key=True),
        Column("updated_at", DateTime),
        Column("sync_version", BigInteger),
    )


class TestGetChangedRecordsSyncVersion:
    def test_with_sync_version_and_last_version(self):
        """表含 sync_version 且 last_sync_version>0：追加版本过滤（265）与排序列（270）."""
        from app.services.data_sync_enhanced import get_changed_records

        tbl = _fake_table()
        mock_db = MagicMock()
        mock_db.execute.return_value.all.return_value = []

        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"fake_sync_table": tbl}):
            rows = get_changed_records(
                mock_db,
                "fake_sync_table",
                datetime(2024, 1, 1, 0, 0, 0),
                last_sync_version=5,
            )

        assert rows == []
        mock_db.execute.assert_called_once()

    def test_with_sync_version_default_last_version(self):
        """表含 sync_version 但 last_sync_version==0：只追加排序列（270），不加版本过滤."""
        from app.services.data_sync_enhanced import get_changed_records

        tbl = _fake_table()
        mock_db = MagicMock()
        mock_db.execute.return_value.all.return_value = []

        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"fake_sync_table": tbl}):
            rows = get_changed_records(
                mock_db,
                "fake_sync_table",
                datetime(2024, 1, 1, 0, 0, 0),
            )

        assert rows == []
