import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, Date, DateTime


@pytest.fixture(autouse=True)
def clear_env():
    import os
    os.environ.pop("DISABLE_AUTO_MIGRATION", None)
    yield


# =========== _sqlite_col_spec ===========

class TestSqliteColSpec:
    def test_int_type(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", Integer, default=0)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "INTEGER"
        assert default_clause == "DEFAULT 0"

    def test_bool_type(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", Boolean, default=True)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "INTEGER"
        assert default_clause == "DEFAULT 1"

    def test_float_type(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", Float, default=3.14)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "REAL"
        assert default_clause == "DEFAULT 3.14"

    def test_numeric_type(self):
        from app.core.migration_helper import _sqlite_col_spec
        from sqlalchemy import Numeric
        col = Column("test", Numeric, default=42)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "REAL"
        assert default_clause == "DEFAULT 42"

    def test_text_type(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", String, default="hello")
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == "DEFAULT 'hello'"

    def test_text_type_with_single_quote(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", String, default="it's")
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == "DEFAULT 'it''s'"

    def test_date_type_default_none(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", Date)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == ""

    def test_datetime_type_default_none(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", DateTime)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == ""

    def test_server_default_skipped(self):
        from app.core.migration_helper import _sqlite_col_spec
        from sqlalchemy import func
        col = Column("test", DateTime, server_default=func.now())
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == ""

    def test_not_nullable_int_no_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", Integer, nullable=False)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "INTEGER"
        assert default_clause == "DEFAULT 0"

    def test_not_nullable_real_no_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", Float, nullable=False)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "REAL"
        assert default_clause == "DEFAULT 0"

    def test_not_nullable_text_no_default(self):
        from app.core.migration_helper import _sqlite_col_spec
        col = Column("test", String, nullable=False)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == "DEFAULT ''"

    def test_callable_default_skipped(self):
        from app.core.migration_helper import _sqlite_col_spec
        import uuid
        col = Column("test", String, default=lambda: uuid.uuid4().hex)
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == ""

    def test_configurable_enum_fallback(self):
        from app.core.migration_helper import _sqlite_col_spec
        from sqlalchemy import Enum
        col = Column("test", Enum("a", "b"), default="a")
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "TEXT"
        assert default_clause == "DEFAULT 'a'"

    def test_non_standard_default_type_falls_through(self):
        from app.core.migration_helper import _sqlite_col_spec
        from decimal import Decimal
        col = Column("test", Integer, default=Decimal("42"))
        stype, default_clause = _sqlite_col_spec(col)
        assert stype == "INTEGER"
        assert default_clause == ""


# =========== migrate_missing_columns ===========

class TestMigrateMissingColumns:
    def test_disabled_by_env(self):
        import os
        os.environ["DISABLE_AUTO_MIGRATION"] = "1"
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        model_base = Mock()
        result = migrate_missing_columns(engine, model_base)
        assert result is None

    def test_inspector_creation_failure(self):
        from app.core.migration_helper import migrate_missing_columns
        from sqlalchemy import inspect as sa_inspect
        with patch("app.core.migration_helper.sa_inspect", side_effect=Exception("no engine")):
            engine = Mock()
            model_base = Mock()
            result = migrate_missing_columns(engine, model_base)
            assert result is None

    def test_table_not_in_db_skipped(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        inspector = Mock()
        inspector.has_table.return_value = False
        model_base = Mock()
        table_mock = Mock()
        table_mock.name = "missing_table"
        model_base.metadata.tables = {"missing_table": table_mock}
        with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
            with patch.object(engine, "connect") as mock_connect:
                result = migrate_missing_columns(engine, model_base)
                assert result is None
                mock_connect.assert_not_called()

    def test_no_missing_columns(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        inspector = Mock()
        inspector.has_table.return_value = True
        inspector.get_columns.return_value = [{"name": "id"}, {"name": "name"}]
        model_base = Mock()
        col_id = Mock()
        col_id.name = "id"
        col_name = Mock()
        col_name.name = "name"
        table_mock = Mock()
        table_mock.name = "test_table"
        table_mock.columns = [col_id, col_name]
        model_base.metadata.tables = {"test_table": table_mock}
        with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
            with patch.object(engine, "connect") as mock_connect:
                result = migrate_missing_columns(engine, model_base)
                assert result is None
                mock_connect.assert_not_called()

    def test_adds_missing_column_with_default(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        conn = Mock()
        cm = MagicMock()
        cm.__enter__.return_value = conn
        engine.connect.return_value = cm
        inspector = Mock()
        inspector.has_table.return_value = True
        inspector.get_columns.return_value = [{"name": "id"}]
        model_base = Mock()
        col_name = Column("name", String, default="test")
        table_mock = Mock()
        table_mock.name = "test_table"
        table_mock.c = {"name": col_name}
        col_id_mock = MagicMock()
        col_id_mock.name = "id"
        table_mock.columns = [col_id_mock, col_name]
        model_base.metadata.tables = {"test_table": table_mock}
        with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
            result = migrate_missing_columns(engine, model_base)
            assert conn.execute.called

    def test_adds_not_nullable_column(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        conn = Mock()
        cm = MagicMock()
        cm.__enter__.return_value = conn
        engine.connect.return_value = cm
        inspector = Mock()
        inspector.has_table.return_value = True
        inspector.get_columns.return_value = [{"name": "id"}]
        model_base = Mock()
        col_name = Column("name", String, nullable=False)
        col_name.default = None
        col_name.server_default = None
        table_mock = Mock()
        table_mock.name = "test_table"
        table_mock.c = {"name": col_name}
        col_id_mock = MagicMock()
        col_id_mock.name = "id"
        table_mock.columns = [col_id_mock, col_name]
        model_base.metadata.tables = {"test_table": table_mock}
        with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
            result = migrate_missing_columns(engine, model_base)
            assert conn.execute.called

    def test_column_add_value_error(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        conn = Mock()
        cm = MagicMock()
        cm.__enter__.return_value = conn
        engine.connect.return_value = cm
        inspector = Mock()
        inspector.has_table.return_value = True
        inspector.get_columns.return_value = [{"name": "id"}]
        model_base = Mock()
        col_name = Mock()
        col_name.name = "bad_col"
        table_mock = Mock()
        table_mock.name = "test_table"
        table_mock.c = {"bad_col": col_name}
        col_id_mock = MagicMock()
        col_id_mock.name = "id"
        table_mock.columns = [col_id_mock, col_name]
        model_base.metadata.tables = {"test_table": table_mock}
        with patch("app.core.migration_helper._sqlite_col_spec", side_effect=ValueError("bad col")):
            with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
                result = migrate_missing_columns(engine, model_base)
                assert result is None

    def test_table_processing_error(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        inspector = Mock()
        model_base = Mock()
        table_mock = Mock()
        table_mock.name = "bad_table"
        model_base.metadata.tables = {"bad_table": table_mock}
        with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
            inspector.has_table.side_effect = KeyError("bad table")
            result = migrate_missing_columns(engine, model_base)
            assert result is None

    def test_all_tables_up_to_date(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        inspector = Mock()
        inspector.has_table.return_value = True
        inspector.get_columns.return_value = [{"name": "id"}, {"name": "name"}]
        model_base = Mock()
        col_id = Mock()
        col_id.name = "id"
        col_name = Mock()
        col_name.name = "name"
        table_mock = Mock()
        table_mock.name = "test_table"
        table_mock.columns = [col_id, col_name]
        model_base.metadata.tables = {"test_table": table_mock}
        with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
            with patch.object(engine, "connect") as mock_connect:
                result = migrate_missing_columns(engine, model_base)
                assert result is None
                mock_connect.assert_not_called()

    def test_no_tables(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        inspector = Mock()
        model_base = Mock()
        model_base.metadata.tables = {}
        with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
            result = migrate_missing_columns(engine, model_base)
            assert result is None

    def test_summary_added_failed(self):
        from app.core.migration_helper import migrate_missing_columns
        engine = Mock()
        conn = Mock()
        cm = MagicMock()
        cm.__enter__.return_value = conn
        engine.connect.return_value = cm
        inspector = Mock()
        inspector.has_table.return_value = True
        inspector.get_columns.return_value = [{"name": "id"}]
        model_base = Mock()
        col_name = Mock()
        col_name.name = "new_col"
        table_mock = Mock()
        table_mock.name = "test_table"
        table_mock.c = {"new_col": col_name}
        col_id_mock = MagicMock()
        col_id_mock.name = "id"
        table_mock.columns = [col_id_mock, col_name]
        model_base.metadata.tables = {"test_table": table_mock}
        with patch("app.core.migration_helper._sqlite_col_spec", return_value=("INTEGER", "DEFAULT 0")):
            with patch("app.core.migration_helper.sa_inspect", return_value=inspector):
                result = migrate_missing_columns(engine, model_base)
                assert conn.execute.called
