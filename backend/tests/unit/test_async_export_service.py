"""TDD: 异步导出服务."""
import pytest
from unittest.mock import MagicMock, patch
import uuid


class TestAsyncExportThreshold:
    def test_large_dataset_uses_async(self):
        from app.services.async_export_service import AsyncExportService
        assert AsyncExportService.should_use_async("supported_villages", 6000) is True

    def test_small_dataset_uses_sync(self):
        from app.services.async_export_service import AsyncExportService
        assert AsyncExportService.should_use_async("supported_villages", 500) is False

    def test_threshold_boundary(self):
        from app.services.async_export_service import AsyncExportService
        assert AsyncExportService.should_use_async("supported_villages", 5000) is False
        assert AsyncExportService.should_use_async("supported_villages", 5001) is True


class TestEstimateRecordCount:
    def test_estimate_returns_integer(self, real_db_session):
        from app.services.async_export_service import AsyncExportService
        count = AsyncExportService.estimate_record_count(real_db_session, "supported_villages", {})
        assert isinstance(count, int)
        assert count >= 0

    def test_estimate_unknown_entity_returns_zero(self):
        from app.services.async_export_service import AsyncExportService
        mock_db = MagicMock()
        count = AsyncExportService.estimate_record_count(mock_db, "nonexistent", {})
        assert count == 0


class TestExportSync:
    def test_village_export_returns_bytes(self, real_db_session):
        from app.services.async_export_service import AsyncExportService
        from app.services.export_service import ExcelExportService
        data = [{"name": "test", "department": "dept"}]
        result = AsyncExportService.export_supported_villages_sync(data)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestExportTaskManagement:
    def test_get_export_task(self, real_db_session):
        from app.services.async_export_service import AsyncExportService
        from app.models.export_task import ExportTask
        import uuid as _uuid
        task = ExportTask(
            user_id=1,
            task_id=str(_uuid.uuid4()),
            export_type="supported_villages",
            query_params={},
            file_name="test.xlsx",
            file_size=1024,
            record_count=100,
            status="completed",
            file_path="/tmp/test.xlsx",
        )
        real_db_session.add(task)
        real_db_session.commit()
        result = AsyncExportService.get_export_task(real_db_session, task.id)
        assert result is not None
        assert result.status == "completed"

    def test_get_export_file_not_found(self, real_db_session):
        from app.services.async_export_service import AsyncExportService
        result = AsyncExportService.get_export_file(real_db_session, 99999)
        assert result is None

    def test_get_user_export_tasks(self, real_db_session):
        from app.services.async_export_service import AsyncExportService
        tasks = AsyncExportService.get_user_export_tasks(real_db_session, user_id=0)
        assert isinstance(tasks, list)
