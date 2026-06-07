"""智能报表摘要生成 — 离线模板引擎."""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def generate_village_summary(data: Dict[str, Any]) -> str:
    """生成帮扶村工作摘要."""
    total = data.get("total_villages", 0)
    pop = data.get("total_population", 0)
    funds = data.get("total_funds", 0)
    projects = data.get("total_projects", 0)
    completed = data.get("completed_projects", 0)
    growth = data.get("avg_income_growth", 0)

    if total == 0 and pop == 0:
        return "暂无帮扶村数据，请先录入基础信息。"

    parts = [f"共覆盖 {total} 个帮扶村，惠及 {pop:,} 人。"]
    if funds > 0:
        parts.append(f"累计投入帮扶资金 {funds/10000:.0f} 万元。")
    if projects > 0:
        rate = (completed / projects * 100) if projects > 0 else 0
        parts.append(f"实施帮扶项目 {projects} 个，已完成 {completed} 个（完成率 {rate:.0f}%）。")
    if growth:
        parts.append(f"村民人均收入同比增长 {growth:.1f}%。")
    return "".join(parts)


def generate_fund_summary(data: Dict[str, Any]) -> str:
    """生成经费使用摘要."""
    allocated = data.get("total_allocated", 0)
    used = data.get("total_used", 0)
    rate = data.get("utilization_rate", 0)
    anomalies = data.get("anomaly_count", 0)
    warnings = data.get("warning_count", 0)

    if allocated == 0:
        return "暂无经费数据。"

    parts = [
        f"经费总额 {allocated/10000:.0f} 万元，"
        f"已使用 {used/10000:.0f} 万元（使用率 {rate:.1f}%）。"
    ]
    if anomalies or warnings:
        parts.append(f"检测到 {anomalies} 个异常、{warnings} 个告警，建议及时处理。")
    else:
        parts.append("经费使用正常，无异常告警。")
    return "".join(parts)


def generate_project_summary(data: Dict[str, Any]) -> str:
    """生成项目进度摘要."""
    total = data.get("total", 0)
    in_progress = data.get("in_progress", 0)
    completed = data.get("completed", 0)
    overdue = data.get("overdue", 0)

    if total == 0:
        return "暂无项目数据。"

    parts = [f"共 {total} 个项目，进行中 {in_progress} 个，已完成 {completed} 个。"]
    if overdue > 0:
        parts.append(f"⚠️ {overdue} 个项目已延期，请关注处理。")
    else:
        parts.append("所有项目进展正常。")
    return "".join(parts)


def fill_report_template(template: str, variables: Dict[str, str]) -> str:
    """填充报表模板中的变量（格式：{var_name}）."""
    result = template
    for key, value in variables.items():
        result = result.replace("{" + key + "}", str(value))
    return result
