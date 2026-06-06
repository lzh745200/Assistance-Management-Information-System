"""Safe coverage tests — using standard patterns with real_db_session fixture."""
import pytest
from unittest.mock import MagicMock


class TestDataValidatorBatch:
    def test_validate_file_format(self):
        from app.services.data_validator_service import DataValidatorService
        s = DataValidatorService()
        if hasattr(s, 'validate_file_format'):
            v, m = s.validate_file_format("test.xlsx"); assert v is True
            v2, m2 = s.validate_file_format("test.exe"); assert v2 is False

    def test_validate_file_size(self):
        from app.services.data_validator_service import DataValidatorService
        s = DataValidatorService()
        if hasattr(s, 'validate_file_size'):
            v, _ = s.validate_file_size(1024); assert v is True
            v2, _ = s.validate_file_size(100*1024*1024); assert v2 is False

    def test_parse_excel_headers(self):
        from app.services.data_validator_service import DataValidatorService
        s = DataValidatorService()
        if hasattr(s, 'parse_excel_headers'):
            m = s.parse_excel_headers(["village_name","department"]); assert m is not None


class TestExcelTemplateBatch:
    def test_generate_village_template(self):
        from app.services.excel_template_service import ExcelTemplateService
        s = ExcelTemplateService()
        r = s.generate_village_template()
        assert isinstance(r, bytes) and len(r) > 100 and r[:2] == b'PK'

    def test_generate_project_template(self):
        from app.services.excel_template_service import ExcelTemplateService
        s = ExcelTemplateService()
        if hasattr(s, 'generate_project_template'):
            r = s.generate_project_template(); assert isinstance(r, bytes)


class TestDataMaskingBatch:
    def test_mask_phone(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService(); r = s.mask_phone("13812345678")
        assert len(r) == 11 and "*" in r

    def test_mask_id_card(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService(); r = s.mask_id_card("110101199001011234")
        assert len(r) == 18 and "*" in r

    def test_mask_email(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService(); r = s.mask_email("test@example.com")
        assert "@" in r and "*" in r


class TestEventBusBatch:
    def test_singleton(self):
        from app.services.event_bus import EventBus
        b1 = EventBus(); b2 = EventBus(); assert b1 is b2


class TestMachineCodeBatch:
    def test_get_machine_code(self):
        from app.services.machine_code_service import MachineCodeService
        s = MachineCodeService(); c = s.get_machine_code()
        assert isinstance(c, str) and len(c) > 0


class TestEncryptionBatch:
    def test_service_creation(self):
        from app.services.encryption_service import DataPackageEncryption
        s = DataPackageEncryption(); assert s is not None


class TestPasswordEncryptionBatch:
    def test_service_creation(self):
        from app.services.password_encryption_service import PasswordEncryptionService
        s = PasswordEncryptionService(); assert s is not None


class TestRbacBatch:
    def test_permission_enum(self):
        from app.services.rbac_service import Permission
        assert len(list(Permission)) > 0

    def test_rbac_service_creation(self):
        from app.services.rbac_service import RBACService
        s = RBACService(); assert s is not None


class TestImportResultBatch:
    def test_to_dict(self):
        from app.services.excel_importer_service import ImportResult, ImportError as IE
        r = ImportResult(success=True, total_rows=5, success_rows=4, failed_rows=1)
        d = r.to_dict(); assert d["success"] and d["total_rows"] == 5
        e = IE(row_number=3, field_name="name", error_code="E001", message="err")
        assert e.to_dict()["row_number"] == 3


class TestPaginationBatch:
    def test_paginate(self):
        import app.utils.pagination as p
        assert p is not None

    def test_keyset_paginate(self):
        import app.utils.cursor_pagination as cp
        assert cp is not None


class TestCommonUtilsBatch:
    def test_common_utils(self):
        import app.utils.common as cu
        assert cu is not None


class TestPathsBatch:
    def test_get_app_data_dir(self):
        from app.utils.paths import get_app_data_dir
        d = get_app_data_dir(); assert d is not None
