"""
Comprehensive tests for remaining core modules (part 2).
Covers: mock_data, prophet_status, redis_adapter, cache_settings, user_info,
migration_helper, database_indexes, database_root, database_compat,
static_files, audit_middleware, middleware, logging, structured_logging,
token_blacklist, token_manager, security helpers, data_permission,
unified_data_scope, permission_utils, upload_security, file_upload.
"""
import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ══════════════════════════════════════════════════════════════
# mock_data
# ══════════════════════════════════════════════════════════════


class TestMockData:
    def test_create_mock_user(self):
        from app.core.mock_data import create_mock_user
        user = create_mock_user()
        assert 'username' in user
        assert 'phone' in user
        assert 'email' in user

    def test_create_mock_user_with_name(self):
        from app.core.mock_data import create_mock_user
        user = create_mock_user(username='testuser')
        assert user['username'] == 'testuser'

    def test_create_mock_user_with_role(self):
        from app.core.mock_data import create_mock_user
        user = create_mock_user(role='admin')
        assert user['role'] == 'admin'

    def test_create_mock_users(self):
        from app.core.mock_data import create_mock_users
        users = create_mock_users(5)
        assert len(users) == 5

    def test_create_mock_village(self):
        from app.core.mock_data import create_mock_village
        v = create_mock_village()
        assert 'name' in v
        assert 'region' in v

    def test_create_mock_village_with_name(self):
        from app.core.mock_data import create_mock_village
        v = create_mock_village(name='测试村')
        assert v['name'] == '测试村'

    def test_create_mock_villages(self):
        from app.core.mock_data import create_mock_villages
        vs = create_mock_villages(3)
        assert len(vs) == 3

    def test_seed_id(self):
        from app.core.mock_data import seed_id
        sid = seed_id()
        assert len(sid) == 12

    def test_random_status(self):
        from app.core.mock_data import random_status
        s = random_status()
        assert isinstance(s, str)

    def test_random_status_custom(self):
        from app.core.mock_data import random_status
        s = random_status(['a', 'b'])
        assert s in ['a', 'b']

    def test_random_amount(self):
        from app.core.mock_data import random_amount
        a = random_amount()
        assert 1000 <= a <= 500000


# ══════════════════════════════════════════════════════════════
# prophet_status
# ══════════════════════════════════════════════════════════════


class TestProphetStatus:
    def test_is_prophet_available(self):
        from app.core.prophet_status import is_prophet_available
        result = is_prophet_available()
        assert isinstance(result, bool)


# ══════════════════════════════════════════════════════════════
# redis_adapter
# ══════════════════════════════════════════════════════════════


class TestRedisAdapter:
    def test_get_set(self):
        from app.core.redis_adapter import RedisAdapter
        r = RedisAdapter()
        r.set('key', 'value')
        assert r.get('key') == 'value'

    def test_get_missing(self):
        from app.core.redis_adapter import RedisAdapter
        r = RedisAdapter()
        assert r.get('missing') is None

    def test_set_with_ttl(self):
        from app.core.redis_adapter import RedisAdapter
        r = RedisAdapter()
        r.set('k', 'v', ttl=3600)
        assert r.get('k') == 'v'

    def test_delete(self):
        from app.core.redis_adapter import RedisAdapter
        r = RedisAdapter()
        r.set('k', 'v')
        assert r.delete('k') is True
        assert r.get('k') is None

    def test_delete_missing(self):
        from app.core.redis_adapter import RedisAdapter
        r = RedisAdapter()
        assert r.delete('missing') is True

    def test_exists(self):
        from app.core.redis_adapter import RedisAdapter
        r = RedisAdapter()
        r.set('k', 'v')
        assert r.exists('k') is True
        assert r.exists('missing') is False

    def test_flush(self):
        from app.core.redis_adapter import RedisAdapter
        r = RedisAdapter()
        r.set('k', 'v')
        r.flush()
        assert r.exists('k') is False

    def test_singleton(self):
        from app.core.redis_adapter import redis_adapter
        assert redis_adapter is not None


# ══════════════════════════════════════════════════════════════
# cache_settings
# ══════════════════════════════════════════════════════════════


