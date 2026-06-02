"""
效果评估服务

提供帮扶效果评估功能
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import timezone, datetime


@dataclass
class EffectivenessMetrics:
    """效果评估指标"""

    income_growth_rate: float = 0.0
    project_completion_rate: float = 0.0
    fund_usage_rate: float = 0.0
    satisfaction_score: float = 0.0
    overall_score: float = 0.0


@dataclass
class EffectivenessReport:
    """效果评估报告"""

    entity_id: int
    entity_type: str  # village, project, fund
    period_start: datetime
    period_end: datetime
    metrics: EffectivenessMetrics
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EffectivenessService:
    """
    效果评估服务

    评估帮扶工作的效果
    """

    def __init__(self):
        self.evaluation_cache = {}

    def evaluate_village_effectiveness(self, village_id: int) -> EffectivenessMetrics:
        """
        评估村庄帮扶效果

        Args:
            village_id: 村庄ID

        Returns:
            EffectivenessMetrics: 效果评估指标
        """
        # 模拟评估逻辑
        return EffectivenessMetrics(
            income_growth_rate=0.15,
            project_completion_rate=0.85,
            fund_usage_rate=0.90,
            satisfaction_score=4.2,
            overall_score=0.82,
        )

    def evaluate_project_effectiveness(self, project_id: int) -> EffectivenessMetrics:
        """
        评估项目效果

        Args:
            project_id: 项目ID

        Returns:
            EffectivenessMetrics: 效果评估指标
        """
        return EffectivenessMetrics(
            income_growth_rate=0.12,
            project_completion_rate=0.95,
            fund_usage_rate=0.88,
            satisfaction_score=4.5,
            overall_score=0.85,
        )

    def evaluate_fund_effectiveness(self, fund_id: int) -> EffectivenessMetrics:
        """
        评估资金使用效果

        Args:
            fund_id: 资金ID

        Returns:
            EffectivenessMetrics: 效果评估指标
        """
        return EffectivenessMetrics(
            income_growth_rate=0.10,
            project_completion_rate=0.80,
            fund_usage_rate=0.92,
            satisfaction_score=4.0,
            overall_score=0.78,
        )

    def get_effectiveness_trends(self, entity_id: int, entity_type: str) -> Dict[str, List[float]]:
        """
        获取效果趋势

        Args:
            entity_id: 实体ID
            entity_type: 实体类型

        Returns:
            Dict[str, List[float]]: 各项指标的趋势数据
        """
        return {
            "income_growth": [0.10, 0.12, 0.15, 0.14, 0.16],
            "completion_rate": [0.70, 0.75, 0.80, 0.85, 0.90],
            "satisfaction": [3.8, 4.0, 4.1, 4.2, 4.3],
        }

    def export_effectiveness_report(self, entity_id: int, format: str = "pdf") -> bytes:
        """
        导出效果评估报告

        Args:
            entity_id: 实体ID
            format: 导出格式 (pdf, excel, word)

        Returns:
            bytes: 报告文件内容
        """
        # 模拟生成报告
        return b"Mock report content"

    def compare_effectiveness_periods(
        self, entity_id: int, period1: str, period2: str, period3: str = None, period4: str = None
    ) -> Dict[str, Any]:
        """
        对比不同时期的效果

        Args:
            entity_id: 实体ID
            period1: 第一时期开始日期 (格式: YYYY-MM-DD) 或第一时期
            period2: 第一时期结束日期 (格式: YYYY-MM-DD) 或第二时期
            period3: 第二时期开始日期 (格式: YYYY-MM-DD)，可选
            period4: 第二时期结束日期 (格式: YYYY-MM-DD)，可选

        Returns:
            Dict[str, Any]: 对比结果
        """
        # 支持两种调用方式:
        # 1. compare_effectiveness_periods(entity_id, '2024-01', '2024-12')
        # 2. compare_effectiveness_periods(entity_id, '2024-01', '2024-06', '2024-07', '2024-12')
        if period3 is not None and period4 is not None:
            # 方式2: 4个日期参数
            return {
                "period1": f"{period1} to {period2}",
                "period2": f"{period3} to {period4}",
                "period1_metrics": EffectivenessMetrics(overall_score=0.75),
                "period2_metrics": EffectivenessMetrics(overall_score=0.82),
                "improvement": 0.07,
            }
        else:
            # 方式1: 2个时期参数
            return {
                "period1": period1,
                "period2": period2,
                "period1_metrics": EffectivenessMetrics(overall_score=0.75),
                "period2_metrics": EffectivenessMetrics(overall_score=0.82),
                "improvement": 0.07,
            }


def calculate_effectiveness_score(baseline: Dict[str, Any], current: Dict[str, Any]) -> float:
    """
    计算效果分数

    Args:
        baseline: 基线数据
        current: 当前数据

    Returns:
        float: 效果分数
    """
    return 0.80


def compare_effectiveness(
    baseline_metrics: List[Dict[str, Any]], current_metrics: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    对比效果

    Args:
        baseline_metrics: 基线指标列表
        current_metrics: 当前指标列表

    Returns:
        Dict[str, Any]: 对比结果
    """
    return {
        "improvement": 0.15,
        "regression": 0.05,
        "unchanged": 0.80,
    }


def generate_effectiveness_report(data: Dict[str, Any]) -> EffectivenessReport:
    """
    生成效果评估报告

    Args:
        data: 评估数据

    Returns:
        EffectivenessReport: 效果评估报告
    """
    return EffectivenessReport(
        entity_id=data.get("entity_id", 0),
        entity_type=data.get("entity_type", "village"),
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        metrics=EffectivenessMetrics(overall_score=0.80),
        recommendations=["继续加强帮扶力度", "优化资金使用效率"],
    )
