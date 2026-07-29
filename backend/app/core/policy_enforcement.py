"""模块策略执行依赖

根据组织级模块策略拦截写操作（POST/PUT/DELETE），
对 read_only 或 disabled 模块返回 403。

用法：在需要管控的路由上添加依赖：
    dependencies=[Depends(check_module_write_policy("funds"))]
"""

import logging

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_active_user, get_db
from app.models.org_module_policy import OrgModulePolicy
from app.models.user import User

logger = logging.getLogger(__name__)


def check_module_write_policy(module_key: str):
    """生成模块写操作策略检查依赖

    Args:
        module_key: 模块标识（如 "funds", "projects", "map"）

    Returns:
        FastAPI 依赖函数
    """

    def _check(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        # 仅拦截写操作
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return

        # super_admin 不受策略限制
        if getattr(current_user, "is_superuser", False) or current_user.role == "super_admin":
            return

        org_id = current_user.organization_id
        if not org_id:
            return

        policy = db.query(OrgModulePolicy).filter(
            OrgModulePolicy.organization_id == org_id,
            OrgModulePolicy.module_key == module_key,
        ).first()

        if policy and policy.edit_mode in ("read_only", "disabled"):
            mode_label = "只读" if policy.edit_mode == "read_only" else "禁用"
            logger.info(
                "策略拦截: user=%s org=%s module=%s mode=%s method=%s",
                current_user.username, org_id, module_key, policy.edit_mode, request.method,
            )
            raise HTTPException(
                status_code=403,
                detail=f"该模块已被上级设为{mode_label}，禁止写操作",
            )

    return _check


def check_module_read_policy(module_key: str):
    """生成模块读操作策略检查依赖（disabled 模块连读也禁止）"""

    def _check(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if getattr(current_user, "is_superuser", False) or current_user.role == "super_admin":
            return

        org_id = current_user.organization_id
        if not org_id:
            return

        policy = db.query(OrgModulePolicy).filter(
            OrgModulePolicy.organization_id == org_id,
            OrgModulePolicy.module_key == module_key,
        ).first()

        if policy and policy.edit_mode == "disabled":
            raise HTTPException(
                status_code=403,
                detail="该模块已被上级禁用",
            )

    return _check
