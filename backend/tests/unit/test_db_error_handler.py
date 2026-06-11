"""Tests for app/utils/db_error_handler.py — 100% coverage."""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError


# ── Helpers ──

def mock_db_session():
    """Create a mock that isinstance check passes for Session."""
    db = MagicMock(spec=Session)
    db.rollback.return_value = None
    db.commit.return_value = None
    return db


def mock_db_plain():
    """Simple mock without spec, for DBTransaction tests."""
    db = MagicMock()
    db.rollback.return_value = None
    db.commit.return_value = None
    return db


class TestHandleDbErrorsSync:
    """handle_db_errors decorator (sync version)."""

    def test_success_no_db(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(x):
            return x * 2

        result = my_func(21)
        assert result == 42

    def test_success_with_db_in_args(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db, value):
            return value

        db = mock_db_session()
        result = my_func(db, 99)
        assert result == 99

    def test_success_with_db_in_kwargs(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(value, db=None):
            return value

        db = mock_db_session()
        result = my_func(42, db=db)
        assert result == 42

    def test_integrity_unique_constraint(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise IntegrityError("orig", "params", Exception("UNIQUE constraint failed"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 409
        assert "唯一性约束" in exc.value.detail
        db.rollback.assert_called_once()

    def test_integrity_unique_constraint_no_db(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func():
            raise IntegrityError("orig", "params", Exception("UNIQUE constraint failed"))

        with pytest.raises(HTTPException) as exc:
            my_func()
        assert exc.value.status_code == 409

    def test_integrity_duplicate_key(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise IntegrityError("orig", "params", Exception("duplicate key value"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 409
        assert "唯一性约束" in exc.value.detail

    def test_integrity_foreign_key(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise IntegrityError("orig", "params", Exception("FOREIGN KEY constraint failed"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 400
        assert "关联数据不存在" in exc.value.detail

    def test_integrity_other(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise IntegrityError("orig", "params", Exception("some other constraint"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 400
        assert "数据完整性错误" in exc.value.detail

    def test_integrity_without_orig_attr(self):
        """e.orig might not exist on all IntegrityError instances."""
        from app.utils.db_error_handler import handle_db_errors

        err = IntegrityError("orig", "params", Exception("test"))
        # Remove the orig attribute
        del err.orig

        @handle_db_errors
        def my_func(db):
            raise err

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        # Without orig, error_msg = str(e); "UNIQUE" and "FOREIGN KEY" not in msg, so falls to else
        assert exc.value.status_code == 400
        assert "数据完整性错误" in exc.value.detail

    def test_operational_error(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise OperationalError("orig", "params", Exception("connection lost"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 503
        assert "请稍后重试" in exc.value.detail
        db.rollback.assert_called_once()

    def test_operational_error_no_db(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func():
            raise OperationalError("orig", "params", Exception("connection lost"))

        with pytest.raises(HTTPException) as exc:
            my_func()
        assert exc.value.status_code == 503

    def test_sqlalchemy_error(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise SQLAlchemyError("generic db error")

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 500
        assert "请联系管理员" in exc.value.detail
        db.rollback.assert_called_once()

    def test_sqlalchemy_error_no_db(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func():
            raise SQLAlchemyError("generic db error")

        with pytest.raises(HTTPException) as exc:
            my_func()
        assert exc.value.status_code == 500

    def test_http_exception_re_raised(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise HTTPException(status_code=403, detail="forbidden")

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 403
        assert exc.value.detail == "forbidden"
        db.rollback.assert_called_once()

    def test_http_exception_no_db(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func():
            raise HTTPException(status_code=403, detail="forbidden")

        with pytest.raises(HTTPException) as exc:
            my_func()
        assert exc.value.status_code == 403

    def test_business_error_re_raised(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise BusinessError("业务异常")

        db = mock_db_session()
        with pytest.raises(BusinessError) as exc:
            my_func(db)
        assert "业务异常" in str(exc.value)
        db.rollback.assert_called_once()

    def test_business_error_no_db(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func():
            raise BusinessError("业务异常")

        with pytest.raises(BusinessError) as exc:
            my_func()
        assert "业务异常" in str(exc.value)

    def test_unexpected_exception(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func(db):
            raise ValueError("unexpected value")

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            my_func(db)
        assert exc.value.status_code == 500
        assert "操作失败" in exc.value.detail
        db.rollback.assert_called_once()

    def test_unexpected_exception_no_db(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_func():
            raise ValueError("unexpected value")

        with pytest.raises(HTTPException) as exc:
            my_func()
        assert exc.value.status_code == 500

    def test_wrapper_preserves_name(self):
        from app.utils.db_error_handler import handle_db_errors

        @handle_db_errors
        def my_custom_func():
            return 1

        assert my_custom_func.__name__ == "my_custom_func"


class TestHandleDbErrorsAsync:
    """handle_db_errors_async decorator (async version)."""

    async def test_success_no_db(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(x):
            return x * 2

        result = await my_func(21)
        assert result == 42

    async def test_success_with_db_in_args(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db, value):
            return value

        db = mock_db_session()
        result = await my_func(db, 99)
        assert result == 99

    async def test_success_with_db_in_kwargs(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(value, db=None):
            return value

        db = mock_db_session()
        result = await my_func(42, db=db)
        assert result == 42

    async def test_integrity_unique(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise IntegrityError("orig", "params", Exception("UNIQUE constraint failed"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 409
        db.rollback.assert_called_once()

    async def test_integrity_unique_no_db(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func():
            raise IntegrityError("orig", "params", Exception("UNIQUE constraint failed"))

        with pytest.raises(HTTPException) as exc:
            await my_func()
        assert exc.value.status_code == 409

    async def test_integrity_foreign_key(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise IntegrityError("orig", "params", Exception("FOREIGN KEY constraint failed"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 400
        assert "关联数据不存在" in exc.value.detail

    async def test_integrity_other(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise IntegrityError("orig", "params", Exception("other constraint"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 400

    async def test_integrity_no_orig(self):
        from app.utils.db_error_handler import handle_db_errors_async

        err = IntegrityError("orig", "params", Exception("test"))
        del err.orig

        @handle_db_errors_async
        async def my_func(db):
            raise err

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 400

    async def test_operational_error(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise OperationalError("orig", "params", Exception("conn lost"))

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 503
        db.rollback.assert_called_once()

    async def test_operational_error_no_db(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func():
            raise OperationalError("orig", "params", Exception("conn lost"))

        with pytest.raises(HTTPException) as exc:
            await my_func()
        assert exc.value.status_code == 503

    async def test_sqlalchemy_error(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise SQLAlchemyError("generic")

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 500
        db.rollback.assert_called_once()

    async def test_sqlalchemy_error_no_db(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func():
            raise SQLAlchemyError("generic")

        with pytest.raises(HTTPException) as exc:
            await my_func()
        assert exc.value.status_code == 500

    async def test_http_exception(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise HTTPException(401, "unauthorized")

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 401
        db.rollback.assert_called_once()

    async def test_http_exception_no_db(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func():
            raise HTTPException(401, "unauthorized")

        with pytest.raises(HTTPException) as exc:
            await my_func()
        assert exc.value.status_code == 401

    async def test_business_error(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise BusinessError("业务异常")

        db = mock_db_session()
        with pytest.raises(BusinessError) as exc:
            await my_func(db)
        assert "业务异常" in str(exc.value)
        db.rollback.assert_called_once()

    async def test_business_error_no_db(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func():
            raise BusinessError("业务异常")

        with pytest.raises(BusinessError) as exc:
            await my_func()
        assert "业务异常" in str(exc.value)

    async def test_unexpected_exception(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func(db):
            raise ValueError("unexpected")

        db = mock_db_session()
        with pytest.raises(HTTPException) as exc:
            await my_func(db)
        assert exc.value.status_code == 500
        db.rollback.assert_called_once()

    async def test_unexpected_exception_no_db(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_func():
            raise ValueError("unexpected")

        with pytest.raises(HTTPException) as exc:
            await my_func()
        assert exc.value.status_code == 500

    async def test_wrapper_preserves_name(self):
        from app.utils.db_error_handler import handle_db_errors_async

        @handle_db_errors_async
        async def my_custom_func():
            return 1

        assert my_custom_func.__name__ == "my_custom_func"


class TestDBTransaction:
    """DBTransaction context manager."""

    def test_enter_returns_db(self):
        from app.utils.db_error_handler import DBTransaction
        db = mock_db_session()
        with DBTransaction(db) as ctx:
            assert ctx is db

    def test_exit_no_exception_no_auto_commit(self):
        from app.utils.db_error_handler import DBTransaction
        db = mock_db_session()
        with DBTransaction(db) as ctx:
            ctx.add("something")
        db.rollback.assert_not_called()
        db.commit.assert_not_called()

    def test_exit_no_exception_with_auto_commit(self):
        from app.utils.db_error_handler import DBTransaction
        db = mock_db_session()
        with DBTransaction(db, auto_commit=True) as ctx:
            ctx.add("something")
        db.commit.assert_called_once()
        db.rollback.assert_not_called()

    def test_exit_with_exception_rollback(self):
        from app.utils.db_error_handler import DBTransaction
        db = mock_db_session()
        with pytest.raises(ValueError):
            with DBTransaction(db) as ctx:
                ctx.add("something")
                raise ValueError("test error")
        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_exit_auto_commit_failure_rollback(self):
        from app.utils.db_error_handler import DBTransaction
        db = mock_db_session()
        db.commit.side_effect = Exception("commit failed")

        with pytest.raises(Exception) as exc:
            with DBTransaction(db, auto_commit=True) as ctx:
                ctx.add("something")
        assert "commit failed" in str(exc.value)
        db.rollback.assert_called_once()
        db.commit.assert_called_once()
