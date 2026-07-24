"""app.utils.query_optimizer 覆盖率攻坚测试

模块现状：原有 test_query_optimizer*.py 针对的是 app.core.query_optimizer，
本文件补齐 app.utils.query_optimizer（索引管理/维护工具）的全部分支。

覆盖点：
- analyze_slow_queries 正常/异常
- create_indexes 新建/已存在/非法表名/非法索引名/非法列名/单条失败/提交失败
- optimize_query_cache / vacuum_database / analyze_tables 正常+异常
- get_index_stats 正常/异常
- check_missing_indexes 缺失/已存在/表不存在/描述缺省/异常
- get_table_sizes 正常/非法表名/计数失败/整体异常
- optimize_specific_table 非法表名/正常/异常
- get_optimization_report 两类建议的有无组合
- optimize_database 全流程编排
"""

from unittest.mock import MagicMock, patch

import app.utils.query_optimizer as qo
from app.utils.query_optimizer import QueryOptimizer, optimize_database


def _sess():
    sess = MagicMock()
    sess.close = MagicMock()
    return sess


def _exec_result(rows):
    """构造可迭代的结果集 mock（行按 tuple 取下标）"""
    result = MagicMock()
    result.__iter__ = lambda self: iter(rows)
    return result


# ==================== analyze_slow_queries ====================


class TestAnalyzeSlowQueries:
    def test_returns_empty_list(self):
        assert QueryOptimizer.analyze_slow_queries(MagicMock()) == []

    def test_exception_returns_empty(self):
        with patch.object(qo.logger, "info", side_effect=Exception("x")):
            assert QueryOptimizer.analyze_slow_queries(MagicMock()) == []


# ==================== create_indexes ====================


class TestCreateIndexes:
    def test_create_all_new_indexes(self):
        sess = _sess()
        sess.execute.return_value.fetchone.return_value = None  # 索引不存在 → 创建
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.create_indexes()
        # 每个推荐索引两次 execute（检查+创建）
        assert sess.execute.call_count == len(QueryOptimizer.RECOMMENDED_INDEXES) * 2
        sess.commit.assert_called_once()
        sess.close.assert_called_once()

    def test_all_indexes_exist(self):
        sess = _sess()
        sess.execute.return_value.fetchone.return_value = ("idx_x",)  # 已存在 → 跳过创建
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.create_indexes()
        # 仅检查调用，无创建
        assert sess.execute.call_count == len(QueryOptimizer.RECOMMENDED_INDEXES)
        sess.commit.assert_called_once()

    def test_unsafe_names_and_inner_error(self, monkeypatch):
        """非法表名/索引名/列名跳过 + 单条创建失败仅告警"""
        monkeypatch.setattr(QueryOptimizer, "RECOMMENDED_INDEXES", [
            {"table": "bad;table", "columns": ["a"], "name": "idx_a"},      # 表名非法
            {"table": "t1", "columns": ["a"], "name": "bad;idx"},           # 索引名非法
            {"table": "t1", "columns": ["bad;col", "ok"], "name": "idx_b"},  # 列名非法（告警后继续）
            {"table": "t1", "columns": ["a"], "name": "idx_err"},           # 创建时抛异常
            {"table": "t1", "columns": ["a"], "name": "idx_ok"},            # 正常创建
        ])

        def _exec(stmt, params=None):
            sql = str(stmt)
            if "CREATE INDEX" in sql and "idx_err" in sql:
                raise Exception("create boom")
            m = MagicMock()
            m.fetchone.return_value = None
            return m

        sess = _sess()
        sess.execute.side_effect = _exec
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.create_indexes()  # 不向外抛
        sess.commit.assert_called_once()
        sess.close.assert_called_once()

    def test_commit_failure_rolls_back(self):
        sess = _sess()
        sess.execute.return_value.fetchone.return_value = None
        sess.commit.side_effect = Exception("commit boom")
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.create_indexes()  # 外层 except：rollback + error
        sess.rollback.assert_called_once()
        sess.close.assert_called_once()


# ==================== 维护类方法 ====================


class TestMaintenance:
    def test_optimize_query_cache_success(self):
        sess = _sess()
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.optimize_query_cache()
        assert sess.execute.call_count == 4  # 四条 PRAGMA
        sess.commit.assert_called_once()
        sess.close.assert_called_once()

    def test_optimize_query_cache_exception(self):
        sess = _sess()
        sess.execute.side_effect = Exception("x")
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.optimize_query_cache()  # 异常被吞
        sess.close.assert_called_once()

    def test_vacuum_success(self):
        sess = _sess()
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.vacuum_database()
        sess.commit.assert_called_once()
        sess.close.assert_called_once()

    def test_vacuum_exception(self):
        sess = _sess()
        sess.execute.side_effect = Exception("x")
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.vacuum_database()
        sess.close.assert_called_once()

    def test_analyze_tables_success(self):
        sess = _sess()
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.analyze_tables()
        sess.commit.assert_called_once()
        sess.close.assert_called_once()

    def test_analyze_tables_exception(self):
        sess = _sess()
        sess.execute.side_effect = Exception("x")
        with patch.object(qo, "SessionLocal", return_value=sess):
            QueryOptimizer.analyze_tables()
        sess.close.assert_called_once()


# ==================== get_index_stats ====================


class TestGetIndexStats:
    def test_returns_index_dicts(self):
        db = MagicMock()
        db.execute.return_value = _exec_result([
            ("idx_a", "users", "CREATE INDEX idx_a ON users (a)"),
            ("idx_b", "funds", "CREATE INDEX idx_b ON funds (b)"),
        ])
        stats = QueryOptimizer.get_index_stats(db)
        assert stats == [
            {"index_name": "idx_a", "table_name": "users", "definition": "CREATE INDEX idx_a ON users (a)"},
            {"index_name": "idx_b", "table_name": "funds", "definition": "CREATE INDEX idx_b ON funds (b)"},
        ]

    def test_exception_returns_empty(self):
        db = MagicMock()
        db.execute.side_effect = Exception("x")
        assert QueryOptimizer.get_index_stats(db) == []


