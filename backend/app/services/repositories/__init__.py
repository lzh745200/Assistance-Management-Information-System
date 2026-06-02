"""Repository 数据访问层。

领域服务通过 Repository 访问数据库，不直接使用 ORM Session/Model。
"""
from .base import BaseRepository
from .fund_repository import FundRepository

__all__ = ["BaseRepository", "FundRepository"]
