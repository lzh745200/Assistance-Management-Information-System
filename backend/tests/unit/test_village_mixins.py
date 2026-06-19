"""Tests for app.services.village.mixins - zero coverage → 100%"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.village.mixins import (
    VillageQueryMixin,
    VillageExportMixin,
)


# ---------------------------------------------------------------------------
# VillageQueryMixin.apply_region_filter
# ---------------------------------------------------------------------------

class TestApplyRegionFilter:
    def test_no_region_code_returns_query_unchanged(self):
        query = MagicMock()
        model = MagicMock()
        result = VillageQueryMixin.apply_region_filter(query, model, None)
        assert result is query

    def test_empty_string_returns_unchanged(self):
        query = MagicMock()
        model = MagicMock()
        result = VillageQueryMixin.apply_region_filter(query, model, "")
        assert result is query

    def test_filters_by_region_code_when_attr_exists(self):
        query = MagicMock()
        query.filter.return_value = "filtered_query"
        model = MagicMock()
        type(model).region_code = "some_column"
        result = VillageQueryMixin.apply_region_filter(query, model, "440000")
        query.filter.assert_called_once()
        assert result == "filtered_query"

    def test_filters_by_county_when_region_code_absent(self):
        query = MagicMock()
        query.filter.return_value = "county_filtered"
        model = MagicMock()
        # Remove region_code so it defaults to None; county remains
        del model.region_code
        type(model).county = "county_col"
        result = VillageQueryMixin.apply_region_filter(query, model, "440100")
        query.filter.assert_called_once()
        assert result == "county_filtered"

    def test_returns_query_when_neither_attr_exists(self):
        query = MagicMock()
        model = MagicMock()
        # Delete both attributes so getattr with default returns None
        del model.region_code
        del model.county
        result = VillageQueryMixin.apply_region_filter(query, model, "440000")
        assert result is query


# ---------------------------------------------------------------------------
# VillageQueryMixin.apply_keyword_search
# ---------------------------------------------------------------------------

class TestApplyKeywordSearch:
    def test_no_keyword_returns_unchanged(self):
        query = MagicMock()
        model = MagicMock()
        result = VillageQueryMixin.apply_keyword_search(query, model, None)
        assert result is query

    def test_empty_string_returns_unchanged(self):
        query = MagicMock()
        model = MagicMock()
        result = VillageQueryMixin.apply_keyword_search(query, model, "")
        assert result is query

    def test_filters_by_name_and_code(self):
        query = MagicMock()
        query.filter.return_value = "search_result"
        model = MagicMock()
        # ilike must return a MagicMock that represents a SQL clause
        name_ilike_clause = MagicMock(name="name_ilike_clause")
        code_ilike_clause = MagicMock(name="code_ilike_clause")
        type(model).name = MagicMock(ilike=MagicMock(return_value=name_ilike_clause))
        type(model).code = MagicMock(ilike=MagicMock(return_value=code_ilike_clause))

        with patch("sqlalchemy.or_", return_value="or_clause"):
            result = VillageQueryMixin.apply_keyword_search(query, model, "test")
            query.filter.assert_called_once_with("or_clause")
            assert result == "search_result"

    def test_filters_by_name_only_when_code_missing(self):
        query = MagicMock()
        query.filter.return_value = "name_only_result"
        model = MagicMock()
        name_ilike_clause = MagicMock(name="name_ilike")
        type(model).name = MagicMock(ilike=MagicMock(return_value=name_ilike_clause))
        del model.code

        with patch("sqlalchemy.or_", return_value="just_name"):
            result = VillageQueryMixin.apply_keyword_search(query, model, "x")
            query.filter.assert_called_once_with("just_name")
            assert result == "name_only_result"

    def test_returns_query_when_no_name_or_code(self):
        query = MagicMock()
        model = MagicMock()
        del model.name
        del model.code
        result = VillageQueryMixin.apply_keyword_search(query, model, "test")
        assert result is query


# ---------------------------------------------------------------------------
# VillageExportMixin.to_export_dict
# ---------------------------------------------------------------------------

class TestToExportDict:
    def test_full_village_export(self):
        village = MagicMock()
        village.name = "桃花村"
        village.code = "V001"
        village.province = "广东省"
        village.city = "广州市"
        village.county = "从化区"
        village.township = "吕田镇"
        village.ethnic_group = "汉族"
        village.is_ethnic_village = True
        village.longitude = 113.5
        village.latitude = 23.7

        result = VillageExportMixin.to_export_dict(village)
        assert result["村庄名称"] == "桃花村"
        assert result["村庄编码"] == "V001"
        assert result["省份"] == "广东省"
        assert result["城市"] == "广州市"
        assert result["县/市"] == "从化区"
        assert result["乡镇"] == "吕田镇"
        assert result["民族属性"] == "汉族"
        assert result["是否民族村寨"] == "是"
        assert result["经度"] == 113.5
        assert result["纬度"] == 23.7

    def test_non_ethnic_village(self):
        village = MagicMock()
        # Provide defaults so getattr works
        village.name = ""
        village.code = ""
        village.province = ""
        village.city = ""
        village.county = ""
        village.township = ""
        village.ethnic_group = ""
        village.is_ethnic_village = False
        village.longitude = ""
        village.latitude = ""
        result = VillageExportMixin.to_export_dict(village)
        assert result["是否民族村寨"] == "否"

    def test_missing_attributes_default_to_empty(self):
        class PlainVillage:
            pass
        v = PlainVillage()
        result = VillageExportMixin.to_export_dict(v)
        assert result["村庄名称"] == ""
        assert result["是否民族村寨"] == "否"
