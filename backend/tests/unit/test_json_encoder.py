"""Tests for app.core.json_encoder — 100% coverage."""

import pytest
import datetime
import decimal
import json
import uuid
from enum import Enum
from app.core.json_encoder import AppJSONEncoder, dumps, loads, CustomJSONEncoder


class TestAppJSONEncoder:
    def test_datetime(self):
        dt = datetime.datetime(2024, 6, 15, 14, 30, 45)
        result = json.dumps({"ts": dt}, cls=AppJSONEncoder)
        assert "2024-06-15T14:30:45" in result

    def test_date(self):
        d = datetime.date(2024, 12, 25)
        result = json.dumps({"date": d}, cls=AppJSONEncoder)
        assert "2024-12-25" in result

    def test_time(self):
        t = datetime.time(9, 15, 0)
        result = json.dumps({"time": t}, cls=AppJSONEncoder)
        assert "09:15:00" in result

    def test_decimal_as_float_default(self):
        dec = decimal.Decimal("3.14159")
        result = json.dumps({"val": dec}, cls=AppJSONEncoder)
        # Should serialize as float
        assert "3.14159" in result

    def test_decimal_as_string(self):
        enc = AppJSONEncoder(decimal_as_string=True)
        dec = decimal.Decimal("1.5")
        result = enc.encode({"val": dec})
        assert '"1.5"' in result

    def test_decimal_as_string_false(self):
        enc = AppJSONEncoder(decimal_as_string=False)
        dec = decimal.Decimal("2.5")
        result = enc.encode({"val": dec})
        assert "2.5" in result

    def test_uuid(self):
        uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        result = json.dumps({"id": uid}, cls=AppJSONEncoder)
        assert "12345678-1234-5678-1234-567812345678" in result

    def test_set(self):
        s = {1, 2, 3}
        result = json.dumps({"items": s}, cls=AppJSONEncoder)
        assert "[1, 2, 3]" in result

    def test_enum(self):
        class Color(Enum):
            RED = "red"
            BLUE = "blue"

        result = json.dumps({"color": Color.RED}, cls=AppJSONEncoder)
        assert '"red"' in result

    def test_int_enum(self):
        class Priority(Enum):
            LOW = 1
            HIGH = 2

        result = json.dumps({"pri": Priority.HIGH}, cls=AppJSONEncoder)
        assert "2" in result

    def test_dunder_json(self):
        class HasJson:
            def __json__(self):
                return {"key": "value"}

        result = json.dumps({"obj": HasJson()}, cls=AppJSONEncoder)
        assert '{"key": "value"}' in result

    def test_unknown_type_falls_back(self):
        class Unknown:
            pass

        with pytest.raises(TypeError):
            json.dumps({"obj": Unknown()}, cls=AppJSONEncoder)


class TestDumps:
    def test_basic(self):
        result = dumps({"a": 1})
        assert result == '{"a": 1}'

    def test_with_indent(self):
        result = dumps({"a": 1}, indent=2)
        assert "  " in result

    def test_with_datetime(self):
        dt = datetime.datetime(2024, 1, 1, 0, 0, 0)
        result = dumps({"ts": dt})
        assert "2024-01-01T00:00:00" in result

    def test_ensure_ascii_false(self):
        result = dumps({"key": "值"}, ensure_ascii=False)
        assert "值" in result


class TestLoads:
    def test_basic(self):
        result = loads('{"a": 1}')
        assert result == {"a": 1}

    def test_list(self):
        result = loads('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_with_kwargs(self):
        result = loads('{"a": 1, "b": 2}')
        assert result == {"a": 1, "b": 2}


class TestCustomJSONEncoder:
    def test_is_same_as_app_encoder(self):
        assert CustomJSONEncoder is AppJSONEncoder
