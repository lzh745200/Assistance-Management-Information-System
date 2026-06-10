"""数据库模型模块

使用显式导入替代动态 __import__，确保 PyInstaller 冻结环境能正确分析依赖。
"""

# flake8: noqa: E402

from .approval import (
    ApprovalNode,
    ApprovalRecord,
    ApprovalTask,
    ApprovalWorkflow,
)
from .annual_population import AnnualPopulation
from .annual_infrastructure import AnnualInfrastructure
from .annual_industry import AnnualIndustry
from .annual_income import AnnualIncome
import logging

logger = logging.getLogger(__name__)

# ---------- 年度数据 ----------

# ---------- 审批与消息 ----------

# ---------- 军队单位 ----------
from .army_unit import ArmyUnit  # noqa: E402

# ---------- 审计与监控 ----------
from .audit import (
    APIAccessLog,
    AuditLog,
    DataExportLog,  # noqa: E402
    LoginAttempt,
    SecurityEvent,
)
from .audit_change import AuditChange  # noqa: E402
from .base import (
    Base,
    BaseModel,
    SoftDeleteMixin,  # noqa: E402
    TimestampMixin,
    VersionMixin,
)

# ---------- 仪表盘 ----------
from .dashboard import DashboardActivity, HiddenDashboardActivity  # noqa: E402

# ---------- 成效评估 ----------
from .effectiveness import EffectivenessEvaluation, EffectivenessIndicator  # noqa: E402

# ---------- 数据与导入导出 ----------
from .data_package import DataPackage  # noqa: E402
from .data_report import DataReport  # noqa: E402
from .data_sync import DataConflict, DataSyncLog  # noqa: E402
from .data_version import DataVersion  # noqa: E402
from .export_task import ExportTask  # noqa: E402
from .fee_standard import FeeStandard  # noqa: E402
from .fund import BudgetRecord, Fund, FundAttachment  # noqa: E402
from .fund_allocation_order import (
    AllocationOrderItem,  # noqa: E402
    FundAllocationOrder,
)
from .fund_asset_verification import FundAssetVerification  # noqa: E402
from .fund_budget import FundBudget, FundTransaction  # noqa: E402
from .fund_history import (
    FundFieldChange,  # noqa: E402
    FundOperationLog,
    FundStatusHistory,
)
from .fund_lifecycle import (
    BudgetBaseline,
    BudgetVersion,  # noqa: E402
    FundAnomaly,
    FundContract,
    FundContractPayment,
    FundSettlement,
    FundTransferVoucher,
    ProjectFundPhase,
)
from .import_export_history import ImportExportHistory  # noqa: E402
from .import_history import ImportHistory  # noqa: E402
from .inspection_rule import InspectionRule  # noqa: E402
from .issue_tracking import Feedback, Issue, VersionHistory  # noqa: E402
from .machine_code import MachineCode  # noqa: E402
from .message import Message  # noqa: E402
from .message_template import MessageTemplate  # noqa: E402
from .notification_preference import NotificationPreference  # noqa: E402
from .organization import Organization  # noqa: E402
from .package_edit_log import PackageEditLog  # noqa: E402
from .package_version import PackageVersion  # noqa: E402
from .policy import Policy, PolicyCategory, PolicyFavorite  # noqa: E402
from .project import Project, ProjectFile, ProjectTask  # noqa: E402
from .project_milestone import ProjectChangeLog, ProjectMilestone  # noqa: E402
from .rbac import (
    AccessLog,
    RbacRole,
    ResourceAccessControl,  # noqa: E402
    RolePermission,
    UserPermission,
    UserRole,
)
from .report_template import ReportTemplate  # noqa: E402
from .role import BasicRole  # noqa: E402
from .rural_task import RuralTask  # noqa: E402
from .rural_work import RuralWork  # noqa: E402

from .school import (
    ScholarshipStudent,
    School,  # noqa: E402
    SchoolAttachment,
    SchoolProject,
    SchoolSupport,
)

# ---------- 业务模型 ----------
from .supported_village import (
    ConsumptionSupport,  # noqa: E402
    EducationSupport,
    EmploymentSupport,
    ForceInvestment,
    IndustrySupport,
    InfrastructureImprovement,
    MedicalSupport,
    PartyBuildingSupport,
    ReportSubscription,
    SupportedVillage,
    SupportFunding,
    VillageAttachment,
    VillageCommitteeInfo,
    VillageCommitteeMember,
    VillageIncome,
    VillagePopulation,
)

