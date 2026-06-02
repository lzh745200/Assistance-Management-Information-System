"""
数据包同步增强 - HMAC签名验证和冲突检测升级

在现有 data_sync_service.py 基础上添加:
- HMAC-SHA256 数据包签名/验证
- 字段级冲突检测（而非记录级）
- 导入预检 dry-run 模式
- 增量同步支持
"""

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  HMAC-SHA256 签名
# ══════════════════════════════════════════════════════════════

def sign_data_package(data: bytes, secret: str) -> str:
    """对数据包内容生成HMAC-SHA256签名"""
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    return hmac.new(secret, data, hashlib.sha256).hexdigest()


def verify_data_package(data: bytes, signature: str, secret: str) -> bool:
    """验证数据包HMAC签名（恒定时间比较）"""
    expected = sign_data_package(data, secret)
    return hmac.compare_digest(expected, signature)


# ══════════════════════════════════════════════════════════════
#  字段级冲突检测
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


class FieldLevelConflictDetector:
    """字段级冲突检测器 —— 比记录级更细粒度"""

    def detect_conflicts(
        self,
        local_records: List[Dict],
        remote_records: List[Dict],
        key_field: str = "id",
        ignore_fields: Optional[Set[str]] = None,
    ) -> List[FieldConflict]:
        """
        检测字段级冲突

        Args:
            local_records: 本地记录列表
            remote_records: 远程记录列表
            key_field: 主键字段名
            ignore_fields: 忽略的字段（如updated_at）

        Returns:
            字段级冲突列表
        """
        if ignore_fields is None:
            ignore_fields = {"updated_at", "synced_at", "version"}

        conflicts = []

        # 建立索引
        local_index = {r[key_field]: r for r in local_records if key_field in r}
        remote_index = {r[key_field]: r for r in remote_records if key_field in r}

        # 找出共同记录
        common_keys = set(local_index.keys()) & set(remote_index.keys())

        for key in common_keys:
            local = local_index[key]
            remote = remote_index[key]

            # 逐字段比较
            all_fields = set(local.keys()) | set(remote.keys())
            for field in sorted(all_fields - ignore_fields):
                local_val = local.get(field)
                remote_val = remote.get(field)

                if local_val != remote_val:
                    conflicts.append(FieldConflict(
                        table="unknown",  # caller should set
                        record_id=key,
                        field=field,
                        local_value=local_val,
                        remote_value=remote_val,
                    ))

        return conflicts


# ══════════════════════════════════════════════════════════════
#  导入预检 (Dry Run)
# ══════════════════════════════════════════════════════════════

class ImportDryRunResult:
    """导入预检结果"""

    def __init__(self):
        self.total_rows = 0
        self.new_rows = 0
        self.update_rows = 0
        self.conflict_rows = 0
        self.error_rows = 0
        self.warnings: List[str] = []
        self.conflicts: List[FieldConflict] = []
        self.errors: List[Dict] = []

    @property
    def can_import(self) -> bool:
        return self.error_rows == 0

    def summary(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "new_rows": self.new_rows,
            "update_rows": self.update_rows,
            "conflict_rows": self.conflict_rows,
            "error_rows": self.error_rows,
            "warning_count": len(self.warnings),
            "conflict_count": len(self.conflicts),
        }


def dry_run_import(
    db_session,
    table_name: str,
    records: List[Dict],
    key_field: str = "id",
) -> ImportDryRunResult:
    """
    预检导入 —— 不实际写入，只报告冲突和异常

    Args:
        db_session: 数据库会话
        table_name: 目标表名
        records: 待导入记录
        key_field: 主键字段

    Returns:
        ImportDryRunResult 包含冲突和异常的完整报告
    """
    from sqlalchemy import text

    result = ImportDryRunResult()
    result.total_rows = len(records)

    # 获取现有记录ID集合
    try:
        existing = db_session.execute(
            text(f"SELECT {key_field} FROM {table_name}")
        ).fetchall()
        existing_ids = {row[0] for row in existing}
    except Exception as e:
        result.errors.append({"row": 0, "error": f"查询表失败: {e}"})
        result.error_rows = len(records)
        return result

    for i, record in enumerate(records):
        try:
            record_id = record.get(key_field)
            if record_id is None:
                result.warnings.append(f"行{i}: 缺少主键 {key_field}")
                result.error_rows += 1
                continue

            if record_id in existing_ids:
                result.update_rows += 1
            else:
                result.new_rows += 1

        except Exception as e:
            result.errors.append({"row": i, "error": str(e)})
            result.error_rows += 1

    return result


# ══════════════════════════════════════════════════════════════
#  增量同步支持
# ══════════════════════════════════════════════════════════════

def get_changed_records(
    db_session,
    table_name: str,
    since: datetime,
    key_field: str = "id",
    timestamp_field: str = "updated_at",
) -> List[Dict]:
    """
    获取指定时间后的变更记录（增量同步）

    Args:
        db_session: 数据库会话
        table_name: 表名
        since: 起始时间（UTC）
        key_field: 主键字段
        timestamp_field: 时间戳字段

    Returns:
        变更记录列表
    """
    from sqlalchemy import text

    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    sql = f"""
        SELECT * FROM {table_name}
        WHERE {timestamp_field} >= :since
        ORDER BY {timestamp_field} ASC
    """

    try:
        rows = db_session.execute(text(sql), {"since": since.isoformat()}).fetchall()
        columns = rows[0]._fields if rows else []
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"增量查询失败 [{table_name}]: {e}")
        return []
