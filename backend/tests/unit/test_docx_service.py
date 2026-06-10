"""
测试 - app.services.docx_service
覆盖率目标: 100%
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import importlib

class TestDocxService:
    """测试 DocxReportService 和 DocxService"""

    @pytest.fixture(autouse=True)
    def mock_docx(self, request):
        """Mock python-docx 模块 (skip for generate_*_report tests that need real docx)."""
        # Skip mock for tests that need real docx module
        if request.node.name.startswith('test_generate_') or request.node.name == 'test_service_creation_no_docx':
            yield
            return

        mock_docx_module = MagicMock()
        mock_docx_module.Document = MagicMock
        mock_docx_module.WD_TABLE_ALIGNMENT = MagicMock()
        mock_docx_module.WD_ALIGN_PARAGRAPH = MagicMock()
        mock_docx_module.Pt = MagicMock()
        mock_docx_module.RGBColor = MagicMock()

        sys.modules['docx'] = mock_docx_module
        sys.modules['docx.enum'] = MagicMock()
        sys.modules['docx.enum.table'] = MagicMock()
        sys.modules['docx.enum.text'] = MagicMock()
        sys.modules['docx.shared'] = MagicMock()

        yield

        # 清理
        for mod in ['docx', 'docx.enum', 'docx.enum.table', 'docx.enum.text', 'docx.shared']:
            if mod in sys.modules:
                del sys.modules[mod]

    def test_service_creation_no_docx(self):
        """测试服务创建 - python-docx 未安装"""
        # 临时移除 docx 模块
        original_docx = sys.modules.pop('docx', None)

        with patch.dict('sys.modules', {'docx': None}):
            # 重新导入模块以触发 ImportError 路径
            if 'app.services.docx_service' in sys.modules:
                del sys.modules['app.services.docx_service']

            import app.services.docx_service as docx_module
            docx_module.HAS_DOCX = False
            docx_module.Document = None

            with pytest.raises(ImportError):
                docx_module.DocxReportService()

        # 恢复模块
        if original_docx:
            sys.modules['docx'] = original_docx

    def test_service_creation(self, mock_docx):
        """测试服务创建"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()
            assert service is not None

    def test_create_document(self, mock_docx):
        """测试创建文档"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            # 只需验证方法可以执行且不抛出异常
            mock_doc = MagicMock()
            mock_doc.add_heading.return_value.alignment = None
            mock_para = MagicMock()
            mock_para.runs = [MagicMock()]
            mock_doc.add_paragraph.return_value = mock_para

            with patch('docx.Document', return_value=mock_doc):
                doc = service._create_document("Test Title", "Test Subtitle")
                assert doc is not None

    def test_create_document_no_subtitle(self, mock_docx):
        """测试创建文档 - 无副标题"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            mock_doc = MagicMock()
            mock_doc.add_heading = MagicMock(return_value=MagicMock())
            mock_doc.add_paragraph = MagicMock(return_value=MagicMock())

            with patch('docx.Document', return_value=mock_doc):
                doc = service._create_document("Test Title")
                assert doc is not None

    def test_add_table(self, mock_docx):
        """测试添加表格"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            mock_doc = MagicMock()
            mock_table = MagicMock()
            # 创建足够数量的 cells 来匹配 headers
            mock_header_cells = [MagicMock(paragraphs=[MagicMock(runs=[MagicMock()])]) for _ in range(2)]
            mock_row_cells = [MagicMock(paragraphs=[MagicMock(runs=[MagicMock()])]) for _ in range(2)]
            mock_table.rows = [MagicMock(cells=mock_header_cells), MagicMock(cells=mock_row_cells)]
            mock_doc.add_table = MagicMock(return_value=mock_table)

            headers = ["Col1", "Col2"]
            rows = [["A", "B"]]

            service._add_table(mock_doc, headers, rows)
            mock_doc.add_table.assert_called_once()

    def test_doc_to_bytes(self, mock_docx):
        """测试文档转字节"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            mock_doc = MagicMock()
            result = service._doc_to_bytes(mock_doc)
            assert isinstance(result, bytes)

    def test_generate_users_report(self, mock_docx):
        """测试生成用户报表"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            users = [
                {"id": 1, "username": "user1", "email": "user1@test.com", "full_name": "User One", "role": "admin", "is_active": True},
                {"id": 2, "username": "user2", "email": None, "full_name": None, "role": None, "is_active": False},
            ]

            mock_doc = MagicMock()
            mock_doc.add_heading = MagicMock(return_value=MagicMock())
            mock_doc.add_paragraph = MagicMock(return_value=MagicMock(
                runs=[MagicMock()],
                alignment=None
            ))
            mock_doc.add_table = MagicMock(return_value=MagicMock(
                rows=[MagicMock(cells=[MagicMock(paragraphs=[MagicMock(runs=[MagicMock()])])])]
            ))

            with patch('docx.Document', return_value=mock_doc):
                result = service.generate_users_report(users)
                assert isinstance(result, bytes)

    def test_generate_villages_report(self, mock_docx):
        """测试生成村庄报表"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            villages = [
                {"id": 1, "village_name": "Village 1", "county": "County A", "support_unit": "Unit 1", "department": "Dept 1", "is_revitalization_tier": True},
                {"id": 2, "name": "Village 2", "county": None, "support_unit": None, "department": None, "is_revitalization_tier": False},
            ]

            mock_doc = MagicMock()
            mock_doc.add_heading = MagicMock(return_value=MagicMock())
            mock_doc.add_paragraph = MagicMock(return_value=MagicMock(
                runs=[MagicMock()],
                alignment=None
            ))
            mock_doc.add_table = MagicMock(return_value=MagicMock(
                rows=[MagicMock(cells=[MagicMock(paragraphs=[MagicMock(runs=[MagicMock()])])])]
            ))

            with patch('docx.Document', return_value=mock_doc):
                result = service.generate_villages_report(villages)
                assert isinstance(result, bytes)

    def test_generate_projects_report(self, mock_docx):
        """测试生成项目报表"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            projects = [
                {"id": 1, "name": "Project 1", "type": "Type A", "status": "active", "budget": 100, "actual_cost": 80, "progress": 80},
            ]

            mock_doc = MagicMock()
            mock_doc.add_heading = MagicMock(return_value=MagicMock())
            mock_doc.add_paragraph = MagicMock(return_value=MagicMock(
                runs=[MagicMock()],
                alignment=None
            ))
            mock_doc.add_table = MagicMock(return_value=MagicMock(
                rows=[MagicMock(cells=[MagicMock(paragraphs=[MagicMock(runs=[MagicMock()])])])]
            ))

            with patch('docx.Document', return_value=mock_doc):
                result = service.generate_projects_report(projects)
                assert isinstance(result, bytes)

    def test_generate_funds_report(self, mock_docx):
        """测试生成经费报表"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxReportService
            service = DocxReportService()

            funds = [
                {"id": 1, "name": "Fund 1", "amount": 100, "status": "approved", "operator": "Operator 1", "date": "2024-01-01"},
                {"id": 2, "name": None, "amount": 0, "status": None, "operator": None, "date": None},
            ]

            mock_doc = MagicMock()
            mock_doc.add_heading = MagicMock(return_value=MagicMock())
            mock_doc.add_paragraph = MagicMock(return_value=MagicMock(
                runs=[MagicMock()],
                alignment=None
            ))
            mock_doc.add_table = MagicMock(return_value=MagicMock(
                rows=[MagicMock(cells=[MagicMock(paragraphs=[MagicMock(runs=[MagicMock()])])])]
            ))

            with patch('docx.Document', return_value=mock_doc):
                result = service.generate_funds_report(funds)
                assert isinstance(result, bytes)

