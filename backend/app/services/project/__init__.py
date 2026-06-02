"""
项目管理域 (Project Domain)

聚合根:
- Project: 帮扶项目
- ProjectMilestone: 项目里程碑
- ProjectDocument: 项目文档

领域服务:
- project_service.py: 项目核心服务
- project_monitoring_service.py: 项目监控
- project_evaluation_service.py: 项目评估
"""

# 注: project_monitoring_service 和 project_service 暂由顶层服务覆盖。
# 在阶段三创建独立的 project 子服务后添加导入。
from app.services.effectiveness_service import EffectivenessService  # noqa: E402

__all__ = [
    "EffectivenessService",
]
