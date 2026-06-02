"""
数据包版本管理模型
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class PackageVersion(Base):
    """数据包版本管理"""

    __tablename__ = "package_versions"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(
        Integer,
        ForeignKey("data_packages.id", ondelete="CASCADE"),
        nullable=False,
        comment="数据包ID",
    )
    version = Column(String(20), nullable=False, comment="版本号")
    changes = Column(Text, comment="变更记录（JSON格式）")
    description = Column(Text, comment="版本说明")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建人ID",
    )

    # 关系
    package = relationship("DataPackage", backref="versions")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<PackageVersion(id={self.id}, package_id={self.package_id}, version='{self.version}')>"
