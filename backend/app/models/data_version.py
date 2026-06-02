"""
DataVersion Model - 数据版本管理
在帮扶数据的 update 操作中，自动将修改前的完整记录快照写入此表
支持历史版本查看、对比和回滚
"""

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.models.base import Base


class DataVersion(Base):
    __tablename__ = "data_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 实体类型: supported_village / school / fund / project / rural_task
    entity_type = Column(String(50), nullable=False, index=True)
    # 实体ID
    entity_id = Column(Integer, nullable=False, index=True)
    # 版本号（自增）
    version_no = Column(Integer, nullable=False, default=1)
    # 快照（JSON 存储修改前的完整记录）
    snapshot = Column(Text, nullable=False)  # JSON string
    # 变更摘要（可选）
    change_summary = Column(String(500), nullable=True)
    # 修改人
    modified_by = Column(Integer, nullable=True)
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
