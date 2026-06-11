"""Tests for app/utils/cursor_pagination.py — 100% coverage."""

import base64
import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import column
from sqlalchemy.orm import Query

from app.utils.cursor_pagination import (
    CursorData,
    CursorDirection,
    CursorPaginationRequest,
    CursorPaginationResponse,
    CursorPaginator,
    KeysetPaginator,
    cursor_paginate,
)


# ============================================================================
# Helpers
# ============================================================================

def mock_model(**col_names):
    """Create a mock SQLAlchemy model class with real column objects."""
    m = MagicMock()
    for name, col_name in col_names.items():
        setattr(m, name, column(col_name))
    if "id" not in col_names:
        m.id = column("id")
    return m


def mock_query(items):
    """Create a mock Query that returns *items* from .limit(N).all()."""
    q = MagicMock(spec=Query)
    q.filter.return_value = q
    q.order_by.return_value = q
    limited = MagicMock()
    limited.all.return_value = items
    q.limit.return_value = limited
    return q


def mock_item(**attrs):
    item = MagicMock()
    for k, v in attrs.items():
        setattr(item, k, v)
    return item


def encode_cursor_data(id_val, sort_val, sort_field="f", direction="next"):
    if isinstance(sort_val, datetime):
        cd = CursorData(id=id_val, sort_value=sort_val, sort_field=sort_field, direction=direction)
    else:
        cd = CursorData(id=id_val, sort_value=sort_val, sort_field=sort_field, direction=direction)
    return cd.encode()


# ============================================================================
# CursorDirection
# ============================================================================

class TestCursorDirection:
    def test_values(self):
        assert CursorDirection.NEXT == "next"
        assert CursorDirection.PREV == "prev"

    def test_members(self):
        assert CursorDirection("next") is CursorDirection.NEXT
        assert CursorDirection("prev") is CursorDirection.PREV


# ============================================================================
# CursorData
# ============================================================================

class TestCursorDataEncode:
    def test_encode_non_datetime(self):
        cd = CursorData(id=42, sort_value="hello", sort_field="name", direction="next")
        encoded = cd.encode()
        pad = 4 - len(encoded) % 4 if len(encoded) % 4 else 0
        decoded = json.loads(base64.urlsafe_b64decode(encoded + "=" * pad))
        assert decoded["id"] == 42
        assert decoded["sv"] == "hello"
        assert decoded["sf"] == "name"
        assert decoded["d"] == "next"
        assert "st" not in decoded

    def test_encode_datetime(self):
        dt = datetime(2024, 6, 15, 10, 30, 0)
        cd = CursorData(id=1, sort_value=dt, sort_field="created_at", direction="prev")
        encoded = cd.encode()
        pad = 4 - len(encoded) % 4 if len(encoded) % 4 else 0
        decoded = json.loads(base64.urlsafe_b64decode(encoded + "=" * pad))
        assert decoded["id"] == 1
        assert decoded["sv"] == dt.isoformat()
        assert decoded["st"] == "datetime"

    def test_encode_fallback(self):
        class CantSerialize:
            def __str__(self):
                return "fallback"

        cd = CursorData(id=1, sort_value=CantSerialize(), sort_field="x", direction="next")
        encoded = cd.encode()
        pad = 4 - len(encoded) % 4 if len(encoded) % 4 else 0
        decoded = json.loads(base64.urlsafe_b64decode(encoded + "=" * pad))
        assert decoded["sv"] == "fallback"


class TestCursorDataDecode:
    def test_decode_valid(self):
        raw = base64.urlsafe_b64encode(json.dumps({"id": 10, "sv": "abc", "sf": "name", "d": "next"}).encode()).decode()
        cd = CursorData.decode(raw)
        assert cd is not None
        assert cd.id == 10
        assert cd.sort_value == "abc"
        assert cd.sort_field == "name"
        assert cd.direction == "next"

    def test_decode_datetime(self):
        dt = datetime(2024, 1, 1, 12, 0, 0)
        data = {"id": 5, "sv": dt.isoformat(), "sf": "ts", "d": "prev", "st": "datetime"}
        raw = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
        cd = CursorData.decode(raw)
        assert cd is not None
        assert cd.sort_value == dt

    def test_decode_default_direction(self):
        raw = base64.urlsafe_b64encode(json.dumps({"id": 1, "sv": "v", "sf": "f"}).encode()).decode()
        cd = CursorData.decode(raw)
        assert cd is not None
        assert cd.direction == "next"

    def test_decode_invalid_base64(self):
        assert CursorData.decode("!!!bad!!!") is None

    def test_decode_invalid_json(self):
        raw = base64.urlsafe_b64encode(b"not-json").decode()
        assert CursorData.decode(raw) is None

    def test_decode_missing_keys(self):
        raw = base64.urlsafe_b64encode(json.dumps({"id": 1}).encode()).decode()
        assert CursorData.decode(raw) is None


