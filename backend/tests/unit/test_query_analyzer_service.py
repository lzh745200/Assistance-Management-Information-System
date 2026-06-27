"""Tests for app/services/query_analyzer_service.py — 目标 100% 覆盖。"""
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.query_analyzer_service import (
    QueryAnalyzer,
    QueryAnalyzerService,
    monitor_query_performance,
    query_analyzer,
)


class TestQueryAnalyzerInit:
    def test_default_initialization(self):
        qa = QueryAnalyzer()
        assert qa._slow_queries == []
        assert qa._max_slow_queries == 1000
        assert qa._n_plus_one_cache == {}

    def test_global_instance(self):
        assert isinstance(query_analyzer, QueryAnalyzer)

    def test_alias(self):
        assert QueryAnalyzerService is QueryAnalyzer


class TestLogSlowQuery:
    def test_basic_logging(self):
        qa = QueryAnalyzer()
        qa.log_slow_query("SELECT 1", 150.5, params={"x": 1})
        assert len(qa._slow_queries) == 1
        assert qa._slow_queries[0]["duration_ms"] == 150.5
        assert qa._slow_queries[0]["params"] == {"x": 1}

    def test_query_truncated_to_500(self):
        qa = QueryAnalyzer()
        long_q = "X" * 1000
        qa.log_slow_query(long_q, 100.0)
        assert len(qa._slow_queries[0]["query"]) == 500

    def test_list_size_limited(self):
        qa = QueryAnalyzer()
        qa._max_slow_queries = 5
        for i in range(10):
            qa.log_slow_query(f"query_{i}", float(i))
        assert len(qa._slow_queries) == 5
        assert qa._slow_queries[-1]["query"] == "query_9"

    def test_with_explain_plan(self):
        qa = QueryAnalyzer()
        qa.log_slow_query("SELECT 1", 50.0, explain_plan="SCAN TABLE")
        assert qa._slow_queries[0]["explain_plan"] == "SCAN TABLE"


class TestGetSlowQueries:
    def test_all_queries_returned(self):
        qa = QueryAnalyzer()
        for i in range(5):
            qa.log_slow_query(f"q{i}", float(i * 10))
        result = qa.get_slow_queries()
        assert len(result) == 5

    def test_filter_by_min_duration(self):
        qa = QueryAnalyzer()
        for i in range(5):
            qa.log_slow_query(f"q{i}", float(i * 10))
        result = qa.get_slow_queries(min_duration_ms=20.0)
        assert len(result) == 3  # 20, 30, 40

    def test_limit_parameter(self):
        qa = QueryAnalyzer()
        for i in range(10):
            qa.log_slow_query(f"q{i}", float(i))
        result = qa.get_slow_queries(limit=3)
        assert len(result) == 3

    def test_sorted_by_timestamp_desc(self):
        import datetime as dt_mod
        qa = QueryAnalyzer()
        with patch("app.services.query_analyzer_service.datetime") as mock_dt:
            mock_dt.now.side_effect = [
                dt_mod.datetime(2025, 1, 1),
                dt_mod.datetime(2025, 1, 2),
            ]
            mock_dt.side_effect = dt_mod.datetime
            qa.log_slow_query("second", 20.0)
            qa.log_slow_query("first", 10.0)
        result = qa.get_slow_queries()
        assert result[0]["query"] == "first"


class TestGetQueryStats:
    def test_empty_returns_zeros(self):
        qa = QueryAnalyzer()
        stats = qa.get_query_stats()
        assert stats["total_slow_queries"] == 0
        assert stats["avg_duration_ms"] == 0

    def test_with_data(self):
        qa = QueryAnalyzer()
        qa.log_slow_query("q1", 100.0)
        qa.log_slow_query("q2", 200.0)
        qa.log_slow_query("q3", 300.0)
        stats = qa.get_query_stats()
        assert stats["total_slow_queries"] == 3
        assert stats["avg_duration_ms"] == 200.0
        assert stats["max_duration_ms"] == 300.0
        assert stats["min_duration_ms"] == 100.0
        assert stats["p50_duration_ms"] == 200.0
        assert stats["p95_duration_ms"] == 300.0
        assert stats["p99_duration_ms"] == 300.0

    def test_single_query(self):
        qa = QueryAnalyzer()
        qa.log_slow_query("q1", 50.0)
        stats = qa.get_query_stats()
        assert stats["p50_duration_ms"] == 50.0
        assert stats["p95_duration_ms"] == 50.0
        assert stats["p99_duration_ms"] == 50.0


