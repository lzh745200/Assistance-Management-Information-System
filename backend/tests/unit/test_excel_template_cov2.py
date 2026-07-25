# -*- coding: utf-8 -*-
"""excel_template_service 覆盖率补测：_add_validation 各枚举分支 + 三个映射方法"""

from unittest.mock import MagicMock

from app.services.excel_template_service import ExcelTemplateService


def test_add_validation_all_enum_branches():
    ws = MagicMock()
    fields = [
        {"name": "f_bool", "type": "bool"},
        {"name": "f_ptype", "type": "project_type"},
        {"name": "f_pstatus", "type": "project_status"},
        {"name": "f_ftype", "type": "fund_type"},
        {"name": "f_fsource", "type": "fund_source"},
        {"name": "f_fstatus", "type": "fund_status"},
        {"name": "f_stype", "type": "school_type"},
        {"name": "f_sstatus", "type": "support_status"},
        {"name": "f_text", "type": "text"},  # 未命中 → continue
    ]
    validator = MagicMock()
    validator.ENUM_VALUES = {}
    ExcelTemplateService._add_validation(ws, fields, 2, 100, validator=validator)
    # 8 个命中分支各添加一个 DataValidation（text 分支 continue 不添加）
    assert ws.add_data_validation.call_count == 8


def test_add_validation_with_validator_enum():
    ws = MagicMock()
    fields = [{"name": "f_custom", "type": "custom_enum"}]
    validator = MagicMock()
    validator.ENUM_VALUES = {"custom_enum": ["甲", "乙"]}
    ExcelTemplateService._add_validation(ws, fields, 2, 10, validator=validator)
    ws.add_data_validation.assert_called_once()


def test_field_mappings():
    svc = ExcelTemplateService()
    mapping = svc.get_field_mapping()
    assert mapping
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items())
    required = svc.get_required_fields()
    assert required
    assert all(f["required"] for f in svc.VILLAGE_FIELDS if f["name"] in required)
    types = svc.get_field_types()
    assert set(types.keys()) == {f["name"] for f in svc.VILLAGE_FIELDS}
