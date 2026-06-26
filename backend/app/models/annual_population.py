# coding: utf-8
from sqlalchemy import Column, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class AnnualPopulation(BaseModel):
    """年度人口数据"""

    __tablename__ = "annual_population"
    __table_args__ = (
        UniqueConstraint("supported_village_id", "year", name="uq_annual_population_year"),
        Index("ix_annual_population_village_id", "supported_village_id"),
        Index("ix_annual_pop_village_year", "supported_village_id", "year"),
        {"extend_existing": True},
    )

    supported_village_id = Column(
        Integer,
        ForeignKey("supported_villages.id", ondelete="CASCADE"),
        nullable=False,
        comment="帮扶村ID",
    )
    year = Column(Integer, nullable=False, comment="年份")

    households = Column(Integer, default=0, comment="户数")
    population = Column(Integer, default=0, comment="总人口")
    resident_population = Column(Integer, default=0, comment="常住人口")

    village = relationship("SupportedVillage")

    def __repr__(self):
        return f"<AnnualPopulation village_id={self.supported_village_id} year={self.year}>"
