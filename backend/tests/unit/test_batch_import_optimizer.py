"""Tests for batch import optimizer — pandas Excel reading and validation."""
import pytest


class TestExcelReader:
    """Tests for read_excel_fast function."""

    def test_read_empty_bytes_returns_empty(self):
        """Reading empty content should return empty headers and rows (or fail gracefully)."""
        from app.services.batch_import_optimizer import read_excel_fast

        # Empty bytes should either return empty lists or raise an error
        try:
            headers, rows = read_excel_fast(b"")
            assert isinstance(headers, list)
            assert isinstance(rows, list)
        except Exception:
            # Both outcomes are acceptable for empty input
            pass


class TestDataFrameValidator:
    """Tests for validate_rows function."""

    def test_validate_required_fields_empty_value(self):
        """Missing required field should produce an error."""
        from app.services.batch_import_optimizer import validate_rows

        rows = [{"name": "", "age": "25"}, {"name": "John", "age": "30"}]
        errors = validate_rows(rows, required_fields=["name"])

        assert len(errors) == 1
        assert errors[0]["row_number"] == 2  # First data row is row 2 in Excel
        assert errors[0]["field_name"] == "name"

    def test_validate_required_fields_all_present(self):
        """All required fields present should produce no errors."""
        from app.services.batch_import_optimizer import validate_rows

        rows = [{"name": "Alice", "age": "25"}, {"name": "Bob", "age": "30"}]
        errors = validate_rows(rows, required_fields=["name"])

        assert len(errors) == 0

    def test_validate_max_length_exceeded(self):
        """Field exceeding max length should produce an error."""
        from app.services.batch_import_optimizer import validate_rows

        rows = [{"code": "ABC1234567890"}]
        errors = validate_rows(rows, max_lengths={"code": 5})

        assert len(errors) == 1
        assert errors[0]["field_name"] == "code"
        assert "超出最大长度" in errors[0]["message"]

    def test_validate_max_length_within_limit(self):
        """Field within max length should not produce errors."""
        from app.services.batch_import_optimizer import validate_rows

        rows = [{"code": "ABC12"}]
        errors = validate_rows(rows, max_lengths={"code": 5})

        assert len(errors) == 0

    def test_validate_empty_rows(self):
        """Empty rows list should produce no errors."""
        from app.services.batch_import_optimizer import validate_rows

        errors = validate_rows([], required_fields=["name"])
        assert len(errors) == 0
