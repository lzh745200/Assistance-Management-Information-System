from sqlalchemy import Column, Integer, String, Text

from .base import Base, TimestampMixin


class ArmyUnit(Base, TimestampMixin):
    """军队单位模型"""

    __tablename__ = "army_units"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(100), nullable=False, index=True, comment="单位名称")
    unit_code = Column(String(50), unique=True, nullable=False, index=True, comment="单位编码")
    unit_level = Column(String(50), comment="单位级别")
    location = Column(String(200), comment="驻地")
    description = Column(Text, comment="描述")
    contact_person = Column(String(100), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")

    def __repr__(self):
        return f"<ArmyUnit(id={self.id}, name={self.unit_name})>"
