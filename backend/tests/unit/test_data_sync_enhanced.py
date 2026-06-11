import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime, timezone
from decimal import Decimal


class TestValidateIdentifier:
    def test_valid_identifier(self):
        from app.services.data_sync_enhanced import _validate_identifier
        assert _validate_identifier("hello") == "hello"
        assert _validate_identifier("abc_123") == "abc_123"

    def test_empty_identifier(self):
        from app.services.data_sync_enhanced import _validate_identifier
        with pytest.raises(ValueError, match="非法的"):
            _validate_identifier("")

    def test_invalid_chars(self):
        from app.services.data_sync_enhanced import _validate_identifier
        with pytest.raises(ValueError, match="非法的"):
            _validate_identifier("123abc")
        with pytest.raises(ValueError, match="非法的"):
            _validate_identifier("a-b")
        with pytest.raises(ValueError, match="非法的"):
            _validate_identifier("a.b")


class TestValidateTableName:
    def test_valid_table(self):
        from app.services.data_sync_enhanced import _validate_table_name
        assert _validate_table_name("users") == "users"

    def test_table_not_registered(self):
        from app.services.data_sync_enhanced import _validate_table_name
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {}):
            with pytest.raises(ValueError, match="表未注册"):
                _validate_table_name("nonexistent")

    def test_invalid_name(self):
        from app.services.data_sync_enhanced import _validate_table_name
        with pytest.raises(ValueError, match="非法的"):
            _validate_table_name("")


class TestGetTableObject:
    def test_returns_table(self):
        from app.services.data_sync_enhanced import _get_table_object
        from sqlalchemy import Table, Column, Integer, MetaData
        meta = MetaData()
        tbl = Table("foo", meta, Column("id", Integer))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"foo": tbl}):
            result = _get_table_object("foo")
            assert result is tbl


class TestSignAndVerify:
    def test_sign_data_package_string_secret(self):
        from app.services.data_sync_enhanced import sign_data_package
        sig = sign_data_package(b"hello", "mysecret")
        assert isinstance(sig, str)
        assert len(sig) == 64

    def test_sign_data_package_bytes_secret(self):
        from app.services.data_sync_enhanced import sign_data_package
        sig = sign_data_package(b"hello", b"mysecret")
        assert isinstance(sig, str)

    def test_verify_valid(self):
        from app.services.data_sync_enhanced import sign_data_package, verify_data_package
        data = b"test data"
        secret = "secret123"
        sig = sign_data_package(data, secret)
        assert verify_data_package(data, sig, secret) is True

    def test_verify_invalid(self):
        from app.services.data_sync_enhanced import verify_data_package
        assert verify_data_package(b"data", "wrong_sig", "secret") is False


class TestNormalizeValue:
    def test_none(self):
        from app.services.data_sync_enhanced import _normalize_value
        assert _normalize_value(None) is None

    def test_datetime_naive(self):
        from app.services.data_sync_enhanced import _normalize_value
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = _normalize_value(dt)
        assert result == "2024-01-15 10:30:00"

    def test_datetime_with_tz(self):
        from app.services.data_sync_enhanced import _normalize_value
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = _normalize_value(dt)
        assert result == "2024-01-15 10:30:00"

    def test_decimal(self):
        from app.services.data_sync_enhanced import _normalize_value
        result = _normalize_value(Decimal("123.45"))
        assert result == 123.45

    def test_iso_string(self):
        from app.services.data_sync_enhanced import _normalize_value
        result = _normalize_value("2024-01-15T10:30:00Z")
        assert result == "2024-01-15 10:30:00"

    def test_iso_string_with_offset(self):
        from app.services.data_sync_enhanced import _normalize_value
        result = _normalize_value("2024-01-15T10:30:00+00:00")
        assert result == "2024-01-15 10:30:00"

    def test_invalid_iso_string(self):
        from app.services.data_sync_enhanced import _normalize_value
        result = _normalize_value("not-a-datetimeTstringZ")
        assert result == "not-a-datetimeTstringZ"

    def test_plain_string(self):
        from app.services.data_sync_enhanced import _normalize_value
        result = _normalize_value("  hello world  ")
        assert result == "hello world"

    def test_other_type(self):
        from app.services.data_sync_enhanced import _normalize_value
        assert _normalize_value(42) == 42
        assert _normalize_value(True) is True