class TestCalculatePercentile:
    def test_empty_list(self):
        qa = QueryAnalyzer()
        assert qa._calculate_percentile([], 50) == 0.0

    def test_exact_percentile(self):
        qa = QueryAnalyzer()
        # int(4 * 50 / 100) = 2, sorted_values[2] = 3
        assert qa._calculate_percentile([1, 2, 3, 4], 50) == 3.0

    def test_rounding(self):
        qa = QueryAnalyzer()
        # int(2 * 50 / 100) = 1, sorted_values[1] = 2.345, round(2.345, 2) = 2.35
        result = qa._calculate_percentile([1.234, 2.345], 50)
        assert result == 2.35


class TestDetectNPlusOne:
    def test_first_query_added_to_cache(self):
        qa = QueryAnalyzer()
        qa.detect_n_plus_one("SELECT * FROM users WHERE id = 1")
        assert len(qa._n_plus_one_cache) == 2  # timestamp + count

    def test_under_threshold_no_warning(self):
        qa = QueryAnalyzer()
        for _ in range(5):
            qa.detect_n_plus_one("SELECT * FROM users WHERE id = 1")
        assert qa._n_plus_one_cache.get(":SELECT * FROM users WHERE id = ?_count", 0) == 5

    def test_over_threshold_triggers_warning(self):
        qa = QueryAnalyzer()
        with patch("app.services.query_analyzer_service.logger.warning") as mock_warn:
            for _ in range(8):
                qa.detect_n_plus_one("SELECT * FROM users WHERE id = 1")
            # 第 6 次开始触发警告（count=6,7,8），至少 1 次
            assert mock_warn.call_count >= 1

    def test_expired_keys_cleaned(self):
        qa = QueryAnalyzer()
        with patch("app.services.query_analyzer_service.time.time", return_value=100.0):
            qa.detect_n_plus_one("SELECT 1")
        assert len(qa._n_plus_one_cache) == 2
        with patch("app.services.query_analyzer_service.time.time", return_value=102.0):
            qa.detect_n_plus_one("SELECT 2")
        # expired key from 100.0 should be removed (current_time=102.0, stored at 100.0, diff=2.0 > 1.0)
        assert len(qa._n_plus_one_cache) == 2  # only new entry


class TestGetQuerySignature:
    def test_removes_numbers(self):
        qa = QueryAnalyzer()
        sig = qa._get_query_signature("SELECT * FROM t WHERE id = 123")
        assert "?" in sig
        assert "123" not in sig

    def test_removes_single_quoted_strings(self):
        qa = QueryAnalyzer()
        sig = qa._get_query_signature("SELECT * FROM t WHERE name = 'hello'")
        assert "'?'" in sig

    def test_removes_double_quoted_strings(self):
        qa = QueryAnalyzer()
        sig = qa._get_query_signature('SELECT * FROM t WHERE name = "hello"')
        assert '"?"' in sig

    def test_truncated_to_200(self):
        qa = QueryAnalyzer()
        long_q = "X" * 300
        sig = qa._get_query_signature(long_q)
        assert len(sig) == 200


class TestAnalyzeQueryPlan:
    def test_success(self):
        qa = QueryAnalyzer()
        db = MagicMock()
        mock_result = [("SCAN TABLE users",), ("USE INDEX idx_id",)]
        db.execute.return_value = mock_result
        plan = qa.analyze_query_plan(db, "SELECT * FROM users")
        assert "SCAN TABLE users" in plan
        assert "USE INDEX idx_id" in plan
        db.execute.assert_called_once()

    def test_exception_returns_none(self):
        qa = QueryAnalyzer()
        db = MagicMock()
        db.execute.side_effect = Exception("explain error")
        plan = qa.analyze_query_plan(db, "SELECT 1")
        assert plan is None


class TestClearSlowQueries:
    def test_clears_list(self):
        qa = QueryAnalyzer()
        qa.log_slow_query("test", 100.0)
        assert len(qa._slow_queries) == 1
        qa.clear_slow_queries()
        assert len(qa._slow_queries) == 0


class TestMonitorQueryPerformance:
    def test_below_threshold_no_logging(self):
        qa = QueryAnalyzer()
        with patch("app.services.query_analyzer_service.query_analyzer", qa):
            @monitor_query_performance(threshold_ms=1000.0)
            def fast_func():
                return 42

            assert fast_func() == 42
            assert len(qa._slow_queries) == 0

    def test_above_threshold_logs_slow_query(self):
        qa = QueryAnalyzer()
        with patch("app.services.query_analyzer_service.query_analyzer", qa):
            @monitor_query_performance(threshold_ms=1.0)
            def slow_func():
                time.sleep(0.01)
                return 99

            assert slow_func() == 99
            assert len(qa._slow_queries) == 1
            assert qa._slow_queries[0]["query"] == "slow_func"
