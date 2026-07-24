"""app.core.database_indexes 覆盖率攻坚测试

覆盖点：
- create_indexes：engine None / 成功创建 / 表缺失跳过 / 列缺失告警 / 执行异常
- drop_indexes：engine None / 成功 / 执行异常
- analyze_table_stats：engine None / 全路径 / 单表计数异常 / ANALYZE 异常
"""

from unittest.mock import MagicMock

from sqlalchemy import create_engine, text

import app.core.database_indexes as di


def _engine():
    return create_engine("sqlite:///:memory:")


class TestCreateIndexes:
    def test_engine_none(self):
        assert di.create_indexes(None) is None

    def test_full_branches(self, monkeypatch):
        engine = _engine()
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE t1 (c1 INTEGER)"))
            monkeypatch.setattr(di, "EXTRA_INDEXES", [
                ("t1", "ix_t1_c1", ["c1"]),            # 成功创建
                ("missing_table", "ix_x", ["c1"]),     # 表不存在 → 跳过
                ("t1", "ix_bad_col", ["nope"]),        # 列不存在 → 告警
                ("t1", "ix bad name", ["c1"]),         # SQL 语法错 → 执行异常
            ])
            di.create_indexes(engine)
        # 幂等：再次执行不报错
        di.create_indexes(engine)

    def test_validate_columns_table_missing(self):
        engine = _engine()
        assert di._validate_columns(engine, "no_table", "ix", ["c1"]) is None
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE t2 (a INTEGER)"))
        assert di._validate_columns(engine, "t2", "ix", ["a", "b"]) == ["b"]


class TestDropIndexes:
    def test_engine_none(self):
        assert di.drop_indexes(None) is None

    def test_full_branches(self, monkeypatch):
        engine = _engine()
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE t1 (c1 INTEGER)"))
            monkeypatch.setattr(di, "EXTRA_INDEXES", [
                ("t1", "ix_t1_c1", ["c1"]),
                ("t1", "ix bad name", ["c1"]),  # 执行异常
            ])
            di.create_indexes(engine)
            di.drop_indexes(engine)


class TestAnalyzeTableStats:
    def test_engine_none(self):
        assert di.analyze_table_stats(None) == {}

    def test_full_path_with_count_error(self):
        engine = _engine()
        with engine.connect() as conn:
            conn.execute(text('CREATE TABLE normal_t (c1 INTEGER)'))
            conn.execute(text('INSERT INTO normal_t VALUES (1)'))
            # 表名含 ] 使 [table] 计数查询语法错误 → row_count=0 降级
            conn.execute(text('CREATE TABLE "x]y" (c1 INTEGER)'))
            conn.commit()
        stats = di.analyze_table_stats(engine)
        assert stats["normal_t"]["row_count"] == 1
        assert stats["x]y"]["row_count"] == 0

    def test_analyze_exception(self):
        engine = MagicMock()
        conn = engine.connect.return_value.__enter__.return_value
        conn.execute.side_effect = RuntimeError("analyze boom")
        assert di.analyze_table_stats(engine) == {}