# ============================================================================
# CursorPaginationRequest
# ============================================================================

class TestCursorPaginationRequest:
    def test_defaults(self):
        r = CursorPaginationRequest()
        assert r.cursor is None
        assert r.limit == 20
        assert r.direction == CursorDirection.NEXT
        assert r.sort_field == "id"
        assert r.sort_desc is True

    def test_custom(self):
        r = CursorPaginationRequest(cursor="x", limit=5, direction=CursorDirection.PREV,
                                    sort_field="ts", sort_desc=False)
        assert r.cursor == "x"
        assert r.limit == 5
        assert r.direction == CursorDirection.PREV
        assert r.sort_field == "ts"
        assert r.sort_desc is False

    def test_limit_validation(self):
        with pytest.raises(ValueError):
            CursorPaginationRequest(limit=0)
        with pytest.raises(ValueError):
            CursorPaginationRequest(limit=101)


# ============================================================================
# CursorPaginationResponse
# ============================================================================

class TestCursorPaginationResponse:
    def test_defaults(self):
        r = CursorPaginationResponse(limit=20)
        assert r.items == []
        assert r.next_cursor is None and r.prev_cursor is None
        assert r.has_next is False and r.has_prev is False
        assert r.limit == 20

    def test_custom(self):
        r = CursorPaginationResponse(items=[1], next_cursor="n", prev_cursor="p",
                                     has_next=True, has_prev=True, limit=10)
        assert r.next_cursor == "n"
        assert r.has_next is True


# ============================================================================
# CursorPaginator internals
# ============================================================================

class TestPaginatorInternals:
    def test_get_sort_column(self):
        m = mock_model(name="name_col")
        p = CursorPaginator(m, sort_field="name")
        assert p._get_sort_column(MagicMock()).key == "name_col"

    def test_get_id_column(self):
        m = mock_model(id="pk")
        p = CursorPaginator(m)
        assert p._get_id_column(MagicMock()).key == "pk"

    def test_create_cursor(self):
        m = mock_model(val="v_col", id="pk")
        p = CursorPaginator(m, sort_field="val")
        item = mock_item(val="xyz", id=99)
        cursor = p._create_cursor(item, "next")
        assert isinstance(cursor, str) and len(cursor) > 0


# ============================================================================
# _apply_cursor_filter — 4 branches
# ============================================================================

class TestApplyCursorFilter:
    def test_next_desc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=True)
        q = mock_query([])
        cd = CursorData(id=10, sort_value=50, sort_field="val", direction="next")
        p._apply_cursor_filter(q, cd, CursorDirection.NEXT)
        q.filter.assert_called_once()

    def test_next_asc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=False)
        q = mock_query([])
        cd = CursorData(id=10, sort_value=50, sort_field="val", direction="next")
        p._apply_cursor_filter(q, cd, CursorDirection.NEXT)
        q.filter.assert_called_once()

    def test_prev_desc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=True)
        q = mock_query([])
        cd = CursorData(id=10, sort_value=50, sort_field="val", direction="prev")
        p._apply_cursor_filter(q, cd, CursorDirection.PREV)
        q.filter.assert_called_once()

    def test_prev_asc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=False)
        q = mock_query([])
        cd = CursorData(id=10, sort_value=50, sort_field="val", direction="prev")
        p._apply_cursor_filter(q, cd, CursorDirection.PREV)
        q.filter.assert_called_once()


# ============================================================================
# _apply_sort — 4 branches
# ============================================================================

class TestApplySort:
    def test_not_reverse_desc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=True)
        q = mock_query([])
        r = p._apply_sort(q, reverse=False)
        assert r is q
        q.order_by.assert_called_once()

    def test_not_reverse_asc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=False)
        q = mock_query([])
        p._apply_sort(q, reverse=False)
        q.order_by.assert_called_once()

    def test_reverse_desc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=True)
        q = mock_query([])
        p._apply_sort(q, reverse=True)
        q.order_by.assert_called_once()

    def test_reverse_asc(self):
        m = mock_model(val="v", id="pk")
        p = CursorPaginator(m, sort_field="val", sort_desc=False)
        q = mock_query([])
        p._apply_sort(q, reverse=True)
        q.order_by.assert_called_once()


# ============================================================================
# CursorPaginator.paginate  — comprehensive
# ============================================================================

