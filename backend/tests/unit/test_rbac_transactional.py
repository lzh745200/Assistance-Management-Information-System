"""
RBAC 事务性修复单元测试
覆盖：commit→flush 迁移、TransactionManager 包裹、弃用行为
对应提交：0bfc5da, 60800be, eeae49b, 512fcc8, eac00ef, 5749b75, 51945f9

注意：所有变更方法均为 async def（内部无 await），因此测试必须 await。
"""
import asyncio
import pytest
from unittest.mock import MagicMock

from app.services.rbac_service import RBACService, Permission


# ──────────────────────────────────────────────
# 辅助工具
# ──────────────────────────────────────────────

def _chain_mock(base_mock, **return_values):
    """为链式调用配置 MagicMock：_chain_mock(m, first=val, all=[...], delete=3)。"""
    for attr, val in return_values.items():
        getattr(base_mock, attr).return_value = val
    return base_mock


def _mock_db_for_model(db, model_name: str):
    """返回 db.query(Model) 链的 mock 起点。将 db.query 设为根据 model 分发的 side_effect。"""
    # 导出模型类名（None → 返回默认链）
    from app.models.user import User
    from app.models.rbac import RbacRole, UserRole, UserPermission, RolePermission

    _model_map = {
        "User": User,
        "RbacRole": RbacRole,
        "UserRole": UserRole,
        "UserPermission": UserPermission,
        "RolePermission": RolePermission,
    }

    model_class = _model_map.get(model_name)
    if model_class is None:
        return db.query.return_value  # fallback

    # 为指定模型创建独立链
    mock_chain = MagicMock()
    db.query.return_value = mock_chain  # default
    return mock_chain


def run(coro):
    """同步执行协程——适用于所有 await-free async 方法。"""
    return asyncio.get_event_loop().run_until_complete(coro)


# ──────────────────────────────────────────────
# 1. db.flush() 替代 db.commit()
# ──────────────────────────────────────────────

class TestFlushNotCommit:
    """所有变更方法使用 db.flush() 而非 db.commit()。"""

    @pytest.fixture
    def svc(self):
        return RBACService()

    # ── assign_role ──

    def test_assign_role_existing_calls_no_flush(self, svc):
        """角色已分配 → early return，无 flush 无 commit。"""
        db = MagicMock()
        # 查询链：RbacRole → 返回角色 | UserRole → 返回已有记录（early return）
        role = MagicMock(); role.id = "r1"

        def query_side_effect(model):
            m = MagicMock()
            if model.__name__ == "RbacRole":
                _chain_mock(m, first=role)
            else:
                _chain_mock(m, first=MagicMock())  # 已有 UserRole
            return m

        db.query.side_effect = query_side_effect

        result = run(svc.assign_role("42", "r1", "1", None, db))
        assert result is True
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    def test_assign_role_new_calls_flush_not_commit(self, svc):
        """新分配 → db.flush() 一次，无 commit。"""
        db = MagicMock()
        role = MagicMock(); role.id = "r1"

        def query_side_effect(model):
            m = MagicMock()
            if model.__name__ == "RbacRole":
                _chain_mock(m, first=role)
            else:
                _chain_mock(m, first=None)  # 无已有 UserRole
            return m

        db.query.side_effect = query_side_effect

        result = run(svc.assign_role("42", "r1", "1", None, db))
        assert result is True
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    # ── revoke_role ──

    def test_revoke_role_calls_flush_not_commit(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, delete=1)

        result = run(svc.revoke_role("42", "r1", db))
        assert result is True
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    # ── grant_permission ──

    def test_grant_permission_new_calls_flush_not_commit(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, first=None)  # 权限不存在

        result = run(svc.grant_permission("42", "user:read", "1", None, db))
        assert result is True
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_grant_permission_existing_calls_no_flush(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, first=MagicMock())  # 已存在

        result = run(svc.grant_permission("42", "user:read", "1", None, db))
        assert result is True
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    # ── revoke_permission (单数，已弃用) ──

    def test_revoke_permission_singular_calls_flush_not_commit(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, delete=1)

        result = run(svc.revoke_permission("42", "user:read", db))
        assert result is True
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    # ── revoke_permissions_batch ──

    def test_revoke_permissions_batch_calls_flush_not_commit(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, all=[("user:read",)])

        result = run(svc.revoke_permissions_batch("42", ["user:read"], db))
        assert result == (["user:read"], [])
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_revoke_permissions_batch_empty_calls_no_flush(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, all=[])

        result = run(svc.revoke_permissions_batch("42", [], db))
        assert result == ([], [])
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    # ── create_role ──

    def test_create_role_calls_flush_no_commit(self, svc):
        db = MagicMock()

        role_id = run(svc.create_role("test", "desc", ["user:read"], False, db))
        assert role_id is not None
        assert db.flush.call_count == 2
        db.commit.assert_not_called()


