"""
RBAC 事务性修复单元测试
覆盖：commit→flush 迁移、TransactionManager 包裹、弃用行为
对应提交：0bfc5da, 60800be, eeae49b, 512fcc8, eac00ef, 5749b75, 51945f9

策略：直接测试服务方法，使用 MagicMock 构建数据库链。对于需要实例化模型类的方法，
在同一调用中去糖后验证——因为所有模型构造参数仅为原始值，无副作用。
对于需要复杂查询链（如 Role.id、UserRole.user_id 等列属性访问）的方法，
利用 MagicMock 的 __getattr__ 特性——MagicMock 自动 mock 任意属性访问。"""
import asyncio
import pytest
from unittest.mock import ANY, MagicMock, patch

from app.services.rbac_service import RBACService, Permission


# ──────────────────────────────────────────────
# 辅助
# ──────────────────────────────────────────────

def run(coro):
    """同步运行 async 协程。"""
    return asyncio.get_event_loop().run_until_complete(coro)


_UNSET = object()  # 哨兵——区分"未配置"与"显式 None"


def mkq(db, first=_UNSET, all=_UNSET, delete=_UNSET, scalar=_UNSET):
    """
    在 db mock 上搭建完整 SQLAlchemy query 链。

    链：db.query(Model) → q → .filter(...) → mid → .first()/.all()/.delete()/.scalar()

    注意：first/all/delete/scalar 挂在 mid（单次 .filter() 的返回值）上，
    因为实际代码中的查询是 db.query(X).filter(...).first()，只有一层 filter。
    """
    mid = MagicMock()
    if first is not _UNSET:
        mid.first.return_value = first
    if all is not _UNSET:
        mid.all.return_value = all
    if delete is not _UNSET:
        mid.delete.return_value = delete
    if scalar is not _UNSET:
        mid.scalar.return_value = scalar

    # .filter().filter() 链也回到 mid（处理双重 filter 的查询）
    mid.filter.return_value = mid

    q = MagicMock()
    q.filter.return_value = mid

    db.query.return_value = q
    return db


def mkq_multi(db, spec: dict):
    """
    多模型分发 mock 查询。

    spec: {
        "RbacRole": {"first": mock_role},
        "UserRole": {"first": None, "delete": 1},
    }

    其中键为模型类对象（需导入），值指定该模型查询的预期返回值。
    """
    from app.models.rbac import RbacRole, RolePermission, UserRole, UserPermission

    _map = {
        "RbacRole": RbacRole,
        "RolePermission": RolePermission,
        "UserRole": UserRole,
        "UserPermission": UserPermission,
    }

    chains = {}
    for key, returns in spec.items():
        mid = MagicMock()
        # 始终设置——mkq_multi 的 spec 始终显式包含所有需要的返回值
        for method, val in returns.items():
            getattr(mid, method).return_value = val
        mid.filter.return_value = mid  # 二次 filter 也回到 mid
        q = MagicMock()
        q.filter.return_value = mid
        chains[_map[key]] = q

    default = MagicMock()

    def _side(*args):
        model = args[0] if args else None
        return chains.get(model, default)

    db.query.side_effect = _side
    db.query.return_value = default
    return db


# ──────────────────────────────────────────────
# 模型导入 — 测试需要真实列属性以便 SQLAlchemy query 正常运行
# ──────────────────────────────────────────────

from app.models.rbac import RbacRole, RolePermission, UserRole, UserPermission


# ──────────────────────────────────────────────
# 1. db.flush() vs db.commit()
# ──────────────────────────────────────────────

class TestFlushNotCommit:
    @pytest.fixture
    def svc(self):
        return RBACService()

    # ── revoke_role ──

    def test_revoke_role_calls_flush_not_commit(self, svc):
        db = MagicMock(); mkq(db, delete=1)
        result = run(svc.revoke_role("42", "r1", db))
        assert result is True
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    # ── revoke_permission（单数，已弃用）──

    def test_revoke_permission_singular_calls_flush_not_commit(self, svc):
        db = MagicMock(); mkq(db, delete=1)
        result = run(svc.revoke_permission("42", "user:read", db))
        assert result is True
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    # ── revoke_permissions_batch ──

    def test_revoke_permissions_batch_calls_flush_not_commit(self, svc):
        db = MagicMock(); mkq(db, all=[("user:read",)])
        result = run(svc.revoke_permissions_batch("42", ["user:read"], db))
        assert result == (["user:read"], [])
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_revoke_permissions_batch_empty_calls_no_flush(self, svc):
        db = MagicMock(); mkq(db, all=[])
        result = run(svc.revoke_permissions_batch("42", [], db))
        assert result == ([], [])
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    # ── grant_permission（已存在——无需实例化 UserPermission）──

    def test_grant_permission_existing_calls_no_flush(self, svc):
        db = MagicMock(); mkq(db, first=MagicMock())
        result = run(svc.grant_permission("42", "user:read", "1", None, db))
        assert result is True
        db.flush.assert_not_called()
        db.commit.assert_not_called()


