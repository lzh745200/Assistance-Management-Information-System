"""b3 攻坚：覆盖 app.models.import_history 的状态属性与 success_rate"""
from app.models.import_history import ImportHistory, ImportStatus


class TestImportHistoryProperties:
    def test_repr(self):
        h = ImportHistory(id=1, file_name="data.xlsx", status=ImportStatus.PENDING.value)
        assert "data.xlsx" in repr(h)

    def test_is_completed(self):
        assert ImportHistory(status=ImportStatus.COMPLETED.value).is_completed is True
        assert ImportHistory(status=ImportStatus.PENDING.value).is_completed is False

    def test_is_failed(self):
        assert ImportHistory(status=ImportStatus.FAILED.value).is_failed is True
        assert ImportHistory(status=ImportStatus.PENDING.value).is_failed is False

    def test_is_processing(self):
        assert ImportHistory(status=ImportStatus.PROCESSING.value).is_processing is True
        assert ImportHistory(status=ImportStatus.PENDING.value).is_processing is False


class TestImportHistorySuccessRate:
    def test_zero_total_rows(self):
        h = ImportHistory(total_rows=0, success_rows=0)
        assert h.success_rate == 0.0

    def test_zero_success_rows(self):
        h = ImportHistory(total_rows=10, success_rows=0)
        assert h.success_rate == 0.0

    def test_normal_rate(self):
        h = ImportHistory(total_rows=10, success_rows=5)
        assert h.success_rate == 50.0
