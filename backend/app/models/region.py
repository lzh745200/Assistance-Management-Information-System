"""
行政区划模型

存储贵州省及下辖市州、县级行政区划数据。
"""

from sqlalchemy import Column, Float, Index, Integer, String, Text
from .base import Base, TimestampMixin


class Region(Base, TimestampMixin):
    """行政区划"""

    __tablename__ = "regions"

    __table_args__ = (
        Index("ix_regions_level", "level"),
        Index("ix_regions_parent_code", "parent_code"),
        Index("ix_regions_code", "code", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="区划名称")
    code = Column(String(20), nullable=False, unique=True, comment="行政区划编码")
    level = Column(String(20), nullable=False, comment="层级: province/prefecture/county")
    parent_code = Column(String(20), nullable=True, comment="上级区划编码")
    center_lng = Column(Float, nullable=True, comment="中心经度")
    center_lat = Column(Float, nullable=True, comment="中心纬度")
    geometry_text = Column(Text, nullable=True, comment="GeoJSON geometry")

    def __repr__(self):
        return f"<Region(code={self.code}, name={self.name}, level={self.level})>"

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "code": self.code,
            "level": self.level, "parent_code": self.parent_code,
            "center_lng": self.center_lng, "center_lat": self.center_lat,
        }
