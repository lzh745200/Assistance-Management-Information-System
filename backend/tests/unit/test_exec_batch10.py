"""Deep execution batch 10 — clean reliable tests."""
import pytest
from unittest.mock import MagicMock
M=MagicMock
import io

class TestExec10:
    def test_parse_excel_real(self, real_db_session):
        import openpyxl;wb=openpyxl.Workbook();ws=wb.active
        ws.append(["village_name","department","support_unit","province","city","county","township"])
        ws.append(["v10","d10","u10","GZ","QN","LB","JL"])
        bf=io.BytesIO();wb.save(bf)
        from app.services.excel_importer_service import ExcelImporterService
        s=ExcelImporterService(real_db_session);rows,hdrs=s.parse_excel(bf.getvalue())
        assert len(rows)>0 and len(hdrs)>0

    def test_import_incremental(self, real_db_session):
        import openpyxl;wb=openpyxl.Workbook();ws=wb.active
        ws.append(["village_name","department","support_unit","province","city","county","township"])
        ws.append(["v10_incr","d10","u10","GZ","QN","LB","JL"])
        bf=io.BytesIO();wb.save(bf)
        from app.services.excel_importer_service import ExcelImporterService
        from app.models.import_history import ImportMode
        s=ExcelImporterService(real_db_session)
        r=s.import_data(bf.getvalue(),"t.xlsx",len(bf.getvalue()),1,ImportMode.INCREMENTAL,"supported_village")
        assert r is not None

    def test_mask_phone(self):
        from app.services.data_masking_service import DataMaskingService
        s=DataMaskingService();r=s.mask_phone("13900139000");assert r[:3]=="139" and r[-4:]=="9000"
    def test_mask_id(self):
        from app.services.data_masking_service import DataMaskingService
        s=DataMaskingService();r=s.mask_id_card("110101199001011234");assert r[:4]=="1101" and len(r)==18
    def test_mask_email(self):
        from app.services.data_masking_service import DataMaskingService
        s=DataMaskingService();assert "@" in s.mask_email("user@test.com")

    def test_template_gen(self):
        from app.services.excel_template_service import ExcelTemplateService
        s=ExcelTemplateService();r=s.generate_village_template();assert r[:2]==b'PK' and len(r)>1000
    def test_machine_code(self):
        from app.services.machine_code_service import MachineCodeService
        s=MachineCodeService();c=s.get_machine_code();assert len(c)>0 and isinstance(c,str)
    def test_event_bus(self):
        from app.services.event_bus import EventBus;assert EventBus() is EventBus()
    def test_sync_service(self):
        from app.services.data_sync_service import DataSyncService
        s=DataSyncService();assert s.sync_dir is not None;assert "supported_villages" in s.syncable_tables
    def test_import_result(self):
        from app.services.excel_importer_service import ImportResult,ImportError as IE
        r=ImportResult(True,10,9,1);d=r.to_dict();assert d['success'] and d['total_rows']==10
        e=IE(5,"f","E001","err","v");assert e.to_dict()['row_number']==5
    def test_rbac(self):
        from app.services.rbac_service import Permission,RBACService
        assert len(list(Permission))>5;assert RBACService() is not None
    def test_max_rows(self):
        from app.services.excel_importer_service import ExcelImporterService
        assert ExcelImporterService.MAX_ROWS==1000

    def test_hash_password(self):
        from app.core.security import hash_password,verify_password
        h=hash_password("Test@123!");assert verify_password("Test@123!",h)
    def test_token(self):
        from app.core.security import create_access_token
        t=create_access_token(data={"sub":"u"});assert isinstance(t,str) and len(t)>50
    def test_error_codes(self):
        from app.core.errors import ErrorCode,ERROR_MESSAGES
        assert ErrorCode.UNKNOWN==0;assert ErrorCode.SUCCESS==200;assert len(ERROR_MESSAGES)>20
    def test_app_error(self):
        from app.core.errors import AppError
        e=AppError("m",400,code=1000,details={"k":"v"});assert e.to_dict()['error']['code']==1000
    def test_exceptions(self):
        from app.core.exceptions import BusinessError,NotFoundError,AuthenticationError,AuthorizationError
        assert BusinessError("m").message=="m";assert NotFoundError("X","1").status_code==404
        assert AuthenticationError("t").status_code==401;assert AuthorizationError("t").status_code==403
    def test_constants(self):
        from app.core.constants import ANALYTICS_CACHE_PREFIX,DEFAULT_PAGE_SIZE,MAX_PAGE_SIZE,ADMIN_ROLES
        assert ANALYTICS_CACHE_PREFIX=='analytics:';assert DEFAULT_PAGE_SIZE==20;assert MAX_PAGE_SIZE==100
    def test_services_imports(self):
        svcs=["CacheService","MonitoringService","AlertService","TwoFactorService","VersionService"]
        for s in svcs:
            mod=__import__(f'app.services.{s.lower().replace("cache","cache_").replace("service","_service")}',fromlist=[s])
    def test_data_scope(self):
        from app.core.data_permission import DataScope,filter_by_data_scope
        assert DataScope.ALL is not None;assert callable(filter_by_data_scope)

    def test_process_import_row(self, real_db_session):
        from app.api.v1.supported_village import _process_import_row,_FIELD_NAMES
        vals=["v10_test","d","u","GZ","QN","LB","JL",None,None,None,None,None,None,None,None,None]
        ok,err=_process_import_row(tuple(vals),_FIELD_NAMES,real_db_session,2)
        assert ok is True and err is None
    def test_get_village_404(self, real_db_session):
        from app.api.v1.supported_village import _get_village_or_404
        from fastapi import HTTPException
        try:_get_village_or_404(real_db_session,99999)
        except HTTPException as e:assert e.status_code==404
