"""
报表导出API路由
提供报表导出和订阅管理接口
Feature: data - analytics - enhancement
Requirements: 19.3 - 19.5, 3.1, 3.5
"""
import io
import json
import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.supported_village import ReportSubscription
from app.schemas.supported_village import (
    DrillDownQuery,
    ExportQuery,
    ReportSubscriptionCreate,
    ReportSubscriptionResponse,
    ReportSubscriptionUpdate,
)
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["报表管理"])


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """获取报表服务实例"""
    return ReportService(db)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """获取分析服务实例"""
    return AnalyticsService(db)


# ==================== 报表导出接口 ====================


@router.post("/export/excel")
async def export_excel(
    query: ExportQuery, current_user=Depends(get_current_user), service: ReportService = Depends(get_report_service)
):
    """
    导出Excel报表

    Args:
        query: 导出查询参数
            - year: 导出年份
            - village_ids: 帮扶村ID列表（可选）
            - include_sections: 包含的数据板块

    Returns:
        Excel文件流
    """
    try:
        excel_bytes = service.export_to_excel(query)
        filename = service.get_export_filename(query)

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/export/pdf")
async def export_pdf(
    query: ExportQuery, current_user=Depends(get_current_user), service: ReportService = Depends(get_report_service)
):
    """
    导出PDF报表

    Args:
        query: 导出查询参数

    Returns:
        PDF文件流
    """
    try:
        # 强制设置格式为PDF
        query.format = "pdf"
        pdf_bytes = service.export_to_pdf(query)
        filename = service.get_export_filename(query)

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )
    except ImportError:
        raise HTTPException(status_code=501, detail="PDF导出功能未启用，请安装reportlab库")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/export/comprehensive/{year}")
