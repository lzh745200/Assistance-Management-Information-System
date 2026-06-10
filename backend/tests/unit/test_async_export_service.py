"""TDD: 异步导出服务 — 100% 行覆盖."""
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta


class TestAsyncExportThreshold:
    """should_use_async: 分支全覆盖."""

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
    """estimate_record_count: 全分支覆盖."""

    def test_unknown_entity_returns_zero(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        assert AsyncExportService.estimate_record_count(db, "nonexistent", {}) == 0

    @patch("importlib.import_module")
    def test_known_entity_returns_count(self, mock_import):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        db.query.return_value.count.return_value = 42
        mock_mod = MagicMock()
        mock_import.return_value = mock_mod
        result = AsyncExportService.estimate_record_count(
            db, "supported_villages", {}
        )
        assert result == 42

    @patch("importlib.import_module", side_effect=ImportError("test error"))
    def test_import_exception_returns_zero(self, mock_import):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        result = AsyncExportService.estimate_record_count(
            db, "supported_villages", {}
        )
        assert result == 0

    @patch("importlib.import_module")
    def test_getattr_exception_returns_zero(self, mock_import):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        mock_mod = MagicMock()
        del mock_mod.SupportedVillage  # make attribute access fail
        mock_import.return_value = mock_mod
        result = AsyncExportService.estimate_record_count(
            db, "supported_villages", {}
        )
        assert result == 0


class TestExportSync:
    """同步导出方法全覆盖."""

    def test_export_supported_villages_sync(self):
        from app.services.async_export_service import AsyncExportService
        with patch("app.services.async_export_service.ExcelExportService") as MockSvc:
            instance = MockSvc.return_value
            instance.export_village_list.return_value = b"excel data"
            result = AsyncExportService.export_supported_villages_sync(
                [{"name": "test"}]
            )
            assert result == b"excel data"
            instance.export_village_list.assert_called_once_with([{"name": "test"}])

    @patch("app.services.async_export_service.ExcelExportService")
    def test_export_report_sync_supported_villages(self, MockSvc):
        from app.services.async_export_service import AsyncExportService
        instance = MockSvc.return_value
        instance.export_village_list.return_value = b"data"
        result = AsyncExportService.export_report_sync(
            "supported_villages", {"items": [1, 2]}
        )
        assert result == b"data"
        instance.export_village_list.assert_called_once_with([1, 2])

    @patch("app.services.async_export_service.ExcelExportService")
    def test_export_report_sync_funds(self, MockSvc):
        from app.services.async_export_service import AsyncExportService
        instance = MockSvc.return_value
        instance.export_fund_list.return_value = b"data"
        result = AsyncExportService.export_report_sync(
            "funds", {"items": ["f1"]}
        )
        assert result == b"data"
        instance.export_fund_list.assert_called_once_with(["f1"])

    @patch("app.services.async_export_service.ExcelExportService")
    def test_export_report_sync_projects(self, MockSvc):
        from app.services.async_export_service import AsyncExportService
        instance = MockSvc.return_value
        instance.export_project_list.return_value = b"data"
        result = AsyncExportService.export_report_sync(
            "projects", {"items": ["p1"]}
        )
        assert result == b"data"
        instance.export_project_list.assert_called_once_with(["p1"])

    @patch("app.services.async_export_service.ExcelExportService")
    def test_export_report_sync_schools(self, MockSvc):
        from app.services.async_export_service import AsyncExportService
        instance = MockSvc.return_value
        instance.export_school_list.return_value = b"data"
        result = AsyncExportService.export_report_sync(
            "schools", {"items": ["s1"]}
        )
        assert result == b"data"
        instance.export_school_list.assert_called_once_with(["s1"])

    @patch("app.services.async_export_service.ExcelExportService")
    def test_export_report_sync_comprehensive(self, MockSvc):
        from app.services.async_export_service import AsyncExportService
        instance = MockSvc.return_value
        instance.export_comprehensive_report.return_value = b"data"
        params = {
            "summary": {"total": 100},
            "village_data": [{"v": 1}],
            "project_data": [{"p": 2}],
            "fund_data": [{"f": 3}],
        }
        result = AsyncExportService.export_report_sync("comprehensive", params)
        assert result == b"data"
        instance.export_comprehensive_report.assert_called_once_with(
            {"total": 100}, [{"v": 1}], [{"p": 2}], [{"f": 3}]
        )

    @patch("app.services.async_export_service.ExcelExportService")
    def test_export_report_sync_default_fallback(self, MockSvc):
        from app.services.async_export_service import AsyncExportService
        instance = MockSvc.return_value
        instance.export_village_list.return_value = b"data"
        result = AsyncExportService.export_report_sync(
            "unknown_type", {"items": ["x"]}
        )
        assert result == b"data"
        instance.export_village_list.assert_called_once_with(["x"])

    @patch("app.services.async_export_service.ExcelExportService")
    def test_export_report_sync_default_when_items_missing(self, MockSvc):
        from app.services.async_export_service import AsyncExportService
        instance = MockSvc.return_value
        instance.export_village_list.return_value = b"data"
        result = AsyncExportService.export_report_sync("unknown_type", {})
        assert result == b"data"
        instance.export_village_list.assert_called_once_with([])


class TestExportAsync:
    """异步导出任务启动全覆盖."""

    @patch(
        "app.services.async_export_service.AsyncExportService.estimate_record_count"
    )
    @patch("app.services.async_export_service._uuid")
    @patch("app.services.async_export_service.datetime")
    def test_export_supported_villages_async(
        self, mock_dt, mock_uuid, mock_est
    ):
        from app.services.async_export_service import AsyncExportService
        from app.models.export_task import ExportTask

        mock_uuid.uuid4.return_value = "task-uuid-123"
        mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0, 0)
        mock_est.return_value = 42

        db = MagicMock()
        task = AsyncExportService.export_supported_villages_async(
            db, 1, {"filter": "test"}
        )

        assert isinstance(task, ExportTask)
        assert task.task_id == "task-uuid-123"
        assert task.user_id == 1
        assert task.export_type == "supported_villages"
        assert task.record_count == 42
        assert task.status == "pending"
        assert task.file_name == "帮扶村导出_20250101120000.xlsx"
        assert task.expires_at == datetime(2025, 1, 2, 12, 0, 0)
        db.add.assert_called_once_with(task)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(task)

