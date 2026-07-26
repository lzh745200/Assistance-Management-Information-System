"""补齐 app.services.offline_map_service 覆盖率缺口（22-28 行模块级回退、42-44 行 mkdir 失败、81 行缓存命中）."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

import app.services.offline_map_service as oms
from app.services.offline_map_service import OfflineMapService


class TestModuleLevelFallback:
    def test_tile_cache_dir_falls_back_to_tempdir(self):
        spec = importlib.util.spec_from_file_location(
            "offline_map_service_b4b_fallback", oms.__file__
        )
        module = importlib.util.module_from_spec(spec)
        with patch("app.utils.paths.get_data_path", side_effect=PermissionError("denied")):
            spec.loader.exec_module(module)
        assert "bumofu_offline_tiles" in str(module.TILE_CACHE_DIR)


class TestInitMkdirFailure:
    def test_mkdir_failure_is_tolerated(self, tmp_path):
        with patch.object(Path, "mkdir", side_effect=OSError("denied")):
            svc = OfflineMapService(cache_dir=tmp_path / "tiles")
        assert svc.cache_dir.name == "tiles"


class TestGetCoverageCacheHit:
    @pytest.mark.asyncio
    async def test_returns_cached_coverage(self, tmp_path):
        svc = OfflineMapService(cache_dir=tmp_path)
        svc._coverage_cache = {"total_tiles": 9, "total_size_mb": 0.1, "zoom_levels": [10]}
        assert await svc.get_coverage() == {"total_tiles": 9, "total_size_mb": 0.1, "zoom_levels": [10]}
