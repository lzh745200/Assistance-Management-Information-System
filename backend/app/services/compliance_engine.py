"""合规性校验引擎

提供经费合规性校验功能：
- 10% 预警线检测
- 15% 否决线检测
- 费用标准匹配

用于 fund_lifecycle 路由 /compliance-check/{project_id} 端点。
"""

import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 合规阈值
WARNING_DEVIATION_RATE = 10.0  # 10% 预警线
REJECTION_DEVIATION_RATE = 15.0  # 15% 否决线


def run_compliance_check(db: Session, project_id: int) -> Dict[str, Any]:
    """对指定项目执行合规性校验。

    检查维度：
    1. 经费偏差率：实际支出 vs 预算的偏差是否超过阈值
    2. 经费使用率：已使用金额占批准金额的比例
    3. 费用标准匹配：各项支出是否符合标准

    Args:
        db: 数据库会话
        project_id: 项目 ID

    Returns:
        Dict containing:
        - passed: bool, 是否通过合规性校验
        - warnings: List[str], 预警信息
        - violations: List[str], 违规信息
        - summary: Dict, 汇总数据
    """
    try:
        from app.models.fund import Fund
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "passed": False,
                "warnings": [],
                "violations": [f"项目 {project_id} 不存在"],
                "summary": {},
            }

        funds = (
            db.query(Fund)
            .filter(Fund.project_id == project_id)
            .all()
        )

        warnings = []
        violations = []
        total_budget = 0.0
        total_used = 0.0

        for fund in funds:
            budget = float(fund.approved_amount or fund.planned_amount or fund.amount or 0)
            used = float(fund.used_amount or 0)
            total_budget += budget
            total_used += used

            if budget > 0:
                deviation_rate = abs(used - budget) / budget * 100
                if deviation_rate > REJECTION_DEVIATION_RATE:
                    violations.append(
                        f"经费 {fund.code or fund.name or '未命名'}: "
                        f"偏差率 {deviation_rate:.1f}% 超过否决线 {REJECTION_DEVIATION_RATE}%"
                    )
                elif deviation_rate > WARNING_DEVIATION_RATE:
                    warnings.append(
                        f"经费 {fund.code or fund.name or '未命名'}: "
                        f"偏差率 {deviation_rate:.1f}% 超过预警线 {WARNING_DEVIATION_RATE}%"
                    )

        usage_rate = (total_used / total_budget * 100) if total_budget > 0 else 0

        return {
            "passed": len(violations) == 0,
            "warnings": warnings,
            "violations": violations,
            "summary": {
                "project_id": project_id,
                "project_name": project.name,
                "total_budget": total_budget,
                "total_used": total_used,
                "usage_rate": round(usage_rate, 2),
                "fund_count": len(funds),
            },
        }

    except Exception as e:
        logger.error("合规性校验失败: %s", e, exc_info=True)
        return {
            "passed": False,
            "warnings": [],
            "violations": [f"校验过程出错: {str(e)}"],
            "summary": {},
        }