class TestDocxServiceWrapper:
    """测试 DocxService 包装器"""

    @pytest.fixture(autouse=True)
    def mock_docx(self):
        """Mock python-docx 模块"""
        mock_docx_module = MagicMock()
        mock_docx_module.Document = MagicMock
        mock_docx_module.WD_TABLE_ALIGNMENT = MagicMock()
        mock_docx_module.WD_ALIGN_PARAGRAPH = MagicMock()
        mock_docx_module.Pt = MagicMock()
        mock_docx_module.RGBColor = MagicMock()

        sys.modules['docx'] = mock_docx_module
        sys.modules['docx.enum'] = MagicMock()
        sys.modules['docx.enum.table'] = MagicMock()
        sys.modules['docx.enum.text'] = MagicMock()
        sys.modules['docx.shared'] = MagicMock()

        yield

        for mod in ['docx', 'docx.enum', 'docx.enum.table', 'docx.enum.text', 'docx.shared']:
            if mod in sys.modules:
                del sys.modules[mod]

    def test_docx_service_wrapper(self, mock_docx):
        """测试 DocxService 包装器"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxService
            service = DocxService(db=None)
            assert service is not None
            assert service._service is not None

    def test_docx_service_create(self, mock_docx):
        """测试 DocxService.create 工厂方法"""
        with patch('app.services.docx_service.HAS_DOCX', True):
            from app.services.docx_service import DocxService
            service = DocxService.create(db=None)
            assert isinstance(service, DocxService)