class TestCacheSettings:
    def test_default_settings(self):
        from app.core.cache_settings import CacheSettings
        cs = CacheSettings()
        assert cs.enabled is True
        assert cs.backend == 'memory'
        assert cs.default_ttl == 3600

    def test_from_settings(self):
        from app.core.cache_settings import CacheSettings
        cs = CacheSettings.from_settings()
        assert cs is not None

    def test_get_cache_settings(self):
        from app.core.cache_settings import get_cache_settings
        cs = get_cache_settings()
        assert cs is not None


# ══════════════════════════════════════════════════════════════
# user_info
# ══════════════════════════════════════════════════════════════


class TestUserInfo:
    def test_attribute_access(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1, name='test')
        assert u.id == 1
        assert u.name == 'test'

    def test_get_method(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1, name='test')
        assert u.get('id') == 1
        assert u.get('missing', 'default') == 'default'

    def test_item_access(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1)
        assert u['id'] == 1

    def test_item_access_missing(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1)
        with pytest.raises(KeyError):
            _ = u['missing']

    def test_item_set(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1)
        u['name'] = 'test'
        assert u.name == 'test'

    def test_contains(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1)
        assert 'id' in u
        assert 'missing' not in u

    def test_repr(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1, name='test')
        r = repr(u)
        assert 'UserInfo' in r

    def test_keys(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1, name='test')
        assert 'id' in u.keys()

    def test_values(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1)
        assert 1 in u.values()

    def test_items(self):
        from app.core.user_info import UserInfo
        u = UserInfo(id=1, name='test')
        items = dict(u.items())
        assert items['id'] == 1


# ══════════════════════════════════════════════════════════════
# migration_helper
# ══════════════════════════════════════════════════════════════


