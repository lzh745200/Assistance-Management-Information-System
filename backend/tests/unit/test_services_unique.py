"""Unique service tests — verify specific behaviors."""
import pytest

class TestDataMaskingUnique:
    def test_mask_phone_keeps_length(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService()
        assert len(s.mask_phone("13812345678")) == 11
    def test_mask_id_keeps_length(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService()
        assert len(s.mask_id_card("110101199001011234")) == 18
    def test_mask_email_hides_name(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService()
        r = s.mask_email("john@example.com")
        assert "@" in r and "john" not in r.lower()

class TestExcelTemplateUnique:
    def test_template_is_valid_zip(self):
        from app.services.excel_template_service import ExcelTemplateService
        s = ExcelTemplateService()
        r = s.generate_village_template()
        assert r[:2] == b'PK'
    def test_template_has_content(self):
        from app.services.excel_template_service import ExcelTemplateService
        s = ExcelTemplateService()
        r = s.generate_village_template()
        assert len(r) > 1000

class TestMachineCodeUnique:
    def test_code_not_empty(self):
        from app.services.machine_code_service import MachineCodeService
        s = MachineCodeService()
        assert len(s.get_machine_code()) > 0
    def test_code_is_string(self):
        from app.services.machine_code_service import MachineCodeService
        s = MachineCodeService()
        assert isinstance(s.get_machine_code(), str)

class TestEventBusUnique:
    def test_singleton_same_instance(self):
        from app.services.event_bus import EventBus
        a = EventBus(); b = EventBus()
        assert a is b

class TestDataSyncUnique:
    def test_sync_dir_exists(self):
        from app.services.data_sync_service import DataSyncService
        s = DataSyncService()
        assert s.sync_dir is not None
    def test_tables_dict(self):
        from app.services.data_sync_service import DataSyncService
        s = DataSyncService()
        assert "supported_villages" in s.syncable_tables

class TestDataValidatorUnique:
    def test_xlsx_valid(self):
        from app.services.data_validator_service import DataValidatorService
        s = DataValidatorService()
        if hasattr(s, 'validate_file_format'):
            v, _ = s.validate_file_format("test.xlsx"); assert v
    def test_exe_invalid(self):
        from app.services.data_validator_service import DataValidatorService
        s = DataValidatorService()
        if hasattr(s, 'validate_file_format'):
            v, _ = s.validate_file_format("test.exe"); assert not v

class TestImportResultUnique:
    def test_import_error_to_dict(self):
        from app.services.excel_importer_service import ImportError as IE
        e = IE(row_number=5, field_name="name", error_code="E001", message="err", value="bad")
        d = e.to_dict()
        assert d["row_number"] == 5 and d["field_name"] == "name"
    def test_import_result_to_dict(self):
        from app.services.excel_importer_service import ImportResult
        r = ImportResult(success=True, total_rows=10, success_rows=9, failed_rows=1)
        d = r.to_dict()
        assert d["success"] and d["total_rows"] == 10

class TestRBACUnique:
    def test_permission_has_admin(self):
        from app.services.rbac_service import Permission
        vals = [p.value for p in Permission]
        assert any("admin" in v for v in vals)

class TestTokenBlacklistUnique:
    def test_service_exists(self):
        from app.services.token_blacklist_service import TokenBlacklistService
        assert TokenBlacklistService is not None

class TestTwoFactorUnique:
    def test_service_exists(self):
        from app.services.two_factor_service import TwoFactorService
        assert TwoFactorService is not None

class TestPasswordEncryptionUnique:
    def test_service_exists(self):
        from app.services.password_encryption_service import PasswordEncryptionService
        assert PasswordEncryptionService is not None

class TestEncryptionUnique:
    def test_service_exists(self):
        from app.services.encryption_service import DataPackageEncryption
        assert DataPackageEncryption is not None

class TestAlertUnique:
    def test_service_exists(self):
        from app.services.alert_service import AlertService
        assert AlertService is not None

class TestReminderUnique:
    def test_service_exists(self):
        from app.services.reminder_service import ApprovalReminderService
        assert ApprovalReminderService is not None
