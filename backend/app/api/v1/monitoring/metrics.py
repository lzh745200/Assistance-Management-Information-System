"""
监控指标 API
提供业务指标查询和 Prometheus 格式导出
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.business_metrics_service import business_metrics_service

router = APIRouter(prefix="/metrics", tags=["监控指标"])


@router.get("/business")
async def get_business_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取业务指标
    - 资金审批成功率
    - 资金拨付率
    - 数据上报完成率
    - 用户活跃度
    - 系统错误率
    """
    return business_metrics_service.get_all_metrics()


@router.get("/prometheus")
async def get_prometheus_metrics():
    """
    获取 Prometheus 格式的指标
    用于 Grafana 等监控工具集成
    """
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(
        content=business_metrics_service.to_prometheus_format(), media_type="text/plain; charset=utf-8"
    )
