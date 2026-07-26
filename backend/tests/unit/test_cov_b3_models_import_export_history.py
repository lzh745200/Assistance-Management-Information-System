"""b3 攻坚：覆盖 app.models.import_export_history 的 is_success / is_failed 属性"""
from app.models.import_export_history import (
    ImportExportHistory,
    OperationResult,
    OperationType,
)


class TestImportExportHistoryProperties:
    def test_repr(self):
        h = ImportExportHistory(id=1, operation_type=OperationType.EXPORT.value, result="success")
        assert "export" in repr(h)

    def test_is_success_true(self):
        h = ImportExportHistory(result=OperationResult.SUCCESS.value)
        assert h.is_success is True
        assert h.is_failed is False

    def test_is_failed_true(self):
        h = ImportExportHistory(result=OperationResult.FAILED.value)
        assert h.is_failed is True
        assert h.is_success is False

    def test_partial_result(self):
        h = ImportExportHistory(result=OperationResult.PARTIAL.value)
        assert h.is_success is False
        assert h.is_failed is False
