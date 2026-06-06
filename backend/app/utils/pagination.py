"""
Keyset Pagination Utility

高性能游标分页替代传统OFFSET分页，适用于SQLite大数据量表。

使用示例:
    from app.utils.pagination import keyset_paginate

    query = db.query(Fund).filter(Fund.village_id == 1)
    result = keyset_paginate(
        query,
        order_column=Fund.id,
        page_size=20,
        cursor=request.cursor  # 上一页返回的next_cursor
    )
    # result = {"items": [...], "total": 100, "next_cursor": "eyJ..."}
"""

import base64
import json
import logging
from typing import Any, Dict, Optional, TypeVar

from sqlalchemy.orm import Query

logger = logging.getLogger(__name__)

T = TypeVar("T")


def encode_cursor(value: Any) -> str:
    """将游标值编码为Base64字符串"""
    payload = json.dumps({"v": value}, default=str, sort_keys=True)
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: Optional[str]) -> Optional[Any]:
    """解码Base64游标字符串"""
    if not cursor:
        return None
    try:
        # 补齐Base64填充
        padded = cursor + "=" * (4 - len(cursor) % 4) if len(cursor) % 4 else cursor
        payload = base64.urlsafe_b64decode(padded).decode()
        return json.loads(payload)["v"]
    except Exception as e:
        logger.warning(f"Invalid cursor '{cursor[:20]}...': {e}")
        return None


def keyset_paginate(
    query: Query,
    order_column,
    page_size: int = 20,
    cursor: Optional[str] = None,
    desc: bool = True,
    max_page_size: int = 100,
) -> Dict[str, Any]:
    """
    Keyset pagination (seek method).

    比OFFSET快得多：O(log N + page_size) vs O(N + page_size)
    在大数据集上（>10万行），OFFSET退化到全表扫描，keyset保持索引查找。

    Args:
        query: SQLAlchemy Query对象（已应用filter）
        order_column: 排序列（通常是主键ID）
        page_size: 每页条数
        cursor: 上一页的next_cursor（None表示第一页）
        desc: True=降序（最新在前），False=升序
        max_page_size: 最大页大小

    Returns:
        {"items": [...], "total": total_count, "next_cursor": str|None}
    """
    page_size = min(max(page_size, 1), max_page_size)

    # 获取总计数
    total = query.count()

    # 应用游标过滤
    cursor_value = decode_cursor(cursor)
    if cursor_value is not None:
        if desc:
            query = query.filter(order_column < cursor_value)
        else:
            query = query.filter(order_column > cursor_value)

    # 排序和限制
    if desc:
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    items = query.limit(page_size + 1).all()  # 多取1条判断是否有下一页

    # 判断是否有下一页
    has_more = len(items) > page_size
    if has_more:
        items = items[:page_size]

    # 生成下一页游标
    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        last_value = (
            getattr(last_item, order_column.key)
            if hasattr(order_column, "key")
            else getattr(last_item, str(order_column.name))
        )
        next_cursor = encode_cursor(last_value)

    return {
        "items": items,
        "total": total,
        "next_cursor": next_cursor,
        "page_size": page_size,
        "has_more": has_more,
    }
