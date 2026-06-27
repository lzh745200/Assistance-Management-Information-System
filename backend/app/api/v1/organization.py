"""
组织管理API
支持部门单位和帮扶单位的层级管理
与权限管理集成：组织创建、修改需要管理员权限
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from ...core.cache import cache_manager
from ...core.database import get_db
from ...core.logging import logger
from ...core.permission_utils import is_superuser
from ...core.security import get_current_user
from ...models.organization import Organization, OrganizationLevel, OrganizationType
from ...services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["组织管理"])


# ==================== Pydantic模型 ====================


class OrganizationBase(BaseModel):
    name: str
    code: Optional[str] = None
    org_type: Optional[str] = None  # department 或 support_unit
    level: Optional[str] = None
    parent_id: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    description: Optional[str] = None
    sort_order: int = 0


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    org_type: Optional[str] = None
    level: Optional[str] = None
    parent_id: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class OrganizationSortItem(BaseModel):
    """组织排序项"""

    id: int
    sort_order: int


class BatchUpdateSortRequest(BaseModel):
    """批量更新排序请求"""

    items: List[OrganizationSortItem]


class OrganizationResponse(OrganizationBase):
    id: int
    level: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationTreeNode(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    org_type: Optional[str] = None
    level: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool
    children: List["OrganizationTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    """分页响应"""

    items: List[OrganizationResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# ==================== API端点 ====================


@router.get("", response_model=OrganizationListResponse)
async def get_organizations(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
    org_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    keyword: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    response: Response = None,
):
    """获取组织列表（分页）"""
    # 无过滤条件的默认列表请求使用缓存（5分钟）
    _cache_key = "orgs:list"
    if not any([org_type, parent_id, is_active, keyword, search]) and page == 1 and page_size == 20:
        cached = await cache_manager.get(_cache_key)
        if cached is not None:
            return cached
    try:
        query = db.query(Organization)

        if org_type:
            query = query.filter(Organization.org_type == org_type)
        if parent_id is not None:
            query = query.filter(Organization.parent_id == parent_id)
        # is_active 参数说明：
        # - 不传递或传递 null：返回所有组织（包括已停用的）
        # - 传递 true：只返回活跃组织
        # - 传递 false：只返回已停用的组织
        if is_active is not None:
            query = query.filter(Organization.is_active == is_active)
        # 兼容前端参数名: keyword 或 search
        search_term = keyword or search
        if search_term:
            # 转义 SQL LIKE 通配符以防止注入
            escaped_term = search_term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            # 使用 like() 方法配合 escape 参数
            query = query.filter(
                (Organization.name.like(f"%{escaped_term}%", escape="\\"))
                | (Organization.code.like(f"%{escaped_term}%", escape="\\"))
            )

        total = query.count()
        items = (
            query.order_by(Organization.sort_order, Organization.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        result = {"items": items, "total": total, "page": page, "page_size": page_size}
        # 仅对默认无过滤请求写缓存
        if not any([org_type, parent_id, is_active, keyword, search]) and page == 1 and page_size == 20:
            await cache_manager.set(_cache_key, result, ttl=300)
        return result
    except Exception as e:
        logger.error(f"获取组织列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取组织列表失败: {str(e)}")


def _set_no_cache_headers(response: Response):
    """设置无缓存响应头"""
    if response:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"


def _org_level_to_number(org: Organization) -> int:
    """将组织 level 枚举值转为数字"""
    if not org.level:
        return 0
    level_str = str(org.level)
    if not level_str.startswith("level_"):
        return 0
    try:
        return int(level_str.split("_")[1])
    except (ValueError, IndexError):
        return 0


def _org_to_tree_node(org: Organization, org_dict: dict) -> dict:
    """将组织对象转为树节点字典"""
    path = _build_org_path(org.id, org_dict)
    return {
        "id": str(org.id),
        "name": org.name,
        "code": org.code or "",
        "org_type": str(org.org_type) if org.org_type else None,
        "level": _org_level_to_number(org),
        "parent_id": str(org.parent_id) if org.parent_id is not None else None,
        "is_active": org.is_active,
        "path": path,
        "description": org.description or "",
        "contact_person": org.contact_person or "",
        "contact_phone": org.contact_phone or "",
        "address": org.address or "",
        "created_at": org.created_at.isoformat() if org.created_at else None,
        "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        "children": [],
    }


def _build_org_path(org_id: int, org_dict: dict, visited: set = None) -> str:
    """构建组织路径（避免循环）"""
    if visited is None:
        visited = set()
    if org_id in visited:
        return ""
    visited.add(org_id)
    org = org_dict.get(org_id)
    if not org:
        return ""
    if not org.parent_id or org.parent_id not in org_dict:
        return f"/{org.name}"
    parent_path = _build_org_path(org.parent_id, org_dict, visited)
    return f"{parent_path}/{org.name}" if parent_path else f"/{org.name}"


def _build_org_tree(organizations: list, org_map: dict) -> list:
    """将扁平的节点字典构建为树形结构"""
    tree = []
    for org in organizations:
        node = org_map[org.id]
        if org.parent_id and org.parent_id in org_map:
            org_map[org.parent_id]["children"].append(node)
        else:
            tree.append(node)
    return tree


@router.get("/tree")
async def get_organization_tree(
    org_type: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    response: Response = None,
):
    """获取组织树形结构"""
    _set_no_cache_headers(response)
    try:
        query = db.query(Organization).filter(Organization.is_active == True)  # noqa: E712

        if org_type:
            query = query.filter(Organization.org_type == org_type)

        organizations = query.order_by(Organization.sort_order, Organization.id).all()
        org_dict = {org.id: org for org in organizations}

        org_map = {}
        for org in organizations:
            org_map[org.id] = _org_to_tree_node(org, org_dict)

        tree = _build_org_tree(organizations, org_map)
        return tree
    except Exception as e:
        logger.error(f"获取组织树失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取组织树失败: {str(e)}")


@router.get("/my-organization", response_model=OrganizationResponse)
async def get_my_organization(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户所属组织"""
    try:
        # 优先返回用户关联的组织
        if hasattr(current_user, "organization_id") and current_user.organization_id:
            org = (
                db.query(Organization)
                .filter(
                    Organization.id == current_user.organization_id,
                    Organization.is_active == True,  # noqa: E712
                )
                .first()
            )
            if org:
                return org

        # 如果用户没有关联组织,返回第一个激活的组织
        org = (
            db.query(Organization)
            .filter(Organization.is_active == True)  # noqa: E712
            .order_by(Organization.id)
            .first()
        )

        if not org:
            raise HTTPException(status_code=404, detail="未找到组织信息")

        return org
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户组织失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取当前用户组织失败: {str(e)}")


