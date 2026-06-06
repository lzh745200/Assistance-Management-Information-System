"""导入冲突检测引擎 — 3 层冲突检测 + 自动裁决."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


def detect_id_conflicts(
    local: List[Dict],
    imported: List[Dict],
    id_field: str = "id",
) -> List[Dict[str, Any]]:
    """检测 ID 冲突：同一 ID 的实体字段差异."""
    local_by_id = {r.get(id_field): r for r in local if r.get(id_field) is not None}
    conflicts = []
    for imp in imported:
        imp_id = imp.get(id_field)
        if imp_id is None or imp_id not in local_by_id:
            continue
        local_rec = local_by_id[imp_id]
        diff = {}
        for key in set(list(local_rec.keys()) + list(imp.keys())):
            if key == id_field or key.startswith("_"):
                continue
            lv = local_rec.get(key)
            iv = imp.get(key)
            if lv != iv and not (lv is None and iv is None):
                diff[key] = {"local": lv, "imported": iv}
        if diff:
            conflicts.append({
                "type": "id_conflict",
                "id": imp_id,
                "diff_fields": diff,
                "local": local_rec,
                "imported": imp,
            })
    return conflicts


def detect_unique_key_conflicts(
    local: List[Dict],
    imported: List[Dict],
    keys: List[str],
) -> List[Dict[str, Any]]:
    """检测唯一键冲突（如 帮扶村名称+县区）."""
    local_set = {
        tuple(str(r.get(k, "")) for k in keys): r for r in local
    }
    conflicts = []
    for imp in imported:
        key_tuple = tuple(str(imp.get(k, "")) for k in keys)
        if key_tuple in local_set:
            conflicts.append({
                "type": "unique_key_conflict",
                "keys": dict(zip(keys, key_tuple)),
                "local": local_set[key_tuple],
                "imported": imp,
            })
    return conflicts


def detect_orphan_records(
    imported: List[Dict],
    fk_field: str,
    target_fk_set: Set[int],
) -> List[Dict[str, Any]]:
    """检测孤儿记录：外键在目标库中不存在."""
    orphans = []
    for imp in imported:
        fk_val = imp.get(fk_field)
        if fk_val is not None and fk_val not in target_fk_set:
            orphans.append({
                "type": "orphan",
                "record": imp,
                "fk_field": fk_field,
                "fk_value": fk_val,
            })
    return orphans


def resolve_by_timestamp(local: Dict, imported: Dict, ts_field: str = "updated_at") -> Dict:
    """时间戳优先裁决：默认取最新版本."""
    local_ts = _parse_ts(local.get(ts_field))
    import_ts = _parse_ts(imported.get(ts_field))
    if import_ts and (not local_ts or import_ts > local_ts):
        return {**local, **imported}
    return local


def _parse_ts(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
