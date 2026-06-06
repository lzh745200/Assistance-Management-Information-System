"""
用户服务单元测试
覆盖: app/services/user_service.py
"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    """Create a mock SQLAlchemy session."""
    db = MagicMock()
    return db


@pytest.fixture
def user_service(mock_db):
    """Create UserService with mock DB."""
    from app.services.user_service import UserService
    return UserService(db=mock_db)


class TestUserServiceInit:
    def test_init_with_db(self, mock_db):
        from app.services.user_service import UserService
        svc = UserService(db=mock_db)
        assert svc.db is mock_db

    def test_init_without_db(self):
        from app.services.user_service import UserService
        svc = UserService()
        assert svc.db is None

    def test_get_user_by_username_no_db_returns_none(self):
        from app.services.user_service import UserService
        svc = UserService()
        assert svc.get_user_by_username("admin") is None

    def test_get_user_by_id_no_db_returns_none(self):
        from app.services.user_service import UserService
        svc = UserService()
        assert svc.get_user_by_id(1) is None

    def test_get_users_no_db_returns_empty(self):
        from app.services.user_service import UserService
        svc = UserService()
        assert svc.get_users() == []

    def test_create_user_no_db_returns_none(self):
        from app.services.user_service import UserService
        svc = UserService()
        assert svc.create_user({"username": "test", "password": "pw"}) is None


class TestUserServiceWithDB:
    def test_get_user_by_username(self, user_service, mock_db):
        mock_user = MagicMock()
        mock_user.username = "admin"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = user_service.get_user_by_username("admin")
        assert result is mock_user
        mock_db.query.assert_called_once()

    def test_get_user_by_id(self, user_service, mock_db):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = user_service.get_user_by_id(1)
        assert result is mock_user

    def test_get_user_by_email(self, user_service, mock_db):
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = user_service.get_user_by_email("test@example.com")
        assert result is mock_user

    def test_get_users_with_filters(self, user_service, mock_db):
        mock_users = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        # role + is_active = 2 chained filters
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_users

        result = user_service.get_users(skip=0, limit=10, role="admin", is_active=True)
        assert result == mock_users

    def test_get_users_with_search(self, user_service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = user_service.get_users(search="test")
        assert result == []

    def test_update_user_not_found(self, user_service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = user_service.update_user(999, {"full_name": "New"})
        assert result is None

    def test_delete_user_not_found(self, user_service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = user_service.delete_user(999)
        assert result is False

    def test_delete_user_success(self, user_service, mock_db):
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        result = user_service.delete_user(1)
        assert result is True
        mock_db.delete.assert_called_once_with(mock_user)


class TestValidRoles:
    def test_valid_roles_contains_expected(self):
        from app.services.user_service import VALID_ROLES
        assert "super_admin" in VALID_ROLES
        assert "admin" in VALID_ROLES
        assert "viewer" in VALID_ROLES
        assert len(VALID_ROLES) == 6

    def test_valid_roles_all_strings(self):
        from app.services.user_service import VALID_ROLES
        for role in VALID_ROLES:
            assert isinstance(role, str)


class TestUserServiceAsyncCompat:
    def test_get_user_async_returns_none(self):
        import asyncio
        from app.services.user_service import UserService
        result = asyncio.run(UserService.get_user(1))
        assert result is None