class TestMigrationHelper:
    def test_sqlite_col_spec_integer(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'INTEGER'
        col.default = None
        col.server_default = None
        col.nullable = False
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == 'INTEGER'

    def test_sqlite_col_spec_float(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'FLOAT'
        col.default = None
        col.server_default = None
        col.nullable = True
        stype, _ = _sqlite_col_spec(col)
        assert stype == 'REAL'

    def test_sqlite_col_spec_text(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'VARCHAR(100)'
        col.default = None
        col.server_default = None
        col.nullable = True
        stype, _ = _sqlite_col_spec(col)
        assert stype == 'TEXT'

    def test_sqlite_col_spec_with_bool_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'BOOLEAN'
        col.default = MagicMock()
        col.default.arg = True
        col.default.__class__ = type('ColDef', (), {})
        col.server_default = None
        col.nullable = True
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == 'INTEGER'
        assert 'DEFAULT 1' in default_clause

    def test_sqlite_col_spec_with_int_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'INTEGER'
        col.default = MagicMock()
        col.default.arg = 42
        col.server_default = None
        col.nullable = True
        stype, default_clause = _sqlite_col_spec(col)
        assert 'DEFAULT 42' in default_clause

    def test_sqlite_col_spec_with_string_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'VARCHAR(50)'
        col.default = MagicMock()
        col.default.arg = "hello"
        col.server_default = None
        col.nullable = True
        stype, default_clause = _sqlite_col_spec(col)
        assert "DEFAULT 'hello'" in default_clause

    def test_sqlite_col_spec_with_callable_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'DATETIME'
        col.default = MagicMock()
        col.default.arg = datetime.now  # callable
        col.server_default = None
        col.nullable = True
        stype, default_clause = _sqlite_col_spec(col)
        assert default_clause == ''

    def test_sqlite_col_spec_nullable_no_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'INTEGER'
        col.default = None
        col.server_default = None
        col.nullable = False
        stype, default_clause = _sqlite_col_spec(col)
        assert 'DEFAULT 0' in default_clause

    def test_sqlite_col_spec_with_server_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = MagicMock()
        col.type = MagicMock()
        col.type.__str__ = lambda self: 'DATETIME'
        col.default = None
        col.server_default = MagicMock()  # server_default set
        col.nullable = True
        stype, default_clause = _sqlite_col_spec(col)
        assert default_clause == ''

    def test_migrate_missing_columns_disabled(self):
        from app.core.migration_helper import migrate_missing_columns
        with patch.dict(os.environ, {'DISABLE_AUTO_MIGRATION': '1'}):
            engine = MagicMock()
            migrate_missing_columns(engine, MagicMock())  # should return early

    def test_migrate_missing_columns_inspector_error(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = MagicMock()
        with patch('app.core.migration_helper.sa_inspect', side_effect=Exception('fail')):
            with patch.dict(os.environ, {'DISABLE_AUTO_MIGRATION': ''}):
                migrate_missing_columns(engine, MagicMock())


# ══════════════════════════════════════════════════════════════
# database_indexes
# ══════════════════════════════════════════════════════════════


class TestDatabaseIndexes:
    def test_module_importable(self):
        import app.core.database_indexes as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# database_root
# ══════════════════════════════════════════════════════════════


class TestDatabaseRoot:
    def test_module_importable(self):
        import app.core.database_root as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# database_compat
# ══════════════════════════════════════════════════════════════


class TestDatabaseCompat:
    def test_module_importable(self):
        import app.core.database_compat as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# static_files
# ══════════════════════════════════════════════════════════════


class TestStaticFiles:
    def test_module_importable(self):
        import app.core.static_files as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# audit_middleware
# ══════════════════════════════════════════════════════════════


class TestAuditMiddleware:
    def test_module_importable(self):
        import app.core.audit_middleware as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# middleware
# ══════════════════════════════════════════════════════════════


class TestMiddleware:
    def test_module_importable(self):
        import app.core.middleware as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# logging
# ══════════════════════════════════════════════════════════════


class TestLogging:
    def test_module_importable(self):
        import app.core.logging as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# structured_logging
# ══════════════════════════════════════════════════════════════


class TestStructuredLogging:
    def test_module_importable(self):
        import app.core.structured_logging as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# token_blacklist
# ══════════════════════════════════════════════════════════════


class TestTokenBlacklist:
    def test_module_importable(self):
        import app.core.token_blacklist as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# token_manager
# ══════════════════════════════════════════════════════════════


class TestTokenManager:
    def test_module_importable(self):
        import app.core.token_manager as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# permissions
# ══════════════════════════════════════════════════════════════


class TestPermissions:
    def test_module_importable(self):
        import app.core.permissions as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# permission_utils
# ══════════════════════════════════════════════════════════════


class TestPermissionUtils:
    def test_module_importable(self):
        import app.core.permission_utils as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# upload_security
# ══════════════════════════════════════════════════════════════


class TestUploadSecurity:
    def test_module_importable(self):
        import app.core.upload_security as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# file_upload
# ══════════════════════════════════════════════════════════════


class TestFileUpload:
    def test_module_importable(self):
        import app.core.file_upload as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# data_permission
# ══════════════════════════════════════════════════════════════


class TestDataPermission:
    def test_module_importable(self):
        import app.core.data_permission as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# unified_data_scope
# ══════════════════════════════════════════════════════════════


class TestUnifiedDataScope:
    def test_module_importable(self):
        import app.core.unified_data_scope as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# error_handler
# ══════════════════════════════════════════════════════════════


class TestErrorHandler:
    def test_module_importable(self):
        import app.core.error_handler as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# auth_root
# ══════════════════════════════════════════════════════════════


class TestAuthRoot:
    def test_module_importable(self):
        import app.core.auth_root as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# audit
# ══════════════════════════════════════════════════════════════


class TestAudit:
    def test_module_importable(self):
        import app.core.audit as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# logging_config
# ══════════════════════════════════════════════════════════════


class TestLoggingConfig:
    def test_module_importable(self):
        import app.core.logging_config as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# cache
# ══════════════════════════════════════════════════════════════


class TestCache:
    def test_module_importable(self):
        import app.core.cache as mod
        assert mod is not None


# ══════════════════════════════════════════════════════════════
# config
# ══════════════════════════════════════════════════════════════


class TestConfig:
    def test_settings_importable(self):
        from app.core.config import settings
        assert settings is not None

    def test_settings_has_required_attrs(self):
        from app.core.config import settings
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'DATABASE_URL')