class TestPaginate:
    def test_no_cursor_empty(self):
        m = mock_model(name="n")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        result = p.paginate(mock_query([]), cursor=None, limit=20)
        assert result.items == []
        assert result.has_next is False
        assert result.has_prev is False
        assert result.next_cursor is None

    def test_no_cursor_has_next_false(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name="a", id=1), mock_item(name="b", id=2)]
        result = p.paginate(mock_query(items), cursor=None, limit=5)
        assert len(result.items) == 2
        assert result.has_next is False
        assert result.has_prev is False

    def test_no_cursor_has_next_true(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name=f"n{i}", id=i) for i in range(4)]
        result = p.paginate(mock_query(items), cursor=None, limit=3)
        assert len(result.items) == 3
        assert result.has_next is True
        assert result.has_prev is False
        assert result.next_cursor is not None
        assert result.prev_cursor is None

    def test_with_cursor_next_has_more(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name=f"n{i}", id=i) for i in range(4)]
        cursor = encode_cursor_data(1, "n1", "name")
        result = p.paginate(mock_query(items), cursor=cursor, limit=3)
        assert len(result.items) == 3
        assert result.has_next is True
        assert result.has_prev is True
        assert result.next_cursor is not None
        assert result.prev_cursor is not None

    def test_with_cursor_next_no_more(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name="a", id=1)]
        cursor = encode_cursor_data(0, "z", "name")
        result = p.paginate(mock_query(items), cursor=cursor, limit=5)
        assert len(result.items) == 1
        assert result.has_next is False
        assert result.has_prev is True

    def test_direction_prev_has_more(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name=f"n{i}", id=i) for i in range(4)]
        cursor = encode_cursor_data(3, "n3", "name", "prev")
        result = p.paginate(mock_query(items), cursor=cursor, limit=3,
                            direction=CursorDirection.PREV)
        assert len(result.items) == 3
        assert result.has_next is True
        assert result.has_prev is True

    def test_direction_prev_no_more(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name="a", id=1)]
        cursor = encode_cursor_data(10, "z", "name", "prev")
        result = p.paginate(mock_query(items), cursor=cursor, limit=5,
                            direction=CursorDirection.PREV)
        assert len(result.items) == 1
        assert result.has_next is True
        assert result.has_prev is False

    def test_cursor_decode_fails(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name="a", id=1)]
        result = p.paginate(mock_query(items), cursor="!!!bad!!!", limit=5)
        assert len(result.items) == 1

    def test_single_item_no_cursor(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name="a", id=1)]
        result = p.paginate(mock_query(items), cursor=None, limit=5)
        assert len(result.items) == 1
        assert result.has_next is False
        assert result.has_prev is False

    def test_single_item_with_cursor(self):
        m = mock_model(name="n", id="pk")
        p = CursorPaginator(m, sort_field="name", sort_desc=True)
        items = [mock_item(name="a", id=1)]
        cursor = encode_cursor_data(0, "z", "name")
        result = p.paginate(mock_query(items), cursor=cursor, limit=5)
        assert len(result.items) == 1
        assert result.has_next is False
        assert result.has_prev is True


# ============================================================================
# cursor_paginate convenience function
# ============================================================================

class TestCursorPaginateFunction:
    def test_convenience(self):
        m = mock_model(name="n", id="pk")
        items = [mock_item(name="a", id=1)]
        cursor = encode_cursor_data(0, "z", "name")
        result = cursor_paginate(mock_query(items), m, cursor=cursor, limit=5,
                                 direction=CursorDirection.NEXT, sort_field="name",
                                 sort_desc=True)
        assert len(result.items) == 1
        assert result.limit == 5

    def test_convenience_no_cursor(self):
        m = mock_model(name="n", id="pk")
        items = [mock_item(name="a", id=1)]
        result = cursor_paginate(mock_query(items), m, cursor=None, limit=10,
                                 direction=CursorDirection.NEXT, sort_field="name",
                                 sort_desc=False)
        assert len(result.items) == 1
        assert result.limit == 10


# ============================================================================
# KeysetPaginator.paginate_by_id
# ============================================================================

