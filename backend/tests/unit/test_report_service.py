import io
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from app.services.report_service import ReportService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def svc(mock_db):
    return ReportService(db=mock_db)


class MockSupportedVillage:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.village_name = kwargs.get("village_name", "Test Village")
        self.province = kwargs.get("province", "Guizhou")
        self.county = kwargs.get("county", "County X")
        self.is_revitalization_tier = kwargs.get("is_revitalization_tier", True)
        self.updated_at = kwargs.get("updated_at", datetime(2025, 1, 1))


class TestReportService:
    def test_constructor(self, svc, mock_db):
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_get_reports(self, svc):
        reports = await svc.get_reports()
        assert len(reports) == 2
        assert reports[0]["id"] == 1
        assert reports[0]["name"] == "村庄数据综合报表"
        assert reports[0]["type"] == "comprehensive"
        assert reports[1]["id"] == 2
        assert reports[1]["name"] == "资金使用统计报表"

    @pytest.mark.asyncio
    async def test_get_reports_with_user_id(self, svc):
        reports = await svc.get_reports(user_id=123)
        assert len(reports) == 2

    @pytest.mark.asyncio
    async def test_get_report_found(self, svc):
        report = await svc.get_report(1)
        assert report is not None
        assert report["id"] == 1

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, svc):
        report = await svc.get_report(999)
        assert report is None

    @pytest.mark.asyncio
    async def test_export_to_excel_success(self, svc):
        with patch.object(svc, "_fetch_report_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                [1, "Village A", "Guizhou", "County X", "示范级", "2025", "100", "2025-01-01"]
            ]
            result = await svc.export_to_excel({"year": 2025})
            assert isinstance(result, bytes)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_export_to_excel_no_query_params(self, svc):
        with patch.object(svc, "_fetch_report_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            result = await svc.export_to_excel()
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_export_to_excel_import_error(self, svc):
        with patch("builtins.__import__", side_effect=ImportError("no openpyxl")):
            with patch.object(svc, "_empty_excel", return_value=b"empty") as mock_empty:
                result = await svc.export_to_excel({"year": 2025})
                assert result == b"empty"
                mock_empty.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_to_excel_generic_exception(self, svc):
        with patch.object(svc, "_fetch_report_data", side_effect=Exception("DB error")):
            with pytest.raises(Exception, match="DB error"):
                await svc.export_to_excel({"year": 2025})

    @pytest.mark.asyncio
    async def test_export_to_pdf_success(self, svc):
        with patch.object(svc, "_fetch_report_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                [1, "Village A", "Guizhou", "示范级"]
            ]
            result = await svc.export_to_pdf({"report_type": "综合报表"})
            assert isinstance(result, bytes)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_export_to_pdf_no_query_params(self, svc):
        with patch.object(svc, "_fetch_report_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            result = await svc.export_to_pdf()
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_export_to_pdf_page_break(self, svc):
        with patch.object(svc, "_fetch_report_data", new_callable=AsyncMock) as mock_fetch:
            rows = [[i, f"Village {i}", "Guizhou", "示范级"] for i in range(60)]
            mock_fetch.return_value = rows
            result = await svc.export_to_pdf({"report_type": "综合报表"})
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_export_to_pdf_short_row_data(self, svc):
        with patch.object(svc, "_fetch_report_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                [1]
            ]
            result = await svc.export_to_pdf({"report_type": "综合报表"})
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_export_to_pdf_import_error(self, svc):
        with patch("builtins.__import__", side_effect=ImportError("no reportlab")):
            with patch.object(svc, "_empty_pdf", return_value=b"empty") as mock_empty:
                result = await svc.export_to_pdf({"report_type": "综合报表"})
                assert result == b"empty"
                mock_empty.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_to_pdf_generic_exception(self, svc):
        with patch.object(svc, "_fetch_report_data", side_effect=Exception("PDF gen error")):
            with pytest.raises(Exception, match="PDF gen error"):
                await svc.export_to_pdf({"report_type": "综合报表"})

    @pytest.mark.asyncio
    async def test_export_comprehensive_report(self, svc):
        with patch.object(svc, "export_to_excel", new_callable=AsyncMock) as mock_export:
            mock_export.return_value = b"excel data"
            result = await svc.export_comprehensive_report(year=2025, village_ids=[1, 2, 3])
            assert result == b"excel data"
            mock_export.assert_called_once_with({
                "year": 2025,
                "village_ids": [1, 2, 3],
                "report_type": "comprehensive",
            })

    @pytest.mark.asyncio
    async def test_export_comprehensive_report_default_year(self, svc):
        with patch.object(svc, "export_to_excel", new_callable=AsyncMock) as mock_export:
            mock_export.return_value = b"excel data"
            result = await svc.export_comprehensive_report()
            assert result == b"excel data"

    @pytest.mark.asyncio
    async def test_get_export_filename(self, svc):
        with patch("app.services.report_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 1, 12, 30, 0)
            filename = await svc.get_export_filename({"report_type": "comprehensive"})
            assert filename == "comprehensive_20250601_123000.xlsx"

    @pytest.mark.asyncio
    async def test_get_export_filename_default(self, svc):
        with patch("app.services.report_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 1, 12, 30, 0)
            filename = await svc.get_export_filename()
            assert filename == "report_20250601_123000.xlsx"

    @pytest.mark.asyncio
    async def test_get_export_filename_empty_params(self, svc):
        with patch("app.services.report_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 1, 12, 30, 0)
            filename = await svc.get_export_filename({})
            assert filename == "report_20250601_123000.xlsx"

    @pytest.mark.asyncio
    async def test_get_report_subscriptions(self, svc):
        result = await svc.get_report_subscriptions(user_id=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_create_subscription(self, svc):
        result = await svc.create_subscription(user_id=1, data={"name": "Weekly"})
        assert result["id"] == 1
        assert result["user_id"] == 1
        assert result["name"] == "Weekly"

    @pytest.mark.asyncio
    async def test_update_subscription(self, svc):
        result = await svc.update_subscription(subscription_id=5, data={"name": "Updated"})
        assert result["id"] == 5
        assert result["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, svc):
        result = await svc.cancel_subscription(subscription_id=10)
        assert result is True

    @pytest.mark.asyncio
    async def test_fetch_report_data_success(self, svc, mock_db):
        mock_village = MockSupportedVillage(
            village_name="TestV",
            province="Guizhou",
            county="CountyY",
            is_revitalization_tier=False,
            updated_at=datetime(2025, 6, 1, 10, 0, 0),
        )
        mock_db.query.return_value.limit.return_value.all.return_value = [mock_village]
        result = await svc._fetch_report_data({"year": 2025})
        assert len(result) == 1
        assert result[0][0] == 1
        assert result[0][1] == "TestV"
        assert result[0][2] == "Guizhou"
        assert result[0][3] == "CountyY"
        assert result[0][4] == "否"

    @pytest.mark.asyncio
    async def test_fetch_report_data_no_query_params(self, svc, mock_db):
        mock_db.query.return_value.limit.return_value.all.return_value = []
        result = await svc._fetch_report_data()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_report_data_exception(self, svc, mock_db):
        mock_db.query.side_effect = Exception("DB error")
        result = await svc._fetch_report_data({"year": 2025})
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_report_data_none_values(self, svc, mock_db):
        mock_village = MockSupportedVillage(
            village_name="",
            province=None,
            county=None,
            is_revitalization_tier=False,
            updated_at=None,
            id=5,
        )
        mock_db.query.return_value.limit.return_value.all.return_value = [mock_village]
        result = await svc._fetch_report_data({})
        assert len(result) == 1
        assert result[0][0] == 1
        assert result[0][1] == ""
        assert result[0][2] == ""
        assert result[0][7] == ""

    def test_empty_excel_success(self):
        result = ReportService._empty_excel()
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_empty_excel_import_error(self):
        with patch("builtins.__import__", side_effect=ImportError("no openpyxl")):
            result = ReportService._empty_excel()
            assert result == b""

    def test_empty_pdf_success(self):
        result = ReportService._empty_pdf()
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_empty_pdf_import_error(self):
        with patch("builtins.__import__", side_effect=ImportError("no reportlab")):
            result = ReportService._empty_pdf()
            assert result == b""