class TestFieldLevelConflictDetector:
    def test_no_conflicts(self):
        from app.services.data_sync_enhanced import FieldLevelConflictDetector
        detector = FieldLevelConflictDetector()
        local = [{"id": 1, "name": "a", "value": 10}]
        remote = [{"id": 1, "name": "a", "value": 10}]
        conflicts = detector.detect_conflicts(local, remote, "test")
        assert conflicts == []

    def test_with_conflicts(self):
        from app.services.data_sync_enhanced import FieldLevelConflictDetector
        detector = FieldLevelConflictDetector()
        local = [{"id": 1, "name": "a", "value": 10}]
        remote = [{"id": 1, "name": "b", "value": 10}]
        conflicts = detector.detect_conflicts(local, remote, "test")
        assert len(conflicts) == 1
        assert conflicts[0].field == "name"
        assert conflicts[0].local_value == "a"
        assert conflicts[0].remote_value == "b"

    def test_custom_ignore_fields(self):
        from app.services.data_sync_enhanced import FieldLevelConflictDetector
        detector = FieldLevelConflictDetector()
        local = [{"id": 1, "name": "a", "custom": "x"}]
        remote = [{"id": 1, "name": "b", "custom": "y"}]
        conflicts = detector.detect_conflicts(local, remote, "test", ignore_fields={"custom"})
        assert len(conflicts) == 1
        assert conflicts[0].field == "name"

    def test_missing_key_field_in_record(self):
        from app.services.data_sync_enhanced import FieldLevelConflictDetector
        detector = FieldLevelConflictDetector()
        local = [{"not_id": 1, "name": "a"}]
        remote = [{"id": 1, "name": "b"}]
        conflicts = detector.detect_conflicts(local, remote, "test")
        assert conflicts == []

    def test_no_common_keys(self):
        from app.services.data_sync_enhanced import FieldLevelConflictDetector
        detector = FieldLevelConflictDetector()
        local = [{"id": 1, "name": "a"}]
        remote = [{"id": 2, "name": "b"}]
        conflicts = detector.detect_conflicts(local, remote, "test")
        assert conflicts == []

    def test_normalized_equality_no_conflict(self):
        from app.services.data_sync_enhanced import FieldLevelConflictDetector
        detector = FieldLevelConflictDetector()
        local = [{"id": 1, "amount": Decimal("10.00")}]
        remote = [{"id": 1, "amount": 10.0}]
        conflicts = detector.detect_conflicts(local, remote, "test", ignore_fields=set())
        assert conflicts == []

    def test_all_fields_ignored(self):
        from app.services.data_sync_enhanced import FieldLevelConflictDetector
        detector = FieldLevelConflictDetector()
        local = [{"id": 1, "name": "a"}]
        remote = [{"id": 1, "name": "b"}]
        conflicts = detector.detect_conflicts(local, remote, "test", ignore_fields={"name", "id"})
        assert conflicts == []


class TestImportDryRunResult:
    def test_can_import_true(self):
        from app.services.data_sync_enhanced import ImportDryRunResult
        r = ImportDryRunResult()
        assert r.can_import is True

    def test_can_import_false(self):
        from app.services.data_sync_enhanced import ImportDryRunResult
        r = ImportDryRunResult(error_rows=1)
        assert r.can_import is False

    def test_summary(self):
        from app.services.data_sync_enhanced import ImportDryRunResult
        from app.services.data_sync_enhanced import FieldConflict
        r = ImportDryRunResult(total_rows=10, new_rows=5, update_rows=3, conflict_rows=1, error_rows=1)
        r.warnings.append("warn")
        r.conflicts.append(FieldConflict("t", 1, "f", "a", "b"))
        s = r.summary()
        assert s["total_rows"] == 10
        assert s["new_rows"] == 5
        assert s["conflict_count"] == 1
        assert s["warning_count"] == 1