# ──────────────────────────────────────────────
# 2. grant_permission 始终返回 True
# ──────────────────────────────────────────────

class TestGrantPermissionAlwaysTrue:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_returns_true_when_exists(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, first=MagicMock())
        assert run(svc.grant_permission("42", "user:read", "1", None, db)) is True

    def test_returns_true_when_new(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, first=None)
        assert run(svc.grant_permission("42", "user:read", "1", None, db)) is True

    def test_never_returns_false(self, svc):
        """grant_permission 无误时绝不返回 False → 调用方 granted/failed 拆分是死代码。"""
        assert run(svc.grant_permission(
            "42", "user:read", "1", None,
            MagicMock(**{"query.return_value.filter.return_value.first.return_value": MagicMock()}),
        )) is True
        assert run(svc.grant_permission(
            "42", "user:write", "1", None,
            MagicMock(**{"query.return_value.filter.return_value.first.return_value": None}),
        )) is True


# ──────────────────────────────────────────────
# 3. assign_role 两条路径均返回 True
# ──────────────────────────────────────────────

class TestAssignRoleBothPathsReturnTrue:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def _make_assign_db(self, role_exists=True, user_has_role=False):
        db = MagicMock()
        role = MagicMock(); role.id = "r1"

        def side_effect(model):
            m = MagicMock()
            if model.__name__ == "RbacRole":
                _chain_mock(m, first=role if role_exists else None)
            else:
                _chain_mock(m, first=MagicMock() if user_has_role else None)
            return m

        db.query.side_effect = side_effect
        return db

    def test_returns_true_when_already_assigned(self, svc):
        db = self._make_assign_db(role_exists=True, user_has_role=True)
        assert run(svc.assign_role("42", "r1", "1", None, db)) is True

    def test_returns_true_when_newly_assigned(self, svc):
        db = self._make_assign_db(role_exists=True, user_has_role=False)
        assert run(svc.assign_role("42", "r1", "1", None, db)) is True

    def test_both_paths_indistinguishable(self, svc):
        db_existing = self._make_assign_db(role_exists=True, user_has_role=True)
        db_new = self._make_assign_db(role_exists=True, user_has_role=False)
        r1 = run(svc.assign_role("42", "r1", "1", None, db_existing))
        r2 = run(svc.assign_role("42", "r1", "1", None, db_new))
        assert r1 == r2 == True   # 不可区分


# ──────────────────────────────────────────────
# 4. revoke_permission（单数）弃用行为
# ──────────────────────────────────────────────

class TestRevokePermissionSingularDeprecated:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_has_deprecated_docstring(self, svc):
        doc = svc.revoke_permission.__doc__ or ""
        assert "deprecated" in doc.lower()
        assert "revoke_permissions_batch" in doc

    def test_uses_flush_not_commit(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, delete=1)
        run(svc.revoke_permission("42", "user:read", db))
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_returns_true_when_permission_existed(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, delete=1)
        assert run(svc.revoke_permission("42", "user:read", db)) is True

    def test_returns_false_when_permission_not_found(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, delete=0)
        assert run(svc.revoke_permission("42", "nonexistent", db)) is False


