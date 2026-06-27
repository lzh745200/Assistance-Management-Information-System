"""Tests for app/services/policy_fts_service.py — 目标 100% 覆盖。"""
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from app.services.policy_fts_service import (
    FTS_TABLE,
    ensure_fts_table,
    highlight_keywords,
    search_policies_fts,
)


# ---------------------------------------------------------------------------
# ensure_fts_table
# ---------------------------------------------------------------------------

class TestEnsureFtsTable:
    def test_table_already_exists(self):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = ("policies_fts",)
        ensure_fts_table(db)
        db.execute.assert_called_once()
        db.commit.assert_not_called()

    def test_table_created(self):
        db = MagicMock()
        db.execute.return_value.fetchone.side_effect = [None, None, None]
        ensure_fts_table(db)
        assert db.commit.called
        assert db.execute.call_count == 3


# ---------------------------------------------------------------------------
# search_policies_fts
# ---------------------------------------------------------------------------

class TestSearchPoliciesFts:
    def test_empty_query_returns_empty_list(self):
        db = MagicMock()
        assert search_policies_fts(db, "") == []

    def test_whitespace_only_query_returns_empty_list(self):
        db = MagicMock()
        assert search_policies_fts(db, "   ") == []

    def test_fts_success(self):
        db = MagicMock()
        db.execute.return_value.fetchall.return_value = [
            (1, "标题", "摘要", "关键词", "国家", "agriculture",
             "这是<mark>示例</mark>摘要", 1.5),
        ]
        results = search_policies_fts(db, "示例", limit=10, offset=0)
        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["title"] == "标题"
        assert results[0]["rank"] == 1.5
        assert results[0]["snippet"] == "这是<mark>示例</mark>摘要"

    def test_fts_fallback_to_like(self):
        db = MagicMock()
        first_call = MagicMock()
        first_call.fetchall.side_effect = Exception("FTS error")
        second_call = MagicMock()
        second_call.fetchall.return_value = [
            (2, "回退", "fallback", "", "local", "education", "snippet", 0.0),
        ]
        db.execute.side_effect = [first_call, second_call]
        results = search_policies_fts(db, "fallback")
        assert len(results) == 1
        assert results[0]["id"] == 2

    def test_multi_word_query_uses_quotes(self):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = ("policies_fts",)
        db.execute.return_value.fetchall.return_value = []
        search_policies_fts(db, "乡村 振兴")
        calls = db.execute.call_args_list
        # 找到带 MATCH 的调用
        match_call = None
        for args, kwargs in calls:
            sql_str = str(args[0])
            if "MATCH" in sql_str and len(args) > 1:
                match_call = args[1]
                break
        assert match_call is not None
        assert '"乡村 振兴"' in match_call["query"]

    def test_none_rank_returns_zero(self):
        db = MagicMock()
        db.execute.return_value.fetchall.return_value = [
            (1, "t", "s", "k", "l", "c", "sn", None),
        ]
        results = search_policies_fts(db, "test")
        assert results[0]["rank"] == 0.0


# ---------------------------------------------------------------------------
# highlight_keywords
# ---------------------------------------------------------------------------

class TestHighlightKeywords:
    def test_none_text_returns_none(self):
        assert highlight_keywords(None, "keyword") is None

    def test_empty_text_returns_empty(self):
        assert highlight_keywords("", "keyword") == ""

    def test_no_keyword_returns_original(self):
        assert highlight_keywords("一些文本", "") == "一些文本"

    def test_already_highlighted_skips(self):
        text = "已有<mark>标记</mark>的文字"
        assert highlight_keywords(text, "标记") == text

    def test_highlight_matches(self):
        result = highlight_keywords("乡村振兴战略", "振兴")
        assert result == "乡村<mark>振兴</mark>战略"

    def test_case_insensitive_highlight(self):
        result = highlight_keywords("Hello World", "hello")
        assert result == "<mark>Hello</mark> World"
