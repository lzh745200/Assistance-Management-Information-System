"""app.api.v1.offline_map 覆盖率攻坚测试

覆盖 4 个端点全部分支：
- GET /tiles/{z}/{x}/{y}：缩放非法400 / 命中200 / 未命中404 / 服务异常
- GET /status：成功 / 异常
- POST /download：纬度/经度/缩放/顺序四类参数400 / 成功 / 异常（管理员）
- DELETE /clear：成功 / 异常（管理员）
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_current_active_user

BASE = "/api/v1/offline-map"


@pytest.fixture
def client():
    from app.main import app

    original = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_active_user] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", is_superuser=True
    )
    svc = MagicMock()
    svc.get_tile = AsyncMock(return_value=b"\x89PNG-tile")
    svc.get_coverage = AsyncMock(return_value={"tiles": 100})
    with patch("app.api.v1.offline_map.offline_map_service", svc):
        yield TestClient(app, raise_server_exceptions=False), svc
    app.dependency_overrides = original


class TestGetTile:
    def test_zoom_too_low_400(self, client):
        c, _ = client
        assert c.get(f"{BASE}/tiles/-1/0/0").status_code == 400

    def test_zoom_too_high_400(self, client):
        c, _ = client
        assert c.get(f"{BASE}/tiles/19/0/0").status_code == 400

    def test_tile_found_200(self, client):
        c, _ = client
        resp = c.get(f"{BASE}/tiles/10/1/2")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert "max-age=86400" in resp.headers["cache-control"]
        assert resp.content == b"\x89PNG-tile"

    def test_tile_not_found_404(self, client):
        c, svc = client
        svc.get_tile = AsyncMock(return_value=None)
        assert c.get(f"{BASE}/tiles/10/1/2").status_code == 404

    def test_tile_service_error(self, client):
        c, svc = client
        svc.get_tile = AsyncMock(side_effect=RuntimeError("io fail"))
        resp = c.get(f"{BASE}/tiles/10/1/2")
        assert resp.status_code in (400, 500)
        assert "获取地图瓦片失败" in resp.text


class TestGetStatus:
    def test_status_success(self, client):
        c, _ = client
        resp = c.get(f"{BASE}/status")
        assert resp.status_code == 200
        assert resp.json()["data"]["tiles"] == 100

    def test_status_error(self, client):
        c, svc = client
        svc.get_coverage = AsyncMock(side_effect=RuntimeError("x"))
        resp = c.get(f"{BASE}/status")
        assert resp.status_code in (400, 500)
        assert "获取离线地图状态失败" in resp.text


class TestDownloadTiles:
    def _post(self, c, **kw):
        params = dict(min_lat=30.0, max_lat=31.0, min_lon=120.0, max_lon=121.0, min_zoom=4, max_zoom=12)
        params.update(kw)
        return c.post(f"{BASE}/download", params=params)

    def test_invalid_latitude_400(self, client):
        c, _ = client
        assert self._post(c, min_lat=-91).status_code == 400
        assert self._post(c, max_lat=91).status_code == 400

    def test_invalid_longitude_400(self, client):
        c, _ = client
        assert self._post(c, min_lon=-181).status_code == 400
        assert self._post(c, max_lon=181).status_code == 400

    def test_invalid_zoom_400(self, client):
        c, _ = client
        assert self._post(c, min_zoom=-1).status_code == 400
        assert self._post(c, max_zoom=19).status_code == 400

    def test_zoom_order_400(self, client):
        c, _ = client
        assert self._post(c, min_zoom=12, max_zoom=4).status_code == 400

    def test_download_success(self, client):
        c, svc = client
        svc.download_region.return_value = True
        resp = self._post(c)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "30.0,120.0-31.0,121.0@4-12" == resp.json()["data"]["region"]
        svc.download_region.assert_called_once()

    def test_download_error(self, client):
        c, svc = client
        svc.download_region.side_effect = RuntimeError("net down")
        resp = self._post(c)
        assert resp.status_code in (400, 500)
        assert "下载地图瓦片失败" in resp.text


class TestClearTiles:
    def test_clear_success(self, client):
        c, _ = client
        resp = c.delete(f"{BASE}/clear")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_clear_error(self, client):
        c, svc = client
        svc.clear_cache.side_effect = RuntimeError("locked")
        resp = c.delete(f"{BASE}/clear")
        assert resp.status_code in (400, 500)
        assert "清理瓦片缓存失败" in resp.text
