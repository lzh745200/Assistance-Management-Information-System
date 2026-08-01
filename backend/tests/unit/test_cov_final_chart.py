"""补齐 app.utils.chart 覆盖率缺口。

目标行：155-157 —— create_line_chart 传入 file_path 时保存图片并返回路径。
"""

import pytest

from app.utils.chart import HAS_MATPLOTLIB, ChartGenerator


@pytest.mark.skipif(not HAS_MATPLOTLIB, reason="matplotlib 不可用")
class TestCreateLineChartSaveToFile:
    def test_savefig_branch(self, tmp_path):
        gen = ChartGenerator()
        target = tmp_path / "line.png"

        out = gen.create_line_chart(
            {"系列A": [1, 3, 2, 5]}, title="测试", xlabel="x", ylabel="y", file_path=target
        )

        assert out == target
        assert target.exists()