@router.get("/my", response_model=OrganizationResponse)
async def get_my_organization_alias(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户所属组织（/my 别名，兼容前端调用）"""
    return await get_my_organization(current_user, db)


@router.get("/subordinates", response_model=List[OrganizationResponse])
async def get_subordinates(
    include_self: bool = Query(False, description="是否包含自身"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取下级组织列表"""
    try:
        query = db.query(Organization).filter(Organization.is_active == True)  # noqa: E712
        if not include_self:
            query = query.filter(Organization.parent_id.isnot(None))
        return query.order_by(Organization.sort_order, Organization.id).all()
    except Exception as e:
        logger.error(f"获取下级组织失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取下级组织失败: {str(e)}")


@router.get("/types/options")
async def get_type_options():
    """获取组织类型选项"""
    return {
        "types": [
            {"value": "department", "label": "部门单位"},
            {"value": "support_unit", "label": "帮扶单位"},
        ],
        "levels": [
            {"value": "level_1", "label": "一级单位"},
            {"value": "level_2", "label": "二级单位"},
            {"value": "level_3", "label": "三级单位"},
            {"value": "level_4", "label": "四级单位"},
        ],
    }


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取组织详情"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    return org


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    data: OrganizationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建组织"""
    # 权限检查：仅管理员可创建组织
    if getattr(current_user, "role", None) not in (
        "admin",
        "super_admin",
    ) and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    # 检查编码是否重复
    if data.code:
        existing = db.query(Organization).filter(Organization.code == data.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="组织编码已存在")

    # 转换枚举类型
    org_data = data.model_dump(exclude_defaults=False)
    if org_data.get("org_type"):
        org_data["org_type"] = OrganizationType(org_data["org_type"])
    if org_data.get("level"):
        org_data["level"] = OrganizationLevel(org_data["level"])

    # 确保 is_active 有值
    if "is_active" not in org_data:
        org_data["is_active"] = True

    org = Organization(**org_data)
    db.add(org)
    db.commit()
    db.refresh(org)
    await cache_manager.delete("orgs:list")
    return org


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: int,
    data: OrganizationUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新组织"""
    # 权限检查：仅管理员可更新组织
    if getattr(current_user, "role", None) not in (
        "admin",
        "super_admin",
    ) and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    # 检查编码是否重复
    if data.code:
        existing = db.query(Organization).filter(Organization.code == data.code, Organization.id != org_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="组织编码已存在")

    update_data = data.model_dump(exclude_unset=True)

    # 安全检查：禁止将 parent_id 设为自身（防止循环引用）
    if "parent_id" in update_data and update_data["parent_id"] == org_id:
        raise HTTPException(status_code=400, detail="不能将组织自身设为上级组织")

    # 转换枚举类型
    if "org_type" in update_data and update_data["org_type"]:
        update_data["org_type"] = OrganizationType(update_data["org_type"])
    if "level" in update_data and update_data["level"]:
        update_data["level"] = OrganizationLevel(update_data["level"])

    for key, value in update_data.items():
        setattr(org, key, value)

    db.commit()
    db.refresh(org)
    await cache_manager.delete("orgs:list")
    return org


@router.delete("/{org_id}")
async def delete_organization(
    org_id: int,
    force: bool = Query(False, description="保留参数，暂未使用"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    删除组织（逻辑删除：将 is_active 设为 False）

    Args:
        org_id: 组织ID
        force: 保留参数，暂未使用

    Returns:
        删除结果
    """

    # 权限检查：仅管理员可删除组织
    if getattr(current_user, "role", None) not in (
        "admin",
        "super_admin",
    ) and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    logger.info(f"=== 开始删除组织 === org_id={org_id}, user={current_user.id}")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        logger.error(f"组织不存在: org_id={org_id}")
        raise HTTPException(status_code=404, detail="组织不存在")

    logger.info(f"找到组织: id={org.id}, name={org.name}")

    # 检查是否有激活的子组织（软删除的子组织不阻止父级删除）
    children = db.query(Organization).filter(
        Organization.parent_id == org_id,
        Organization.is_active == True  # noqa: E712 — SQLAlchemy boolean filter
    ).count()
    if children > 0:
        logger.warning(f"组织有子组织: org_id={org_id}, children_count={children}")
        raise HTTPException(status_code=400, detail="该组织下有子组织，请先删除子组织")

    # 逻辑删除：将 is_active 设置为 False
    logger.info(f"执行逻辑删除: org_id={org_id}")
    org.is_active = False
    db.commit()
    logger.info(f"删除成功: org_id={org_id}")
    await cache_manager.delete("orgs:list")

    return {
        "message": "组织已删除",
        "type": "soft_delete",
    }


@router.get("/{org_id}/children", response_model=List[OrganizationResponse])
async def get_children(org_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取子组织"""
    return (
        db.query(Organization)
        .filter(Organization.parent_id == org_id)
        .order_by(Organization.sort_order, Organization.id)
        .all()
    )


@router.get("/{org_id}/ancestors", response_model=List[OrganizationResponse])
async def get_ancestors(org_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取祖先组织（沿父链逐级查询，避免全表加载）"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    # 沿父链逐级向上查询（组织层级通常≤5层，最多5次高效索引查询）
    ancestors = []
    visited: set = set()
    current_id = org.parent_id
    while current_id and current_id not in visited:
        visited.add(current_id)
        parent = db.query(Organization).filter(Organization.id == current_id).first()
        if not parent:
            break
        ancestors.append(parent)
        current_id = parent.parent_id

    return ancestors


class MoveOrganizationRequest(BaseModel):
    """移动组织请求体"""

    new_parent_id: Optional[int] = None


@router.post("/{org_id}/move")
async def move_organization(
    org_id: int,
    body: MoveOrganizationRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """移动组织到新的父级"""
    # 权限检查：仅管理员可移动组织
    if getattr(current_user, "role", None) not in (
        "admin",
        "super_admin",
    ) and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    new_parent_id = body.new_parent_id

    # 检查新父级是否存在
    if new_parent_id:
        new_parent = db.query(Organization).filter(Organization.id == new_parent_id).first()
        if not new_parent:
            raise HTTPException(status_code=404, detail="目标父组织不存在")

        # 检查是否会形成循环（沿父链逐级查询，避免全表加载）
        visited: set = set()
        check_id: Optional[int] = new_parent_id
        while check_id and check_id not in visited:
            if check_id == org_id:
                raise HTTPException(status_code=400, detail="不能将组织移动到其子组织下")
            visited.add(check_id)
            check_node = db.query(Organization).filter(Organization.id == check_id).first()
            check_id = check_node.parent_id if check_node else None

    org.parent_id = new_parent_id
    db.commit()
    await cache_manager.delete("orgs:list")
    return {"message": "移动成功"}


@router.post("/batch-update-sort")
async def batch_update_sort_orders(
    request: BatchUpdateSortRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量更新组织排序

    管理员接口，用于拖拽排序后批量更新排序号。

    Args:
        request: 批量更新请求，包含组织ID和排序号列表
    """
    # 权限检查：仅管理员可更新排序
    if getattr(current_user, "role", None) not in (
        "admin",
        "super_admin",
    ) and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    try:
        service = OrganizationService(db)

        # 转换为字典列表
        sort_list = [{"id": item.id, "sort_order": item.sort_order} for item in request.items]

        # 批量更新
        success, updated_count = service.batch_update_sort_orders(sort_list)

        if not success:
            raise HTTPException(status_code=500, detail="批量更新排序失败")

        await cache_manager.delete("orgs:list")
        return {
            "code": 200,
            "data": {"updated_count": updated_count},
            "message": f"成功更新 {updated_count} 个组织的排序",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新排序失败: {str(e)}")


@router.post("/{org_id}/activate", summary="激活组织")
async def activate_organization(
    org_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """激活指定组织（将 is_active 设为 True）"""
    if getattr(current_user, "role", None) not in (
        "admin",
        "super_admin",
    ) and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    org.is_active = True
    db.commit()
    await cache_manager.delete("orgs:list")
    return {"message": "组织已激活", "id": org_id, "is_active": True}


@router.post("/{org_id}/deactivate", summary="停用组织")
async def deactivate_organization(
    org_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """停用指定组织（将 is_active 设为 False）"""
    if getattr(current_user, "role", None) not in (
        "admin",
        "super_admin",
    ) and not is_superuser(current_user):
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    org.is_active = False
    db.commit()
    await cache_manager.delete("orgs:list")
    return {"message": "组织已停用", "id": org_id, "is_active": False}
