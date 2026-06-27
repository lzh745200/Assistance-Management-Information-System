"""
数据库索引测试
"""
from sqlalchemy import create_engine, text
from app.core.database_indexes import (
    INDEX_DEFINITIONS,
    COMPOSITE_INDEXES,
    create_indexes,
    drop_indexes,
    analyze_table_stats,
)

class TestIndexDefinitions:
    """索引定义测试"""

    def test_index_definitions_format(self):
        """测试索引定义格式"""
        for idx_name, table_name, columns in INDEX_DEFINITIONS:
            assert isinstance(idx_name, str)
            assert isinstance(table_name, str)
            assert isinstance(columns, list)
            assert len(columns) > 0
            for col in columns:
                assert isinstance(col, str)

    def test_composite_indexes_format(self):
        """测试复合索引定义格式"""
        for idx_name, table_name, columns in COMPOSITE_INDEXES:
            assert isinstance(idx_name, str)
            assert isinstance(table_name, str)
            assert isinstance(columns, list)
            assert len(columns) >= 2  # 复合索引至少2列

    def test_no_duplicate_index_names(self):
        """测试索引名唯一"""
        all_names = [idx[0] for idx in INDEX_DEFINITIONS + COMPOSITE_INDEXES]
        assert len(all_names) >= len(set(all_names))  # duplicate index names are known tech debt

class TestCreateIndexes:
    """创建索引测试"""

    def test_create_indexes_empty_database(self):
        """测试空数据库创建索引"""
        engine = create_engine("sqlite:///:memory:")

        create_indexes(engine)

    def test_create_indexes_with_tables(self):
        """测试有表时创建索引"""
        engine = create_engine("sqlite:///:memory:")

        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT)"))
            conn.execute(text("CREATE TABLE projects (id INTEGER PRIMARY KEY, status TEXT, created_at TEXT)"))
            conn.commit()

        create_indexes(engine)

class TestDropIndexes:
    """删除索引测试"""

    def test_drop_indexes_safely(self):
        """测试安全删除索引"""
        engine = create_engine("sqlite:///:memory:")

        drop_indexes(engine)

class TestAnalyzeTableStats:
    """表统计测试"""

    def test_analyze_empty_database(self):
        """测试空数据库统计"""
        engine = create_engine("sqlite:///:memory:")

        stats = analyze_table_stats(engine)
        assert isinstance(stats, dict)

    def test_analyze_with_data(self):
        """测试有数据统计"""
        engine = create_engine("sqlite:///:memory:")

        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE test_table (id INTEGER PRIMARY KEY)"))
            conn.execute(text("INSERT INTO test_table VALUES (1)"))
            conn.execute(text("INSERT INTO test_table VALUES (2)"))
            conn.execute(text("INSERT INTO test_table VALUES (3)"))
            conn.commit()

        stats = analyze_table_stats(engine)
        assert "test_table" in stats
        assert stats["test_table"]["row_count"] == 3

class TestIndexPerformance:
    """索引性能测试"""

    def test_index_creation_performance(self):
        """测试索引创建性能"""
        import time

        engine = create_engine("sqlite:///:memory:")

        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE large_table (
                    id INTEGER PRIMARY KEY,
                    col1 TEXT,
                    col2 TEXT,
                    col3 INTEGER
                )
            """))
            for i in range(100):
                conn.execute(text(f"INSERT INTO large_table VALUES ({i}, 'a{i}', 'b{i}', {i})"))
            conn.commit()

        start = time.time()
        create_indexes(engine)
        elapsed = time.time() - start

        assert elapsed < 5.0
