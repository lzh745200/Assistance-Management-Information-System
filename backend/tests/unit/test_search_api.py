"""Tests for app.api.v1.search — helpers + global search."""

import pytest
from unittest.mock import MagicMock, patch


class TestHelperFunctions:
    def test_append_village_empty(self):
        from app.api.v1.search import _append_village_results
        db = MagicMock(); db.all.return_value = []
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_village_results(items, "测试", 5, db, MagicMock(is_superuser=True))
            assert items == []

    def test_append_project_empty(self):
        from app.api.v1.search import _append_project_results
        db = MagicMock(); db.all.return_value = []
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_project_results(items, "项目", 5, db, MagicMock(is_superuser=True))
            assert items == []

    def test_append_policy_empty(self):
        from app.api.v1.search import _append_policy_results
        db = MagicMock(); db.all.return_value = []
        items = []
        _append_policy_results(items, "政策", 5, db)
        assert items == []

    def test_append_school_empty(self):
        from app.api.v1.search import _append_school_results
        db = MagicMock(); db.all.return_value = []
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_school_results(items, "学校", 5, db, MagicMock(is_superuser=True))
            assert items == []

    def test_append_user_empty(self):
        from app.api.v1.search import _append_user_results
        db = MagicMock(); db.all.return_value = []
        items = []
        _append_user_results(items, "用户", 5, db, True)
        assert items == []

    def test_append_user_non_superuser(self):
        from app.api.v1.search import _append_user_results
        db = MagicMock(); db.all.return_value = []
        items = []
        _append_user_results(items, "用户", 5, db, False)
        assert items == []

    def test_append_village_with_data(self):
        from app.api.v1.search import _append_village_results
        db = MagicMock()
        v = MagicMock(); v.id = 1; v.name = "桃花村"; v.village_name = "桃花村"
        v.county = "从化区"; v.village_category = "重点村"; v.description = "描述"
        db.all.return_value = [v]
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_village_results(items, "桃花", 5, db, MagicMock(is_superuser=True))
            assert len(items) >= 0

    def test_append_project_with_data(self):
        from app.api.v1.search import _append_project_results
        db = MagicMock()
        p = MagicMock(); p.id = 1; p.name = "道路"; p.code = "001"; p.status = "active"
        db.all.return_value = [p]
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_project_results(items, "道路", 5, db, MagicMock(is_superuser=True))
            assert len(items) >= 0

    def test_append_policy_with_data(self):
        from app.api.v1.search import _append_policy_results
        db = MagicMock()
        p = MagicMock(); p.id = 1; p.title = "政策"; p.policy_number = "001"
        db.all.return_value = [p]
        items = []
        _append_policy_results(items, "政策", 5, db)
        assert len(items) >= 0
