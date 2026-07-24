"""app.api.v1.sentiment 覆盖率攻坚测试

覆盖 6 个端点全部成功/权限/异常分支：
- POST /collect：非管理员 403、成功、HTTPException 透传、通用异常 500
- POST /analyze：非管理员 403、成功、HTTPException 透传、通用异常 500
- GET /news：全过滤参数 + published_at 为空分支、异常 500
- GET /statistics：聚合统计 + 热词、异常 500
- GET /hot-keywords：成功、异常 500
- GET /alerts：成功 + published_at 为空分支、异常 500
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.v1.deps import get_current_active_user, get_db
from app.api.v1.sentiment import AnalysisService, CrawlerService

BASE = "/api/v1/sentiment"


# ==================== 公共设施 ====================


def _news(**kw):
    defaults = dict(
        id=1,
        title="乡村振兴新闻",
        source="测试来源",
        url="http://example.com/1",
        published_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        sentiment_score=0.8,
        sentiment_label="positive",
        keywords=["乡村", "振兴"],
        is_alert=False,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _q(**kw):
    q = MagicMock()
    for attr in ("filter", "order_by", "offset", "limit", "group_by"):
        getattr(q, attr).return_value = q
    q.scalar.return_value = kw.get("scalar", 0)
    q.all.return_value = kw.get("all", [])
    return q


@pytest.fixture
def admin_client():
    from app.main import app

    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_active_user] = lambda: SimpleNamespace(
        id=1, username="admin", is_superuser=True
    )
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides = original


@pytest.fixture
def user_client():
    from app.main import app

    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_active_user] = lambda: SimpleNamespace(
        id=2, username="user", is_superuser=False
    )
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides = original


def _use_db(client, db):
    client.app.dependency_overrides[get_db] = lambda: db


# ==================== POST /collect ====================


class TestCollectNews:
    def test_forbidden_for_non_admin(self, user_client):
        resp = user_client.post(f"{BASE}/collect", json={"keywords": ["乡村"]})
        assert resp.status_code == 403

    def test_collect_success(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with (
            patch.object(CrawlerService, "fetch_rss_feeds", return_value=[{"t": 1}, {"t": 2}]) as m_fetch,
            patch.object(CrawlerService, "save_news", return_value=2) as m_save,
        ):
            resp = admin_client.post(f"{BASE}/collect", json={"keywords": ["乡村", "振兴"]})
        assert resp.status_code == 200
        assert resp.json()["data"] == {"collected": 2, "saved": 2}
        m_fetch.assert_called_once()
        m_save.assert_called_once()

    def test_collect_http_exception_passthrough(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with patch.object(
            CrawlerService, "fetch_rss_feeds", side_effect=HTTPException(status_code=400, detail="bad")
        ):
            resp = admin_client.post(f"{BASE}/collect", json={"keywords": ["乡村"]})
        assert resp.status_code == 400

    def test_collect_generic_exception_500(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with patch.object(CrawlerService, "fetch_rss_feeds", side_effect=RuntimeError("boom")):
            resp = admin_client.post(f"{BASE}/collect", json={"keywords": ["乡村"]})
        assert resp.status_code == 500
        assert resp.json()["detail"] == "新闻采集失败"


# ==================== POST /analyze ====================


class TestAnalyzeNews:
    def test_forbidden_for_non_admin(self, user_client):
        resp = user_client.post(f"{BASE}/analyze")
        assert resp.status_code == 403

    def test_analyze_success(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with patch.object(AnalysisService, "analyze_news_batch", return_value=7) as m_analyze:
            resp = admin_client.post(f"{BASE}/analyze?limit=50")
        assert resp.status_code == 200
        assert resp.json()["data"] == {"processed": 7}
        m_analyze.assert_called_once()

    def test_analyze_http_exception_passthrough(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with patch.object(
            AnalysisService, "analyze_news_batch", side_effect=HTTPException(status_code=400, detail="bad")
        ):
            resp = admin_client.post(f"{BASE}/analyze")
        assert resp.status_code == 400

    def test_analyze_generic_exception_500(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with patch.object(AnalysisService, "analyze_news_batch", side_effect=RuntimeError("boom")):
            resp = admin_client.post(f"{BASE}/analyze")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "情感分析失败"


# ==================== GET /news ====================


class TestGetNewsList:
    def test_news_with_all_filters(self, admin_client):
        q = _q(all=[_news(), _news(id=2, published_at=None)])
        db = MagicMock()
        db.query = MagicMock(return_value=q)
        _use_db(admin_client, db)
        resp = admin_client.get(
            f"{BASE}/news?sentiment_label=positive&is_alert=false&days=3&limit=10&offset=0"
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert data["items"][0]["published_at"] is not None
        assert data["items"][1]["published_at"] is None
        assert data["items"][0]["sentiment_label"] == "positive"

    def test_news_exception_500(self, admin_client):
        db = MagicMock()
        db.query = MagicMock(side_effect=RuntimeError("boom"))
        _use_db(admin_client, db)
        resp = admin_client.get(f"{BASE}/news")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "获取新闻列表失败"


# ==================== GET /statistics ====================


class TestGetStatistics:
    def test_statistics_success(self, admin_client):
        q_stats = _q(all=[("positive", 5), ("negative", 2)])
        q_alert = _q(scalar=3)
        db = MagicMock()
        db.query = MagicMock(side_effect=[q_stats, q_alert])
        _use_db(admin_client, db)
        with patch.object(
            AnalysisService, "generate_hot_keywords", return_value=[{"word": "乡村", "count": 9}]
        ):
            resp = admin_client.get(f"{BASE}/statistics?days=7")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["period_days"] == 7
        assert data["total_news"] == 7
        assert data["positive_count"] == 5
        assert data["negative_count"] == 2
        assert data["neutral_count"] == 0
        assert data["alert_count"] == 3
        assert data["hot_keywords"] == [{"word": "乡村", "count": 9}]

    def test_statistics_exception_500(self, admin_client):
        db = MagicMock()
        db.query = MagicMock(side_effect=RuntimeError("boom"))
        _use_db(admin_client, db)
        resp = admin_client.get(f"{BASE}/statistics")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "获取舆情统计失败"


# ==================== GET /hot-keywords ====================


class TestGetHotKeywords:
    def test_hot_keywords_success(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with patch.object(
            AnalysisService, "generate_hot_keywords", return_value=[{"word": "振兴", "count": 4}]
        ) as m_hot:
            resp = admin_client.get(f"{BASE}/hot-keywords?days=14&top_k=5")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["period_days"] == 14
        assert data["keywords"] == [{"word": "振兴", "count": 4}]
        m_hot.assert_called_once()

    def test_hot_keywords_exception_500(self, admin_client):
        db = MagicMock()
        _use_db(admin_client, db)
        with patch.object(
            AnalysisService, "generate_hot_keywords", side_effect=RuntimeError("boom")
        ):
            resp = admin_client.get(f"{BASE}/hot-keywords")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "获取热词失败"


# ==================== GET /alerts ====================


class TestGetAlerts:
    def test_alerts_success(self, admin_client):
        q = _q(all=[_news(is_alert=True), _news(id=2, is_alert=True, published_at=None)])
        db = MagicMock()
        db.query = MagicMock(return_value=q)
        _use_db(admin_client, db)
        resp = admin_client.get(f"{BASE}/alerts?days=7&limit=20")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert data["items"][0]["published_at"] is not None
        assert data["items"][1]["published_at"] is None
        assert "sentiment_score" in data["items"][0]

    def test_alerts_exception_500(self, admin_client):
        db = MagicMock()
        db.query = MagicMock(side_effect=RuntimeError("boom"))
        _use_db(admin_client, db)
        resp = admin_client.get(f"{BASE}/alerts")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "获取预警列表失败"
