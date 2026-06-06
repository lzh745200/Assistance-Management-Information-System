"""Test enum values and constants."""
import pytest

class TestErrorCodes:
    def test_unknown_is_0(self):
        from app.core.errors import ErrorCode; assert ErrorCode.UNKNOWN == 0
    def test_success_is_200(self):
        from app.core.errors import ErrorCode; assert ErrorCode.SUCCESS == 200
    def test_not_found_is_404(self):
        from app.core.errors import ErrorCode; assert ErrorCode.NOT_FOUND == 404
    def test_unauthorized_is_401(self):
        from app.core.errors import ErrorCode; assert ErrorCode.UNAUTHORIZED == 401
    def test_forbidden_is_403(self):
        from app.core.errors import ErrorCode; assert ErrorCode.FORBIDDEN == 403
    def test_internal_error_is_500(self):
        from app.core.errors import ErrorCode; assert ErrorCode.INTERNAL_ERROR == 500
    def test_validation_error_code(self):
        from app.core.errors import ErrorCode; assert ErrorCode.VALIDATION_ERROR == 422

class TestPhaseLabels:
    def test_phase1(self):
        from app.models.fund_lifecycle import PHASE_LABELS; assert len(PHASE_LABELS) > 0
    def test_phase_labels_keys(self):
        from app.models.fund_lifecycle import PHASE_LABELS
        for i in range(1,8): assert i in PHASE_LABELS

class TestPhaseStatusValues:
    def test_not_started(self):
        from app.models.fund_lifecycle import PhaseStatus; assert PhaseStatus.NOT_STARTED == 'not_started'
    def test_in_progress(self):
        from app.models.fund_lifecycle import PhaseStatus; assert PhaseStatus.IN_PROGRESS == 'in_progress'
    def test_completed(self):
        from app.models.fund_lifecycle import PhaseStatus; assert PhaseStatus.COMPLETED == 'completed'

class TestConstants:
    def test_cache_prefix(self):
        from app.core.constants import ANALYTICS_CACHE_PREFIX; assert ANALYTICS_CACHE_PREFIX == 'analytics:'
    def test_default_page_size(self):
        from app.core.constants import DEFAULT_PAGE_SIZE; assert DEFAULT_PAGE_SIZE == 20
    def test_max_page_size(self):
        from app.core.constants import MAX_PAGE_SIZE; assert MAX_PAGE_SIZE == 100
    def test_admin_roles(self):
        from app.core.constants import ADMIN_ROLES; assert 'admin' in ADMIN_ROLES

class TestPermissionEnumValues:
    def test_admin_all_exists(self):
        from app.services.rbac_service import Permission
        vals = [p.value for p in Permission]; assert any('admin' in v for v in vals)
    def test_village_read_exists(self):
        from app.services.rbac_service import Permission
        vals = [p.value for p in Permission]; assert any('village' in v for v in vals)
    def test_permission_count(self):
        from app.services.rbac_service import Permission
        assert len(list(Permission)) > 10

class TestDataSyncValues:
    def test_tables_dict_size(self):
        from app.services.data_sync_service import DataSyncService
        s = DataSyncService(); assert len(s.syncable_tables) > 0
    def test_village_label(self):
        from app.services.data_sync_service import DataSyncService
        s = DataSyncService(); assert s.syncable_tables.get('supported_villages') is not None

class TestExcelImporterValues:
    def test_max_rows(self):
        from app.services.excel_importer_service import ExcelImporterService
        assert ExcelImporterService.MAX_ROWS == 1000
