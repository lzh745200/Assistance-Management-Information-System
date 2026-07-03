from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.import_export_history_service import ImportExportHistoryService


@pytest.fixture
def db():
    db = AsyncMock()
    db.add = MagicMock()  # add() is synchronous in SQLAlchemy
    return db


@pytest.fixture
def svc(db):
    return ImportExportHistoryService(db)


class TestListHistory:
    def _setup_execute(self, db, scalar_value, items):
        execute_result = MagicMock()
        execute_result.scalar.return_value = scalar_value
        execute_result.scalars.return_value.all.return_value = items
        db.execute.return_value = execute_result

    async def test_without_user_id(self, svc, db):
        self._setup_execute(db, 5, [
            MagicMock(), MagicMock(),
        ])
        result = await svc.list_history(page=1, page_size=20)
        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 20

    async def test_with_user_id(self, svc, db):
        self._setup_execute(db, 3, [MagicMock()])
        result = await svc.list_history(page=1, page_size=10, user_id=42)
        assert result["total"] == 3
        assert len(result["items"]) == 1
        assert result["page"] == 1
        assert result["page_size"] == 10

    async def test_empty_result(self, svc, db):
        self._setup_execute(db, 0, [])
        result = await svc.list_history(page=2, page_size=50, user_id=99)
        assert result["total"] == 0
        assert result["items"] == []
        assert result["page"] == 2
        assert result["page_size"] == 50

    async def test_no_user_id_no_filter(self, svc, db):
        self._setup_execute(db, 0, [])
        result = await svc.list_history(page=1, page_size=20)
        assert result["total"] == 0
        assert result["items"] == []


class TestRecord:
    async def test_record_created(self, svc, db):
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await svc.record(
            operation_type="export",
            org_id=1,
            user_id=2,
            result="success",
        )
        db.add.assert_called_once()

    async def test_record_with_full_kwargs(self, svc, db):
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await svc.record(
            operation_type="import",
            org_id=1,
            user_id=2,
            result="success",
            file_name="test.rrs",
            file_size=1024,
            record_count=10,
        )
        db.add.assert_called_once()

    async def test_record_commits_and_refreshes(self, svc, db):
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await svc.record(
            operation_type="export",
            org_id=1,
            user_id=2,
            result="success",
        )
        db.add.assert_called_once()
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once()
