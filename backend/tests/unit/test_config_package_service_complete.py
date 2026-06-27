"""
完整测试 - app.services.config_package_service
覆盖率目标: 100%
"""
import json
from unittest.mock import MagicMock, patch

class TestConstants:
    """测试常量"""

    def test_current_version(self):
        """测试当前版本号"""
        from app.services.config_package_service import CURRENT_VERSION
        assert CURRENT_VERSION == "1.0"

class TestConfigPackageServiceCreation:
    """测试 ConfigPackageService 创建"""

    def test_service_creation(self):
        """测试创建服务"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)
        assert service.db is mock_db

class TestExportPackage:
    """测试 export_package 方法"""

    @patch('app.utils.paths.get_uploads_path')
    @patch('app.services.config_package_service.os.makedirs')
    @patch('app.services.config_package_service.zipfile.ZipFile')
    @patch('app.services.config_package_service.logger')
    def test_export_all_users_and_orgs(self, mock_logger, mock_zipfile, mock_makedirs, mock_get_uploads):
        """测试导出所有用户和组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()

        # 模拟用户 - 使用简单对象而不是MagicMock来避免JSON序列化问题
        class MockUser:
            username = "testuser"
            hashed_password = "hashed_pw"
            full_name = "Test User"
            email = "test@example.com"
            phone = "123456789"
            role = "user"
            department = "IT"
            position = "Developer"
            organization_id = 1
            is_superuser = False

        # 模拟组织
        class MockOrg:
            id = 1
            name = "Test Org"
            code = "ORG001"
            parent_id = None
            level = 1
            type = "company"
            org_type = "company"
            sort_order = 0
            description = "Test"
            contact_person = "Contact"
            contact_phone = "123"
            is_active = True

        # 设置mock返回值 - 使用side_effect来区分不同查询
        def mock_query(model):
            mock_q = MagicMock()
            if model.__name__ == 'User':
                mock_q.filter.return_value.all.return_value = [MockUser()]
            elif model.__name__ == 'Organization':
                mock_q.all.return_value = [MockOrg()]
            return mock_q

        mock_db.query.side_effect = mock_query
        mock_get_uploads.return_value = "/tmp/uploads"

        service = ConfigPackageService(db=mock_db)
        result = service.export_package(export_all_users=True, export_all_orgs=True)

        assert result["user_count"] == 1
        assert result["org_count"] == 1
        assert "file_path" in result
        assert "file_name" in result
        mock_zipfile.assert_called_once()

    @patch('app.utils.paths.get_uploads_path')
    @patch('app.services.config_package_service.os.makedirs')
    @patch('app.services.config_package_service.zipfile.ZipFile')
    def test_export_specific_users(self, mock_zipfile, mock_makedirs, mock_get_uploads):
        """测试导出指定用户"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()

        class MockUser:
            username = "user1"
            hashed_password = "pw"
            full_name = "User One"
            email = None
            phone = None
            role = None
            department = None
            position = None
            organization_id = None
            is_superuser = None

        class MockOrg:
            id = 1
            name = "Default Org"
            code = "DEF001"
            parent_id = None
            level = 1
            type = "company"
            org_type = "company"
            sort_order = 0
            description = None
            contact_person = None
            contact_phone = None
            is_active = True

        def mock_query(model):
            mock_q = MagicMock()
            if model.__name__ == 'User':
                mock_q.filter.return_value.all.return_value = [MockUser()]
            elif model.__name__ == 'Organization':
                mock_q.all.return_value = [MockOrg()]
            return mock_q

        mock_db.query.side_effect = mock_query
        mock_get_uploads.return_value = "/tmp/uploads"

        service = ConfigPackageService(db=mock_db)
        result = service.export_package(user_ids=[1])

        assert result["user_count"] == 1
        assert "config_package_" in result["file_name"]

    @patch('app.utils.paths.get_uploads_path')
    @patch('app.services.config_package_service.os.makedirs')
    @patch('app.services.config_package_service.zipfile.ZipFile')
    def test_export_with_linked_orgs(self, mock_zipfile, mock_makedirs, mock_get_uploads):
        """测试导出时自动包含关联组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()

        class MockUser:
            username = "user1"
            hashed_password = "pw"
            full_name = "User One"
            email = None
            phone = None
            role = "user"
            department = None
            position = None
            organization_id = 1
            is_superuser = False

        class MockOrg:
            id = 1
            name = "Linked Org"
            code = "LINK001"
            parent_id = None
            level = 1
            type = "company"
            org_type = "company"
            sort_order = 0
            description = "Test"
            contact_person = "Contact"
            contact_phone = "123"
            is_active = True

        def mock_query(model):
            mock_q = MagicMock()
            if model.__name__ == 'User':
                mock_q.filter.return_value.all.return_value = [MockUser()]
            elif model.__name__ == 'Organization':
                mock_q.filter.return_value.all.return_value = [MockOrg()]
            return mock_q

        mock_db.query.side_effect = mock_query
        mock_get_uploads.return_value = "/tmp/uploads"

        service = ConfigPackageService(db=mock_db)

        with patch.object(service, '_expand_parent_orgs', return_value=[MockOrg()]):
            result = service.export_package(user_ids=[1])

        assert result["user_count"] == 1

    @patch('app.utils.paths.get_uploads_path')
    @patch('app.services.config_package_service.os.makedirs')
    @patch('app.services.config_package_service.zipfile.ZipFile')
    def test_export_specific_orgs(self, mock_zipfile, mock_makedirs, mock_get_uploads):
        """测试导出指定组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()

        class MockOrg:
            id = 1
            name = "Org 1"
            code = "ORG001"
            parent_id = None
            level = 1
            type = "company"
            org_type = "company"
            sort_order = 0
            description = None
            contact_person = None
            contact_phone = None
            is_active = True

        def mock_query(model):
            mock_q = MagicMock()
            if model.__name__ == 'Organization':
                mock_q.filter.return_value.all.return_value = [MockOrg()]
            return mock_q

        mock_db.query.side_effect = mock_query
        mock_get_uploads.return_value = "/tmp/uploads"

        service = ConfigPackageService(db=mock_db)
        result = service.export_package(org_ids=[1], export_all_orgs=False)

        assert result["org_count"] == 1

class TestExpandParentOrgs:
    """测试 _expand_parent_orgs 方法"""

    def test_expand_no_parents(self):
        """测试无需扩展父组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.parent_id = None

        result = service._expand_parent_orgs([mock_org])

        assert len(result) == 1
        assert result[0].id == 1

    def test_expand_with_parents(self):
        """测试扩展父组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        mock_child = MagicMock()
        mock_child.id = 2
        mock_child.parent_id = 1

        mock_parent = MagicMock()
        mock_parent.id = 1
        mock_parent.parent_id = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_parent]

        result = service._expand_parent_orgs([mock_child])

        assert len(result) == 2
        assert result[0].id == 2
        assert result[1].id == 1

    def test_expand_multiple_levels(self):
        """测试多级父组织扩展"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        mock_grandchild = MagicMock()
        mock_grandchild.id = 3
        mock_grandchild.parent_id = 2

        mock_parent = MagicMock()
        mock_parent.id = 2
        mock_parent.parent_id = 1

        mock_grandparent = MagicMock()
        mock_grandparent.id = 1
        mock_grandparent.parent_id = None

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_parent],
            [mock_grandparent],
        ]

        result = service._expand_parent_orgs([mock_grandchild])

        assert len(result) == 3

    def test_expand_parents_not_found(self):
        """测试父组织不存在的情况"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        mock_child = MagicMock()
        mock_child.id = 2
        mock_child.parent_id = 999  # 不存在的父组织

        # 父组织查询返回空
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service._expand_parent_orgs([mock_child])

        # 应该只有子组织，没有父组织
        assert len(result) == 1
        assert result[0].id == 2

class TestImportPackage:
    """测试 import_package 方法"""

    def test_import_file_not_found(self):
        """测试导入不存在的文件"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        with patch('app.services.config_package_service.os.path.exists', return_value=False):
            result = service.import_package("/nonexistent/file.zip")

        assert result["success"] is False
        assert "文件不存在" in result["message"]

    def test_import_not_zip_file(self):
        """测试导入非ZIP文件"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        with patch('app.services.config_package_service.os.path.exists', return_value=True):
            with patch('app.services.config_package_service.zipfile.is_zipfile', return_value=False):
                result = service.import_package("/path/to/file.txt")

        assert result["success"] is False
        assert "不是有效的ZIP文件" in result["message"]

    def test_import_missing_config_json(self):
        """测试导入缺少config.json的ZIP"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        with patch('app.services.config_package_service.os.path.exists', return_value=True):
            with patch('app.services.config_package_service.zipfile.is_zipfile', return_value=True):
                mock_zip = MagicMock()
                mock_zip.namelist.return_value = ["users.json"]

                with patch('app.services.config_package_service.zipfile.ZipFile', return_value=mock_zip):
                    result = service.import_package("/path/to/package.zip")

        assert result["success"] is False
        assert "缺少config.json" in result["message"]

    @patch('app.services.config_package_service.logger')
    def test_import_success(self, mock_logger):
        """测试成功导入"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        config_data = {"version": "1.0", "user_count": 1, "org_count": 1}
        orgs_data = [{"id": 1, "name": "Test Org", "code": "ORG001"}]
        users_data = [{"username": "testuser", "hashed_password": "pw", "organization_id": 1}]

        # Create a mock zip file that returns correct data for each file
        class MockZipFile:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def namelist(self):
                return ["config.json", "organizations.json", "users.json"]
            def read(self, name):
                if name == "config.json":
                    return json.dumps(config_data).encode()
                elif name == "organizations.json":
                    return json.dumps(orgs_data).encode()
                elif name == "users.json":
                    return json.dumps(users_data).encode()
                raise KeyError(name)

        with patch('app.services.config_package_service.os.path.exists', return_value=True):
            with patch('app.services.config_package_service.zipfile.is_zipfile', return_value=True):
                with patch('app.services.config_package_service.zipfile.ZipFile', return_value=MockZipFile()):
                    with patch.object(service, '_import_organizations') as mock_import_orgs:
                        with patch.object(service, '_import_users') as mock_import_users:
                            mock_import_orgs.return_value = {"created": 1, "updated": 0, "id_mapping": {1: 1}, "errors": []}
                            mock_import_users.return_value = {"created": 1, "skipped": 0, "errors": []}

                            result = service.import_package("/path/to/package.zip")

        assert result["success"] is True
        assert result["orgs_created"] == 1
        assert result["users_created"] == 1
        mock_db.commit.assert_called_once()

    def test_import_version_mismatch(self):
        """测试导入版本不匹配的包"""
        from app.services.config_package_service import ConfigPackageService
        from app.services import config_package_service

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        config_data = {"version": "2.0", "user_count": 0, "org_count": 0}

        class MockZipFile:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def namelist(self):
                return ["config.json"]
            def read(self, name):
                return json.dumps(config_data).encode()

        with patch('app.services.config_package_service.os.path.exists', return_value=True):
            with patch('app.services.config_package_service.zipfile.is_zipfile', return_value=True):
                with patch('app.services.config_package_service.zipfile.ZipFile', return_value=MockZipFile()):
                    with patch.object(service, '_import_organizations') as mock_import_orgs:
                        with patch.object(service, '_import_users') as mock_import_users:
                            mock_import_orgs.return_value = {"created": 0, "updated": 0, "id_mapping": {}, "errors": []}
                            mock_import_users.return_value = {"created": 0, "skipped": 0, "errors": []}

                            with patch.object(config_package_service.logger, 'warning') as mock_warning:
                                result = service.import_package("/path/to/package.zip")

        # Version mismatch should log warning but not fail
        mock_warning.assert_called_once()

    def test_import_json_decode_error(self):
        """测试导入JSON解析错误"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        class MockZipFile:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def namelist(self):
                return ["config.json"]
            def read(self, name):
                return b"invalid json {"

        with patch('app.services.config_package_service.os.path.exists', return_value=True):
            with patch('app.services.config_package_service.zipfile.is_zipfile', return_value=True):
                with patch('app.services.config_package_service.zipfile.ZipFile', return_value=MockZipFile()):
                    result = service.import_package("/path/to/package.zip")

        assert result["success"] is False
        assert "JSON" in result["message"]  # Check for JSON-related error

    def test_import_exception(self):
        """测试导入异常处理"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        class MockZipFile:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def namelist(self):
                raise Exception("Unexpected error")

        with patch('app.services.config_package_service.os.path.exists', return_value=True):
            with patch('app.services.config_package_service.zipfile.is_zipfile', return_value=True):
                with patch('app.services.config_package_service.zipfile.ZipFile', return_value=MockZipFile()):
                    with patch('app.services.config_package_service.logger'):
                        result = service.import_package("/path/to/package.zip")

        assert result["success"] is False
        mock_db.rollback.assert_called_once()

class TestImportOrganizations:
    """测试 _import_organizations 方法"""

    def test_import_empty_orgs(self):
        """测试导入空组织列表"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        result = service._import_organizations([])

        assert result["created"] == 0
        assert result["updated"] == 0
        assert result["id_mapping"] == {}

    def test_import_new_organization(self):
        """测试导入新组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = ConfigPackageService(db=mock_db)

        orgs_data = [{
            "id": 1,
            "name": "New Org",
            "code": "NEW001",
            "level": 1,
            "type": "company",
            "parent_id": None,
        }]

        result = service._import_organizations(orgs_data)

        assert result["created"] == 1
        assert result["updated"] == 0
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    def test_import_update_existing_organization(self):
        """测试更新现有组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_existing.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
        service = ConfigPackageService(db=mock_db)

        orgs_data = [{
            "id": 1,
            "name": "Updated Org",
            "code": "ORG001",
            "level": 2,
            "type": "department",
            "parent_id": None,
        }]

        result = service._import_organizations(orgs_data)

        assert result["created"] == 0
        assert result["updated"] == 1
        assert mock_existing.name == "Updated Org"

    def test_import_update_org_with_parent_mapping(self):
        """测试更新现有组织时映射parent_id"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()

        # 使用具有真实属性的简单类替代MagicMock
        class MockOrg:
            def __init__(self, org_id, parent_id=None):
                self.id = org_id
                self.parent_id = parent_id
                self.name = ""

        # 模拟两个现有组织 - 父组织和子组织
        mock_parent = MockOrg(org_id=100)
        mock_child = MockOrg(org_id=200, parent_id=1)  # 原始parent_id=1

        # 先查code匹配父组织，再查code匹配子组织
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_parent,  # 第一次查询 - 父组织
            mock_child,   # 第二次查询 - 子组织
        ]

        service = ConfigPackageService(db=mock_db)

        # 父组织id=1映射到新id=100，子组织id=2映射到新id=200
        # 子组织的parent_id=1应该被映射到100
        orgs_data = [
            {"id": 1, "name": "Parent Org", "code": "PARENT", "parent_id": None},
            {"id": 2, "name": "Child Org", "code": "CHILD", "parent_id": 1},
        ]

        result = service._import_organizations(orgs_data)

        assert result["updated"] == 2
        # 子组织的parent_id应该被设置为父组织的新ID
        assert mock_child.parent_id == 100

    def test_import_org_with_parent_mapping(self):
        """测试导入带父组织映射的组织"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = ConfigPackageService(db=mock_db)

        # First create parent, then child
        orgs_data = [
            {"id": 1, "name": "Parent", "code": "PARENT", "parent_id": None},
            {"id": 2, "name": "Child", "code": "CHILD", "parent_id": 1},
        ]

        result = service._import_organizations(orgs_data)

        assert result["created"] == 2
        # Check that child's parent_id was mapped

    def test_import_org_error(self):
        """测试导入组织错误处理"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB Error")
        service = ConfigPackageService(db=mock_db)

        orgs_data = [{"id": 1, "name": "Org", "code": "ORG001"}]

        result = service._import_organizations(orgs_data)

        assert len(result["errors"]) == 1
        assert "导入失败" in result["errors"][0]

class TestImportUsers:
    """测试 _import_users 方法"""

    def test_import_empty_users(self):
        """测试导入空用户列表"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        result = service._import_users([], {})

        assert result["created"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == []

    def test_import_new_user(self):
        """测试导入新用户"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = ConfigPackageService(db=mock_db)

        users_data = [{
            "username": "newuser",
            "hashed_password": "hashed_pw",
            "full_name": "New User",
            "email": "new@example.com",
            "organization_id": 1,
        }]

        result = service._import_users(users_data, {1: 2})

        assert result["created"] == 1
        assert result["skipped"] == 0
        mock_db.add.assert_called_once()

    def test_import_existing_user(self):
        """测试跳过已存在用户"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing
        service = ConfigPackageService(db=mock_db)

        users_data = [{"username": "existinguser", "hashed_password": "pw"}]

        result = service._import_users(users_data, {})

        assert result["created"] == 0
        assert result["skipped"] == 1

    def test_import_user_no_username(self):
        """测试导入缺少用户名的用户"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        service = ConfigPackageService(db=mock_db)

        users_data = [{"hashed_password": "pw"}]

        result = service._import_users(users_data, {})

        assert result["created"] == 0
        assert result["skipped"] == 1
        assert len(result["errors"]) == 1

    def test_import_user_error(self):
        """测试导入用户错误处理"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB Error")
        service = ConfigPackageService(db=mock_db)

        users_data = [{"username": "testuser", "hashed_password": "pw"}]

        result = service._import_users(users_data, {})

        assert len(result["errors"]) == 1
        assert "导入失败" in result["errors"][0]
        assert result["skipped"] == 1

    def test_import_user_with_org_mapping(self):
        """测试导入带组织映射的用户"""
        from app.services.config_package_service import ConfigPackageService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = ConfigPackageService(db=mock_db)

        users_data = [{"username": "user1", "hashed_password": "pw", "organization_id": 1}]

        result = service._import_users(users_data, {1: 10})

        assert result["created"] == 1
