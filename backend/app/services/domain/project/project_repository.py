"""
项目仓储接口
"""

from typing import List, Optional
from app.services.domain import Repository
from .project_aggregate import ProjectAggregate, ProjectStatus


class ProjectRepository(Repository[ProjectAggregate]):
    """项目仓储"""

    def get_by_id(self, id: str) -> Optional[ProjectAggregate]:
        """根据ID获取项目"""
        raise NotImplementedError()

    def save(self, aggregate: ProjectAggregate) -> None:
        """保存项目"""
        raise NotImplementedError()

    def delete(self, id: str) -> None:
        """删除项目"""
        raise NotImplementedError()

    def get_by_village(self, village_id: str) -> List[ProjectAggregate]:
        """根据帮扶村ID获取项目列表"""
        raise NotImplementedError()

    def get_by_status(self, status: ProjectStatus) -> List[ProjectAggregate]:
        """根据状态获取项目列表"""
        raise NotImplementedError()

    def get_overdue_projects(self) -> List[ProjectAggregate]:
        """获取逾期的项目"""
        raise NotImplementedError()

    def get_active_projects(self) -> List[ProjectAggregate]:
        """获取进行中的项目"""
        raise NotImplementedError()
