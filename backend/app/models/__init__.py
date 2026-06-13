"""数据库模型模块 — 按需懒加载。

所有应用代码应使用 `from app.models.xxx import Y` 直接导入具体模型。
此模块仅导出基础类供 Alembic 和测试使用。
"""

from .base import Base, BaseModel, TimestampMixin, SoftDeleteMixin, VersionMixin

# ── 懒加载机制：支持 `from app.models import SomeModel` 但仅在访问时导入 ──
_MODULE_MAP = {
    # 基础
    "Base": ".base", "BaseModel": ".base", "TimestampMixin": ".base",
    "SoftDeleteMixin": ".base", "VersionMixin": ".base",
    # 核心
    "User": ".user", "UserSession": ".user_session",
    "BasicRole": ".role", "RbacRole": ".rbac", "UserRole": ".rbac",
    "RolePermission": ".rbac", "UserPermission": ".rbac",
    "ResourceAccessControl": ".rbac", "AccessLog": ".rbac",
    "Organization": ".organization",
    # 业务
    "SupportedVillage": ".supported_village", "VillagePopulation": ".supported_village",
    "VillageIncome": ".supported_village", "ForceInvestment": ".supported_village",
    "IndustrySupport": ".supported_village", "InfrastructureImprovement": ".supported_village",
    "PartyBuildingSupport": ".supported_village", "MedicalSupport": ".supported_village",
    "ConsumptionSupport": ".supported_village", "EmploymentSupport": ".supported_village",
    "EducationSupport": ".supported_village", "SupportFunding": ".supported_village",
    "ReportSubscription": ".supported_village", "VillageAttachment": ".supported_village",
    "VillageCommitteeInfo": ".supported_village", "VillageCommitteeMember": ".supported_village",
    "Village": ".village", "Villager": ".village", "Industry": ".village",
    "TeaPlantation": ".industry", "CactusFruitPlot": ".industry",
    "Region": ".region",
    "Project": ".project", "ProjectTask": ".project", "ProjectFile": ".project",
    "ProjectMilestone": ".project_milestone", "ProjectChangeLog": ".project_milestone",
    "Fund": ".fund", "FundAttachment": ".fund", "BudgetRecord": ".fund",
    "FundBudget": ".fund_budget", "FundTransaction": ".fund_budget",
    "ProjectFundPhase": ".fund_lifecycle", "BudgetBaseline": ".fund_lifecycle",
    "BudgetVersion": ".fund_lifecycle", "FundTransferVoucher": ".fund_lifecycle",
    "FundContract": ".fund_lifecycle", "FundContractPayment": ".fund_lifecycle",
    "FundAnomaly": ".fund_lifecycle", "FundSettlement": ".fund_lifecycle",
    "FeeStandard": ".fee_standard", "InspectionRule": ".inspection_rule",
    "FundAllocationOrder": ".fund_allocation_order", "AllocationOrderItem": ".fund_allocation_order",
    "FundAssetVerification": ".fund_asset_verification",
    "FundStatusHistory": ".fund_history", "FundFieldChange": ".fund_history",
    "FundOperationLog": ".fund_history",
    "Policy": ".policy", "PolicyCategory": ".policy", "PolicyFavorite": ".policy",
    "School": ".school", "SchoolSupport": ".school", "SchoolAttachment": ".school",
    "SchoolProject": ".school", "ScholarshipStudent": ".school",
    "RuralWork": ".rural_work", "RuralTask": ".rural_task",
    "Issue": ".issue_tracking", "VersionHistory": ".issue_tracking", "Feedback": ".issue_tracking",
    "Todo": ".todo",
    # 审批与消息
    "ApprovalWorkflow": ".approval", "ApprovalNode": ".approval",
    "ApprovalTask": ".approval", "ApprovalRecord": ".approval",
    "Message": ".message", "MessageTemplate": ".message_template",
    "NotificationPreference": ".notification_preference",
    # 数据与导入导出
    "DataPackage": ".data_package", "PackageEditLog": ".package_edit_log",
    "PackageVersion": ".package_version", "DataReport": ".data_report",
    "ExportTask": ".export_task", "ImportHistory": ".import_history",
    "ImportExportHistory": ".import_export_history", "MachineCode": ".machine_code",
    # 审计与监控
    "AuditLog": ".audit", "AuditChange": ".audit_change",
    "SecurityEvent": ".audit", "LoginAttempt": ".audit",
    "APIAccessLog": ".audit", "DataExportLog": ".audit",
    "SystemMonitor": ".system_monitor",
    # 年度数据
    "AnnualIncome": ".annual_income", "AnnualIndustry": ".annual_industry",
    "AnnualInfrastructure": ".annual_infrastructure", "AnnualPopulation": ".annual_population",
    # 其他
    "ArmyUnit": ".army_unit", "ValidationRule": ".validation_rule",
    "DataVersion": ".data_version", "ReportTemplate": ".report_template",
    "WorkLog": ".work_log", "DashboardActivity": ".dashboard",
    "HiddenDashboardActivity": ".dashboard",
    "EffectivenessIndicator": ".effectiveness", "EffectivenessEvaluation": ".effectiveness",
    "DataSyncLog": ".data_sync", "DataConflict": ".data_sync",
    "SystemConfig": ".system_config", "SystemUpdateLog": ".system_config",
    "APIMetric": ".monitoring", "AlertHistory": ".monitoring", "AlertRule": ".monitoring",
    "TokenBlacklist": ".token_blacklist", "TwoFactorAuth": ".two_factor_auth",
    "UserOrganization": ".user_organization",
}

import sys as _sys
_current_module = _sys.modules[__name__]

def __getattr__(name):
    if name in _MODULE_MAP:
        import importlib
        mod = importlib.import_module(_MODULE_MAP[name], __name__)
        attr = getattr(mod, name)
        # 缓存到模块字典避免重复延迟加载
        setattr(_current_module, name, attr)
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = list(_MODULE_MAP.keys())