# ==================== check_missing_indexes ====================


class TestCheckMissingIndexes:
    def _patch_session(self, monkeypatch, existing_indexes, existing_tables, configs):
        monkeypatch.setattr(QueryOptimizer, "RECOMMENDED_INDEXES", configs)
        sess = _sess()
        sess.execute.side_effect = [
            _exec_result([(n,) for n in existing_indexes]),
            _exec_result([(t,) for t in existing_tables]),
        ]
        return patch.object(qo, "SessionLocal", return_value=sess)

    def test_missing_present_and_ghost_table(self, monkeypatch):
        configs = [
            {"table": "t_exist", "columns": ["a"], "name": "idx_missing", "description": "d1"},
            {"table": "t_exist", "columns": ["a"], "name": "idx_present"},     # 已存在 → 跳过
            {"table": "t_ghost", "columns": ["a"], "name": "idx_ghost"},       # 表不存在 → 跳过
            {"table": "t_exist", "columns": ["b"], "name": "idx_missing2"},    # 无描述 → 缺省 ""
        ]
        with self._patch_session(monkeypatch, {"idx_present"}, {"t_exist"}, configs) as p:
            p.start()
            missing = QueryOptimizer.check_missing_indexes()
            p.stop()
        assert missing == [
            {"table": "t_exist", "index_name": "idx_missing", "columns": ["a"], "description": "d1"},
            {"table": "t_exist", "index_name": "idx_missing2", "columns": ["b"], "description": ""},
        ]

    def test_exception_returns_empty(self):
        sess = _sess()
        sess.execute.side_effect = Exception("x")
        with patch.object(qo, "SessionLocal", return_value=sess):
            assert QueryOptimizer.check_missing_indexes() == []
        sess.close.assert_called_once()


# ==================== get_table_sizes ====================


class TestGetTableSizes:
    def test_mixed_tables(self):
        def _exec(stmt, params=None):
            sql = str(stmt)
            if "sqlite_master" in sql:
                return _exec_result([
                    ("good_table", 5),
                    ("bad;name", 3),       # 非法表名 → 告警跳过
                    ("err_table", 2),      # 计数失败 → row_count=0
                ])
            if "err_table" in sql:
                raise Exception("no table")
            m = MagicMock()
            m.scalar.return_value = 100
            return m

        sess = _sess()
        sess.execute.side_effect = _exec
        with patch.object(qo, "SessionLocal", return_value=sess):
            tables = QueryOptimizer.get_table_sizes()
        assert tables == [
            {"table_name": "good_table", "column_count": 5, "row_count": 100},
            {"table_name": "err_table", "column_count": 2, "row_count": 0},
        ]
        sess.close.assert_called_once()

    def test_exception_returns_empty(self):
        sess = _sess()
        sess.execute.side_effect = Exception("x")
        with patch.object(qo, "SessionLocal", return_value=sess):
            assert QueryOptimizer.get_table_sizes() == []
        sess.close.assert_called_once()


# ==================== optimize_specific_table ====================


class TestOptimizeSpecificTable:
    def test_invalid_table_name(self):
        assert QueryOptimizer.optimize_specific_table("bad;name") is False

    def test_success(self):
        sess = _sess()
        with patch.object(qo, "SessionLocal", return_value=sess):
            assert QueryOptimizer.optimize_specific_table("users") is True
        sess.commit.assert_called_once()
        sess.close.assert_called_once()

    def test_exception_returns_false(self):
        sess = _sess()
        sess.execute.side_effect = Exception("x")
        with patch.object(qo, "SessionLocal", return_value=sess):
            assert QueryOptimizer.optimize_specific_table("users") is False
        sess.close.assert_called_once()


# ==================== get_optimization_report ====================


class TestOptimizationReport:
    def test_with_missing_indexes_and_large_tables(self):
        with patch.object(QueryOptimizer, "check_missing_indexes", return_value=[{"i": 1}]), patch.object(
            QueryOptimizer, "get_table_sizes",
            return_value=[
                {"table_name": "big", "row_count": 20000},
                {"table_name": "small", "row_count": 1},
            ],
        ):
            report = QueryOptimizer.get_optimization_report()
        assert report["missing_indexes"] == [{"i": 1}]
        assert len(report["recommendations"]) == 2
        assert report["recommendations"][0]["type"] == "index"
        assert report["recommendations"][1]["type"] == "performance"
        assert report["recommendations"][1]["tables"] == ["big"]
        assert "generated_at" in report

    def test_no_recommendations(self):
        with patch.object(QueryOptimizer, "check_missing_indexes", return_value=[]), patch.object(
            QueryOptimizer, "get_table_sizes", return_value=[{"table_name": "t", "row_count": 10}]
        ):
            report = QueryOptimizer.get_optimization_report()
        assert report["recommendations"] == []


# ==================== optimize_database 编排 ====================


class TestOptimizeDatabase:
    def test_full_flow_calls_all_steps(self):
        with patch.object(QueryOptimizer, "create_indexes") as m1, patch.object(
            QueryOptimizer, "optimize_query_cache"
        ) as m2, patch.object(QueryOptimizer, "analyze_tables") as m3, patch.object(
            QueryOptimizer, "vacuum_database"
        ) as m4:
            optimize_database()
        m1.assert_called_once()
        m2.assert_called_once()
        m3.assert_called_once()
        m4.assert_called_once()
