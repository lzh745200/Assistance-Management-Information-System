"""统一提醒中心 API（单机：审批超时/项目截止/预算预警/备份/打包提醒聚合）"""
import logging

from fastapi import APIRouter, Depends

from app.core.response import success_response
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", summary="获取提醒列表（聚合视图）")
async def list_reminders(
    current_user=Depends(get_current_user),
):
    """提醒中心：审批超时/项目截止/预算预警等（按时间倒序）"""
    try:
        from app.services.reminder_orchestrator import list_reminders as _list

        reminders = _list(limit=100)
        unread = sum(1 for r in reminders if not r.get("is_read"))
        return success_response(data={"items": reminders, "total": len(reminders), "unread": unread})
    except Exception as e:
        logger.error("获取提醒失败: %s", e, exc_info=True)
        return success_response(data={"items": [], "total": 0, "unread": 0}, message="获取提醒失败")


@router.post("/scan", summary="手动触发一次提醒扫描")
async def trigger_scan(
    current_user=Depends(get_current_user),
):
    """立即执行一次提醒扫描（审批超时/项目截止/预算预警）——仅管理员"""
    from app.api.v1.deps import require_manager_role

    require_manager_role(current_user)
    try:
        from app.services.reminder_orchestrator import run_reminder_scans

        created = run_reminder_scans()
        return success_response(data={"created": len(created)}, message=f"扫描完成，新增 {len(created)} 条提醒")
    except Exception as e:
        logger.error("手动提醒扫描失败: %s", e, exc_info=True)
        return success_response(data={"created": 0}, message="扫描失败")
