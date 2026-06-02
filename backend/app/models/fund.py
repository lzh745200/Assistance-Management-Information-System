"""
经费模型
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, BaseModel


class FundType(str, enum.Enum):
    """经费类型"""

    PROJECT = "project"
    OPERATION = "operation"
    EDUCATION = "education"
    INFRASTRUCTURE = "infrastructure"
    EMERGENCY = "emergency"
    OTHER = "other"


class FundSource(str, enum.Enum):
    """经费来源"""

    MILITARY = "military"
    GOVERNMENT = "government"
    DONATION = "donation"
    ENTERPRISE = "enterprise"
    OTHER = "other"


class FundStatus(str, enum.Enum):
    """经费状态"""

    PENDING = "pending"
    PLANNED = "planned"
    APPROVED = "approved"
    ALLOCATED = "allocated"
    IN_USE = "in_use"
    COMPLETED = "completed"
    AUDITED = "audited"


class Fund(BaseModel):
    """经费记录模型"""

    __tablename__ = "funds"

    __table_args__ = (
        # 单列索引
        Index("ix_funds_status", "status"),
        Index("ix_funds_type", "type"),
        Index("ix_funds_fund_type", "fund_type"),
        Index("ix_funds_project_id", "project_id"),
        Index("ix_funds_village_id", "village_id"),
        Index("ix_funds_school_id", "school_id"),
        Index("ix_funds_date", "date"),
        Index("ix_funds_fund_source", "fund_source"),
        # 复合索引 - 优化常见查询组合
        Index("ix_funds_project_status", "project_id", "status"),  # 项目级别的资金过滤
        Index("ix_funds_village_status", "village_id", "status"),  # 村庄级别的资金过滤
        Index("ix_funds_status_date", "status", "date"),  # 按状态和日期查询
        Index("ix_funds_created_at", "created_at"),  # 按创建时间排序
        Index("ix_funds_status_type", "status", "fund_type"),  # 按状态和类型组合查询
    )

    date = Column(Date, nullable=True, comment="日期")
    type = Column(String(50), nullable=True, comment="经费类型")
    fund_type = Column(String(50), nullable=True, comment="经费类型(详细)")
    fund_source = Column(String(50), nullable=True, comment="经费来源")
    amount = Column(Numeric(15, 2), default=0, comment="金额")
    planned_amount = Column(Numeric(15, 2), default=0, comment="计划金额")
    approved_amount = Column(Numeric(15, 2), nullable=True, comment="批准金额")
    allocated_amount = Column(Numeric(15, 2), default=0, comment="拨付金额")
    used_amount = Column(Numeric(15, 2), default=0, comment="使用金额")
    remaining_amount = Column(Numeric(15, 2), default=0, comment="剩余金额")
    code = Column(String(50), nullable=True, comment="编号")
    name = Column(String(200), nullable=True, comment="名称")
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        comment="项目ID",
    )
    project_name = Column(String(200), nullable=True, comment="项目名称")
    village_id = Column(
        Integer,
        ForeignKey("supported_villages.id", ondelete="CASCADE"),
        nullable=True,
        comment="帮扶村ID",
    )
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
        comment="学校ID",
    )
    purpose = Column(Text, nullable=True, comment="用途")
    source = Column(String(200), nullable=True, comment="来源")
    operator = Column(String(100), nullable=True, comment="经办人")
    status = Column(String(50), default=FundStatus.PENDING.value, comment="状态")
    applicant = Column(String(100), nullable=True, comment="申请人")
    application_date = Column(DateTime(timezone=True), nullable=True, comment="申请日期")
    approved_by = Column(String(100), nullable=True, comment="审批人")
    approval_date = Column(DateTime(timezone=True), nullable=True, comment="审批日期")
    allocation_date = Column(DateTime(timezone=True), nullable=True, comment="拨付日期")
    allocation_method = Column(String(50), nullable=True, comment="拨付方式")
    receiver = Column(String(100), nullable=True, comment="接收人")
    usage_description = Column(Text, nullable=True, comment="使用说明")
    start_date = Column(DateTime(timezone=True), nullable=True, comment="开始日期")
    end_date = Column(DateTime(timezone=True), nullable=True, comment="结束日期")
    audit_date = Column(DateTime(timezone=True), nullable=True, comment="审计日期")
    audit_result = Column(String(50), nullable=True, comment="审计结果")
    audit_opinion = Column(Text, nullable=True, comment="审计意见")
    remarks = Column(Text, nullable=True, comment="备注")

    # 生命周期扩展字段
    lifecycle_phase = Column(Integer, default=1, comment="当前生命周期阶段(1-7)")
    budget_locked = Column(Boolean, default=False, comment="预算是否已锁定")
    deviation_rate = Column(Numeric(5, 2), default=0, comment="支出偏差率(%)")
    health_score = Column(Integer, default=100, comment="资金健康度(0-100)")
    has_anomaly = Column(Boolean, default=False, comment="是否存在未解决异常")
    settlement_status = Column(String(20), nullable=True, comment="决算状态")

    # 预算版本管理字段
    budget_version = Column(Integer, default=1, comment="预算版本号")
    budget_status = Column(String(20), default="draft", comment="预算状态: draft/submitted/approved")

    # 数据权限字段
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属组织ID",
    )
    created_by = Column(Integer, nullable=True, index=True, comment="创建者ID")

    project = relationship("Project", back_populates="funds", foreign_keys=[project_id])
    village = relationship("SupportedVillage", back_populates="funds", foreign_keys=[village_id])
    organization = relationship("Organization", back_populates="funds", foreign_keys=[organization_id])

    def __repr__(self):
        return f"<Fund(id={self.id}, name={self.name}, amount={self.amount})>"


class FundAttachment(Base):
    """经费附件"""

    __tablename__ = "fund_attachments"

    __table_args__ = (
        Index("ix_fund_attachments_fund_id", "fund_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_id = Column(
        Integer,
        ForeignKey("funds.id", ondelete="CASCADE"),
        nullable=False,
        comment="经费记录ID",
    )
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="存储路径")
    file_size = Column(Integer, default=0, comment="文件大小(字节)")
    file_type = Column(String(50), comment="文件MIME类型")
    category = Column(
        String(50),
        default="other",
        comment="附件分类: contract/invoice/receipt/report/other",
    )
    description = Column(String(500), comment="文件说明")
    uploaded_by = Column(String(50), comment="上传人")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="上传时间")

    def to_dict(self):
        return {
            "id": self.id,
            "fund_id": self.fund_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "category": self.category or "other",
            "description": self.description,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BudgetRecord(Base):
    """预算记录"""

    __tablename__ = "budget_records"

    __table_args__ = (
        Index("ix_budget_records_year", "year"),
        Index("ix_budget_records_category", "category"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, comment="年度")
    category = Column(String(100), nullable=False, comment="预算类别")
    budget_amount = Column(Numeric(15, 2), default=0, comment="预算金额(万元)")
    used_amount = Column(Numeric(15, 2), default=0, comment="已使用金额(万元)")
    remaining_reason = Column(Text, nullable=True, comment="结余原因")
    remarks = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "year": self.year,
            "category": self.category,
            "budget_amount": float(self.budget_amount or 0),
            "used_amount": float(self.used_amount or 0),
            "remaining": float((self.budget_amount or 0) - (self.used_amount or 0)),
            "remaining_reason": self.remaining_reason,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
