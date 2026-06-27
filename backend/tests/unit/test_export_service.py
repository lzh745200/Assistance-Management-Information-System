"""
Excel 导出服务单元测试
覆盖: app/services/export_service.py
"""
import pytest


@pytest.fixture
def export_svc():
    from app.services.export_service import ExcelExportService
    return ExcelExportService()


class TestExcelExportService:
    def test_create_workbook_returns_bytes(self, export_svc):
        headers = ["ID", "名称", "状态"]
        rows = [
            {"ID": 1, "名称": "测试村", "状态": "正常"},
            {"ID": 2, "名称": "测试村2", "状态": "正常"},
        ]
        wb = export_svc._create_workbook("测试", headers, rows)
        assert wb is not None
        # Verify sheet name
        assert wb.active.title == "测试"

    def test_create_workbook_with_empty_rows(self, export_svc):
        headers = ["ID", "名称"]
        wb = export_svc._create_workbook("空数据", headers, [])
        assert wb is not None

    def test_to_bytes(self, export_svc):
        wb = export_svc._create_workbook("Sheet1", ["A", "B"], [{"A": 1, "B": 2}])
        data = export_svc._to_bytes(wb)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_export_user_list(self, export_svc):
        data = [
            {"id": 1, "username": "admin", "full_name": "Admin", "role": "admin", "is_active": True}
        ]
        result = export_svc.export_user_list(data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_village_list(self, export_svc):
        data = [{"id": 1, "name": "测试村", "province": "测试省"}]
        result = export_svc.export_village_list(data)
        assert isinstance(result, bytes)

    def test_export_school_list(self, export_svc):
        data = [{"id": 1, "name": "测试学校"}]
        result = export_svc.export_school_list(data)
        assert isinstance(result, bytes)

    def test_export_project_list(self, export_svc):
        data = [{"id": 1, "name": "测试项目"}]
        result = export_svc.export_project_list(data)
        assert isinstance(result, bytes)

    def test_export_fund_list(self, export_svc):
        data = [{"id": 1, "name": "测试经费"}]
        result = export_svc.export_fund_list(data)
        assert isinstance(result, bytes)

    def test_headers_and_styles_applied(self, export_svc):
        """Verify headers use bold font and specific fill color."""
        headers = ["ID", "名称"]
        rows = [{"ID": 1, "名称": "测试"}]
        wb = export_svc._create_workbook("样式测试", headers, rows)
        ws = wb.active

        # Header should be bold and have fill
        header_cell = ws.cell(row=1, column=1)
        assert header_cell.font.bold is True
        assert header_cell.font.color is not None
        assert header_cell.fill.start_color.rgb == "004472C4"

    def test_column_auto_width(self, export_svc):
        """Verify that columns have reasonable width after auto-fit."""
        headers = ["ID", "一个很长的列名用于测试宽度"]
        rows = [{"ID": 1, "一个很长的列名用于测试宽度": "更长更长更长的数据值"}]
        wb = export_svc._create_workbook("列宽测试", headers, rows)
        ws = wb.active

        # Column width should be set (not default)
        col_a_width = ws.column_dimensions["A"].width
        col_b_width = ws.column_dimensions["B"].width
        assert col_a_width is not None
        assert col_b_width is not None
        # The long column should be wider
        assert col_b_width >= col_a_width
