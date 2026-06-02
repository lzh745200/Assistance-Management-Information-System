"""
项目领域服务

处理跨聚合的业务逻辑
"""

from typing import List, Optional
from decimal import Decimal
from datetime import date

from app.services.domain import DomainService
from .project_aggregate import ProjectAggregate, ProjectStatus


class ProjectDomainService(DomainService):
    """项目领域服务"""

    def execute(self, *args, **kwargs):
        """执行领域服务"""

    def can_allocate_fund(self, project: ProjectAggregate, amount: Decimal) -> bool:
        """检查项目是否可以分配指定金额"""
        if project.status not in [ProjectStatus.APPROVED, ProjectStatus.IN_PROGRESS]:
            return False
        return project.budget_amount >= amount

    def calculate_project_progress(self, project: ProjectAggregate) -> dict:
        """计算项目进度"""
        milestones = project.milestones
        if not milestones:
            return {"overall_progress": 0.0, "completed_milestones": 0, "total_milestones": 0, "overdue_milestones": 0}

        completed = sum(1 for m in milestones if m.is_completed)
        overdue = len(project.get_overdue_milestones())

        return {
            "overall_progress": project.completion_rate * 100,
            "completed_milestones": completed,
            "total_milestones": len(milestones),
            "overdue_milestones": overdue,
        }

    def validate_project_timeline(
        self, planned_start: date, planned_end: date, milestones: List[dict]
    ) -> tuple[bool, Optional[str]]:
        """验证项目时间线是否有效"""
        if planned_end <= planned_start:
            return False, "计划结束时间必须晚于开始时间"

        for milestone in milestones:
            m_date = milestone.get("planned_date")
            if m_date:
                if m_date < planned_start or m_date > planned_end:
                    return False, f"里程碑 '{milestone.get('name')}' 的日期不在项目周期内"

        return True, None

    def check_project_health(self, project: ProjectAggregate) -> dict:
        """检查项目健康状态"""
        status = "healthy"
        issues = []

        if project.is_overdue:
            status = "at_risk"
            issues.append("项目已超期")

        overdue_milestones = project.get_overdue_milestones()
        if overdue_milestones:
            status = "at_risk" if status == "healthy" else "critical"
            issues.append(f"有 {len(overdue_milestones)} 个里程碑逾期")

        if project.completion_rate < 0.3 and project.is_overdue:
            status = "critical"
            issues.append("项目超期且进度严重滞后")

        return {"status": status, "issues": issues, "score": self._calculate_health_score(project)}

    def _calculate_health_score(self, project: ProjectAggregate) -> int:
        """计算健康分数 (0-100)"""
        score = 100

        if project.is_overdue:
            score -= 30

        overdue_count = len(project.get_overdue_milestones())
        score -= overdue_count * 10

        if project.status == ProjectStatus.PAUSED:
            score -= 20

        return max(0, score)