# ---------- 系统配置与更新日志 ----------
from .system_config import SystemConfig, SystemUpdateLog  # noqa: E402
from .system_monitor import SystemMonitor  # noqa: E402
from .todo import Todo  # noqa: E402

# ---------- 核心模型 ----------
from .user import User  # noqa: E402
from .user_session import UserSession  # noqa: E402
from .validation_rule import ValidationRule  # noqa: E402

# ---------- 辅助模型（直接导入，PyInstaller 打包需要） ----------
from .monitoring import AlertHistory, AlertRule, APIMetric  # noqa: E402
from .token_blacklist import TokenBlacklist  # noqa: E402
from .two_factor_auth import TwoFactorAuth  # noqa: E402
from .user_organization import UserOrganization  # noqa: E402
from .village import Industry, Village, Villager  # noqa: E402
from .industry import CactusFruitPlot, TeaPlantation  # noqa: E402
from .region import Region  # noqa: E402

# ---------- 工作日志 ----------
from .work_log import WorkLog  # noqa: E402

# EmailLog removed (offline system, no SMTP)


__all__ = [
    # base
    "Base",
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "VersionMixin",
    # 核心
    "User",
    "UserSession",
    "BasicRole",
    "RbacRole",
    "UserRole",
    "RolePermission",
    "UserPermission",
    "ResourceAccessControl",
    "AccessLog",
    "Organization",
    # 业务
    "SupportedVillage",
    "VillagePopulation",
    "VillageIncome",
    "ForceInvestment",
    "IndustrySupport",
    "InfrastructureImprovement",
    "PartyBuildingSupport",
    "MedicalSupport",
    "ConsumptionSupport",
    "EmploymentSupport",
    "EducationSupport",
    "SupportFunding",
    "ReportSubscription",
    "VillageAttachment",
    "VillageCommitteeInfo",
    "VillageCommitteeMember",
    "Village",
    "Villager",
    "Industry",
    "TeaPlantation",
    "CactusFruitPlot",
    "Region",
    "Project",
    "ProjectTask",
    "ProjectFile",
    "ProjectMilestone",
    "ProjectChangeLog",
    "Fund",
    "FundAttachment",
    "BudgetRecord",
    "FundBudget",
    "FundTransaction",
    "ProjectFundPhase",
    "BudgetBaseline",
    "FundTransferVoucher",
    "FundContract",
    "FundContractPayment",
    "FundAnomaly",
    "FundSettlement",
    "BudgetVersion",
    "FeeStandard",
    "FundAllocationOrder",
    "AllocationOrderItem",
    "InspectionRule",
    "FundAssetVerification",
    "FundStatusHistory",
    "FundFieldChange",
    "FundOperationLog",
    "Policy",
    "PolicyCategory",
    "PolicyFavorite",
    "School",
    "SchoolSupport",
    "SchoolAttachment",
    "SchoolProject",
    "ScholarshipStudent",
    "RuralWork",
    "RuralTask",
    "Issue",
    "VersionHistory",
    "Feedback",
    "Todo",
    # 审批与消息
    "ApprovalWorkflow",
    "ApprovalNode",
    "ApprovalTask",
    "ApprovalRecord",
    "Message",
    "MessageTemplate",
    "NotificationPreference",
    # 数据与导入导出
    "DataPackage",
    "PackageEditLog",
    "PackageVersion",
    "DataReport",
    "ExportTask",
    "ImportHistory",
    "ImportExportHistory",
    "MachineCode",
    # 审计与监控
    "AuditLog",
    "AuditChange",
    "SecurityEvent",
    "LoginAttempt",
    "APIAccessLog",
    "DataExportLog",
    "SystemMonitor",
    # 年度数据
    "AnnualIncome",
    "AnnualIndustry",
    "AnnualInfrastructure",
    "AnnualPopulation",
    # 军队单位
    "ArmyUnit",
    # 校验与模板
    "ValidationRule",
    "DataVersion",
    "ReportTemplate",
    # 工作日志
    "WorkLog",
    # 仪表盘
    "DashboardActivity",
    "HiddenDashboardActivity",
    # 成效评估
    "EffectivenessIndicator",
    "EffectivenessEvaluation",
    # 数据同步
    "DataSyncLog",
    "DataConflict",
    # 系统配置
    "SystemConfig",
    "SystemUpdateLog",
    # 辅助模型
    "APIMetric",
    "AlertHistory",
    "AlertRule",
    "TokenBlacklist",
    "TwoFactorAuth",
    "UserOrganization",
]
