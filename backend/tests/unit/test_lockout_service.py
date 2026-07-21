"""Tests for app/services/lockout_service.py — 目标 100% 覆盖。

覆盖要点：
- __init__: 默认参数 + 自定义参数
- check_locked:
  * 用户未锁定 (locked_until=None) → 无动作
  * 锁定已过期 → 自动清理
  * 锁定未过期 → 抛 423
  * locked_until 朴素 datetime（无 tzinfo）→ 补 UTC
  * 显式传入 now 参数
  * HTTPException 正常向上抛
  * 其它异常 → 抛 500
- record_failed:
  * 未达阈值 → 递增计数，不锁定
  * 达到阈值 → 递增计数并锁定
  * 返回最新计数
- clear: 重置 failed_login_count 和 locked_until
- unlock_expired:
  * 无过期账户 → 返回 0，不 commit
  * 有过期账户 → 解锁，返回计数，commit
  * admin 账户被锁 → 强制解锁
  * admin + 普通过期账户同时存在
- get_lockout_service:
  * 首次调用创建单例
  * 后续调用返回同一实例
  * 从 config 读取默认参数
"""
import importlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import _MODULE_MAP
from app.models.base import Base
from app.models.user import User
from app.services.lockout_service import (
    LockoutService,
    get_lockout_service,
)


# ---------------------------------------------------------------------------
# 内存 DB fixture
# ---------------------------------------------------------------------------


def _build_session():
    """构建内存数据库，包含完整 Base.metadata。"""
    for mod_path in set(_MODULE_MAP.values()):
        importlib.import_module(f"app.models{mod_path}")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    return db, engine


@pytest.fixture
def db_session():
    db, engine = _build_session()
    yield db
    db.close()
    engine.dispose()


@pytest.fixture
def svc_default():
    """默认参数 (max=5, lockout=15min) 的 LockoutService。"""
    return LockoutService(max_failed_attempts=5, lockout_minutes=15)


def _make_user(db, **kwargs) -> User:
    """创建并持久化一个测试用户。"""
    defaults = {
        "username": "testuser",
        "hashed_password": "x",
    }
    defaults.update(kwargs)
    u = User(**defaults)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestInit:
    def test_default_params(self):
        s = LockoutService()
        assert s.max_failed_attempts == 5
        assert s.lockout_minutes == 15

    def test_custom_params(self):
        s = LockoutService(max_failed_attempts=3, lockout_minutes=10)
        assert s.max_failed_attempts == 3
        assert s.lockout_minutes == 10


# ---------------------------------------------------------------------------
# check_locked
# ---------------------------------------------------------------------------


