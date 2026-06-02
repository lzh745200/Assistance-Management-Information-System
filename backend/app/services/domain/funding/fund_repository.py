"""
经费仓储接口
"""

from typing import Optional, List
from .fund_aggregate import FundAggregate


class FundRepository:
    """经费仓储"""

    def get_by_id(self, fund_id: str) -> Optional[FundAggregate]:
        """根据ID获取经费聚合"""
        raise NotImplementedError()

    def save(self, fund: FundAggregate) -> None:
        """保存经费聚合"""
        raise NotImplementedError()

    def delete(self, fund_id: str) -> None:
        """删除经费聚合"""
        raise NotImplementedError()

    def list_by_project(self, project_id: str) -> List[FundAggregate]:
        """获取项目的所有经费记录"""
        raise NotImplementedError()