# ──────────────────────────────────────────────
# 5. revoke_permissions_batch — 两步流程
# ──────────────────────────────────────────────

class TestRevokePermissionsBatch:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_pre_queries_then_deletes(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, all=[("user:read",), ("user:write",)])

        revoked, failed = run(svc.revoke_permissions_batch(
            "42", ["user:read", "user:write", "nonexistent"], db,
        ))
        assert set(revoked) == {"user:read", "user:write"}
        assert set(failed) == {"nonexistent"}

    def test_returns_empty_revoked(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, all=[])
        revoked, failed = run(svc.revoke_permissions_batch("42", ["nonexistent"], db))
        assert revoked == []
        assert failed == ["nonexistent"]

    def test_uses_flush_not_commit(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, all=[("user:read",)])
        run(svc.revoke_permissions_batch("42", ["user:read"], db))
        db.flush.assert_called_once()
        db.commit.assert_not_called()


# ──────────────────────────────────────────────
# 6. TransactionManager 集成
# ──────────────────────────────────────────────

class TestTransactionManagerIntegration:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_flush_from_service_commit_from_tm(self, svc):
        from app.core.transaction import TransactionManager

        db = MagicMock()
        _chain_mock(db.query.return_value, all=[])

        with TransactionManager.transaction(db) as sess:
            run(svc.revoke_permissions_batch("42", [], sess))

        db.flush.assert_not_called()  # 空列表，不调用 flush
        db.commit.assert_called_once()  # TM 提交

    def test_multiple_ops_one_commit(self, svc):
        from app.core.transaction import TransactionManager

        db = MagicMock()
        # 预查询返回一条记录，grant 查不到已有
        def query_side_effect(model):
            m = MagicMock()
            # revoke_permissions_batch 两次 query：一次 .all()，一次 .delete()
            if model.__name__ == "UserPermission":
                _chain_mock(m, all=[("user:read",)], first=None)
            else:
                _chain_mock(m, all=[("user:read",)])
            return m

        db.query.side_effect = query_side_effect

        with TransactionManager.transaction(db) as sess:
            run(svc.revoke_permissions_batch("42", ["user:read"], sess))
            run(svc.grant_permission("42", "user:write", "1", None, sess))

        assert db.commit.call_count == 1  # 仅 TM 退出时提交一次


# ──────────────────────────────────────────────
# 7. 回归测试（第三轮审查）
# ──────────────────────────────────────────────

class TestRegressionFromThirdReview:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_assign_role_raises_not_found_for_inactive_role(self, svc):
        from app.core.exceptions import NotFoundError

        db = MagicMock()
        _chain_mock(db.query.return_value, first=None)  # 角色不存在 / 不活跃

        with pytest.raises(NotFoundError):
            run(svc.assign_role("42", "inactive-role", "1", None, db))

    def test_grant_permission_always_returns_true(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, first=MagicMock())
        assert run(svc.grant_permission("42", "user:read", "1", None, db)) is True

        _chain_mock(db.query.return_value, first=None)
        assert run(svc.grant_permission("42", "user:write", "1", None, db)) is True

    def test_revoke_role_returns_false_when_nothing_deleted(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, delete=0)
        assert run(svc.revoke_role("42", "r1", db)) is False

    def test_revoke_role_returns_true_when_deleted(self, svc):
        db = MagicMock()
        _chain_mock(db.query.return_value, delete=3)
        assert run(svc.revoke_role("42", "r1", db)) is True

    def test_revoke_permissions_batch_uses_flush_semantics(self, svc):
        """revoke_permissions_batch 使用 flush 语义——无 commit。"""
        db = MagicMock()
        _chain_mock(db.query.return_value, all=[("user:read",)])

        run(svc.revoke_permissions_batch("42", ["user:read"], db))
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_create_role_calls_flush_twice(self, svc):
        """create_role flush 两次：获取 role.id + 权限添加后。"""
        db = MagicMock()
        run(svc.create_role("r", "d", ["user:read"], False, db))
        assert db.flush.call_count == 2
        db.commit.assert_not_called()
