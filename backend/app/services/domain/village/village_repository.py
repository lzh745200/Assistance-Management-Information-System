"""
帮扶村仓储接口
"""

from typing import List, Optional
from app.services.domain import Repository
from .village_aggregate import VillageAggregate, VillageStatus


class VillageRepository(Repository[VillageAggregate]):
    """帮扶村仓储"""

    def get_by_id(self, id: str) -> Optional[VillageAggregate]:
        """根据ID获取帮扶村"""
        raise NotImplementedError()

    def save(self, aggregate: VillageAggregate) -> None:
        """保存帮扶村"""
        raise NotImplementedError()

    def delete(self, id: str) -> None:
        """删除帮扶村"""
        raise NotImplementedError()

    def get_by_location(
        self, province: Optional[str] = None, city: Optional[str] = None, county: Optional[str] = None
    ) -> List[VillageAggregate]:
        """根据位置查询帮扶村"""
        raise NotImplementedError()

    def get_by_status(self, status: VillageStatus) -> List[VillageAggregate]:
        """根据状态获取帮扶村列表"""
        raise NotImplementedError()

    def get_active_villages(self) -> List[VillageAggregate]:
        """获取帮扶中的村庄"""
        raise NotImplementedError()

    def search_by_name(self, keyword: str) -> List[VillageAggregate]:
        """按名称搜索"""
        raise NotImplementedError()
