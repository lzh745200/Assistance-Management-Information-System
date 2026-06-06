"""字段级变更差异追踪 — 操作审计辅助."""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 字段中文标签映射
FIELD_LABELS = {
    "village_name": "帮扶村名称", "department": "部门单位", "support_unit": "帮扶单位",
    "province": "省", "city": "市", "county": "县区", "township": "乡镇",
    "longitude": "经度", "latitude": "纬度", "altitude": "海拔",
    "population": "人口", "households": "户数", "income": "收入",
    "name": "名称", "title": "标题", "description": "描述",
    "amount": "金额", "budget": "预算", "planned_amount": "计划金额",
    "approved_amount": "已批金额", "used_amount": "已用金额",
    "status": "状态", "priority": "优先级", "level": "级别",
    "fund_type": "经费类型", "category": "类别", "source": "来源",
    "purpose": "用途", "content": "内容", "summary": "摘要",
    "keywords": "关键词", "remarks": "备注", "honors": "表彰",
    "start_date": "开始日期", "end_date": "结束日期",
    "completed_at": "完成时间", "approved_at": "审批时间",
}


def compute_diff(
    old: Dict[str, Any],
    new: Dict[str, Any],
    skip_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """计算两个版本的字段差异.

    Returns:
        [{"field": str, "old": Any, "new": Any, "label": str}, ...]
    """
    skip = set(skip_fields or [])
    skip.update({"id", "created_at", "updated_at", "_sa_instance_state"})
    diff = []
    all_keys = set(old.keys()) | set(new.keys())
    for key in sorted(all_keys):
        if key in skip or key.startswith("_"):
            continue
        ov = old.get(key)
        nv = new.get(key)
        if ov != nv:
            diff.append({
                "field": key,
                "label": get_field_label(key),
                "old": ov,
                "new": nv,
            })
    return diff


def format_diff_for_display(diff: List[Dict]) -> str:
    """将差异列表格式化为可读的中文描述."""
    lines = []
    for d in diff:
        label = d.get("label", d["field"])
        old_val = _format_value(d["old"])
        new_val = _format_value(d["new"])
        if d["old"] is None:
            lines.append(f'新增 {label}: {new_val}')
        elif d["new"] is None:
            lines.append(f'删除 {label}: {old_val}')
        else:
            lines.append(f'{label}: {old_val} → {new_val}')
    return "; ".join(lines)


def get_field_label(field_name: str) -> str:
    """获取字段的中文标签."""
    return FIELD_LABELS.get(field_name, field_name)


def _format_value(val: Any) -> str:
    if val is None:
        return "(空)"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    if len(s) > 50:
        s = s[:47] + "..."
    return s