async def export_comprehensive_report(
    year: int,
    village_ids: Optional[str] = Query(None, description="帮扶村ID列表，逗号分隔"),
    current_user=Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """
    导出综合报表

    Args:
        year: 报表年份
        village_ids: 帮扶村ID列表（逗号分隔）

    Returns:
        Excel文件流
    """
    try:
        ids = None
        if village_ids:
            ids = [int(id.strip()) for id in village_ids.split(",") if id.strip()]

        excel_bytes = service.export_comprehensive_report(year, ids)
        filename = f"帮扶村综合报表_{year}年_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 数据分析接口 ====================


@router.get("/analytics/filter-options")
async def get_filter_options(
    current_user=Depends(get_current_user), service: AnalyticsService = Depends(get_analytics_service)
):
    """获取所有可用的筛选选项"""
    try:
        return service.get_filter_options()
    except Exception as e:
        logger.error("获取筛选选项失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取筛选选项失败：{str(e)}")


@router.post("/analytics/filter")
async def filter_villages(
    filters: dict,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    多维度筛选帮扶村

    Args:
        filters: 筛选条件
        page: 页码
        page_size: 每页数量

    Returns:
        筛选结果
    """
    try:
        villages, total = service.filter_villages(filters, page, page_size)
        pages = (total + page_size - 1) // page_size

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
            "items": [
                {
                    "id": v.id,
                    "sequence_no": v.sequence_no,
                    "department": v.department,
                    "support_unit": v.support_unit,
                    "village_name": v.village_name,
                    "region_scope": v.region_scope,
                    "is_three_regions": v.is_three_regions,
                    "is_key_county": v.is_key_county,
                    "is_provincial_demo": v.is_provincial_demo,
                }
                for v in villages
            ],
        }
    except Exception as e:
        logger.error("帮扶村筛选查询失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.post("/analytics/drill-down")
async def drill_down(
    query: DrillDownQuery,
    current_user=Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    数据钻取查询

    Args:
        query: 钻取查询参数

    Returns:
        钻取结果
    """
    try:
        return service.drill_down(query)
    except Exception as e:
        logger.error("数据钻取查询失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.post("/analytics/compare-villages")
async def compare_villages(
    village_ids: List[int],
    year: int = Query(..., ge=2020, le=2030),
    metrics: Optional[List[str]] = None,
    current_user=Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    对比多个帮扶村的数据

    Args:
        village_ids: 帮扶村ID列表
        year: 对比年份
        metrics: 对比指标列表

    Returns:
        对比结果
    """
    try:
        return service.compare_villages(village_ids, year, metrics)
    except Exception as e:
        logger.error("帮扶村对比查询失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/analytics/compare-years/{village_id}")
async def compare_years(
    village_id: int,
    years: str = Query(..., description="年份列表，逗号分隔"),
    metrics: Optional[str] = Query(None, description="指标列表，逗号分隔"),
    current_user=Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    对比同一帮扶村不同年份的数据

    Args:
        village_id: 帮扶村ID
        years: 年份列表（逗号分隔）
        metrics: 指标列表（逗号分隔）

    Returns:
        对比结果
    """
    try:
        year_list = [int(y.strip()) for y in years.split(",") if y.strip()]
        metric_list = None
        if metrics:
            metric_list = [m.strip() for m in metrics.split(",") if m.strip()]

        return service.compare_years(village_id, year_list, metric_list)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数格式错误：{str(e)}")
    except Exception as e:
        logger.error("年份对比查询失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/analytics/summary")
async def get_summary_statistics(
    year: Optional[int] = Query(None, ge=2020, le=2030),
    department: Optional[str] = None,
    is_three_regions: Optional[bool] = None,
    is_key_county: Optional[bool] = None,
    current_user=Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """
    获取汇总统计数据

    Args:
        year: 统计年份
        department: 部门筛选
        is_three_regions: 三区三州筛选
        is_key_county: 重点帮扶县筛选

    Returns:
        汇总统计结果
    """
    try:
        filters = {}
        if department:
            filters["department"] = department
        if is_three_regions is not None:
            filters["is_three_regions"] = is_three_regions
        if is_key_county is not None:
            filters["is_key_county"] = is_key_county

        return service.get_summary_statistics(filters, year)
    except Exception as e:
        logger.error("汇总统计查询失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


# ==================== 报表订阅接口 ====================


@router.post("/subscriptions", response_model=ReportSubscriptionResponse)
async def create_subscription(
    subscription: ReportSubscriptionCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    创建报表订阅

    Args:
        subscription: 订阅配置

    Returns:
        创建的订阅信息
    """
    try:
        # 创建订阅记录
        db_subscription = ReportSubscription(
            user_id=current_user.id,
            name=subscription.name,
            report_type=subscription.report_type,
            format=subscription.format,
            year=subscription.year,
            village_ids=json.dumps(subscription.village_ids) if subscription.village_ids else None,
            include_sections=json.dumps(subscription.include_sections) if subscription.include_sections else None,
            frequency=subscription.frequency,
            send_day=subscription.send_day,
            send_time=subscription.send_time,
            email=subscription.email,
            output_dir=subscription.output_dir,
            output_format=subscription.output_format,
            is_active=True,
        )

        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)

        # 转换响应
        return _subscription_to_response(db_subscription)
    except Exception as e:
        logger.error("创建报表订阅失败: %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建订阅失败：{str(e)}")


@router.get("/subscriptions")
async def list_subscriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的报表订阅列表

    Args:
        page: 页码
        page_size: 每页数量
        is_active: 是否只显示启用的订阅

    Returns:
        订阅列表
    """
    try:
        query = db.query(ReportSubscription).filter(ReportSubscription.user_id == current_user.id)

        if is_active is not None:
            query = query.filter(ReportSubscription.is_active == is_active)

        total = query.count()
        subscriptions = (
            query.order_by(ReportSubscription.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        )

        pages = (total + page_size - 1) // page_size

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
            "items": [_subscription_to_response(s) for s in subscriptions],
        }
    except Exception as e:
        logger.error("获取订阅列表失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取订阅列表失败：{str(e)}")


@router.get("/subscriptions/{subscription_id}", response_model=ReportSubscriptionResponse)
async def get_subscription(subscription_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取订阅详情

    Args:
        subscription_id: 订阅ID

    Returns:
        订阅详情
    """
    try:
        subscription = (
            db.query(ReportSubscription)
            .filter(ReportSubscription.id == subscription_id, ReportSubscription.user_id == current_user.id)
            .first()
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        return _subscription_to_response(subscription)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取订阅详情失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取订阅失败：{str(e)}")


@router.put("/subscriptions/{subscription_id}", response_model=ReportSubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: ReportSubscriptionUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新订阅配置

    Args:
        subscription_id: 订阅ID
        update_data: 更新数据

    Returns:
        更新后的订阅信息
    """
    try:
        subscription = (
            db.query(ReportSubscription)
            .filter(ReportSubscription.id == subscription_id, ReportSubscription.user_id == current_user.id)
            .first()
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)

        # 处理JSON字段
        if "village_ids" in update_dict:
            update_dict["village_ids"] = json.dumps(update_dict["village_ids"]) if update_dict["village_ids"] else None
        if "include_sections" in update_dict:
            update_dict["include_sections"] = (
                json.dumps(update_dict["include_sections"]) if update_dict["include_sections"] else None
            )

        for key, value in update_dict.items():
            setattr(subscription, key, value)

        db.commit()
        db.refresh(subscription)

        return _subscription_to_response(subscription)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新订阅配置失败: %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新订阅失败：{str(e)}")


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    删除订阅

    Args:
        subscription_id: 订阅ID

    Returns:
        删除结果
    """
    try:
        subscription = (
            db.query(ReportSubscription)
            .filter(ReportSubscription.id == subscription_id, ReportSubscription.user_id == current_user.id)
            .first()
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        db.delete(subscription)
        db.commit()

        return {"message": "订阅已删除", "id": subscription_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除订阅失败: %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除订阅失败：{str(e)}")


@router.post("/subscriptions/{subscription_id}/toggle")
async def toggle_subscription(
    subscription_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    切换订阅启用状态

    Args:
        subscription_id: 订阅ID

    Returns:
        更新后的状态
    """
    try:
        subscription = (
            db.query(ReportSubscription)
            .filter(ReportSubscription.id == subscription_id, ReportSubscription.user_id == current_user.id)
            .first()
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        subscription.is_active = not subscription.is_active
        db.commit()

        return {
            "id": subscription_id,
            "is_active": subscription.is_active,
            "message": "订阅已启用" if subscription.is_active else "订阅已禁用",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("切换订阅状态失败: %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"切换订阅状态失败：{str(e)}")


def _subscription_to_response(subscription: ReportSubscription) -> dict:
    """将订阅模型转换为响应格式"""
    return {
        "id": subscription.id,
        "user_id": subscription.user_id,
        "name": subscription.name,
        "report_type": subscription.report_type,
        "format": subscription.format,
        "year": subscription.year,
        "village_ids": json.loads(subscription.village_ids) if subscription.village_ids else None,
        "include_sections": json.loads(subscription.include_sections) if subscription.include_sections else None,
        "frequency": subscription.frequency,
        "send_day": subscription.send_day,
        "send_time": subscription.send_time,
        "email": subscription.email,
        "output_dir": subscription.output_dir,
        "output_format": subscription.output_format,
        "is_active": subscription.is_active,
        "last_sent_at": subscription.last_sent_at,
        "next_send_at": subscription.next_send_at,
        "created_at": subscription.created_at,
        "updated_at": subscription.updated_at,
    }
