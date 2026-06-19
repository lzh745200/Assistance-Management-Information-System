"""Tests for app.api.v1.villages — core paths."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Patch Village model relationships BEFORE any imports
import app.models.village as _vmod
if not hasattr(_vmod.Village, 'tea_plantations'):
    _vmod.Village.tea_plantations = PropertyMock()
if not hasattr(_vmod.Village, 'cactus_fruit_plots'):
    _vmod.Village.cactus_fruit_plots = PropertyMock()
if not hasattr(_vmod.Village, 'ethnic_group'):
    _vmod.Village.ethnic_group = PropertyMock()


@pytest.fixture
def mock_db():
    session = MagicMock()
    session.query.return_value = session
    session.options.return_value = session
    session.filter.return_value = session
    session.offset.return_value = session
    session.limit.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    return session


@pytest.fixture
def client(mock_db):
    from app.api.v1 import deps
    app = FastAPI()
    user = MagicMock()
    user.is_superuser = True
    user.role = "admin"
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    from app.api.v1.villages import router
    app.include_router(router)
    return TestClient(app)


def make_mock_village():
    v = MagicMock()
    v.id = 1; v.name = "测试村"; v.code = "V001"
    v.province = "广东"; v.city = "广州"; v.county = "从化"; v.township = "吕田"
    v.ethnic_group = "汉族"; v.is_ethnic_village = False; v.karst_ratio = 0.3
    v.terrain_type = "山区"; v.region_code = "440117"
    v.latitude = 23.5; v.longitude = 113.5; v.description = "描述"
    v.villagers = []; v.industries = []; v.tea_plantations = []; v.cactus_fruit_plots = []
    return v


class TestListVillages:
    def test_empty(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            mock_db.all.return_value = []
            resp = client.get("/villages")
            assert resp.status_code == 200
            assert resp.json() == []

    def test_with_data(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            mock_db.all.return_value = [make_mock_village()]
            resp = client.get("/villages?keyword=测试&ethnic_group=汉族")
            assert resp.status_code == 200
            assert len(resp.json()) == 1

    def test_with_none_relations(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            v = make_mock_village()
            v.villagers = None; v.industries = None
            v.tea_plantations = None; v.cactus_fruit_plots = None
            v.terrain_type = None; v.region_code = None
            del v.ethnic_group
            mock_db.all.return_value = [v]
            resp = client.get("/villages")
            assert resp.status_code == 200
            data = resp.json()[0]
            assert data["ethnic_group"] == ""
            assert data["villager_count"] == 0


class TestGetVillage:
    def test_found(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock"):
            mock_db.first.return_value = make_mock_village()
            resp = client.get("/villages/1")
            assert resp.status_code == 200

    def test_not_found(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock"):
            mock_db.first.return_value = None
            resp = client.get("/villages/999")
            assert resp.status_code == 404

    def test_with_relations(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock"):
            v = make_mock_village()
            vl = MagicMock(); vl.id = 1; vl.name = "张三"; vl.phone = "139"; vl.is_poverty = True
            ind = MagicMock(); ind.id = 1; ind.name = "茶业"; ind.industry_type = "agriculture"
            v.villagers = [vl]; v.industries = [ind]
            mock_db.first.return_value = v
            resp = client.get("/villages/1")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["villagers"]) == 1
            assert len(data["industries"]) == 1
