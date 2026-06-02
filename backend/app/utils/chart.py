"""图表生成工具模块"""

import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ChartGenerator:
    """图表生成器"""

    def __init__(self):
        if HAS_MATPLOTLIB:  # 设置中文字体
            plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False

    def create_bar_chart(
        self,
        data: Dict[str, float],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        file_path: Optional[Path] = None,
        figsize: tuple = (10, 6),
    ) -> Optional[Path]:
        """创建柱状图

        Args:
            data: 数据字典
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            file_path: 保存路径
            figsize: 图表大小

        Returns:
            保存的文件路径
        """
        if not HAS_MATPLOTLIB:
            return None

        plt.figure(figsize=figsize)
        categories = list(data.keys())
        values = list(data.values())

        plt.bar(categories, values, color="steelblue", alpha=0.8)
        plt.title(title, fontsize=16, fontweight="bold")
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        if file_path:
            plt.savefig(file_path, dpi=300, bbox_inches="tight")
            plt.close()
            return file_path
        else:
            plt.close()
            return None

    def create_pie_chart(
        self,
        data: Dict[str, float],
        title: str = "",
        file_path: Optional[Path] = None,
        figsize: tuple = (8, 8),
    ) -> Optional[Path]:
        """创建饼图

        Args:
            data: 数据字典
            title: 图表标题
            file_path: 保存路径
            figsize: 图表大小

        Returns:
            保存的文件路径
        """
        if not HAS_MATPLOTLIB:
            return None

        plt.figure(figsize=figsize)
        labels = list(data.keys())
        sizes = list(data.values())
        colors = plt.cm.Set3(range(len(labels)))

        plt.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 10},
        )
        plt.title(title, fontsize=16, fontweight="bold")
        plt.axis("equal")

        if file_path:
            plt.savefig(file_path, dpi=300, bbox_inches="tight")
            plt.close()
            return file_path
        else:
            plt.close()
            return None

    def create_line_chart(
        self,
        data: Dict[str, List[float]],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        file_path: Optional[Path] = None,
        figsize: tuple = (12, 6),
    ) -> Optional[Path]:
        """创建折线图

        Args:
            data: 数据字典
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            file_path: 保存路径
            figsize: 图表大小

        Returns:
            保存的文件路径
        """
        if not HAS_MATPLOTLIB:
            return None

        plt.figure(figsize=figsize)

        for label, values in data.items():
            plt.plot(values, marker="o", label=label, linewidth=2)

        plt.title(title, fontsize=16, fontweight="bold")
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if file_path:
            plt.savefig(file_path, dpi=300, bbox_inches="tight")
            plt.close()
            return file_path
        else:
            plt.close()
            return None

    @staticmethod
    def chart_to_base64(data: Dict[str, Any], chart_type: str = "bar") -> str:
        """将图表转换为Base64字符串

        Args:
            data: 数据字典
            chart_type: 图表类型

        Returns:
            Base64编码的图片字符串
        """
        if not HAS_MATPLOTLIB:
            return ""

        buffer = BytesIO()
        plt.figure()

        if chart_type == "bar":
            categories = list(data.keys())
            values = list(data.values())
            plt.bar(categories, values, color="steelblue", alpha=0.8)
        elif chart_type == "pie":
            labels = list(data.keys())
            sizes = list(data.values())
            colors = plt.cm.Set3(range(len(labels)))
            plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%")
        elif chart_type == "line":
            for label, values in data.items():
                plt.plot(values, marker="o", label=label, linewidth=2)
            plt.legend()

        plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        plt.close()

        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()

        return f"data:image / png;base64,{image_base64}"


def generate_analysis_charts(data: Dict[str, Any], export_dir: Path, filename_prefix: str = "chart") -> List[Path]:
    """生成分析图表

    Args:
        data: 数据字典
        export_dir: 导出目录
        filename_prefix: 文件名前缀

    Returns:
        生成的图表文件路径列表
    """
    charts = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generator = ChartGenerator()

    if isinstance(data, dict):
        # 生成柱状图
        bar_path = export_dir / f"{filename_prefix}_bar_{timestamp}.png"
        result = generator.create_bar_chart(data, file_path=bar_path)
        if result:
            charts.append(bar_path)

        # 生成饼图
        pie_path = export_dir / f"{filename_prefix}_pie_{timestamp}.png"
        result = generator.create_pie_chart(data, file_path=pie_path)
        if result:
            charts.append(pie_path)

    return charts
