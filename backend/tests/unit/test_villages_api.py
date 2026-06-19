"""Tests for app.api.v1.villages — 100% coverage."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


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
def mock_user():
    u = MagicMock()
    u.is_superuser = True
    u.role = "admin"
    return u


@pytest.fixture
def client(mock_db, mock_user):
    from app.api.v1 import deps
    app = FastAPI()
    app.dependency_overrides[deps.get_current_user] = lambda: mock_user
    app.dependency_overrides[deps.get_db] = lambda: mock_db
    from app.api.v1.villages import router
    app.include_router(router)
    return TestClient(app)


def make_mock_village(id_=1, name="测试村"):
    v = MagicMock()
    v.id = id_
    v.name = name
    v.code = f"V{id_:03d}"
    v.province = "广东省"
    v.city = "广州市"
    v.county = "从化区"
    v.township = "吕田镇"
    v.ethnic_group = "汉族"
    v.is_ethnic_village = False
    v.karst_ratio = 0.3
    v.terrain_type = "山区"
    v.region_code = "440117"
    v.latitude = 23.5
    v.longitude = 113.5
    v.description = "测试描述"
    v.villagers = []
    v.industries = []
    v.tea_plantations = []
    v.cactus_fruit_plots = []
    return v


class TestListVillages:
    def test_empty_list(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            mock_db.all.return_value = []
            resp = client.get("/villages")
            assert resp.status_code == 200
            assert resp.json() == []

    def test_with_keyword(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            v = make_mock_village()
            mock_db.all.return_value = [v]
            resp = client.get("/villages?keyword=测试")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["name"] == "测试村"

    def test_with_ethnic_group(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            v = make_mock_village()
            mock_db.all.return_value = [v]
            resp = client.get("/villages?ethnic_group=汉族")
            assert resp.status_code == 200

    def test_with_villagers(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            v = make_mock_village()
            villager = MagicMock()
            villager.id = 1
            villager.name = "村民甲"
            villager.phone = "13800001111"
            villager.is_poverty = False
            v.villagers = [villager]
            mock_db.all.return_value = [v]
            resp = client.get("/villages")
            assert resp.status_code == 200
            assert resp.json()[0]["villager_count"] == 1

    def test_no_relations(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"), \
             patch("app.api.v1.villages.filter_by_data_scope", return_value=mock_db):
            v = make_mock_village()
            del v.ethnic_group
            v.terrain_type = None
            v.region_code = None
            v.villagers = None
            v.industries = None
            v.tea_plantations = None
            v.cactus_fruit_plots = None
            mock_db.all.return_value = [v]
            resp = client.get("/villages")
            assert resp.status_code == 200
            data = resp.json()[0]
            assert data["ethnic_group"] == ""
            assert data["terrain_type"] == ""
            assert data["villager_count"] == 0


class TestGetVillage:
    def test_village_found(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"):
            v = make_mock_village()
            mock_db.first.return_value = v
            resp = client.get("/villages/1")
            assert resp.status_code == 200

    def test_village_not_found(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"):
            mock_db.first.return_value = None
            resp = client.get("/villages/999")
            assert resp.status_code == 404

    def test_village_with_relations(self, client, mock_db):
        with patch("app.api.v1.villages.selectinload", return_value="mock_load"):
            v = make_mock_village()
            vl = MagicMock()
            vl.id = 1; vl.name = "张三"; vl.phone = "139"; vl.is_poverty = True
            ind = MagicMock()
            ind.id = 1; ind.name = "茶业"; ind.industry_type = "agriculture"
            v.villagers = [vl]
            v.industries = [ind]
            mock_db.first.return_value = v
            resp = client.get("/villages/1")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["villagers"]) == 1
            assert len(data["industries"]) == 1
