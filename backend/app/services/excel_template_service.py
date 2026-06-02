"""
Excel模板生成服务
提供帮扶村数据导入模板的生成和下载功能

Requirements: 1.1, 1.9 - 提供标准化的Excel导入模板下载功能，包含所有帮扶村字段的说明和示例数据
"""

from io import BytesIO
from typing import Any, Dict, List

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from app.services.entity_import_validator import EntityImportValidator


class ExcelTemplateService:
    """Excel模板生成服务"""

    # 帮扶村主表字段定义
    VILLAGE_FIELDS: List[Dict[str, Any]] = [
        {
            "name": "sequence_no",
            "label": "序号",
            "required": False,
            "type": "int",
            "example": "1",
            "description": "自动生成的序号",
        },
        {
            "name": "department",
            "label": "各部门各单位",
            "required": True,
            "type": "str",
            "example": "某某部门",
            "description": "所属部门名称（必填）",
        },
        {
            "name": "support_unit",
            "label": "具体帮扶单位",
            "required": True,
            "type": "str",
            "example": "某某帮扶单位",
            "description": "具体帮扶单位名称（必填）",
        },
        {
            "name": "village_name",
            "label": "定点帮扶村",
            "required": True,
            "type": "str",
            "example": "某某村",
            "description": "帮扶村名称（必填）",
        },
        {
            "name": "region_scope",
            "label": "地区范围",
            "required": False,
            "type": "str",
            "example": "西部地区",
            "description": "所属地区范围",
        },
        {
            "name": "is_three_regions",
            "label": "是否属于三区三州",
            "required": False,
            "type": "bool",
            "example": "是",
            "description": "是 / 否",
        },
        {
            "name": "is_border_area",
            "label": "是否属于边疆地区",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_ethnic_area",
            "label": "是否属于民族地区",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_revolutionary_area",
            "label": "是否属于革命地区",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_key_county",
            "label": "是否属于160个国家乡村振兴重点帮扶县",
            "required": False,
            "type": "bool",
            "example": "是",
            "description": "是 / 否",
        },
        {
            "name": "revitalization_tier",
            "label": "振兴发展梯队系列",
            "required": False,
            "type": "str",
            "example": "第一梯队",
            "description": "振兴发展梯队",
        },
        {
            "name": "is_provincial_demo",
            "label": "省级乡村振兴示范创建对象",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_hundred_village_demo",
            "label": "百村示范创建对象",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_tiered_development",
            "label": "梯次振兴发展对象",
            "required": False,
            "type": "bool",
            "example": "是",
            "description": "是 / 否",
        },
        {
            "name": "is_cross_province",
            "label": "是否跨省",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_cross_city",
            "label": "是否跨市",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_cross_unit_cooperation",
            "label": "是否跨大单位协作帮扶",
            "required": False,
            "type": "bool",
            "example": "否",
            "description": "是 / 否",
        },
        {
            "name": "is_in_overall_plan",
            "label": "是否纳入总盘子",
            "required": False,
            "type": "bool",
            "example": "是",
            "description": "是 / 否",
        },
        {
            "name": "honors",
            "label": "2021年以来获得的国家或省级表彰",
            "required": False,
            "type": "str",
            "example": "全国先进帮扶村",
            "description": "获得的表彰荣誉",
        },
    ]

    # 样式定义
    HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
    REQUIRED_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    EXAMPLE_FILL = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    THIN_BORDER = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    def __init__(self):
        pass

    def generate_village_template(self, include_example: bool = True) -> bytes:
        """
        生成帮扶村数据导入模板

        Args:
            include_example: 是否包含示例数据

        Returns:
            Excel文件的字节内容
        """
        wb = Workbook()

        # 创建数据表
        ws_data = wb.active
        ws_data.title = "帮扶村数据"
        self._create_data_sheet(ws_data, include_example)

        # 创建说明表
        ws_help = wb.create_sheet("填写说明")
        self._create_help_sheet(ws_help)

        # 保存到字节流
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def _create_data_sheet(self, ws, include_example: bool):
        """创建数据表"""
        # 写入表头
        for col_idx, field in enumerate(self.VILLAGE_FIELDS, 1):
            cell = ws.cell(row=1, column=col_idx)
            label = field["label"]
            if field["required"]:
                label = f"*{label}"
            cell.value = label
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = self.THIN_BORDER

            # 设置列宽
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max(len(label) * 2, 15)

        # 写入示例数据
        if include_example:
            for col_idx, field in enumerate(self.VILLAGE_FIELDS, 1):
                cell = ws.cell(row=2, column=col_idx)
                cell.value = field["example"]
                cell.fill = self.EXAMPLE_FILL
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = self.THIN_BORDER

        # 添加数据验证（是 / 否字段）
        bool_validation = DataValidation(type="list", formula1='"是,否"', allow_blank=True)
        bool_validation.error = "请选择是或否"
        bool_validation.errorTitle = "输入错误"

        for col_idx, field in enumerate(self.VILLAGE_FIELDS, 1):
            if field["type"] == "bool":
                col_letter = get_column_letter(col_idx)
                bool_validation.add(f"{col_letter}2:{col_letter}1001")

        ws.add_data_validation(bool_validation)

        # 冻结首行
        ws.freeze_panes = "A2"

    def _create_help_sheet(self, ws):
        """创建填写说明表"""
        # 标题
        ws.merge_cells("A1:D1")
        title_cell = ws["A1"]
        title_cell.value = "帮扶村数据导入模板填写说明"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        # 表头
        headers = ["字段名称", "是否必填", "数据类型", "说明"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_idx)
            cell.value = header
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = self.THIN_BORDER

        # 字段说明
        for row_idx, field in enumerate(self.VILLAGE_FIELDS, 4):
            ws.cell(row=row_idx, column=1).value = field["label"]
            ws.cell(row=row_idx, column=2).value = "是" if field["required"] else "否"
            ws.cell(row=row_idx, column=3).value = self._get_type_label(field["type"])
            ws.cell(row=row_idx, column=4).value = field["description"]

            for col_idx in range(1, 5):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = self.THIN_BORDER
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if field["required"] and col_idx == 2:
                    cell.fill = self.REQUIRED_FILL

        # 设置列宽
        ws.column_dimensions["A"].width = 35
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 12
        ws.column_dimensions["D"].width = 50

        # 添加注意事项
        note_row = len(self.VILLAGE_FIELDS) + 6
        ws.merge_cells(f"A{note_row}:D{note_row}")
        note_cell = ws.cell(row=note_row, column=1)
        note_cell.value = "注意事项："
        note_cell.font = Font(bold=True, size=12)

        notes = [
            "1. 带*号的字段为必填字段，不能为空",
            "2. 是 / 否字段请填写'是'或'否'",
            "3. 单次导入最多支持1000条记录",
            "4. 请勿修改表头名称和顺序",
            "5. 示例数据行（绿色背景）在导入时会被忽略",
        ]

        for idx, note in enumerate(notes, 1):
            cell = ws.cell(row=note_row + idx, column=1)
            cell.value = note
            ws.merge_cells(f"A{note_row + idx}:D{note_row + idx}")

    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取字段映射（Excel列名 -> 数据库字段名）

        Returns:
            字段映射字典
        """
        return {field["label"]: field["name"] for field in self.VILLAGE_FIELDS}

    def get_required_fields(self) -> List[str]:
        """
        获取必填字段列表

        Returns:
            必填字段名称列表
        """
        return [field["name"] for field in self.VILLAGE_FIELDS if field["required"]]

    def get_field_types(self) -> Dict[str, str]:
        """
        获取字段类型映射

        Returns:
            字段类型字典
        """
        return {field["name"]: field["type"] for field in self.VILLAGE_FIELDS}

    # ============== 通用实体模板生成 ==============

    def generate_project_template(self, include_example: bool = True) -> bytes:
        """生成项目导入模板"""
        return self._generate_entity_template("project", "项目数据导入模板", include_example)

    def generate_fund_template(self, include_example: bool = True) -> bytes:
        """生成资金导入模板"""
        return self._generate_entity_template("fund", "资金台账导入模板", include_example)

    def generate_school_template(self, include_example: bool = True) -> bytes:
        """生成学校导入模板"""
        return self._generate_entity_template("school", "学校信息导入模板", include_example)

    def _generate_entity_template(self, entity_type: str, title: str, include_example: bool = True) -> bytes:
        """通用实体模板生成器"""
        validator = EntityImportValidator(entity_type)
        fields = validator.get_field_definitions()

        wb = Workbook()
        ws_data = wb.active
        ws_data.title = f"{validator.config.get('label', '数据')}导入"
        self._create_entity_data_sheet(ws_data, fields, include_example, validator)

        ws_help = wb.create_sheet("填写说明")
        self._create_entity_help_sheet(ws_help, title, fields)

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def _create_entity_data_sheet(
        self, ws, fields: List[Dict[str, Any]], include_example: bool, validator: EntityImportValidator
    ):
        """创建实体数据表"""
        for col_idx, field in enumerate(fields, 1):
            cell = ws.cell(row=1, column=col_idx)
            label = field["label"]
            if field["required"]:
                label = f"*{label}"
            cell.value = label
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = self.THIN_BORDER

            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max(len(label) * 2, 15)

        if include_example:
            for col_idx, field in enumerate(fields, 1):
                cell = ws.cell(row=2, column=col_idx)
                cell.value = field.get("example", "")
                cell.fill = self.EXAMPLE_FILL
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = self.THIN_BORDER

        # 枚举字段添加下拉验证
        for col_idx, field in enumerate(fields, 1):
            ftype = field.get("type", "")
            if ftype in (
                "bool",
                "project_type",
                "project_status",
                "fund_type",
                "fund_source",
                "fund_status",
                "school_type",
                "support_status",
            ):
                col_letter = get_column_letter(col_idx)
                if ftype == "bool":
                    formula = '"是,否"'
                elif ftype in validator.ENUM_VALUES:
                    formula = f'"{",".join(validator.ENUM_VALUES[ftype])}"'
                else:
                    continue
                dv = DataValidation(type="list", formula1=formula, allow_blank=True)
                dv.error = "请选择下拉列表中的值"
                dv.errorTitle = "输入错误"
                dv.add(f"{col_letter}2:{col_letter}1001")
                ws.add_data_validation(dv)

        ws.freeze_panes = "A2"

    def _create_entity_help_sheet(self, ws, title: str, fields: List[Dict[str, Any]]):
        """创建实体填写说明表"""
        ws.merge_cells("A1:D1")
        ws["A1"].value = title + "填写说明"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

        headers = ["字段名称", "是否必填", "数据类型", "说明"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_idx)
            cell.value = header
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = self.THIN_BORDER

        for row_idx, field in enumerate(fields, 4):
            ws.cell(row=row_idx, column=1).value = field["label"]
            ws.cell(row=row_idx, column=2).value = "是" if field["required"] else "否"
            ws.cell(row=row_idx, column=3).value = self._get_type_label(field["type"])
            ws.cell(row=row_idx, column=4).value = field.get("description", "")

            for col_idx in range(1, 5):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = self.THIN_BORDER
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if field["required"] and col_idx == 2:
                    cell.fill = self.REQUIRED_FILL

        ws.column_dimensions["A"].width = 35
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 12
        ws.column_dimensions["D"].width = 50

        note_row = len(fields) + 6
        ws.merge_cells(f"A{note_row}:D{note_row}")
        ws.cell(row=note_row, column=1).value = "注意事项："
        ws.cell(row=note_row, column=1).font = Font(bold=True, size=12)

        notes = [
            "1. 带*号的字段为必填字段，不能为空",
            "2. 日期字段请使用 YYYY-MM-DD 格式",
            "3. 是 / 否字段请填写'是'或'否'",
            "4. 单次导入最多支持1000条记录",
            "5. 请勿修改表头名称和顺序",
        ]
        for idx, note in enumerate(notes, 1):
            cell = ws.cell(row=note_row + idx, column=1)
            cell.value = note
            ws.merge_cells(f"A{note_row + idx}:D{note_row + idx}")

    def _get_type_label(self, type_str: str) -> str:
        """获取类型标签（扩展版）"""
        type_map = {
            "str": "文本",
            "int": "整数",
            "float": "数字",
            "bool": "是 / 否",
            "date": "日期",
            "phone": "手机号",
            "county": "区县",
            "project_type": "项目类型",
            "project_status": "项目状态",
            "fund_type": "资金类型",
            "fund_source": "资金来源",
            "fund_status": "资金状态",
            "school_type": "学校类型",
            "support_status": "帮扶状态",
        }
        return type_map.get(type_str, "文本")
