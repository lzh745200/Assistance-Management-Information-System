"""
数据包同步增强 - 核心算法重构版

重构亮点：
1. 冲突检测：引入“值标准化”机制，彻底解决 DateTime/Decimal 导致的“假冲突”。
2. 预检导入：消灭全表主键加载，改用分块 (Chunk) IN 查询，防止 OOM。
3. 增量同步：废弃原生 SQL，改用 SQLAlchemy 2.0 Table 反射，修复 SQLite 时区比较坑。
4. 安全基线：保留 HMAC 恒定时间比较与严格的标识符白名单校验。
"""

import hashlib
import hmac
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import MetaData, Table, select, text, bindparam
from sqlalchemy.engine import Row

from app.models.base import Base
from app.core.database import engine

logger = logging.getLogger(__name__)

# ── SQL 标识符白名单（防注入） ──
_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

def _validate_identifier(name: str, context: str = "identifier") -> str:
    if not name or not _IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"非法的 {context}: {name!r}")
    return name

def _validate_table_name(table_name: str) -> str:
    name = _validate_identifier(table_name, "table_name")
    if name not in Base.metadata.tables:
        raise ValueError(f"表未注册或不允许访问: {name!r}")
    return name

def _get_table_object(table_name: str) -> Table:
    """获取 SQLAlchemy Table 对象，用于构建 2.0 风格的 Select"""
    _validate_table_name(table_name)
    return Base.metadata.tables[table_name]


# ══════════════════════════════════════════════════════════════
#  1. HMAC-SHA256 签名 (保持原有优秀设计)
# ══════════════════════════════════════════════════════════════

def sign_data_package(data: bytes, secret: str) -> str:
    """对数据包内容生成HMAC-SHA256签名"""
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    return hmac.new(secret, data, hashlib.sha256).hexdigest()

def verify_data_package(data: bytes, signature: str, secret: str) -> bool:
    """验证数据包HMAC签名（恒定时间比较，防时序攻击）"""
    expected = sign_data_package(data, secret)
    return hmac.compare_digest(expected, signature)


# ══════════════════════════════════════════════════════════════
#  2. 字段级冲突检测 (引入值标准化，消灭假冲突)
# ══════════════════════════════════════════════════════════════

@dataclass
class FieldConflict:
    """字段级冲突"""
    table: str
    record_id: Any
    field: str
    local_value: Any
    remote_value: Any
    resolution: str = "manual"  # manual | use_local | use_remote | merge

