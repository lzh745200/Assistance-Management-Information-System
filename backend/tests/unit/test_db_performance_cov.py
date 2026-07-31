"""Coverage tests for app.utils.db_performance module."""

import pytest
import time
from unittest.mock import MagicMock, patch, call


class TestQueryOptimizer:
    """Tests for QueryOptimizer class."""

    def test_add_pagination(self):
        from app.utils.db_performance import QueryOptimizer
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value = mock_query

        result = QueryOptimizer.add_pagination(mock_query, page=2, page_size=10)
        mock_query.offset.assert_called_once_with(10)
        mock_query.offset.return_value.limit.assert_called_once_with(10)

    def test_add_pagination_caps_page_size(self):
        from app.utils.db_performance import QueryOptimizer
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value = mock_query

        QueryOptimizer.add_pagination(mock_query, page=1, page_size=200, max_page_size=100)
        # page_size should be capped to max_page_size
        mock_query.offset.return_value.limit.assert_called_once_with(100)

    def test_add_pagination_negative_page(self):
        from app.utils.db_performance import QueryOptimizer
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value = mock_query

        QueryOptimizer.add_pagination(mock_query, page=-1, page_size=10)
        # page should be at least 1
        mock_query.offset.assert_called_once_with(0)

    def test_optimize_eager_loading(self):
        from app.utils.db_performance import QueryOptimizer
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query

        with patch("sqlalchemy.orm.joinedload") as mock_joinedload:
            mock_joinedload.return_value = mock_joinedload

            result = QueryOptimizer.optimize_eager_loading(mock_query, ["rel1", "rel2"])

        assert mock_joinedload.call_args_list == [call("rel1"), call("rel2")]
        assert mock_query.options.call_count == 2
        assert result is mock_query

    def test_optimize_eager_loading_empty(self):
        from app.utils.db_performance import QueryOptimizer
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query

        result = QueryOptimizer.optimize_eager_loading(mock_query, [])

        assert result is mock_query
        mock_query.options.assert_not_called()

    def test_get_query_count(self):
        from app.utils.db_performance import QueryOptimizer
        mock_query = MagicMock()
        mock_query.count.return_value = 42

        result = QueryOptimizer.get_query_count(mock_query)
        assert result == 42


class TestBatchOperator:
    """Tests for BatchOperator class."""

    def test_bulk_insert_success(self):
        from app.utils.db_performance import BatchOperator
        mock_db = MagicMock()
        data = [{"name": f"item{i}"} for i in range(5)]

        with patch("app.utils.db_performance.safe_commit") as mock_commit:
            mock_commit.return_value = True
            result = BatchOperator.bulk_insert(mock_db, MagicMock(), data, batch_size=2)

        assert result == 5
        assert mock_db.bulk_insert_mappings.call_count == 3  # 2+2+1

    def test_bulk_insert_no_commit(self):
        from app.utils.db_performance import BatchOperator
        mock_db = MagicMock()
        data = [{"name": "item1"}]

        result = BatchOperator.bulk_insert(mock_db, MagicMock(), data, commit=False)
        assert result == 1
        mock_db.bulk_insert_mappings.assert_called_once()

    def test_bulk_insert_error(self):
        from app.utils.db_performance import BatchOperator
        mock_db = MagicMock()
        mock_db.bulk_insert_mappings.side_effect = RuntimeError("insert error")

        with pytest.raises(RuntimeError):
            BatchOperator.bulk_insert(mock_db, MagicMock(), [{"name": "test"}])

    def test_bulk_update_success(self):
        from app.utils.db_performance import BatchOperator
        mock_db = MagicMock()
        data = [{"id": i, "name": f"updated{i}"} for i in range(3)]

        with patch("app.utils.db_performance.safe_commit") as mock_commit:
            mock_commit.return_value = True
            result = BatchOperator.bulk_update(mock_db, MagicMock(), data, batch_size=2)

        assert result == 3

    def test_bulk_update_no_commit(self):
        from app.utils.db_performance import BatchOperator
        mock_db = MagicMock()
        data = [{"id": 1, "name": "updated"}]

        result = BatchOperator.bulk_update(mock_db, MagicMock(), data, commit=False)
        assert result == 1

    def test_bulk_update_error(self):
        from app.utils.db_performance import BatchOperator
        mock_db = MagicMock()
        mock_db.bulk_update_mappings.side_effect = RuntimeError("update error")

        with pytest.raises(RuntimeError):
            BatchOperator.bulk_update(mock_db, MagicMock(), [{"id": 1, "name": "test"}])


class TestSimpleCache:
    """Tests for SimpleCache class."""

    def test_cache_get_set(self):
        from app.utils.db_performance import SimpleCache
        cache = SimpleCache(ttl=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_get_missing(self):
        from app.utils.db_performance import SimpleCache
        cache = SimpleCache(ttl=10)
        assert cache.get("missing") is None

    def test_cache_expired(self):
        from app.utils.db_performance import SimpleCache
        cache = SimpleCache(ttl=0)
        cache.set("key1", "value1")
        # TTL=0 means immediately expired
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_cache_delete(self):
        from app.utils.db_performance import SimpleCache
        cache = SimpleCache(ttl=10)
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_cache_delete_missing(self):
        from app.utils.db_performance import SimpleCache
        cache = SimpleCache(ttl=10)
        cache.delete("nonexistent")  # Should not raise

    def test_cache_clear(self):
        from app.utils.db_performance import SimpleCache
        cache = SimpleCache(ttl=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestCacheQueryDecorator:
    """Tests for cache_query decorator."""

    def test_cache_query_first_call(self):
        from app.utils.db_performance import cache_query, query_cache

        query_cache.clear()
        call_count = 0

        @cache_query(ttl=300)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

    def test_cache_query_cached_call(self):
        from app.utils.db_performance import cache_query, query_cache

        query_cache.clear()
        call_count = 0

        @cache_query(ttl=300)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = test_func(5)
        result2 = test_func(5)  # Should be cached
        assert result1 == result2 == 10
        assert call_count == 1  # Only called once

    def test_cache_query_different_args(self):
        from app.utils.db_performance import cache_query, query_cache

        query_cache.clear()
        call_count = 0

        @cache_query(ttl=300)
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        test_func(5)
        test_func(10)  # Different args, should not be cached
        assert call_count == 2


class TestMeasureQueryTime:
    """Tests for measure_query_time decorator."""

    def test_measure_query_time(self):
        from app.utils.db_performance import measure_query_time

        @measure_query_time
        def test_func(x):
            return x * 2

        result = test_func(5)
        assert result == 10


class TestOptimizeSqliteConnection:
    """Tests for optimize_sqlite_connection function."""

    def test_optimize_sqlite_connection_success(self):
        from app.utils.db_performance import optimize_sqlite_connection

        mock_db = MagicMock()
        with patch("app.utils.db_performance.safe_commit") as mock_commit:
            mock_commit.return_value = True
            optimize_sqlite_connection(mock_db)

        # Should execute 5 PRAGMA statements
        assert mock_db.execute.call_count == 5

    def test_optimize_sqlite_connection_error(self):
        from app.utils.db_performance import optimize_sqlite_connection

        mock_db = MagicMock()
        mock_db.execute.side_effect = RuntimeError("db error")

        # Should not raise
        optimize_sqlite_connection(mock_db)