# ──────────────────────────────────────────────
# 2. grant_permission 始终返回 True
# ──────────────────────────────────────────────

class TestGrantPermissionAlwaysTrue:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_returns_true_when_exists(self, svc):
        db = MagicMock(); mkq(db, first=MagicMock())
        assert run(svc.grant_permission("42", "user:read", "1", None, db)) is True

    def test_returns_true_when_new(self, svc):
        """新权限：应调用 flush 而非 commit。"""
        db = MagicMock(); mkq(db, first=None)
        result = run(svc.grant_permission("42", "user:read", "1", None, db))
        assert result is True
        assert db.flush.called
        assert not db.commit.called

    def test_never_returns_false(self, svc):
        assert run(svc.grant_permission("42", "a", "1", None, mkq(MagicMock(), first=MagicMock()))) is True
        assert run(svc.grant_permission("42", "b", "1", None, mkq(MagicMock(), first=None))) is True


# ──────────────────────────────────────────────
# 3. assign_role 两条路径均返回 True
# ──────────────────────────────────────────────

class TestAssignRoleBothPathsReturnTrue:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_returns_true_when_already_assigned(self, svc):
        """角色已分配 → early return，无 flush。"""
        db = MagicMock()
        mkq_multi(db, {
            "RbacRole": {"first": MagicMock(id="r1")},
            "UserRole": {"first": MagicMock()},
        })
        result = run(svc.assign_role("42", "r1", "1", None, db))
        assert result is True
        db.flush.assert_not_called()

    def test_returns_true_when_newly_assigned(self, svc):
        """新分配 → flush 一次。"""
        db = MagicMock()
        mkq_multi(db, {
            "RbacRole": {"first": MagicMock(id="r1")},
            "UserRole": {"first": None},
        })
        result = run(svc.assign_role("42", "r1", "1", None, db))
        assert result is True
        db.flush.assert_called_once()
        db.commit.assert_not_called()


# ──────────────────────────────────────────────
# 4. revoke_permission（单数）弃用
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
        db = MagicMock(); mkq(db, delete=1)
        run(svc.revoke_permission("42", "user:read", db))
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_returns_true_when_found(self, svc):
        db = MagicMock(); mkq(db, delete=1)
        assert run(svc.revoke_permission("42", "user:read", db)) is True

    def test_returns_false_when_not_found(self, svc):
        db = MagicMock(); mkq(db, delete=0)
        assert run(svc.revoke_permission("42", "x:y", db)) is False


# ──────────────────────────────────────────────
# 5. revoke_permissions_batch — 两步流程
# ──────────────────────────────────────────────

class TestRevokePermissionsBatch:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_pre_queries_then_deletes(self, svc):
        db = MagicMock(); mkq(db, all=[("user:read",), ("user:write",)])
        revoked, failed = run(svc.revoke_permissions_batch("42", ["user:read", "user:write", "nonexistent"], db))
        assert set(revoked) == {"user:read", "user:write"}
        assert set(failed) == {"nonexistent"}

    def test_empty_revoked_when_none_exist(self, svc):
        db = MagicMock(); mkq(db, all=[])
        revoked, failed = run(svc.revoke_permissions_batch("42", ["nonexistent"], db))
        assert revoked == []
        assert failed == ["nonexistent"]

    def test_uses_flush_not_commit(self, svc):
        db = MagicMock(); mkq(db, all=[("user:read",)])
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

    def test_service_flush_tm_commit(self, svc):
        from app.core.transaction import TransactionManager

        db = MagicMock(); mkq(db, all=[("user:read",)])
        with TransactionManager.transaction(db) as sess:
            run(svc.revoke_permissions_batch("42", ["user:read"], sess))

        db.flush.assert_called_once()
        db.commit.assert_called_once()

    def test_multiple_ops_one_commit(self, svc):
        from app.core.transaction import TransactionManager

        db = MagicMock()
        mkq_multi(db, {
            "UserPermission": {"all": [("user:read",)], "first": None},
        })

        with TransactionManager.transaction(db) as sess:
            run(svc.revoke_permissions_batch("42", ["user:read"], sess))
            run(svc.grant_permission("42", "user:write", "1", None, sess))

        assert db.commit.call_count == 1


# ──────────────────────────────────────────────
# 7. 回归——第三轮审查
# ──────────────────────────────────────────────