class TestDryRunImport:
    @patch("app.services.data_sync_enhanced._validate_table_name")
    def test_empty_records(self, mock_validate):
        from app.services.data_sync_enhanced import dry_run_import
        from sqlalchemy import Table, Column, Integer, MetaData
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer, primary_key=True))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            result = dry_run_import(mock_db, "test_table", [])
            assert result.total_rows == 0

    @patch("app.services.data_sync_enhanced._validate_table_name")
    def test_records_with_missing_pk(self, mock_validate):
        from app.services.data_sync_enhanced import dry_run_import
        from sqlalchemy import Table, Column, Integer, MetaData
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer, primary_key=True))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            records = [{"not_id": "a"}]
            result = dry_run_import(mock_db, "test_table", records)
            assert result.error_rows == 1
            assert len(result.warnings) == 1

    @patch("app.services.data_sync_enhanced._validate_table_name")
    def test_chunk_query_exception(self, mock_validate):
        from app.services.data_sync_enhanced import dry_run_import
        from sqlalchemy import Table, Column, Integer, MetaData
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer, primary_key=True))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            mock_db.execute.side_effect = Exception("DB error")
            records = [{"id": 1}]
            result = dry_run_import(mock_db, "test_table", records)
            assert result.error_rows == 1
            assert len(result.errors) == 1

    @patch("app.services.data_sync_enhanced._validate_table_name")
    def test_new_and_update_rows(self, mock_validate):
        from app.services.data_sync_enhanced import dry_run_import
        from sqlalchemy import Table, Column, Integer, MetaData
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer, primary_key=True))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [2, 3]
            mock_db.execute.return_value = mock_result
            records = [{"id": 1}, {"id": 2}, {"id": 3}]
            result = dry_run_import(mock_db, "test_table", records)
            assert result.new_rows == 1
            assert result.update_rows == 2

    @patch("app.services.data_sync_enhanced._validate_table_name")
    def test_multiple_chunks(self, mock_validate):
        from app.services.data_sync_enhanced import dry_run_import
        from sqlalchemy import Table, Column, Integer, MetaData
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer, primary_key=True))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            mock_result = MagicMock()
            existing_ids = list(range(600))
            mock_result.scalars.return_value.all.side_effect = [existing_ids[:500], existing_ids[500:]]
            mock_db.execute.return_value = mock_result
            records = [{"id": i} for i in range(600)]
            result = dry_run_import(mock_db, "test_table", records)
            assert result.new_rows == 0
            assert result.update_rows == 600


class TestGetChangedRecords:
    @patch("app.services.data_sync_enhanced._validate_table_name")
    @patch("app.services.data_sync_enhanced._validate_identifier")
    def test_since_with_tz(self, mock_validate_id, mock_validate_table):
        from app.services.data_sync_enhanced import get_changed_records
        from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer), Column("name", String), Column("updated_at", DateTime))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            mock_row = MagicMock()
            mock_row._mapping = {"id": 1, "name": "test", "updated_at": None}
            mock_db.execute.return_value.all.return_value = [mock_row]
            since = datetime(2024, 1, 1, tzinfo=timezone.utc)
            result = get_changed_records(mock_db, "test_table", since)
            assert len(result) == 1
            assert result[0]["id"] == 1

    @patch("app.services.data_sync_enhanced._validate_table_name")
    @patch("app.services.data_sync_enhanced._validate_identifier")
    def test_since_naive(self, mock_validate_id, mock_validate_table):
        from app.services.data_sync_enhanced import get_changed_records
        from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer), Column("name", String), Column("updated_at", DateTime))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            mock_db.execute.return_value.all.return_value = []
            since = datetime(2024, 1, 1)
            result = get_changed_records(mock_db, "test_table", since)
            assert result == []

    @patch("app.services.data_sync_enhanced._validate_table_name")
    @patch("app.services.data_sync_enhanced._validate_identifier")
    def test_exception_returns_empty(self, mock_validate_id, mock_validate_table):
        from app.services.data_sync_enhanced import get_changed_records
        from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime
        meta = MetaData()
        test_table = Table("test_table", meta, Column("id", Integer), Column("name", String), Column("updated_at", DateTime))
        with patch("app.services.data_sync_enhanced.Base.metadata.tables", {"test_table": test_table}):
            mock_db = MagicMock()
            mock_db.execute.side_effect = Exception("query error")
            since = datetime(2024, 1, 1)
            result = get_changed_records(mock_db, "test_table", since)
            assert result == []
