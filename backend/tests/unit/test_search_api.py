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
        mock_v = MagicMock()
        mock_v.id = 1; mock_v.village_name = "桃花村"; mock_v.county = "从化区"
        mock_v.village_category = "重点村"; mock_v.description = "描述"
        db.all.return_value = [mock_v]
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_village_results(items, "桃花", 5, db, MagicMock(is_superuser=True))
            assert len(items) == 1
            assert items[0].title == "桃花村"

    def test_append_project_with_data(self):
        from app.api.v1.search import _append_project_results
        db = MagicMock()
        mock_p = MagicMock()
        mock_p.id = 1; mock_p.project_name = "道路工程"; mock_p.status = "进行中"; mock_p.type = "基建"
        db.all.return_value = [mock_p]
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_project_results(items, "道路", 5, db, MagicMock(is_superuser=True))
            assert len(items) == 1

    def test_append_policy_with_data(self):
        from app.api.v1.search import _append_policy_results
        db = MagicMock()
        mock_p = MagicMock()
        mock_p.id = 1; mock_p.title = "乡村振兴政策"; mock_p.policy_number = "2025-001"
        db.all.return_value = [mock_p]
        items = []
        _append_policy_results(items, "乡村振兴", 5, db)
        assert len(items) == 1

    def test_append_school_with_data(self):
        from app.api.v1.search import _append_school_results
        db = MagicMock()
        mock_s = MagicMock()
        mock_s.id = 1; mock_s.school_name = "希望小学"; mock_s.school_type = "小学"; mock_s.address = "某县"
        db.all.return_value = [mock_s]
        with patch("app.api.v1.search.filter_by_data_scope", return_value=db):
            items = []
            _append_school_results(items, "希望", 5, db, MagicMock(is_superuser=True))
            assert len(items) == 1

    def test_append_user_with_data(self):
        from app.api.v1.search import _append_user_results
        db = MagicMock()
        mock_u = MagicMock()
        mock_u.id = 1; mock_u.username = "admin"; mock_u.real_name = "管理员"; mock_u.role = "admin"
        db.all.return_value = [mock_u]
        items = []
        _append_user_results(items, "admin", 5, db, True)
        assert len(items) == 1
