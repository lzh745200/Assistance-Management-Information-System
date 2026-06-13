"""异步导出服务 — 大文件后台导出 + 进度追踪."""
import logging
import uuid as _uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.export_task import ExportTask
from app.services.export_service import ExcelExportService

logger = logging.getLogger(__name__)

ASYNC_THRESHOLD = 5000  # 超过此记录数使用异步导出


class AsyncExportService:
    """异步导出服务：封装导出任务的创建、查询、下载."""

    def __init__(self, db: Session):
        self.db = db

    # ── 阈值判断 ──

    def should_use_async(self, entity_type: str, query_params: Dict) -> bool:
        count = self.estimate_record_count(entity_type, query_params)
        return count > ASYNC_THRESHOLD

    # ── 记录数估算 ──

    def estimate_record_count(self, entity_type: str, query_params: Dict) -> int:
        _ = query_params  # 未来可用于构建筛选条件
        models = {
            "supported_villages": ("app.models.supported_village", "SupportedVillage"),
            "supported_village": ("app.models.supported_village", "SupportedVillage"),
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
            return self.db.query(model).count()
        except Exception as e:
            logger.warning("estimate_record_count failed: %s", e)
            return 0

    # ── 同步导出 ──

    def export_supported_villages_sync(self, query_params: Dict) -> Tuple[bytes, str, int]:
        """同步导出帮扶村数据，返回 (content, filename, count)."""
        data = query_params.get("items", []) if query_params else []
        content = ExcelExportService().export_village_list(data)
        filename = f"帮扶村导出_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        count = len(data)
        return content, filename, count

    def export_report_sync(
        self, report_type: str, query_params: Dict
    ) -> Tuple[bytes, str, int]:
        """同步导出报表，返回 (content, filename, count)."""
        excel = ExcelExportService()
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        content = b""
        count = 0

        if report_type == "supported_villages":
            items = query_params.get("items", [])
            content = excel.export_village_list(items)
            count = len(items)
        elif report_type == "funds":
            items = query_params.get("items", [])
            content = excel.export_fund_list(items)
            count = len(items)
        elif report_type == "projects":
            items = query_params.get("items", [])
            content = excel.export_project_list(items)
            count = len(items)
        elif report_type == "schools":
            items = query_params.get("items", [])
            content = excel.export_school_list(items)
            count = len(items)
        elif report_type == "comprehensive":
            content = excel.export_comprehensive_report(
                query_params.get("summary", {}),
                query_params.get("village_data", []),
                query_params.get("project_data", []),
                query_params.get("fund_data", []),
            )
            count = len(query_params.get("village_data", []))
        else:
            items = query_params.get("items", [])
            content = excel.export_village_list(items)
            count = len(items)

        return content, filename, count

    # ── 异步导出 ──

    def export_supported_villages_async(
        self,
        user_id: int,
        query_params: Dict,
    ) -> ExportTask:
        """启动异步导出任务，返回 ExportTask 记录."""
        task_id = str(_uuid.uuid4())
        record_count = self.estimate_record_count("supported_villages", query_params)
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
        self.db.add(export_task)
        self.db.commit()
        self.db.refresh(export_task)
        return export_task

    # ── 任务查询 ──

    def get_export_task(self, task_id: str) -> Optional[ExportTask]:
        return self.db.query(ExportTask).filter(ExportTask.task_id == task_id).first()

    def get_export_file(self, task_id: str) -> Optional[Tuple[bytes, str]]:
        task = self.db.query(ExportTask).filter(ExportTask.task_id == task_id).first()
        if not task or not task.file_path:
            return None
        try:
            with open(task.file_path, "rb") as f:
                return f.read(), task.file_name
        except FileNotFoundError:
            return None

    def get_user_export_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[ExportTask], int]:
        q = self.db.query(ExportTask).filter(ExportTask.user_id == user_id)
        if status:
            q = q.filter(ExportTask.status == status)
        total = q.count()
        tasks = (
            q.order_by(ExportTask.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return tasks, total