class TestGetExportTask:
    """get_export_task 全覆盖."""

    def test_task_found(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        task_mock = MagicMock(id=1, status="completed")
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = task_mock
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

        result = AsyncExportService.get_export_task(db, 1)
        assert result is task_mock
        assert result.id == 1

    def test_task_not_found(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

        result = AsyncExportService.get_export_task(db, 999)
        assert result is None


class TestGetExportFile:
    """get_export_file 全覆盖."""

    def _setup_db_query(self, db, return_value):
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = return_value
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

    def test_task_not_found_returns_none(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        self._setup_db_query(db, None)
        assert AsyncExportService.get_export_file(db, 1) is None

    def test_task_no_file_path_returns_none(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        task = MagicMock()
        task.file_path = None
        self._setup_db_query(db, task)
        assert AsyncExportService.get_export_file(db, 1) is None

    def test_file_read_success(self, tmp_path):
        from app.services.async_export_service import AsyncExportService
        f = tmp_path / "export.xlsx"
        f.write_bytes(b"excel binary content")
        db = MagicMock()
        task = MagicMock()
        task.file_path = str(f)
        self._setup_db_query(db, task)
        result = AsyncExportService.get_export_file(db, 1)
        assert result == b"excel binary content"

    def test_file_not_found_error(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        task = MagicMock()
        task.file_path = os.path.join(
            os.environ.get("TEMP", "/tmp"), "nonexistent_export_12345.xlsx"
        )
        self._setup_db_query(db, task)
        result = AsyncExportService.get_export_file(db, 1)
        assert result is None


class TestGetUserExportTasks:
    """get_user_export_tasks 全覆盖."""

    def _make_query_chain(self, db, result, with_status=False):
        mock_limit = MagicMock()
        mock_limit.all.return_value = result
        mock_offset = MagicMock()
        mock_offset.limit.return_value = mock_limit
        mock_order = MagicMock()
        mock_order.offset.return_value = mock_offset

        if with_status:
            mock_status_filter = MagicMock()
            mock_status_filter.order_by.return_value = mock_order
            mock_user_filter = MagicMock()
            mock_user_filter.filter.return_value = mock_status_filter
        else:
            mock_user_filter = MagicMock()
            mock_user_filter.order_by.return_value = mock_order

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_user_filter
        db.query.return_value = mock_query

    def test_without_status_filter(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        expected = [MagicMock(id=1), MagicMock(id=2)]
        self._make_query_chain(db, expected)
        result = AsyncExportService.get_user_export_tasks(db, 1)
        assert len(result) == 2
        assert result == expected

    def test_with_status_filter(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        expected = [MagicMock(id=1)]
        self._make_query_chain(db, expected, with_status=True)
        result = AsyncExportService.get_user_export_tasks(
            db, 1, status="pending"
        )
        assert len(result) == 1
        assert result == expected

    def test_pagination_applied(self):
        from app.services.async_export_service import AsyncExportService
        db = MagicMock()
        expected = []
        self._make_query_chain(db, expected)
        result = AsyncExportService.get_user_export_tasks(
            db, 1, page=2, page_size=10
        )
        assert result == expected