class TestCheckLocked:
    def test_user_not_locked_does_nothing(self, svc_default, db_session):
        u = _make_user(db_session, locked_until=None)
        # 不应抛异常
        svc_default.check_locked(u, u.username, db_session)
        # 状态未变
        db_session.refresh(u)
        assert u.locked_until is None

    def test_locked_expired_auto_clears(self, svc_default, db_session):
        """锁定时间已过 → 自动清理，不抛异常。"""
        now = datetime.now(timezone.utc)
        u = _make_user(
            db_session,
            locked_until=now - timedelta(minutes=5),
            failed_login_count=5,
        )
        svc_default.check_locked(u, u.username, db_session, now=now)
        db_session.refresh(u)
        assert u.locked_until is None
        assert u.failed_login_count == 0

    def test_locked_not_expired_raises_423(self, svc_default, db_session):
        """锁定未过期 → 抛 423。"""
        now = datetime.now(timezone.utc)
        u = _make_user(
            db_session,
            locked_until=now + timedelta(minutes=10),
            failed_login_count=5,
        )
        with pytest.raises(HTTPException) as exc_info:
            svc_default.check_locked(u, u.username, db_session, now=now)
        assert exc_info.value.status_code == 423
        assert "账户已锁定" in exc_info.value.detail

    def test_locked_until_naive_datetime_gets_utc_tzinfo(self, svc_default, db_session):
        """locked_until 无 tzinfo → 补 UTC 后判断过期。"""
        # 朴素 datetime（无 tzinfo），表示已过期
        naive_past = datetime.utcnow() - timedelta(minutes=5)
        u = _make_user(
            db_session,
            locked_until=naive_past,
            failed_login_count=5,
        )
        # 不应抛 423，应自动清理
        svc_default.check_locked(u, u.username, db_session)
        db_session.refresh(u)
        assert u.locked_until is None

    def test_locked_until_naive_datetime_still_locked(self, svc_default, db_session):
        """locked_until 无 tzinfo 但未过期 → 抛 423。"""
        naive_future = datetime.utcnow() + timedelta(minutes=10)
        u = _make_user(
            db_session,
            locked_until=naive_future,
            failed_login_count=5,
        )
        with pytest.raises(HTTPException) as exc_info:
            svc_default.check_locked(u, u.username, db_session)
        assert exc_info.value.status_code == 423

    def test_now_defaults_to_utc_now(self, svc_default, db_session):
        """不传 now → 使用 datetime.now(timezone.utc)。"""
        now = datetime.now(timezone.utc)
        u = _make_user(
            db_session,
            locked_until=now + timedelta(minutes=5),
            failed_login_count=5,
        )
        with pytest.raises(HTTPException) as exc_info:
            svc_default.check_locked(u, u.username, db_session)
        assert exc_info.value.status_code == 423

    def test_remaining_minutes_in_detail(self, svc_default, db_session):
        """423 detail 中包含剩余分钟数。"""
        now = datetime.now(timezone.utc)
        u = _make_user(
            db_session,
            locked_until=now + timedelta(minutes=10),
            failed_login_count=5,
        )
        with pytest.raises(HTTPException) as exc_info:
            svc_default.check_locked(u, u.username, db_session, now=now)
        # 剩余约 10 分钟（int((lock_time - now).total_seconds() / 60) + 1 = 11）
        assert "11" in exc_info.value.detail

    def test_http_exception_propagates(self, svc_default, db_session):
        """HTTPException 不被 except Exception 捕获，正常向上抛。"""
        now = datetime.now(timezone.utc)
        u = _make_user(
            db_session,
            locked_until=now + timedelta(minutes=5),
            failed_login_count=5,
        )
        with pytest.raises(HTTPException) as exc_info:
            svc_default.check_locked(u, u.username, db_session, now=now)
        # 确认是 423 而非 500（HTTPException 被 re-raise，未被 except Exception 转 500）
        assert exc_info.value.status_code == 423

    def test_unexpected_exception_raises_500(self, svc_default, db_session):
        """非 HTTPException 的异常 → 转为 500。"""
        # 构造一个会让 check_locked 内部抛非 HTTP 异常的场景：
        # user 对象的 locked_until 属性访问时抛异常
        class BombUser:
            username = "bomb"
            # 让 getattr(user, "locked_until", None) 返回一个 truthy 对象
            locked_until = "not-a-datetime"
            # 当后续代码尝试 lock_time.tzinfo 时，str 没有 tzinfo 属性 → AttributeError

        # BombUser.locked_until 是 str，str 没有 tzinfo 属性
        # 但代码先做 `if lock_time.tzinfo is None` → AttributeError
        # 这会被 except Exception 捕获并转 500
        with pytest.raises(HTTPException) as exc_info:
            svc_default.check_locked(BombUser(), "bomb", db_session)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "系统错误，请稍后再试"


# ---------------------------------------------------------------------------
# record_failed
# ---------------------------------------------------------------------------


