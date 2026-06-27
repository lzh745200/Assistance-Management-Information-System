"""
数据库性能优化工具测试

测试 app/utils/db_performance.py 模块
"""
import time
import pytest
from unittest.mock import MagicMock, patch
from app.utils.db_performance import (
    QueryOptimizer,
    BatchOperator,
    SimpleCache,
    cache_query,
    measure_query_time,
    query_cache,
    optimize_sqlite_connection,
)


class TestQueryOptimizer:
    def test_add_pagination(self):
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value = "paginated"
        result = QueryOptimizer.add_pagination(mock_query, page=2, page_size=10)
        mock_query.offset.assert_called_once_with(10)
        assert result == "paginated"

    def test_add_pagination_clamp_page_size(self):
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value = "paginated"
        result = QueryOptimizer.add_pagination(mock_query, page=1, page_size=200, max_page_size=100)
        mock_query.offset.return_value.limit.assert_called_once_with(100)

    def test_add_pagination_min_page(self):
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value = "paginated"
        result = QueryOptimizer.add_pagination(mock_query, page=0, page_size=20)
        mock_query.offset.assert_called_once_with(0)

    def test_optimize_eager_loading(self):
        with patch("sqlalchemy.orm.joinedload") as mock_joinedload:
            mock_query = MagicMock()
            result = QueryOptimizer.optimize_eager_loading(mock_query, ["relation1"])
            mock_joinedload.assert_called_once_with("relation1")
            mock_query.options.assert_called_once()

    def test_get_query_count(self):
        mock_query = MagicMock()
        mock_query.count.return_value = 42
        result = QueryOptimizer.get_query_count(mock_query)
        assert result == 42


class TestBatchOperator:
    def test_bulk_insert_success(self):
        mock_db = MagicMock()
        model_class = MagicMock()
        data_list = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = BatchOperator.bulk_insert(mock_db, model_class, data_list, batch_size=2)
        assert result == 3
        assert mock_db.bulk_insert_mappings.call_count == 2
        mock_db.commit.assert_called()

    def test_bulk_insert_no_commit(self):
        mock_db = MagicMock()
        result = BatchOperator.bulk_insert(mock_db, MagicMock(), [{"id": 1}], commit=False)
        assert result == 1
        mock_db.commit.assert_not_called()

    def test_bulk_insert_exception(self):
        mock_db = MagicMock()
        mock_db.bulk_insert_mappings.side_effect = Exception("Insert failed")
        with pytest.raises(Exception):
            BatchOperator.bulk_insert(mock_db, MagicMock(), [{"id": 1}])
        mock_db.rollback.assert_called_once()

    def test_bulk_update_success(self):
        mock_db = MagicMock()
        data_list = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        result = BatchOperator.bulk_update(mock_db, MagicMock(), data_list, batch_size=1)
        assert result == 2
        assert mock_db.bulk_update_mappings.call_count == 2
        mock_db.commit.assert_called()

    def test_bulk_update_no_commit(self):
        mock_db = MagicMock()
        result = BatchOperator.bulk_update(mock_db, MagicMock(), [{"id": 1}], commit=False)
        assert result == 1
        mock_db.commit.assert_not_called()

    def test_bulk_update_exception(self):
        mock_db = MagicMock()
        mock_db.bulk_update_mappings.side_effect = Exception("Update failed")
        with pytest.raises(Exception):
            BatchOperator.bulk_update(mock_db, MagicMock(), [{"id": 1}])
        mock_db.rollback.assert_called_once()


class TestSimpleCache:
    def test_get_missing(self):
        cache = SimpleCache(ttl=300)
        assert cache.get("missing") is None

    def test_set_and_get(self):
        cache = SimpleCache(ttl=300)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_expiry(self):
        cache = SimpleCache(ttl=0.1)
        cache.set("key", "value")
        time.sleep(0.15)
        assert cache.get("key") is None

    def test_delete(self):
        cache = SimpleCache(ttl=300)
        cache.set("key", "value")
        cache.delete("key")
        assert cache.get("key") is None

    def test_delete_missing(self):
        cache = SimpleCache(ttl=300)
        cache.delete("missing")  # Should not raise

    def test_clear(self):
        cache = SimpleCache(ttl=300)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


class TestCacheQueryDecorator:
    def test_cache_query_different_args(self):
        query_cache.clear()
        call_count = [0]

        @cache_query(ttl=300)
        def get_data_diff(key):
            call_count[0] += 1
            return f"result_{key}"

        result1 = get_data_diff("a")
        result2 = get_data_diff("b")
        assert result1 == "result_a"
        assert result2 == "result_b"
        assert call_count[0] == 2

    def test_cache_query_same_args(self):
        query_cache.clear()
        call_count = [0]

        @cache_query(ttl=300)
        def get_data_same(key):
            call_count[0] += 1
            return f"result_{key}"

        r1 = get_data_same("a")
        r2 = get_data_same("a")
        assert r1 == r2
        assert call_count[0] == 1


class TestMeasureQueryTime:
    def test_measure_time(self):
        call_count = [0]

        @measure_query_time
        def slow_func():
            call_count[0] += 1
            return 42

        result = slow_func()
        assert result == 42
        assert call_count[0] == 1


class TestOptimizeSqlite:
    def test_optimize(self):
        mock_db = MagicMock()
        optimize_sqlite_connection(mock_db)
        assert mock_db.execute.call_count == 5
        mock_db.commit.assert_called_once()

    def test_optimize_exception(self):
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("PRAGMA failed")
        optimize_sqlite_connection(mock_db)  # Should not raise
        mock_db.commit.assert_not_called()
