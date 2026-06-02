"""
离线地图服务测试
"""
import pytest
import asyncio
from pathlib import Path
from app.services.offline_map_service import offline_map_service



class TestOfflineMapService:
    """离线地图服务测试"""

    def test_get_tile_path(self):
        """测试获取瓦片路径"""
        path = offline_map_service.get_tile_path(8, 100, 50)
        assert isinstance(path, Path)
        # 支持 Windows 和 Unix 路径分隔符
        assert str(path).replace("\\", "/").endswith("8/100/50.png")

    @pytest.mark.asyncio
    async def test_get_tile_not_found(self):
        """测试获取不存在的瓦片"""
        tile = await offline_map_service.get_tile(99, 999, 999)
        assert tile is None

    @pytest.mark.asyncio
    async def test_save_and_get_tile(self):
        """测试保存和获取瓦片"""
        test_data = b"test_tile_data"
        z, x, y = 10, 200, 100

        # 保存瓦片
        result = await offline_map_service.save_tile(z, x, y, test_data)
        assert result is True

        # 获取瓦片
        tile = await offline_map_service.get_tile(z, x, y)
        assert tile == test_data

        # 清理
        tile_path = offline_map_service.get_tile_path(z, x, y)
        if tile_path.exists():
            tile_path.unlink()

    @pytest.mark.asyncio
    async def test_get_coverage(self):
        """测试获取覆盖范围"""
        coverage = await offline_map_service.get_coverage()
        assert isinstance(coverage, dict)
        assert "total_tiles" in coverage
        assert "total_size_mb" in coverage
        assert "zoom_levels" in coverage

    def test_tile_to_lat_lon(self):
        """测试瓦片坐标转经纬度"""
        lat, lon = offline_map_service.tile_to_lat_lon(100, 50, 8)
        assert isinstance(lat, float)
        assert isinstance(lon, float)
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180

    def test_lat_lon_to_tile(self):
        """测试经纬度转瓦片坐标"""
        x, y = offline_map_service.lat_lon_to_tile(26.5, 106.7, 8)
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert x >= 0
        assert y >= 0

    def test_coordinate_conversion_roundtrip(self):
        """测试坐标转换往返"""
        original_x, original_y, z = 100, 50, 8

        # 瓦片 -> 经纬度
        lat, lon = offline_map_service.tile_to_lat_lon(original_x, original_y, z)

        # 经纬度 -> 瓦片
        x, y = offline_map_service.lat_lon_to_tile(lat, lon, z)

        # 应该接近原始值
        assert abs(x - original_x) <= 1
        assert abs(y - original_y) <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