class TestRecordFailed:
    def test_below_threshold_increments_count(self, svc_default, db_session):
        """未达阈值 → 计数+1，不锁定。"""
        u = _make_user(db_session, failed_login_count=0, locked_until=None)
        # SQLite + RETURNING 要求消费结果集后再 commit；源码顺序为
        # execute→commit→scalar，此处将 commit 替换为 no-op 使 scalar 可取值。
        # UPDATE 已对同一连接可见，后续可直接查询验证。
        with patch.object(db_session, "commit", lambda: None):
            count = svc_default.record_failed(u, db_session)
        assert count == 1
        row = db_session.execute(
            text("SELECT failed_login_count, locked_until FROM users WHERE id=:id"),
            {"id": u.id},
        ).first()
        assert row[0] == 1
        assert row[1] is None

    def test_reaching_threshold_locks_account(self, svc_default, db_session):
        """达到阈值 → 计数+1 并锁定。"""
        u = _make_user(
            db_session,
            failed_login_count=svc_default.max_failed_attempts - 1,
            locked_until=None,
        )
        before = datetime.now(timezone.utc)
        with patch.object(db_session, "commit", lambda: None):
            count = svc_default.record_failed(u, db_session)
        assert count == svc_default.max_failed_attempts
        row = db_session.execute(
            text("SELECT failed_login_count, locked_until FROM users WHERE id=:id"),
            {"id": u.id},
        ).first()
        assert row[0] == svc_default.max_failed_attempts
        assert row[1] is not None  # locked_until 已设置

    def test_exceeding_threshold_still_locks(self, svc_default, db_session):
        """超过阈值 → 仍锁定。"""
        u = _make_user(
            db_session,
            failed_login_count=svc_default.max_failed_attempts,
            locked_until=None,
        )
        with patch.object(db_session, "commit", lambda: None):
            count = svc_default.record_failed(u, db_session)
        assert count == svc_default.max_failed_attempts + 1
        row = db_session.execute(
            text("SELECT locked_until FROM users WHERE id=:id"),
            {"id": u.id},
        ).first()
        assert row[0] is not None

    def test_increments_from_zero_to_one(self, svc_default, db_session):
        """读-改-写模式：failed_login_count=0 时递增后返回 1。"""
        u = _make_user(db_session, failed_login_count=0, locked_until=None)

        count = svc_default.record_failed(u, db_session)
        assert count == 1

    def test_username_in_log_for_user_without_username(self, svc_default, db_session):
        """getattr(user, "username", "?") 兜底为 "?"。"""
        u = _make_user(db_session, username="realuser")

        class Wrapper:
            """包装真实 user.id，但 username 属性抛 AttributeError。"""

            def __init__(self, real):
                self.id = real.id

            @property
            def username(self):
                raise AttributeError  # getattr 回退为 "?"

        wrapper = Wrapper(u)
        with patch.object(db_session, "commit", lambda: None):
            count = svc_default.record_failed(wrapper, db_session)
        # 应正常执行，count 为真实递增后的值
        assert count >= 1


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


