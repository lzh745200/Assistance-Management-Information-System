"""
模板服务（stub — 未接入路由）。

.. warning::
    本服务为占位实现，**尚未被任何路由调用**（项目中的模板下载功能由
    ``ExcelTemplateService`` / ``MessageTemplateService`` 等独立服务承担）。

    此前实现存在两个问题：
    1. **不持久化**：模板存储在进程内存字典 ``self._templates`` 中，应用重启
       后全部丢失；
    2. **渲染为空操作**：``render_template`` 仅 ``return str(template)``，
       返回字典的字符串表示而非渲染后的内容。

    完整实现（SQLite 持久化 + Jinja2 渲染）超出本次 BugFix 范围。为避免
    被误用为"已实现"，各方法显式抛出 :class:`NotImplementedError` 暴露问题。
    后续专项实现时应：
    - 使用 ``ReportTemplate`` 模型（已存在于 ``app.models.report_template``）持久化；
    - 使用 Jinja2（项目已有依赖）渲染模板内容。
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_NOT_IMPL_MSG = (
    "TemplateService.%s 尚未实现（模板持久化与渲染为占位 stub，未接入路由）。"
    "完整实现需 SQLite 持久化（ReportTemplate 模型）+ Jinja2 渲染，"
    "超出本次 BugFix 范围。"
)


class TemplateService:
    """模板服务（未实现）。

    此前使用内存字典存储模板且渲染为空操作，存在数据丢失与假可用风险。
    完整实现需持久化到数据库并使用 Jinja2 渲染。
    """

    def __init__(self):
        # 保留以兼容历史测试，但不再用于业务逻辑（CRUD 已标注 NotImplementedError）
        self._templates: Dict[str, Dict] = {}

    async def get_templates(self, template_type: str = None) -> List[Dict]:
        """获取模板列表（未实现 — 此前为内存字典，不持久化）。"""
        raise NotImplementedError(_NOT_IMPL_MSG % "get_templates")

    async def get_template(self, template_id: int) -> Optional[Dict]:
        """获取单个模板（未实现 — 此前为内存字典，不持久化）。"""
        raise NotImplementedError(_NOT_IMPL_MSG % "get_template")

    async def create_template(self, data: Dict) -> Dict:
        """创建模板（未实现 — 此前为内存字典，不持久化）。"""
        raise NotImplementedError(_NOT_IMPL_MSG % "create_template")

    async def update_template(self, template_id: int, data: Dict) -> Optional[Dict]:
        """更新模板（未实现 — 此前为内存字典，不持久化）。"""
        raise NotImplementedError(_NOT_IMPL_MSG % "update_template")

    async def delete_template(self, template_id: int) -> bool:
        """删除模板（未实现 — 此前为内存字典，不持久化）。"""
        raise NotImplementedError(_NOT_IMPL_MSG % "delete_template")

    async def render_template(self, template_id: int, data: Dict) -> Optional[str]:
        """渲染模板（未实现 — 此前仅 return str(template)，非真实渲染）。

        完整实现应使用 Jinja2（项目已有依赖）对模板内容进行渲染。
        """
        raise NotImplementedError(_NOT_IMPL_MSG % "render_template")


# 模块级单例
template_service = TemplateService()
