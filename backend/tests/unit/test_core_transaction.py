"""Tests for app.core.transaction (100% coverage)."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseError
from app.core.transaction import (
    BatchOperation,
    TransactionManager,
    get_db_context,
    nested_transaction,
    retry_on_deadlock,
    run_in_transaction,
    savepoint,
    transaction,
    transactional,
    with_transaction,
)
from app.core.database import IS_SQLITE

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def mock_get_db(mock_db):
    def _gen():
        yield mock_db

    with patch("app.core.transaction.get_db", return_value=_gen()) as m:
        yield m


# ===================================================================
# get_db_context
# ===================================================================


class TestGetDbContext:
    def test_success(self, mock_db, mock_get_db):
        with get_db_context() as db:
            assert db is mock_db

    def test_on_error_no_crash(self, mock_db, mock_get_db):
        with pytest.raises(ValueError):
            with get_db_context() as db:
                raise ValueError("boom")
        mock_db.close.assert_not_called()


# ===================================================================
# TransactionManager.transaction (context manager)
# ===================================================================


class TestTransaction:
    def test_success_commits(self, mock_db):
        with transaction(mock_db) as db:
            assert db is mock_db
        mock_db.commit.assert_called_once()

    def test_failure_rollbacks_and_raises(self, mock_db):
        with pytest.raises(DatabaseError):
            with transaction(mock_db) as db:
                raise ValueError("something went wrong")
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()


# ===================================================================
# TransactionManager.transactional (decorator)
# ===================================================================


class TestTransactional:
    def test_session_in_args_success(self, mock_db):
        @transactional
        def my_func(db, x):
            return x * 2

        result = my_func(mock_db, 5)
        assert result == 10

    def test_session_in_args_failure(self, mock_db):
        @transactional
        def my_func(db):
            raise ValueError("oops")

        with pytest.raises(DatabaseError):
            my_func(mock_db)
        mock_db.rollback.assert_called_once()

    def test_session_in_kwargs(self, mock_db):
        @transactional
        def my_func(x, db):
            return x + 1

        result = my_func(41, db=mock_db)
        assert result == 42

    def test_no_session_auto_create_success(self, mock_db, mock_get_db):
        @transactional
        def my_func(session, x):
            return x * 3

        result = my_func(7)
        assert result == 21

    def test_no_session_auto_create_failure(self, mock_db, mock_get_db):
        @transactional
        def my_func(session):
            raise RuntimeError("fail")

        with pytest.raises(DatabaseError):
            my_func()
        mock_db.rollback.assert_called_once()

    def test_session_not_first_positional_arg(self, mock_db):
        @transactional
        def my_func(x, session):
            return 42

        result = my_func(100, mock_db)
        assert result == 42


# ===================================================================
# TransactionManager.run_in_transaction
# ===================================================================


class TestRunInTransaction:
    def test_success(self, mock_db):
        def my_func(db, a, b):
            return a + b

        result = run_in_transaction(my_func, mock_db, 1, 2)
        assert result == 3
        mock_db.commit.assert_called_once()

    def test_failure(self, mock_db):
        def my_func(db):
            raise ValueError("fail")

        with pytest.raises(DatabaseError):
            run_in_transaction(my_func, mock_db)
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()


# ===================================================================
# TransactionManager.nested_transaction
# ===================================================================


class TestNestedTransaction:
    def test_success(self, mock_db):
        mock_nested = MagicMock()
        mock_db.begin_nested.return_value = mock_nested

        with nested_transaction(mock_db) as sp:
            assert sp is mock_nested

        mock_db.begin_nested.assert_called_once()
        mock_nested.commit.assert_called_once()

    def test_failure(self, mock_db):
        mock_nested = MagicMock()
        mock_db.begin_nested.return_value = mock_nested

        with pytest.raises(DatabaseError):
            with nested_transaction(mock_db) as sp:
                raise ValueError("nested fail")

        mock_nested.rollback.assert_called_once()
        mock_nested.commit.assert_not_called()


# ===================================================================
# TransactionManager.savepoint
# ===================================================================


class TestSavepoint:
    def test_with_name(self, mock_db):
        mock_sp = MagicMock()
        mock_db.begin_nested.return_value = mock_sp

        with savepoint(mock_db, "my_sp") as sp:
            assert sp is mock_sp

        mock_sp.commit.assert_called_once()

    def test_without_name(self, mock_db):
        mock_sp = MagicMock()
        mock_db.begin_nested.return_value = mock_sp

        with savepoint(mock_db) as sp:
            assert sp is mock_sp

        mock_sp.commit.assert_called_once()

    def test_failure(self, mock_db):
        mock_sp = MagicMock()
        mock_db.begin_nested.return_value = mock_sp

        with pytest.raises(DatabaseError):
            with savepoint(mock_db, "sp_name") as sp:
                raise RuntimeError("sp fail")

        mock_sp.rollback.assert_called_once()
        mock_sp.commit.assert_not_called()


# ===================================================================
# with_transaction (高级装饰器)
# ===================================================================


class TestWithTransaction:
    def test_invalid_isolation_level(self):
        with pytest.raises(ValueError, match="无效的隔离级别"):
            with_transaction(isolation_level="INVALID")

    @patch("app.core.transaction.get_db")
    def test_auto_create_success(self, mock_get_db):
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        @with_transaction(isolation_level="REPEATABLE READ")
        def my_func(session):
            return "ok"

        result = my_func()
        assert result == "ok"
        mock_db.commit.assert_called_once()
        # SQLite 下 SET TRANSACTION 被短路，不调用 execute；
        # 非 SQLite 下才调用。当前测试环境为 SQLite，故 execute 不应被调用。
        if IS_SQLITE:
            mock_db.execute.assert_not_called()
        else:
            assert mock_db.execute.call_count >= 1

    @patch("app.core.transaction.get_db")
    def test_auto_create_failure(self, mock_get_db):
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        @with_transaction(isolation_level="SERIALIZABLE")
        def my_func(session):
            raise ValueError("fail")

        with pytest.raises(DatabaseError):
            my_func()
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    @patch("app.core.transaction.text", side_effect=lambda x: x)
    def test_session_in_args_success(self, mock_text):
        mock_db = MagicMock(spec=Session)

        @with_transaction(isolation_level="READ COMMITTED")
        def my_func(db, x):
            return x + 1

        result = my_func(mock_db, 41)
        assert result == 42
        mock_db.commit.assert_called_once()

    @patch("app.core.transaction.text", side_effect=lambda x: x)
    def test_session_in_args_failure(self, mock_text):
        mock_db = MagicMock(spec=Session)

        @with_transaction(isolation_level="READ COMMITTED")
        def my_func(db):
            raise RuntimeError("fail")

        with pytest.raises(DatabaseError):
            my_func(mock_db)
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    @patch("app.core.transaction.text", side_effect=lambda x: x)
    def test_readonly(self, mock_text):
        mock_db = MagicMock(spec=Session)

        @with_transaction(readonly=True)
        def my_func(db):
            return "readonly_ok"

        result = my_func(mock_db)
        assert result == "readonly_ok"
        mock_db.commit.assert_called_once()
        # SQLite 下 SET TRANSACTION READ ONLY 被短路，不调用 execute
        if IS_SQLITE:
            mock_db.execute.assert_not_called()
        else:
            mock_db.execute.assert_called_with("SET TRANSACTION READ ONLY")

    @patch("app.core.transaction.text", side_effect=lambda x: x)
    def test_both_isolation_and_readonly(self, mock_text):
        mock_db = MagicMock(spec=Session)

        @with_transaction(isolation_level="SERIALIZABLE", readonly=True)
        def my_func(db):
            return "done"

        result = my_func(mock_db)
        assert result == "done"
        mock_db.commit.assert_called_once()

    @patch("app.core.transaction.text", side_effect=lambda x: x)
    def test_no_isolation_no_readonly(self, mock_text):
        mock_db = MagicMock(spec=Session)

        @with_transaction()
        def my_func(db):
            return "plain"

        result = my_func(mock_db)
        assert result == "plain"
        mock_db.commit.assert_called_once()
        mock_db.execute.assert_not_called()

    @patch("app.core.transaction.get_db")
    def test_no_isolation_auto_create(self, mock_get_db):
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        @with_transaction()
        def my_func(session):
            return "auto"

        result = my_func()
        assert result == "auto"
        mock_db.commit.assert_called_once()

    @patch("app.core.transaction.get_db")
    def test_auto_create_exception_in_apply(self, mock_get_db):
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = iter([mock_db])
        mock_db.execute.side_effect = RuntimeError("exec fail")

        @with_transaction(isolation_level="READ COMMITTED")
        def my_func(session):
            return "never reached"

        # SQLite 下 _apply_tx_settings 被短路，execute 不会被调用，
        # 因此不会触发 RuntimeError，函数正常返回。
        if IS_SQLITE:
            result = my_func()
            assert result == "never reached"
            mock_db.commit.assert_called_once()
            mock_db.rollback.assert_not_called()
        else:
            with pytest.raises(DatabaseError):
                my_func()
            mock_db.rollback.assert_called_once()


# ===================================================================
# retry_on_deadlock
# ===================================================================


class TestRetryOnDeadlock:
    def test_success_first_try(self):
        @retry_on_deadlock(max_retries=3, delay=0)
        def my_func():
            return "done"

        result = my_func()
        assert result == "done"

    def test_deadlock_then_retry_succeeds(self):
        call_count = 0

        @retry_on_deadlock(max_retries=3, delay=0)
        def my_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise SQLAlchemyError("deadlock detected")
            return "ok"

        result = my_func()
        assert result == "ok"
        assert call_count == 2

    def test_all_retries_fail(self):
        call_count = 0

        @retry_on_deadlock(max_retries=3, delay=0)
        def my_func():
            nonlocal call_count
            call_count += 1
            raise SQLAlchemyError("deadlock happened")

        with pytest.raises(SQLAlchemyError):
            my_func()
        assert call_count == 3

    def test_non_deadlock_error_raised_immediately(self):
        @retry_on_deadlock(max_retries=3, delay=0)
        def my_func():
            raise SQLAlchemyError("some other error")

        with pytest.raises(SQLAlchemyError):
            my_func()

    def test_lock_error_retries(self):
        call_count = 0

        @retry_on_deadlock(max_retries=2, delay=0)
        def my_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise SQLAlchemyError("database lock timeout")
            return "ok"

        result = my_func()
        assert result == "ok"
        assert call_count == 2

    def test_zero_max_retries_reaches_fallback_error(self):
        @retry_on_deadlock(max_retries=0, delay=0)
        def my_func():
            raise SQLAlchemyError("deadlock")

        with pytest.raises(DatabaseError) as excinfo:
            my_func()
        assert "重试0次后" in str(excinfo.value)


# ===================================================================
# BatchOperation.batch_insert
# ===================================================================


class TestBatchInsert:
    def test_empty_items(self, mock_db):
        result = BatchOperation.batch_insert(mock_db, None, [])
        assert result == 0

    def test_single_batch(self, mock_db):
        items = [{"name": "a"}, {"name": "b"}]
        result = BatchOperation.batch_insert(mock_db, str, items, batch_size=1000)
        assert result == 2
        mock_db.bulk_insert_mappings.assert_called_once_with(str, items)
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_multiple_batches(self, mock_db):
        items = [{"id": i} for i in range(5)]
        result = BatchOperation.batch_insert(mock_db, dict, items, batch_size=2)
        assert result == 5
        assert mock_db.bulk_insert_mappings.call_count == 3
        assert mock_db.flush.call_count == 3
        mock_db.commit.assert_called_once()

    def test_failure_rollback(self, mock_db):
        mock_db.bulk_insert_mappings.side_effect = RuntimeError("insert fail")
        items = [{"name": "x"}]

        with pytest.raises(DatabaseError):
            BatchOperation.batch_insert(mock_db, str, items)
        mock_db.rollback.assert_called_once()


# ===================================================================
# BatchOperation.batch_update
# ===================================================================


class TestBatchUpdate:
    def test_empty_items(self, mock_db):
        result = BatchOperation.batch_update(mock_db, None, [])
        assert result == 0

    def test_single_batch(self, mock_db):
        updates = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        result = BatchOperation.batch_update(mock_db, str, updates, batch_size=1000)
        assert result == 2
        mock_db.bulk_update_mappings.assert_called_once_with(str, updates)
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_multiple_batches(self, mock_db):
        updates = [{"id": i} for i in range(5)]
        result = BatchOperation.batch_update(mock_db, dict, updates, batch_size=2)
        assert result == 5
        assert mock_db.bulk_update_mappings.call_count == 3
        assert mock_db.flush.call_count == 3
        mock_db.commit.assert_called_once()

    def test_failure_rollback(self, mock_db):
        mock_db.bulk_update_mappings.side_effect = RuntimeError("update fail")
        updates = [{"id": 1}]

        with pytest.raises(DatabaseError):
            BatchOperation.batch_update(mock_db, str, updates)
        mock_db.rollback.assert_called_once()


# ===================================================================
# BatchOperation.batch_delete
# ===================================================================


class TestBatchDelete:
    def test_empty_ids(self, mock_db):
        result = BatchOperation.batch_delete(mock_db, str, [])
        assert result == 0

    def test_single_batch(self, mock_db):
        class MockModel:
            id = MagicMock()

        MockModel.id.in_.return_value = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 3

        ids = [1, 2, 3]
        result = BatchOperation.batch_delete(mock_db, MockModel, ids, batch_size=1000)
        assert result == 3
        mock_db.query.assert_called_once_with(MockModel)
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_multiple_batches(self, mock_db):
        class MockModel:
            id = MagicMock()

        MockModel.id.in_.return_value = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.delete.return_value = 2

        ids = [1, 2, 3, 4, 5]
        result = BatchOperation.batch_delete(mock_db, MockModel, ids, batch_size=2)
        assert result == 5
        assert mock_db.query.call_count == 3
        assert mock_db.flush.call_count == 3
        mock_db.commit.assert_called_once()

    def test_failure_rollback(self, mock_db):
        class MockModel:
            id = "id_col"

        mock_db.query.side_effect = RuntimeError("delete fail")
        ids = [1]

        with pytest.raises(DatabaseError):
            BatchOperation.batch_delete(mock_db, MockModel, ids)
        mock_db.rollback.assert_called_once()


# ===================================================================
# Module-level convenience aliases
# ===================================================================


class TestConvenienceAliases:
    def test_aliases_are_bound(self):
        assert transaction is TransactionManager.transaction
        assert transactional is TransactionManager.transactional
        assert run_in_transaction is TransactionManager.run_in_transaction
        assert nested_transaction is TransactionManager.nested_transaction
        assert savepoint is TransactionManager.savepoint