def _normalize_value(val: Any) -> Any:
    """
    标准化数据库值与 JSON 反序列化值，确保比较时类型一致。
    解决 DateTime、Decimal、布尔值在序列化前后的“假冲突”。
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        # 统一转为无时区的 UTC 字符串格式 (SQLite 默认存储格式)
        if val.tzinfo is not None:
            val = val.astimezone(timezone.utc).replace(tzinfo=None)
        return val.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, str):
        # 尝试将 ISO 格式的日期字符串标准化
        if "T" in val and ("Z" in val or "+" in val or "-" in val):
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                return dt.astimezone(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return val.strip()
    return val

class FieldLevelConflictDetector:
    """字段级冲突检测器"""

    def detect_conflicts(
        self,
        local_records: List[Dict],
        remote_records: List[Dict],
        table: str,
        key_field: str = "id",
        ignore_fields: Optional[Set[str]] = None,
    ) -> List[FieldConflict]:
        if ignore_fields is None:
            ignore_fields = {"updated_at", "synced_at", "version", "created_at"}

        conflicts = []
        local_index = {r[key_field]: r for r in local_records if key_field in r}
        remote_index = {r[key_field]: r for r in remote_records if key_field in r}
        common_keys = set(local_index.keys()) & set(remote_index.keys())

        for key in common_keys:
            local = local_index[key]
            remote = remote_index[key]
            all_fields = set(local.keys()) | set(remote.keys())
            
            for field_name in sorted(all_fields - ignore_fields):
                local_val = _normalize_value(local.get(field_name))
                remote_val = _normalize_value(remote.get(field_name))

                # 只有标准化后仍然不相等，才是真正的冲突
                if local_val != remote_val:
                    conflicts.append(FieldConflict(
                        table=table,
                        record_id=key,
                        field=field_name,
                        local_value=local.get(field_name), # 保留原始值用于展示
                        remote_value=remote.get(field_name),
                    ))
        return conflicts


# ══════════════════════════════════════════════════════════════
#  3. 导入预检 Dry Run (分块查询，防止 OOM)
# ══════════════════════════════════════════════════════════════

@dataclass
class ImportDryRunResult:
    total_rows: int = 0
    new_rows: int = 0
    update_rows: int = 0
    conflict_rows: int = 0
    error_rows: int = 0
    warnings: List[str] = field(default_factory=list)
    conflicts: List[FieldConflict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)

    @property
    def can_import(self) -> bool:
        return self.error_rows == 0

    def summary(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows, "new_rows": self.new_rows,
            "update_rows": self.update_rows, "conflict_rows": self.conflict_rows,
            "error_rows": self.error_rows, "warning_count": len(self.warnings),
            "conflict_count": len(self.conflicts),
        }

def dry_run_import(
    db_session,
    table_name: str,
    records: List[Dict],
    key_field: str = "id",
) -> ImportDryRunResult:
    """预检导入：使用分块 IN 查询，彻底避免大表 OOM"""
    table = _get_table_object(table_name)
    _validate_identifier(key_field, "key_field")
    
    result = ImportDryRunResult(total_rows=len(records))
    if not records:
        return result

    # 提取待检查的 ID 列表
    pending_ids = [r.get(key_field) for r in records if r.get(key_field) is not None]
    missing_pk_count = len(records) - len(pending_ids)
    if missing_pk_count > 0:
        result.warnings.append(f"有 {missing_pk_count} 行缺少主键 {key_field}")
        result.error_rows += missing_pk_count

    # 分块查询已存在的 ID (SQLite 默认 IN 限制为 999，这里用 500 确保安全)
    existing_ids = set()
    chunk_size = 500
    key_col = table.c[key_field]
    
    for i in range(0, len(pending_ids), chunk_size):
        chunk = pending_ids[i:i + chunk_size]
        try:
            stmt = select(key_col).where(key_col.in_(chunk))
            rows = db_session.execute(stmt).scalars().all()
            existing_ids.update(rows)
        except Exception as e:
            result.errors.append({"chunk": i, "error": f"查询表失败: {e}"})
            result.error_rows = result.total_rows
            return result

    # 统计新增与更新
    for record in records:
        rid = record.get(key_field)
        if rid is None:
            continue
        if rid in existing_ids:
            result.update_rows += 1
        else:
            result.new_rows += 1

    return result


# ══════════════════════════════════════════════════════════════
#  4. 增量同步 (SQLAlchemy 2.0 + 修复 SQLite 时区坑)
# ══════════════════════════════════════════════════════════════

def get_changed_records(
    db_session,
    table_name: str,
    since: datetime,
    key_field: str = "id",
    timestamp_field: str = "updated_at",
    limit: int = 5000,
    offset: int = 0,
) -> List[Dict]:
    """
    获取指定时间后的变更记录（增量同步）
    修复：统一时间格式为 SQLite 兼容的无时区 UTC 字符串。
    """
    table = _get_table_object(table_name)
    _validate_identifier(key_field, "key_field")
    _validate_identifier(timestamp_field, "timestamp_field")

    if since.tzinfo is not None:
        since = since.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        # 假设传入的是本地时间，转为 UTC
        local_tz = datetime.now(timezone.utc).astimezone().tzinfo
        if local_tz is not None:
            since = since.replace(tzinfo=local_tz).astimezone(timezone.utc).replace(tzinfo=None)
        
    # 统一格式化为 SQLite 标准格式: YYYY-MM-DD HH:MM:SS
    since_str = since.strftime("%Y-%m-%d %H:%M:%S")

    ts_col = table.c[timestamp_field]
    
    # 构建 SQLAlchemy 2.0 Select
    stmt = (
        select(table)
        .where(ts_col >= since_str)
        .order_by(ts_col.asc())
        .limit(limit)
        .offset(offset)
    )

    try:
        rows = db_session.execute(stmt).all()
        # SQLAlchemy 2.0 推荐使用 _mapping 将 Row 转为字典
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.error(f"增量查询失败 [{table_name}]: {e}")
        return []
