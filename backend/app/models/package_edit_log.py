"""
数据包编辑日志模型
记录上级单位对下级上报数据的编辑历史
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class PackageEditLog(Base):
    """数据包编辑日志表"""

    __tablename__ = "package_edit_logs"

    __table_args__ = (
        Index("ix_package_edit_logs_package_id", "package_id"),
        Index("ix_package_edit_logs_edited_by", "edited_by"),
        Index("ix_package_edit_logs_edited_at", "edited_at"),
        Index("ix_package_edit_logs_data_type", "data_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(
        Integer,
        ForeignKey("data_packages.id", ondelete="CASCADE"),
        nullable=False,
        comment="数据包ID",
    )
    data_type = Column(String(50), nullable=False, comment="数据类型")
    record_id = Column(Integer, nullable=False, comment="记录ID")
    field_name = Column(String(100), nullable=False, comment="字段名称")
    old_value = Column(Text, comment="旧值")
    new_value = Column(Text, comment="新值")
    edit_reason = Column(Text, comment="编辑原因")
    edited_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        comment="编辑人ID",
    )
    edited_at = Column(DateTime(timezone=True), server_default=func.now(), comment="编辑时间")

    # 关系
    package = relationship("DataPackage", backref="edit_logs")
    editor = relationship("User", backref="package_edits")

    def __repr__(self):
        return f"<PackageEditLog(id={self.id}, package_id={self.package_id}, data_type='{self.data_type}')>"