class TestKeysetPaginateById:
    def test_no_last_id_asc(self):
        m = mock_model(id="pk")
        items = [mock_item(id=1), mock_item(id=2)]
        result, next_id = KeysetPaginator.paginate_by_id(mock_query(items), m,
                                                         last_id=None, limit=5, ascending=True)
        assert len(result) == 2
        assert next_id is None

    def test_no_last_id_desc(self):
        m = mock_model(id="pk")
        items = [mock_item(id=2), mock_item(id=1)]
        result, next_id = KeysetPaginator.paginate_by_id(mock_query(items), m,
                                                         last_id=None, limit=5, ascending=False)
        assert len(result) == 2
        assert next_id is None

    def test_with_last_id_asc(self):
        m = mock_model(id="pk")
        items = [mock_item(id=6), mock_item(id=7)]
        result, next_id = KeysetPaginator.paginate_by_id(mock_query(items), m,
                                                         last_id=5, limit=5, ascending=True)
        assert len(result) == 2

    def test_with_last_id_desc(self):
        m = mock_model(id="pk")
        items = [mock_item(id=4), mock_item(id=3)]
        result, next_id = KeysetPaginator.paginate_by_id(mock_query(items), m,
                                                         last_id=5, limit=5, ascending=False)
        assert len(result) == 2

    def test_has_more_true(self):
        m = mock_model(id="pk")
        items = [mock_item(id=i) for i in range(4)]
        result, next_id = KeysetPaginator.paginate_by_id(mock_query(items), m,
                                                         last_id=None, limit=3, ascending=True)
        assert len(result) == 3
        assert next_id == 2

    def test_has_more_false(self):
        m = mock_model(id="pk")
        items = [mock_item(id=1)]
        result, next_id = KeysetPaginator.paginate_by_id(mock_query(items), m,
                                                         last_id=None, limit=5, ascending=False)
        assert len(result) == 1
        assert next_id is None

    def test_empty_result(self):
        m = mock_model(id="pk")
        result, next_id = KeysetPaginator.paginate_by_id(mock_query([]), m,
                                                         last_id=999, limit=5, ascending=True)
        assert result == []
        assert next_id is None


# ============================================================================
# KeysetPaginator.paginate_by_timestamp
# ============================================================================

class TestKeysetPaginateByTimestamp:
    def test_no_ts_asc(self):
        m = mock_model(ts="t", id="pk")
        items = [mock_item(id=1), mock_item(id=2)]
        result, nts, nid = KeysetPaginator.paginate_by_timestamp(
            mock_query(items), m, timestamp_field="ts", last_timestamp=None,
            limit=5, ascending=True)
        assert len(result) == 2
        assert nts is None and nid is None

    def test_no_ts_desc(self):
        m = mock_model(ts="t", id="pk")
        items = [mock_item(id=2), mock_item(id=1)]
        result, nts, nid = KeysetPaginator.paginate_by_timestamp(
            mock_query(items), m, timestamp_field="ts", last_timestamp=None,
            limit=5, ascending=False)
        assert len(result) == 2

    def test_with_ts_asc(self):
        m = mock_model(ts="t", id="pk")
        items = [mock_item(id=3, ts=datetime(2024, 2, 1)), mock_item(id=4, ts=datetime(2024, 2, 2))]
        ts = datetime(2024, 1, 1)
        result, nts, nid = KeysetPaginator.paginate_by_timestamp(
            mock_query(items), m, timestamp_field="ts", last_timestamp=ts, last_id=2,
            limit=5, ascending=True)
        assert len(result) == 2

    def test_with_ts_desc(self):
        m = mock_model(ts="t", id="pk")
        items = [mock_item(id=3, ts=datetime(2024, 2, 1)), mock_item(id=2, ts=datetime(2024, 1, 15))]
        ts = datetime(2024, 3, 1)
        result, nts, nid = KeysetPaginator.paginate_by_timestamp(
            mock_query(items), m, timestamp_field="ts", last_timestamp=ts, last_id=5,
            limit=5, ascending=False)
        assert len(result) == 2

    def test_has_more_true(self):
        m = mock_model(ts="t", id="pk")
        items = [mock_item(id=i, ts=datetime(2024, 1, i)) for i in range(1, 5)]
        result, nts, nid = KeysetPaginator.paginate_by_timestamp(
            mock_query(items), m, timestamp_field="ts", last_timestamp=None,
            limit=3, ascending=True)
        assert len(result) == 3
        assert nts == items[2].ts
        assert nid == items[2].id

    def test_has_more_false(self):
        m = mock_model(ts="t", id="pk")
        items = [mock_item(id=1, ts=datetime(2024, 1, 1))]
        result, nts, nid = KeysetPaginator.paginate_by_timestamp(
            mock_query(items), m, timestamp_field="ts", last_timestamp=None,
            limit=5, ascending=True)
        assert len(result) == 1
        assert nts is None and nid is None

    def test_empty_result(self):
        m = mock_model(ts="t", id="pk")
        result, nts, nid = KeysetPaginator.paginate_by_timestamp(
            mock_query([]), m, timestamp_field="ts",
            last_timestamp=datetime(2024, 6, 1), last_id=999,
            limit=5, ascending=True)
        assert result == []
        assert nts is None and nid is None
