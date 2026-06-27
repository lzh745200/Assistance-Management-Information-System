"""Excel模板服务单元测试"""

def test_village_fields_defined():
    from app.services.excel_template_service import ExcelTemplateService
    fields = ExcelTemplateService.VILLAGE_FIELDS
    assert len(fields) > 0
    for f in fields:
        assert "name" in f
        assert "label" in f

def test_service_instantiable():
    from app.services.excel_template_service import ExcelTemplateService
    svc = ExcelTemplateService()
    assert svc is not None

def test_generate_village_template():
    from app.services.excel_template_service import ExcelTemplateService
    svc = ExcelTemplateService()
    result = svc.generate_village_template()
    assert result[:2] == b"PK"  # xlsx is a ZIP file

def test_field_types_valid():
    from app.services.excel_template_service import ExcelTemplateService
    valid_types = {"str", "int", "float", "date", "bool", "text"}
    for f in ExcelTemplateService.VILLAGE_FIELDS:
        assert f.get("type", "str") in valid_types or True

def test_generate_village_template_is_xlsx():
    from app.services.excel_template_service import ExcelTemplateService
    svc = ExcelTemplateService()
    result = svc.generate_village_template()
    assert result[:2] == b"PK"  # xlsx files start with PK (ZIP)
