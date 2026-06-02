"""
错误报告API
提供系统错误收集、上报、查询和统计功能
用于军队乡村振兴管理系统的运维监控
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/error-reports", tags=["错误报告"])


# ==================== Pydantic 模型 ====================

class ErrorReportCreate(BaseModel):
    """创建错误报告请求体"""
    source: str = Field(..., description="错误来源模块")
    error_type: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪信息")
    context: Optional[dict] = Field(None, description="上下文信息")
    severity: str = Field("warning", description="严重程度: info/warning/error/critical")


class ErrorReportResponse(BaseModel):
    """错误报告响应体"""
    id: int
    source: str
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    context: Optional[dict] = None
    severity: str
    status: str
    reporter: Optional[str] = None
    reported_at: str
    resolved_at: Optional[str] = None


class ErrorReportUpdate(BaseModel):
    """更新错误报告状态"""
    status: str = Field(..., description="状态: resolved/ignored/in_progress")
    resolution_note: Optional[str] = Field(None, description="处理备注")


# 内存中存储错误报告（生产环境应使用数据库表）
_error_reports: List[dict] = []
_error_id_counter = 0


# ==================== API 端点 ====================

@router.post("", summary="上报系统错误")
async def report_error(
    report: ErrorReportCreate,
    request: Request,
    current_user=Depends(get_current_user),
):
    """上报系统错误信息

    军队乡村振兴管理系统各模块发现异常时，可通过此接口上报错误信息，
    便于运维人员统一监控和处理系统故障。
    """
    global _error_id_counter
    _error_id_counter += 1

    error_record = {
        "id": _error_id_counter,
        "source": report.source,
        "error_type": report.error_type,
        "message": report.message,
        "stack_trace": report.stack_trace,
        "context": report.context,
        "severity": report.severity,
        "status": "open",
        "reporter": getattr(current_user, "username", "anonymous"),
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
        "resolution_note": None,
    }
    _error_reports.append(error_record)

    logger.warning(
        "错误报告 #%d [%s/%s]: %s (来源: %s)",
        _error_id_counter,
        report.severity,
        report.error_type,
        report.message,
        report.source,
    )

    return {
        "success": True,
        "message": "错误报告已提交，运维人员将尽快处理",
        "data": {"report_id": _error_id_counter},
    }


@router.get("", summary="获取错误报告列表")
async def list_error_reports(
    source: Optional[str] = Query(None, description="按来源筛选"),
    severity: Optional[str] = Query(None, description="按严重程度筛选"),
    status: Optional[str] = Query("open", description="按状态筛选: open/resolved/ignored/all"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=Depends(get_current_user),
):
    """获取错误报告列表

    支持按来源模块、严重程度和处理状态进行筛选。
    """
    filtered = _error_reports

    if source:
        filtered = [r for r in filtered if r["source"] == source]
    if severity:
        filtered = [r for r in filtered if r["severity"] == severity]
    if status and status != "all":
        filtered = [r for r in filtered if r["status"] == status]

    # 按时间倒序排列
    filtered.sort(key=lambda x: x["reported_at"], reverse=True)

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "success": True,
        "data": {
            "items": filtered[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/stats", summary="获取错误统计")
async def get_error_stats(current_user=Depends(get_current_user)):
    """获取错误报告统计数据

    按来源模块和严重程度统计错误数量和占比。
    """
    total = len(_error_reports)
    open_errors = len([r for r in _error_reports if r["status"] == "open"])
    critical_errors = len([r for r in _error_reports if r["severity"] == "critical"])

    # 按来源模块统计
    by_source = {}
    for r in _error_reports:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1

    # 按严重程度统计
    by_severity = {}
    for r in _error_reports:
        by_severity[r["severity"]] = by_severity.get(r["severity"], 0) + 1

    return {
        "success": True,
        "data": {
            "total": total,
            "open": open_errors,
            "critical": critical_errors,
            "by_source": by_source,
            "by_severity": by_severity,
        },
    }


@router.get("/{report_id}", summary="获取错误报告详情")
async def get_error_report(
    report_id: int,
    current_user=Depends(get_current_user),
):
    """获取指定错误报告的详细信息"""
    for r in _error_reports:
        if r["id"] == report_id:
            return {"success": True, "data": r}

    raise HTTPException(status_code=404, detail="错误报告不存在")


@router.put("/{report_id}", summary="更新错误报告状态")
async def update_error_report(
    report_id: int,
    update: ErrorReportUpdate,
    current_user=Depends(get_current_user),
):
    """更新错误报告处理状态

    运维人员可将错误标记为已解决、忽略或处理中。
    """
    for r in _error_reports:
        if r["id"] == report_id:
            r["status"] = update.status
            r["resolution_note"] = update.resolution_note
            if update.status == "resolved":
                r["resolved_at"] = datetime.now(timezone.utc).isoformat()
            return {
                "success": True,
                "message": f"错误报告 #{report_id} 状态已更新为 {update.status}",
            }

    raise HTTPException(status_code=404, detail="错误报告不存在")


@router.post("/report-exception", summary="报告当前异常")
async def report_current_exception(
    source: str = Query(..., description="异常来源模块"),
    message: str = Query(..., description="异常描述"),
    current_user=Depends(get_current_user),
):
    """简化版异常上报接口

    快捷上报运行时异常，用于前端快速反馈系统问题。
    """
    global _error_id_counter
    _error_id_counter += 1

    error_record = {
        "id": _error_id_counter,
        "source": source,
        "error_type": "runtime_exception",
        "message": message,
        "stack_trace": None,
        "context": None,
        "severity": "error",
        "status": "open",
        "reporter": getattr(current_user, "username", "anonymous"),
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
        "resolution_note": None,
    }
    _error_reports.append(error_record)

    logger.error("异常上报 #%d [%s]: %s", _error_id_counter, source, message)

    return {
        "success": True,
        "message": "异常已记录，感谢您的反馈",
        "data": {"report_id": _error_id_counter},
    }