class TestRegressionFromThirdReview:
    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_assign_role_not_found_for_inactive_role(self, svc):
        from app.core.exceptions import NotFoundError

        db = MagicMock()
        mkq_multi(db, {"RbacRole": {"first": None}})

        with pytest.raises(NotFoundError):
            run(svc.assign_role("42", "inactive-role", "1", None, db))

    def test_grant_permission_always_returns_true(self, svc):
        assert run(svc.grant_permission("42", "a", "1", None, mkq(MagicMock(), first=MagicMock()))) is True
        assert run(svc.grant_permission("42", "b", "1", None, mkq(MagicMock(), first=None))) is True

    def test_revoke_role_false_when_nothing_deleted(self, svc):
        db = MagicMock(); mkq(db, delete=0)
        assert run(svc.revoke_role("42", "r1", db)) is False

    def test_revoke_role_true_when_deleted(self, svc):
        db = MagicMock(); mkq(db, delete=3)
        assert run(svc.revoke_role("42", "r1", db)) is True

    def test_revoke_permissions_batch_uses_flush_semantics(self, svc):
        db = MagicMock(); mkq(db, all=[("user:read",)])
        run(svc.revoke_permissions_batch("42", ["user:read"], db))
        db.flush.assert_called_once()
        db.commit.assert_not_called()

    def test_create_role_calls_flush_twice(self, svc):
        """create_role 两次 flush：获取 role.id + 权限关联。"""
        db = MagicMock()
        run(svc.create_role("r", "d", ["user:read"], False, db))
        assert db.flush.call_count == 2
        db.commit.assert_not_called()


# ──────────────────────────────────────────────
# 8. grant_permissions_batch — 批量授予
# ──────────────────────────────────────────────

class TestGrantPermissionsBatch:
    """验证 grant_permissions_batch 的两步流程"""

    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_grants_only_missing_permissions(self, svc):
        """应仅授予不存在的权限，跳过已存在的。"""
        db = MagicMock()
        # 预查询返回 "user:read" 已存在
        mkq(db, all=[("user:read",)])
        result = run(svc.grant_permissions_batch(
            "42", ["user:read", "user:write", "user:delete"], "1", None, db,
        ))
        assert result["granted"] == ["user:write", "user:delete"]
        assert result["skipped"] == ["user:read"]
        assert result["failed"] == []

    def test_grants_all_when_none_exist(self, svc):
        """无已存在权限时应授予全部。"""
        db = MagicMock()
        mkq(db, all=[])
        result = run(svc.grant_permissions_batch("42", ["a", "b"], "1", None, db))
        assert set(result["granted"]) == {"a", "b"}
        assert result["skipped"] == []

    def test_skips_all_when_all_exist(self, svc):
        """全部已存在时应全部跳过。"""
        db = MagicMock()
        mkq(db, all=[("a",), ("b",)])
        result = run(svc.grant_permissions_batch("42", ["a", "b"], "1", None, db))
        assert result["granted"] == []
        assert set(result["skipped"]) == {"a", "b"}

    def test_uses_batch_insert_when_granting(self, svc):
        """授予多条权限时应使用 db.add_all() 而非逐条 db.add()。"""
        db = MagicMock()
        mkq(db, all=[])  # 无已存在权限

        run(svc.grant_permissions_batch("42", ["a", "b", "c"], "1", None, db))

        # 应调用 add_all 一次
        db.add_all.assert_called_once()
        # 不应调用 add（逐条模式）
        db.add.assert_not_called()

    def test_uses_flush_not_commit(self, svc):
        """grant_permissions_batch 应使用 flush 而非 commit。"""
        db = MagicMock()
        mkq(db, all=[])  # 无已存在 → 新增 → flush
        run(svc.grant_permissions_batch("42", ["user:read"], "1", None, db))
        db.flush.assert_called_once()
        db.commit.assert_not_called()


# ──────────────────────────────────────────────
# 9. revoke_permission（单数）运行时弃用警告
# ──────────────────────────────────────────────

class TestRevokePermissionDeprecationWarning:
    """revoke_permission(单数) 应在运行时发出 DeprecationWarning。"""

    @pytest.fixture
    def svc(self):
        return RBACService()

    def test_emits_deprecation_warning(self, svc):
        """调用时应发出 DeprecationWarning。"""
        import warnings
        db = MagicMock(); mkq(db, delete=1)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            run(svc.revoke_permission("42", "user:read", db))
            # 过滤出我们发出的弃用警告（排除运行时的"no event loop"警告）
            our_warnings = [
                x for x in w
                if issubclass(x.category, DeprecationWarning)
                and "RBACService" in str(x.message)
            ]
            assert len(our_warnings) >= 1
            assert "revoke_permissions_batch" in str(our_warnings[0].message)
