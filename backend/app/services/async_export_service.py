"""异步导出服务 — 大文件后台导出 + 进度追踪."""
import logging
import uuid as _uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.export_task import ExportTask
from app.services.export_service import ExcelExportService

logger = logging.getLogger(__name__)

ASYNC_THRESHOLD = 5000  # 超过此记录数使用异步导出


class AsyncExportService:
    """异步导出服务：静态方法集，供 API 端点调用."""

    # ── 阈值判断 ──

    @staticmethod
    def should_use_async(entity_type: str, record_count: int) -> bool:
        return record_count > ASYNC_THRESHOLD

    # ── 记录数估算 ──

    @staticmethod
    def estimate_record_count(db: Session, entity_type: str, query_params: Dict) -> int:
        models = {
            "supported_villages": ("app.models.supported_village", "SupportedVillage"),
            "projects": ("app.models.project", "Project"),
            "funds": ("app.models.fund", "Fund"),
            "schools": ("app.models.school", "School"),
            "policies": ("app.models.policy", "Policy"),
        }
        if entity_type not in models:
            return 0
        module_path, model_name = models[entity_type]
        import importlib
        try:
            mod = importlib.import_module(module_path)
            model = getattr(mod, model_name)
            return db.query(model).count()
        except Exception as e:
            logger.warning("estimate_record_count failed: %s", e)
            return 0

    # ── 同步导出 ──

    @staticmethod
    def export_supported_villages_sync(data: List[Dict]) -> bytes:
        return ExcelExportService().export_village_list(data)

    @staticmethod
    def export_report_sync(report_type: str, query_params: Dict) -> bytes:
        excel = ExcelExportService()
        if report_type == "supported_villages":
            return excel.export_village_list(query_params.get("items", []))
        if report_type == "funds":
            return excel.export_fund_list(query_params.get("items", []))
        if report_type == "projects":
            return excel.export_project_list(query_params.get("items", []))
        if report_type == "schools":
            return excel.export_school_list(query_params.get("items", []))
        if report_type == "comprehensive":
            return excel.export_comprehensive_report(
                query_params.get("summary", {}),
                query_params.get("village_data", []),
                query_params.get("project_data", []),
                query_params.get("fund_data", []),
            )
        return excel.export_village_list(query_params.get("items", []))

    # ── 异步导出 ──

    @staticmethod
    def export_supported_villages_async(
        db: Session,
        user_id: int,
        query_params: Dict,
    ) -> ExportTask:
        """启动异步导出任务，返回 ExportTask 记录."""
        task_id = str(_uuid.uuid4())
        record_count = AsyncExportService.estimate_record_count(
            db, "supported_villages", query_params
        )
        export_task = ExportTask(
            user_id=user_id,
            task_id=task_id,
            export_type="supported_villages",
            query_params=query_params,
            file_name=f"帮扶村导出_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx",
            file_size=0,
            record_count=record_count,
            status="pending",
            expires_at=datetime.now() + timedelta(hours=24),
        )
        db.add(export_task)
        db.commit()
        db.refresh(export_task)
        return export_task

    # ── 任务查询 ──

    @staticmethod
    def get_export_task(db: Session, task_id: int) -> Optional[ExportTask]:
        return db.query(ExportTask).filter(ExportTask.id == task_id).first()

    @staticmethod
    def get_export_file(db: Session, task_id: int) -> Optional[bytes]:
        task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
        if not task or not task.file_path:
            return None
        try:
            with open(task.file_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None

    @staticmethod
    def get_user_export_tasks(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> List[ExportTask]:
        q = db.query(ExportTask).filter(ExportTask.user_id == user_id)
        if status:
            q = q.filter(ExportTask.status == status)
        return q.order_by(ExportTask.id.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
