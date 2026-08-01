"""app.services.policy_import_service 覆盖率攻坚测试

覆盖点：
- 非法文件魔数 → HTTPException 400（validate_excel_upload 为同步 bool 校验，
  内容经 ``await file.read()`` 读取——此前的 await-bool bug 已修复）
- 行列数 < 2 → continue；标题为空 → 行错误
- result 含 duplicate 标记 → 记入 errors
- 行处理抛 ValueError → 捕获并构造行错误
- 顶层异常 → rollback + HTTPException 500
- _parse_date_cell / _safe_str / _make_row_error 各分支

全部用例使用真实 UploadFile + 真实 validate_excel_upload（不 mock），
端到端诚实覆盖。
"""

import io
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import openpyxl
import pytest
from fastapi import HTTPException, UploadFile

import app.services.policy_import_service as svc
from app.services.policy_import_service import (
    _make_row_error,
    _parse_date_cell,
    _safe_str,
    import_policies_from_excel,
)


def _xlsx_bytes(rows):
    """用 openpyxl 构造真实 xlsx 字节。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _db(existing=None, flush_exc=None):
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = existing
    db.query.return_value = q
    if flush_exc is not None:
        db.flush.side_effect = flush_exc
    return db


async def _run_import(content, db):
    """以真实 UploadFile 走完整校验 + 读取流程。"""
    upload = UploadFile(file=io.BytesIO(content), filename="import.xlsx")
    return await import_policies_from_excel(upload, db)


class TestImportPoliciesFromExcel:
    async def test_invalid_magic_bytes_400(self):
        # 魔数不符 → validate_excel_upload 返回 False → HTTPException 400
        with pytest.raises(HTTPException) as exc_info:
            await _run_import(b"not-an-excel-file", _db())
        assert exc_info.value.status_code == 400
        assert "文件校验失败" in exc_info.value.detail

    async def test_empty_file_400(self):
        # 空文件读不到有效头部 → 400
        with pytest.raises(HTTPException) as exc_info:
            await _run_import(b"", _db())
        assert exc_info.value.status_code == 400

    async def test_import_success_full_row(self):
        content = _xlsx_bytes([
            ["序号", "政策标题*", "政策文号", "政策级别", "发布机关",
             "发布日期", "生效日期", "状态", "关键词", "政策内容"],
            [1, "测试政策", "POL-001", "国家级", "国务院",
             "2026-01-01", "2026-02-01", "有效", "乡村", "内容"],
        ])
        db = _db()
        result = await _run_import(content, db)
        assert result["imported"] == 1
        assert result["errors"] == []
        assert result["total"] == 1
        db.commit.assert_called_once()

    async def test_row_with_less_than_two_columns_skipped(self):
        # 行61-62: len(row) < 2 → continue（单列工作表）
        content = _xlsx_bytes([["序号"], [1], [2]])
        result = await _run_import(content, _db())
        assert result["imported"] == 0
        assert result["errors"] == []
        assert result["total"] == 0

    async def test_empty_title_row_error(self):
        # 行63-66: 标题为空 → 行错误
        content = _xlsx_bytes([
            ["序号", "政策标题*"],
            [1, None],
        ])
        result = await _run_import(content, _db())
        assert result["imported"] == 0
        assert result["errorRows"] == [2]
        assert result["errors"][0]["error"] == "政策标题不能为空"

    async def test_duplicate_flag_branch(self):
        # 行73-75: result 带 duplicate 标记 → 记入 errors/errorRows
        content = _xlsx_bytes([
            ["序号", "政策标题*"],
            [1, "测试政策"],
        ])
        fake = {"row": 2, "title": "测试政策", "duplicate": True}
        with patch.object(svc, "_process_policy_row", return_value=fake):
            result = await _run_import(content, _db())
        assert result["imported"] == 0
        assert result["errors"] == [fake]
        assert result["errorRows"] == [2]

    async def test_duplicate_code_error(self):
        # 行114-117: 文号已存在 → error 分支（行70-72）
        content = _xlsx_bytes([
            ["序号", "政策标题*", "政策文号"],
            [1, "测试", "POL-001"],
        ])
        db = _db(existing=SimpleNamespace(code="POL-001"))
        result = await _run_import(content, db)
        assert result["imported"] == 0
        assert len(result["errors"]) == 1
        assert "已存在" in result["errors"][0]["error"]

    async def test_row_value_error_caught(self):
        # 行136-139: flush 抛错 → nested.rollback + warning + 上抛
        # 行78-80/175-176: ValueError 被行循环捕获 → _make_row_error
        content = _xlsx_bytes([
            ["序号", "政策标题*", "政策文号"],
            [1, "测试", "POL-002"],
        ])
        db = _db(flush_exc=ValueError("bad value"))
        result = await _run_import(content, db)
        assert result["imported"] == 0
        assert result["errorRows"] == [2]
        assert "bad value" in result["errors"][0]["error"]
        assert result["errors"][0]["title"] == "测试"
        db.begin_nested.return_value.rollback.assert_called_once()
        db.commit.assert_called_once()  # 行错误不影响整体提交

    async def test_top_level_exception_500(self):
        # 魔数合法但 zip 体损坏 → load_workbook 失败 → rollback + HTTPException 500
        db = _db()
        with pytest.raises(HTTPException) as exc_info:
            await _run_import(b"PK\x03\x04" + b"\x00" * 64, db)
        assert exc_info.value.status_code == 500
        assert "导入失败" in exc_info.value.detail
        db.rollback.assert_called_once()

    async def test_short_row_dates_none_via_public_path(self):
        # 行145-146: 行长度不足 → 日期为 None；同时覆盖 _safe_str 越界默认值
        content = _xlsx_bytes([
            ["序号", "政策标题*", "政策文号"],
            [1, "短行政策", "POL-003"],
        ])
        result = await _run_import(content, _db())
        assert result["imported"] == 1

    async def test_date_cell_variants_via_public_path(self):
        # 行150: None 日期；行152: datetime 日期；行156-157: 非法字符串日期
        content = _xlsx_bytes([
            ["序号", "政策标题*", "政策文号", "政策级别", "发布机关",
             "发布日期", "生效日期", "状态"],
            [1, "政策A", "A1", "县级", "机关", None, None, "草稿"],
            [2, "政策B", "B1", "专项", "机关",
             datetime(2026, 1, 1), datetime(2026, 2, 1), "已发布"],
            [3, "政策C", "C1", "市级", "机关", "not-a-date", "2026/03/01", "失效"],
        ])
        result = await _run_import(content, _db())
        assert result["imported"] == 3
        assert result["errors"] == []


class _WeirdRow:
    """__len__ 与 __getitem__ 行为不一致：触发 _parse_date_cell 的 TypeError 分支。"""

    def __len__(self):
        return 10

    def __getitem__(self, index):
        raise TypeError("no getitem")


class _BadStr:
    """__str__ 抛 TypeError：触发 _safe_str 的异常回退分支。"""

    def __str__(self):
        raise TypeError("boom")


class TestParseDateCell:
    def test_short_row_returns_none(self):
        # 行145-146
        assert _parse_date_cell(("a", "b"), 5, 2, "发布日期") is None

    def test_none_value_returns_none(self):
        # 行149-150
        assert _parse_date_cell((None,) * 8, 5, 2, "发布日期") is None

    def test_datetime_value_returned(self):
        # 行151-152
        dt = datetime(2026, 1, 1)
        row = (None,) * 5 + (dt,)
        assert _parse_date_cell(row, 5, 2, "发布日期") is dt

    def test_valid_string_parsed(self):
        # 行155
        row = (None,) * 5 + (" 2026-01-01 ",)
        assert _parse_date_cell(row, 5, 2, "发布日期") == datetime(2026, 1, 1)

    def test_invalid_string_returns_none(self):
        # 行156-157
        row = (None,) * 5 + ("not-a-date",)
        assert _parse_date_cell(row, 5, 2, "发布日期") is None

    def test_non_str_non_datetime_falls_through(self):
        # 行160: int 值不匹配任何 isinstance 分支
        row = (None,) * 5 + (12345,)
        assert _parse_date_cell(row, 5, 2, "发布日期") is None

    def test_type_error_during_access(self):
        # 行158-160: row[index] 抛 TypeError → 捕获并返回 None
        assert _parse_date_cell(_WeirdRow(), 5, 2, "发布日期") is None


class TestSafeStr:
    def test_normal_value(self):
        assert _safe_str(("  hello  ",), 0) == "hello"

    def test_none_returns_default(self):
        assert _safe_str((None,), 0, default="d") == "d"

    def test_out_of_range_returns_default(self):
        assert _safe_str(("a",), 5, default="d") == "d"

    def test_default_is_none(self):
        assert _safe_str((None,), 0) is None

    def test_exception_returns_default(self):
        # 行168-170: str(val) 抛 TypeError → 捕获并返回默认值
        assert _safe_str((_BadStr(),), 0, default="fallback") == "fallback"


class TestMakeRowError:
    def test_builds_error_dict(self):
        # 行175-176
        err = _make_row_error((1, "标题X"), 7, "出错原因")
        assert err == {"row": 7, "title": "标题X", "error": "出错原因"}

    def test_missing_title_fallback(self):
        err = _make_row_error((1,), 9, "出错")
        assert err["title"] == "未命名政策9"
