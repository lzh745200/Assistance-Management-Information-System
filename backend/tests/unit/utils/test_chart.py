"""
图表生成工具测试

测试 app/utils/chart.py 模块
"""
import pytest
from unittest.mock import patch, MagicMock
from app.utils.chart import ChartGenerator, generate_analysis_charts

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None


class TestChartGeneratorNoMatplotlib:
    def test_create_bar_chart_no_mpl(self):
        with patch("app.utils.chart.HAS_MATPLOTLIB", False):
            gen = ChartGenerator()
            result = gen.create_bar_chart({"a": 1, "b": 2}, "Test")
        assert result is None

    def test_create_pie_chart_no_mpl(self):
        with patch("app.utils.chart.HAS_MATPLOTLIB", False):
            gen = ChartGenerator()
            result = gen.create_pie_chart({"a": 1, "b": 2}, "Test")
        assert result is None

    def test_create_line_chart_no_mpl(self):
        with patch("app.utils.chart.HAS_MATPLOTLIB", False):
            gen = ChartGenerator()
            result = gen.create_line_chart({"a": [1, 2], "b": [3, 4]}, "Test")
        assert result is None

    def test_chart_to_base64_no_mpl(self):
        with patch("app.utils.chart.HAS_MATPLOTLIB", False):
            result = ChartGenerator.chart_to_base64({"a": 1}, "bar")
        assert result == ""


@pytest.mark.skipif(not HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestChartGeneratorWithMatplotlib:
    def setup_method(self):
        plt.close("all")

    def teardown_method(self):
        plt.close("all")

    def test_create_bar_chart(self):
        gen = ChartGenerator()
        result = gen.create_bar_chart({"a": 1, "b": 2}, "Bar Chart", "X", "Y")
        assert result is None

    def test_create_bar_chart_with_path(self, tmp_path):
        gen = ChartGenerator()
        file_path = tmp_path / "test_bar.png"
        result = gen.create_bar_chart({"a": 1}, file_path=file_path)
        assert result == file_path
        assert file_path.exists()

    def test_create_pie_chart(self):
        gen = ChartGenerator()
        result = gen.create_pie_chart({"a": 25, "b": 75}, "Pie")
        assert result is None

    def test_create_line_chart(self):
        gen = ChartGenerator()
        result = gen.create_line_chart({"series1": [1, 2, 3]}, "Line")
        assert result is None

    def test_chart_to_base64_bar(self):
        result = ChartGenerator.chart_to_base64({"a": 1, "b": 2}, "bar")
        assert "base64" in result
        assert "png" in result

    def test_chart_to_base64_pie(self):
        result = ChartGenerator.chart_to_base64({"a": 25, "b": 75}, "pie")
        assert "base64" in result

    def test_chart_to_base64_line(self):
        result = ChartGenerator.chart_to_base64({"s1": [1, 2, 3]}, "line")
        assert "base64" in result

    def test_create_bar_chart_with_all_options(self, tmp_path):
        gen = ChartGenerator()
        file_path = tmp_path / "full_bar.png"
        result = gen.create_bar_chart(
            {"cat1": 10, "cat2": 20},
            title="Test",
            xlabel="Category",
            ylabel="Value",
            file_path=file_path,
        )
        assert result == file_path
        assert file_path.exists()


class TestGenerateAnalysisCharts:
    def test_generate_without_mpl(self):
        with patch("app.utils.chart.HAS_MATPLOTLIB", False):
            result = generate_analysis_charts({"a": 1}, MagicMock())
        assert result == []

    @pytest.mark.skipif(not HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_generate_with_mpl(self, tmp_path):
        result = generate_analysis_charts({"a": 1, "b": 2}, tmp_path, "prefix")
        assert len(result) == 2
        for p in result:
            assert p.exists()
