"""数据质量自动评分 — 字段完整度 + 合理性校验."""
import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

# 帮扶村必填/重要字段
VILLAGE_REQUIRED = [
    "village_name", "department", "support_unit", "province", "city",
]
VILLAGE_IMPORTANT = [
    "county", "longitude", "latitude", "population", "households",
]

# 经费关键字段
FUND_REQUIRED = ["name", "amount", "fund_type", "source"]
FUND_IMPORTANT = ["project_id", "village_id", "organization_id", "purpose"]


def score_village_data(village: Dict[str, Any]) -> Dict[str, Any]:
    """评分单个帮扶村数据（0-100）."""
    return _score_entity(village, VILLAGE_REQUIRED, VILLAGE_IMPORTANT)


def score_fund_data(fund: Dict[str, Any]) -> Dict[str, Any]:
    """评分单个经费数据."""
    return _score_entity(fund, FUND_REQUIRED, FUND_IMPORTANT)


def _score_entity(
    entity: Dict[str, Any],
    required: List[str],
    important: List[str],
) -> Dict[str, Any]:
    """通用实体评分."""
    missing = []
    score = 100

    for field in required:
        val = entity.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
            score -= 20

    for field in important:
        val = entity.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
            score -= 12

    score = max(0, min(100, score))
    level = get_quality_level(score)

    return {
        "score": score,
        "level": level,
        "missing_fields": missing,
    }


def get_quality_level(score: int) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 50:
        return "fair"
    if score >= 25:
        return "poor"
    return "critical"


def batch_score(
    items: List[Dict],
    score_fn: Callable,
) -> List[Dict]:
    """批量评分."""
    return [score_fn(item) for item in items]


def generate_quality_report(
    scored_results: List[Dict],
    entity_type: str,
) -> Dict[str, Any]:
    """生成质量报告摘要."""
    if not scored_results:
        return {"entity_type": entity_type, "total": 0, "average_score": 0, "distribution": {}}

    total = len(scored_results)
    avg = sum(r["score"] for r in scored_results) / total
    dist = {}
    for r in scored_results:
        level = r["level"]
        dist[level] = dist.get(level, 0) + 1

    return {
        "entity_type": entity_type,
        "total": total,
        "average_score": round(avg, 1),
        "distribution": dist,
        "worst_count": dist.get("critical", 0) + dist.get("poor", 0),
        "best_count": dist.get("excellent", 0) + dist.get("good", 0),
    }
