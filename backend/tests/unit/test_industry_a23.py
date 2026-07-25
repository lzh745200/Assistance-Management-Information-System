"""补齐 app.models.industry 覆盖率缺口（a23）。

缺口：TeaPlantation.calculate_quality (57-59)、CactusFruitPlot.calculate_adaptation (104-110)、
calculate_tea_quality (135-143)、calculate_karst_adaptation (166-176)。
模型类为纯 Python 对象，真实实例化即可，无需数据库。
"""

import pytest

from app.models.industry import (
    CactusFruitPlot,
    TeaPlantation,
    calculate_karst_adaptation,
    calculate_tea_quality,
)


class TestTeaPlantationCalculateQuality:
    def test_missing_altitude_returns_zero(self):
        tea = TeaPlantation(name="都匀毛尖茶园", altitude=None, karst_soil_moisture=0.3)
        assert tea.calculate_quality() == 0.0

    def test_missing_moisture_returns_zero(self):
        tea = TeaPlantation(name="都匀毛尖茶园", altitude=1000.0, karst_soil_moisture=None)
        assert tea.calculate_quality() == 0.0

    def test_with_values_delegates_to_algorithm(self):
        tea = TeaPlantation(name="贵定云雾茶园", altitude=1000.0, karst_soil_moisture=0.3)
        expected = calculate_tea_quality(1000.0, 0.3)
        assert tea.calculate_quality() == expected
        assert 1.0 <= tea.calculate_quality() <= 10.0


class TestCactusFruitPlotCalculateAdaptation:
    def test_missing_params_returns_zero(self):
        plot = CactusFruitPlot(
            name="刺梨园",
            slope_degree=None,
            soil_depth_cm=40.0,
            annual_rainfall_mm=1100.0,
        )
        assert plot.calculate_adaptation() == 0.0

    def test_with_values_delegates_to_algorithm(self):
        plot = CactusFruitPlot(
            name="刺梨园",
            slope_degree=25.0,
            soil_depth_cm=40.0,
            annual_rainfall_mm=1100.0,
        )
        expected = calculate_karst_adaptation(25.0, 40.0, 1100.0)
        assert plot.calculate_adaptation() == expected
        assert 1.0 <= plot.calculate_adaptation() <= 10.0


class TestCalculateTeaQuality:
    def test_high_altitude_dry_soil_high_score(self):
        score = calculate_tea_quality(1200.0, 0.2)
        assert 1.0 <= score <= 10.0

    def test_low_altitude_hits_floor(self):
        # 海拔低于400m时海拔因子被钳到1.0下限
        score = calculate_tea_quality(100.0, 0.9)
        assert score >= 1.0

    def test_extreme_high_altitude_capped(self):
        # 海拔极高时海拔因子被钳到10.0上限
        score = calculate_tea_quality(3000.0, 0.0)
        assert score <= 10.0

    def test_returns_rounded_float(self):
        score = calculate_tea_quality(1000.0, 0.35)
        assert isinstance(score, float)
        assert score == round(score, 2)


class TestCalculateKarstAdaptation:
    def test_optimal_conditions(self):
        score = calculate_karst_adaptation(25.0, 50.0, 1000.0)
        assert score >= 9.0

    def test_steep_slope_lowers_score(self):
        optimal = calculate_karst_adaptation(25.0, 50.0, 1000.0)
        steep = calculate_karst_adaptation(45.0, 50.0, 1000.0)
        assert steep < optimal
        assert steep >= 1.0

    def test_thin_soil_hits_floor(self):
        score = calculate_karst_adaptation(25.0, 1.0, 1000.0)
        assert 1.0 <= score <= 10.0

    def test_extreme_rainfall_clamped(self):
        score = calculate_karst_adaptation(25.0, 50.0, 5000.0)
        assert score >= 1.0