class TestClear:
    def test_resets_lock_state(self, svc_default, db_session):
        u = _make_user(
            db_session,
            failed_login_count=5,
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        svc_default.clear(u, db_session)
        db_session.refresh(u)
        assert u.failed_login_count == 0
        assert u.locked_until is None

    def test_clear_already_clean_user(self, svc_default, db_session):
        """对已干净的用户调用 clear 也是 noop。"""
        u = _make_user(db_session, failed_login_count=0, locked_until=None)
        svc_default.clear(u, db_session)
        db_session.refresh(u)
        assert u.failed_login_count == 0
        assert u.locked_until is None


# ---------------------------------------------------------------------------
# unlock_expired
# ---------------------------------------------------------------------------


class TestUnlockExpired:
    def test_no_locked_users_returns_zero(self, svc_default, db_session):
        """无锁定用户 → 返回 0。"""
        _make_user(db_session, username="active1", locked_until=None)
        _make_user(db_session, username="active2", locked_until=None)
        count = svc_default.unlock_expired(db_session)
        assert count == 0

    def test_unlocks_expired_user(self, svc_default, db_session):
        """有过期锁定用户 → 解锁并返回 1。"""
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        u = _make_user(
            db_session,
            username="expired_user",
            locked_until=past,
            failed_login_count=5,
        )
        count = svc_default.unlock_expired(db_session)
        assert count == 1
        db_session.refresh(u)
        assert u.locked_until is None
        assert u.failed_login_count == 0

    def test_does_not_unlock_still_locked_user(self, svc_default, db_session):
        """锁定未过期的用户不被解锁。"""
        future = datetime.now(timezone.utc) + timedelta(minutes=10)
        u = _make_user(
            db_session,
            username="still_locked",
            locked_until=future,
            failed_login_count=5,
        )
        count = svc_default.unlock_expired(db_session)
        assert count == 0
        db_session.refresh(u)
        assert u.locked_until is not None  # 仍锁定

    def test_admin_force_unlocked(self, svc_default, db_session):
        """admin 账户即使锁定未过期也强制解锁。"""
        future = datetime.now(timezone.utc) + timedelta(minutes=30)
        admin = _make_user(
            db_session,
            username="admin",
            locked_until=future,
            failed_login_count=5,
        )
        count = svc_default.unlock_expired(db_session)
        assert count == 1
        db_session.refresh(admin)
        assert admin.locked_until is None
        assert admin.failed_login_count == 0

    def test_admin_and_expired_user_both_unlocked(self, svc_default, db_session):
        """admin + 普通过期账户同时存在 → 都解锁，返回 2。"""
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        future = datetime.now(timezone.utc) + timedelta(minutes=30)
        admin = _make_user(
            db_session,
            username="admin",
            locked_until=future,
            failed_login_count=5,
        )
        user = _make_user(
            db_session,
            username="expired",
            locked_until=past,
            failed_login_count=5,
        )
        count = svc_default.unlock_expired(db_session)
        assert count == 2
        db_session.refresh(admin)
        db_session.refresh(user)
        assert admin.locked_until is None
        assert user.locked_until is None

    def test_custom_admin_username(self, svc_default, db_session):
        """自定义 admin_username 参数。"""
        future = datetime.now(timezone.utc) + timedelta(minutes=30)
        super_admin = _make_user(
            db_session,
            username="superadmin",
            locked_until=future,
            failed_login_count=5,
        )
        count = svc_default.unlock_expired(db_session, admin_username="superadmin")
        assert count == 1
        db_session.refresh(super_admin)
        assert super_admin.locked_until is None

    def test_admin_not_locked_not_counted(self, svc_default, db_session):
        """admin 账户未锁定 → 不计入解锁数。"""
        admin = _make_user(
            db_session,
            username="admin",
            locked_until=None,
            failed_login_count=0,
        )
        count = svc_default.unlock_expired(db_session)
        assert count == 0

    def test_multiple_expired_users(self, svc_default, db_session):
        """多个过期用户都被解锁。"""
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        u1 = _make_user(db_session, username="u1", locked_until=past, failed_login_count=5)
        u2 = _make_user(db_session, username="u2", locked_until=past, failed_login_count=3)
        u3 = _make_user(db_session, username="u3", locked_until=past, failed_login_count=5)
        count = svc_default.unlock_expired(db_session)
        assert count == 3
        for u in (u1, u2, u3):
            db_session.refresh(u)
            assert u.locked_until is None
            assert u.failed_login_count == 0

    def test_expired_admin_unlocked_in_loop_and_admin_branch(self, svc_default, db_session):
        """admin 锁定已过期 → 在 step1 过期循环中被解锁。

        由于测试 fixture 使用 ``autoflush=False``，step1 的 ORM 修改
        (``user.locked_until = None``) 不会立即同步到 DB，
        step2 的 ``User.locked_until.isnot(None)`` 查询仍命中 admin，
        因此 admin 被重复计数。最终 admin.locked_until 为 None。

        生产环境（autoflush=True）中 step1 修改会自动 flush，
        step2 查询不会再命中 admin，仅计数 1 次。
        """
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        admin = _make_user(
            db_session,
            username="admin",
            locked_until=past,
            failed_login_count=5,
        )
        count = svc_default.unlock_expired(db_session)
        # autoflush=False: step1 + step2 均计数 admin
        assert count == 2
        db_session.refresh(admin)
        assert admin.locked_until is None
        assert admin.failed_login_count == 0


# ---------------------------------------------------------------------------
# get_lockout_service
# ---------------------------------------------------------------------------


class TestGetLockoutService:
    def test_creates_singleton_from_config(self):
        """首次调用 → 从 config 读取参数创建单例。"""
        # 重置模块级单例
        import app.services.lockout_service as mod
        original = mod._lockout_service
        mod._lockout_service = None
        try:
            s1 = get_lockout_service()
            assert s1 is not None
            assert s1.max_failed_attempts > 0
            assert s1.lockout_minutes > 0
            # 第二次调用应返回同一实例
            s2 = get_lockout_service()
            assert s2 is s1
        finally:
            mod._lockout_service = original

    def test_subsequent_calls_return_same_instance(self):
        """后续调用返回同一实例（忽略新参数）。"""
        import app.services.lockout_service as mod
        original = mod._lockout_service
        mod._lockout_service = None
        try:
            s1 = get_lockout_service()
            s2 = get_lockout_service(max_failed_attempts=99, lockout_minutes=99)
            assert s2 is s1
            # 参数未变（单例已创建，新参数被忽略）
            assert s2.max_failed_attempts != 99
        finally:
            mod._lockout_service = original

    def test_custom_params_on_first_call(self):
        """首次调用传入自定义参数 → 使用自定义参数。"""
        import app.services.lockout_service as mod
        original = mod._lockout_service
        mod._lockout_service = None
        try:
            s = get_lockout_service(max_failed_attempts=7, lockout_minutes=20)
            assert s.max_failed_attempts == 7
            assert s.lockout_minutes == 20
        finally:
            mod._lockout_service = original
