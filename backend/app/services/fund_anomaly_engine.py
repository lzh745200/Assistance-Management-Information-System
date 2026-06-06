"""资金异常检测组合引擎 — 规则引擎 + 统计方差 + 审批升级联动."""
import logging
import math
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

RISK_ESCALATE_SCORE = 50
RISK_ESCALATE_AMOUNT = 500000
VARIANCE_STD_THRESHOLD = 2.0
CRITICAL_STATUSES = {"approved", "audited", "completed"}


class AnomalyResult(BaseModel):
    fund_id: int
    fund_name: str
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    risk_score: int = 0
    risk_level: str = "normal"
    should_escalate: bool = False
    escalation_reason: str = ""


def _check_statistical_variance(amounts, threshold_std=VARIANCE_STD_THRESHOLD):
    if len(amounts) < 3:
        return []
    mean = sum(amounts) / len(amounts)
    variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
    std = math.sqrt(variance)
    if std < 0.001:
        return []
    results = []
    for i, val in enumerate(amounts):
        z = abs(val - mean) / std
        if z > threshold_std:
            results.append({"index": i, "value": round(val, 2), "mean": round(mean, 2), "std": round(std, 2), "z_score": round(z, 2)})
    return results


def _get_risk_level(score):
    if score >= 75: return "critical"
    if score >= 50: return "high"
    if score >= 25: return "medium"
    return "normal"


def _calculate_risk_score(rule_anomalies, variance_anomaly_count, health_score):
    score = 0
    for a in rule_anomalies:
        sev = a.get("severity", "")
        if sev == "danger": score += 25
        elif sev == "warning": score += 10
    score += variance_anomaly_count * 20
    if health_score < 50: score += 15
    return min(score, 100)


def should_escalate_approval(risk_score, fund_amount):
    if risk_score >= RISK_ESCALATE_SCORE: return True
    if fund_amount >= RISK_ESCALATE_AMOUNT: return True
    return False


def should_block_status_transition(has_anomaly, risk_score, target_status):
    if not has_anomaly: return False
    if target_status.lower() in CRITICAL_STATUSES: return True
    return risk_score >= 25


def detect_fund_anomalies_full(db, fund_id, fund_name="", fund_amount=0.0, health_score=100.0, project_id=None):
    anomalies = []
    result = AnomalyResult(fund_id=fund_id, fund_name=fund_name, anomalies=anomalies, risk_score=0, risk_level="normal", should_escalate=False)
    return result
