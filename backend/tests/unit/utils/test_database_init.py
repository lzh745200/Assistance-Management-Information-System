"""
数据库初始化工具测试

测试 app/utils/database_init.py 模块
"""
import pytest
from unittest.mock import MagicMock, patch
from app.utils.database_init import (
    check_database_connection,
    create_database_if_not_exists,
    init_database_tables,
    drop_all_tables,
    init_default_roles,
    init_default_users,
    reset_database,
    get_database_info,
)


class TestCheckDatabaseConnection:
    @patch("app.utils.database_init.create_engine")
    def test_connection_success(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        result = check_database_connection("sqlite:///test.db")
        assert result is True

    @patch("app.utils.database_init.create_engine")
    def test_connection_failure(self, mock_create_engine):
        mock_create_engine.side_effect = Exception("Connection failed")
        result = check_database_connection("sqlite:///test.db")
        assert result is False


class TestCreateDatabaseIfNotExists:
    def _setup_mocks(self):
        mock_sqlalchemy_utils = MagicMock()
        mock_sqlalchemy_utils.database_exists = MagicMock()
        mock_sqlalchemy_utils.create_database = MagicMock()
        return mock_sqlalchemy_utils

    @patch.dict('sys.modules', {'sqlalchemy_utils': MagicMock(database_exists=MagicMock(return_value=False), create_database=MagicMock())})
    def test_database_not_exists(self):
        create_database_if_not_exists("sqlite:///test.db")

    @patch.dict('sys.modules', {'sqlalchemy_utils': MagicMock(database_exists=MagicMock(return_value=True), create_database=MagicMock())})
    def test_database_exists(self):
        create_database_if_not_exists("sqlite:///test.db")

    @patch.dict('sys.modules', {'sqlalchemy_utils': MagicMock(
        database_exists=MagicMock(return_value=False),
        create_database=MagicMock(side_effect=Exception("Create failed")),
    )})
    def test_exception_raised(self):
        with pytest.raises(Exception):
            create_database_if_not_exists("sqlite:///test.db")


class TestInitDatabaseTables:
    @patch("app.utils.database_init.ModelBase")
    @patch("app.utils.database_init.inspect")
    def test_create_tables(self, mock_inspect, mock_base):
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users", "roles"]
        mock_inspect.return_value = mock_inspector
        init_database_tables()
        mock_base.metadata.create_all.assert_called_once()

    @patch("app.utils.database_init.ModelBase")
    def test_create_tables_exception(self, mock_base):
        mock_base.metadata.create_all.side_effect = Exception("Create failed")
        with pytest.raises(Exception):
            init_database_tables()


class TestDropAllTables:
    @patch("app.utils.database_init.ModelBase")
    def test_drop_tables(self, mock_base):
        drop_all_tables()
        mock_base.metadata.drop_all.assert_called_once()

    @patch("app.utils.database_init.ModelBase")
    def test_drop_exception(self, mock_base):
        mock_base.metadata.drop_all.side_effect = Exception("Drop failed")
        with pytest.raises(Exception):
            drop_all_tables()


class TestInitDefaultRoles:
    def test_skip_when_roles_exist(self):
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 3
        init_default_roles(mock_db)
        mock_db.add_all.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_create_roles(self):
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        init_default_roles(mock_db)
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_rollback_on_failure(self):
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_db.add_all.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            init_default_roles(mock_db)
        mock_db.rollback.assert_called_once()


class TestInitDefaultUsers:
    @patch("app.utils.database_init.pwd_context")
    def test_skip_when_users_exist(self, mock_pwd):
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 2
        init_default_users(mock_db)
        mock_db.add_all.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch("app.utils.database_init.pwd_context")
    def test_create_users(self, mock_pwd):
        mock_pwd.hash.return_value = "hashed_password"
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.first.return_value = None
        init_default_users(mock_db)
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("app.utils.database_init.pwd_context")
    def test_create_users_with_existing_org(self, mock_pwd):
        mock_pwd.hash.return_value = "hashed_password"
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.name = "Root"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_org
        init_default_users(mock_db)
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("app.utils.database_init.pwd_context")
    def test_rollback_on_failure(self, mock_pwd):
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_db.add_all.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            init_default_users(mock_db)
        mock_db.rollback.assert_called_once()


class TestResetDatabase:
    @patch.dict('sys.modules', {'sqlalchemy_utils': MagicMock(database_exists=MagicMock(return_value=True), drop_database=MagicMock())})
    @patch("app.utils.database_init.create_database_if_not_exists")
    @patch("app.utils.database_init.init_database_tables")
    def test_reset(self, mock_tables, mock_create_db):
        reset_database("sqlite:///test.db")

    @patch.dict('sys.modules', {'sqlalchemy_utils': MagicMock(database_exists=MagicMock(side_effect=Exception("Check failed")))})
    def test_reset_exception(self):
        with pytest.raises(Exception):
            reset_database("sqlite:///test.db")


class TestGetDatabaseInfo:
    @patch("app.utils.database_init.SessionLocal")
    @patch("app.utils.database_init.inspect")
    def test_get_info(self, mock_inspect, mock_session_local):
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users", "roles"]
        mock_inspector.get_columns.return_value = [
            {"name": "id"},
            {"name": "name"},
        ]
        mock_inspect.return_value = mock_inspector

        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_session_local.return_value = mock_db

        get_database_info()

    @patch("app.utils.database_init.inspect")
    def test_get_info_exception(self, mock_inspect):
        mock_inspect.side_effect = Exception("Inspect failed")
        with pytest.raises(Exception):
            get_database_info()
