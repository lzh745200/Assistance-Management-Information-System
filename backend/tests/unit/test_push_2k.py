"""Real function call tests with output verification."""
import pytest

class TC1:
    def t1(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService()
        r1 = s.mask_phone("13912345678"); assert r1[:3] == "139" and r1[-4:] == "5678"
        r2 = s.mask_phone("13800001111"); assert len(r2) == 11
    def t2(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService()
        r1 = s.mask_id_card("110101199001011234"); assert r1[:4] == "1101" and r1[-2:] == "34"
        r2 = s.mask_id_card("123456789012345678"); assert len(r2) == 18
    def t3(self):
        from app.services.data_masking_service import DataMaskingService
        s = DataMaskingService()
        r1 = s.mask_email("admin@army.mil.cn"); assert "@" in r1 and "army" not in r1
        r2 = s.mask_email("user@test.com"); assert "@" in r2
    def t4(self):
        from app.services.excel_template_service import ExcelTemplateService
        s = ExcelTemplateService()
        r = s.generate_village_template()
        assert len(r) > 1000; assert r[:2] == b'PK'; assert r[-1:] != b'\n'
    def t5(self):
        from app.services.machine_code_service import MachineCodeService
        s = MachineCodeService()
        c1 = s.get_machine_code(); c2 = s.get_machine_code()
        assert c1 == c2  # cached, should be same
    def t6(self):
        from app.services.event_bus import EventBus
        a = EventBus(); b = EventBus(); c = EventBus()
        assert a is b is c  # singleton
    def t7(self):
        from app.core.security import hash_password, verify_password
        h = hash_password("Test1234!")
        assert verify_password("Test1234!", h) is True
        assert verify_password("WrongPassword", h) is False
    def t8(self):
        from app.core.security import create_access_token
        t = create_access_token(data={"sub": "test_user_123"})
        assert isinstance(t, str); assert len(t) > 50
    def t9(self):
        from app.services.data_sync_service import DataSyncService
        s = DataSyncService()
        assert "supported_villages" in s.syncable_tables
        assert s.syncable_tables["supported_villages"] is not None
    def t10(self):
        import app.utils.paths as p
        d = p.get_app_data_dir(); assert d is not None; assert d.exists()
    def t11(self):
        from app.services.excel_importer_service import ImportResult, ImportError as IE
        r = ImportResult(True, 5, 4, 1)
        d = r.to_dict(); assert d['success'] and d['total_rows'] == 5
        e = IE(3, "name", "E001", "test")
        assert e.to_dict()["row_number"] == 3
    def t12(self):
        from app.core.constants import ADMIN_ROLES, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
        assert isinstance(ADMIN_ROLES, (set, frozenset))
        assert DEFAULT_PAGE_SIZE == 20; assert MAX_PAGE_SIZE == 100
    def t13(self):
        from app.core.errors import ErrorCode, get_error_message
        assert get_error_message(ErrorCode.NOT_FOUND) is not None
        assert get_error_message(ErrorCode.SUCCESS) is not None
    def t14(self):
        from app.core.exceptions import AppError, BusinessError, NotFoundError
        e1 = AppError("test", 400); assert e1.to_dict() is not None
        e2 = BusinessError("biz"); assert e2.message == "biz"
        e3 = NotFoundError("User", "123"); assert e3.status_code == 404
    def t15(self):
        from app.models.fund_lifecycle import PHASE_LABELS, PhaseStatus
        assert PHASE_LABELS[1] is not None; assert PHASE_LABELS[7] is not None
        assert PhaseStatus.NOT_STARTED.value == 'not_started'
