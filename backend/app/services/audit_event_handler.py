"""
集中式审计事件处理 — 通过 SQLAlchemy 事件自动记录所有写操作。

替代逐个端点手动调用 write_work_log() 的方案——一个事件监听器覆盖全部模型。
使用方法：应用启动时调用 setup_audit_events() 一次即可。

局限性：SQLAlchemy 事件无法访问 HTTP 请求上下文，因此审计记录中的 user_id
为 NULL。需要用户归因时，端点应额外调用 write_work_log()。
"""

import logging

from sqlalchemy import event

logger = logging.getLogger(__name__)


def _get_entity_name(instance) -> str:
    """从 ORM 实例提取可读名称。"""
    for attr in ("name", "title", "village_name", "project_name", "username", "full_name"):
        val = getattr(instance, attr, None)
        if val and isinstance(val, str):
            return str(val)
    return f"{type(instance).__name__}#{getattr(instance, 'id', '?')}"


def _get_entity_type(instance) -> str:
    """从 ORM 实例提取实体类型标识。"""
    cls_name = type(instance).__name__
    mapping = {
        "SupportedVillage": "village",
        "FundBudget": "fund_budget",
        "FundTransferVoucher": "voucher",
        "FundAllocationOrder": "allocation",
        "FundContract": "contract",
        "FundAnomaly": "anomaly",
        "ScholarshipStudent": "scholarship",
        "SchoolProject": "school_project",
        "ApprovalTask": "approval",
        "ApprovalWorkflow": "approval_workflow",
        "RbacRole": "role",
        "UserPermission": "permission",
        "UserRole": "user_role",
        "Organization": "org",
    }
    return mapping.get(cls_name, cls_name.lower())


def _write_audit_from_event(mapper, connection, target, action: str):
    """从 SQLAlchemy 事件写入审计日志。"""
    try:
        from datetime import date

        entity_type = _get_entity_type(target)
        entity_name = _get_entity_name(target)
        content = f"{action}: {entity_name}"

        connection.execute(
            mapper.local_table.metadata.tables["work_logs"].insert().values(
                category=entity_type,
                content=content,
                log_date=date.today(),
                user_id=None,  # 事件级审计无 HTTP 上下文——端点级 write_work_log() 可提供用户归因
            )
        )
    except Exception:
        logger.debug("审计日志写入失败 (non-critical): %s %s", action, type(target).__name__, exc_info=True)


def _after_insert(mapper, connection, target):
    _write_audit_from_event(mapper, connection, target, "create")


def _after_update(mapper, connection, target):
    _write_audit_from_event(mapper, connection, target, "update")


def _after_delete(mapper, connection, target):
    _write_audit_from_event(mapper, connection, target, "delete")


def setup_audit_events(models: list = None):
    """注册 SQLAlchemy 审计事件监听器——应用启动时调用一次。"""
    if models is None:
        from app.models.assessment import AssessmentRecord
        from app.models.fund import Fund
        from app.models.fund_allocation_order import FundAllocationOrder
        from app.models.fund_budget import FundBudget, FundTransaction
        from app.models.organization import Organization
        from app.models.policy import Policy, PolicyCategory
        from app.models.project import Project
        from app.models.school import ScholarshipStudent, School, SchoolProject
        from app.models.supported_village import SupportedVillage
        from app.models.todo import Todo
        from app.models.user import User
        from app.models.rbac import RbacRole, UserPermission, UserRole

        models = [
            AssessmentRecord, Fund, FundAllocationOrder, FundBudget, FundTransaction,
            Organization, Policy, PolicyCategory, Project, ScholarshipStudent,
            School, SchoolProject, SupportedVillage, Todo, User,
            RbacRole, UserPermission, UserRole,
        ]

    registered = 0
    for model in models:
        event.listen(model, "after_insert", _after_insert)
        event.listen(model, "after_update", _after_update)
        event.listen(model, "after_delete", _after_delete)
        registered += 1

    logger.info("审计事件监听已启用——%d 个模型", registered)
    return registered


def teardown_audit_events(models: list = None):
    """移除审计事件监听（测试环境使用）。"""
    if models is None:
        from app.models.fund import Fund
        from app.models.project import Project
        from app.models.school import School
        from app.models.supported_village import SupportedVillage
        from app.models.user import User
        from app.models.fund_budget import FundBudget
        from app.models.organization import Organization
        from app.models.policy import Policy
        from app.models.todo import Todo
        from app.models.rbac import RbacRole, UserPermission, UserRole

        models = [Fund, Project, School, SupportedVillage, User,
                  FundBudget, Organization, Policy, Todo,
                  RbacRole, UserPermission, UserRole]

    for model in models:
        event.remove(model, "after_insert", _after_insert)
        event.remove(model, "after_update", _after_update)
        event.remove(model, "after_delete", _after_delete)
