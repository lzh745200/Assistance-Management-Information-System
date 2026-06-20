"""
游标分页工具模块

实现高效的游标分页功能，避免深度分页性能问题。

Task 11.3: 实施性能优化 - 优化分页查询（游标分页）
Requirements: 10.3 - 实现分页查询优化（游标分页）
"""

import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.orm import Query

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CursorDirection(str, Enum):
    """游标方向"""

    NEXT = "next"
    PREV = "prev"


@dataclass
class CursorData:
    """游标数据结构"""

    id: Any
    sort_value: Any
    sort_field: str
    direction: str

    def encode(self) -> str:
        """编码游标为字符串"""
        data = {
            "id": self.id,
            "sv": self.sort_value,
            "sf": self.sort_field,
            "d": self.direction,
        }
        # 处理datetime类型
        if isinstance(self.sort_value, datetime):
            data["sv"] = self.sort_value.isoformat()
            data["st"] = "datetime"

        json_str = json.dumps(data, default=str)
        return base64.urlsafe_b64encode(json_str.encode()).decode()

    @classmethod
    def decode(cls, cursor: str) -> Optional["CursorData"]:
        """解码游标字符串"""
        try:
            json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
            data = json.loads(json_str)

            sort_value = data["sv"]
            # 处理datetime类型
            if data.get("st") == "datetime":
                sort_value = datetime.fromisoformat(sort_value)

            return cls(
                id=data["id"],
                sort_value=sort_value,
                sort_field=data["sf"],
                direction=data.get("d", "next"),
            )
        except Exception:
            logger.warning("游标解析失败", exc_info=True)
            return None


class CursorPaginationRequest(BaseModel):
    """游标分页请求参数"""

    cursor: Optional[str] = Field(default=None, description="游标值")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量")
    direction: CursorDirection = Field(default=CursorDirection.NEXT, description="分页方向")
    sort_field: str = Field(default="id", description="排序字段")
    sort_desc: bool = Field(default=True, description="是否降序")


class CursorPaginationResponse(BaseModel, Generic[T]):
    """游标分页响应"""

    items: List[Any] = Field(default_factory=list, description="数据列表")
    next_cursor: Optional[str] = Field(default=None, description="下一页游标")
    prev_cursor: Optional[str] = Field(default=None, description="上一页游标")
    has_next: bool = Field(default=False, description="是否有下一页")
    has_prev: bool = Field(default=False, description="是否有上一页")
    limit: int = Field(description="每页数量")


class CursorPaginator:
    """
    游标分页器

    使用游标分页代替传统的OFFSET分页，解决深度分页性能问题。

    优势：
    - 避免OFFSET导致的全表扫描
    - 查询性能稳定，不随页数增加而下降
    - 支持实时数据场景（新增数据不影响分页）

    Requirements: 10.3
    """

    def __init__(
        self,
        model_class: Any,
        sort_field: str = "id",
        sort_desc: bool = True,
        id_field: str = "id",
    ):
        """
        初始化游标分页器

        Args:
            model_class: SQLAlchemy模型类
            sort_field: 排序字段名
            sort_desc: 是否降序
            id_field: ID字段名（用于唯一标识）
        """
        self.model_class = model_class
        self.sort_field = sort_field
        self.sort_desc = sort_desc
        self.id_field = id_field

    def _get_sort_column(self, query: Query):
        """获取排序列"""
        return getattr(self.model_class, self.sort_field)

    def _get_id_column(self, query: Query):
        """获取ID列"""
        return getattr(self.model_class, self.id_field)

    def _apply_cursor_filter(self, query: Query, cursor_data: CursorData, direction: CursorDirection) -> Query:
        """应用游标过滤条件"""
        sort_col = self._get_sort_column(query)
        id_col = self._get_id_column(query)

        # 确定比较方向
        if direction == CursorDirection.NEXT:
            if self.sort_desc:
                # 降序，下一页：sort_value < cursor 或 (sort_value == cursor 且 id < cursor_id)
                condition = or_(
                    sort_col < cursor_data.sort_value,
                    and_(sort_col == cursor_data.sort_value, id_col < cursor_data.id),
                )
            else:
                # 升序，下一页：sort_value > cursor 或 (sort_value == cursor 且 id > cursor_id)
                condition = or_(
                    sort_col > cursor_data.sort_value,
                    and_(sort_col == cursor_data.sort_value, id_col > cursor_data.id),
                )
        else:  # PREV
            if self.sort_desc:
                # 降序，上一页：sort_value > cursor 或 (sort_value == cursor 且 id > cursor_id)
                condition = or_(
                    sort_col > cursor_data.sort_value,
                    and_(sort_col == cursor_data.sort_value, id_col > cursor_data.id),
                )
            else:
                # 升序，上一页：sort_value < cursor 或 (sort_value == cursor 且 id < cursor_id)
                condition = or_(
                    sort_col < cursor_data.sort_value,
                    and_(sort_col == cursor_data.sort_value, id_col < cursor_data.id),
                )

        return query.filter(condition)

    def _apply_sort(self, query: Query, reverse: bool = False) -> Query:
        """应用排序"""
        sort_col = self._get_sort_column(query)
        id_col = self._get_id_column(query)

        # 确定排序方向
        is_desc = self.sort_desc
        if reverse:
            is_desc = not is_desc

        if is_desc:
            return query.order_by(desc(sort_col), desc(id_col))
        else:
            return query.order_by(asc(sort_col), asc(id_col))

    def _create_cursor(self, item: Any, direction: str) -> str:
        """为数据项创建游标"""
        sort_value = getattr(item, self.sort_field)
        item_id = getattr(item, self.id_field)

        cursor_data = CursorData(
            id=item_id,
            sort_value=sort_value,
            sort_field=self.sort_field,
            direction=direction,
        )
        return cursor_data.encode()

    def paginate(
        self,
        query: Query,
        cursor: Optional[str] = None,
        limit: int = 20,
        direction: CursorDirection = CursorDirection.NEXT,
    ) -> CursorPaginationResponse:
        """
        执行游标分页

        Args:
            query: SQLAlchemy查询对象
            cursor: 游标字符串
            limit: 返回数量
            direction: 分页方向

        Returns:
            CursorPaginationResponse: 分页结果
        """
        # 解析游标
        cursor_data = None
        if cursor:
            cursor_data = CursorData.decode(cursor)

        # 应用游标过滤
        if cursor_data:
            query = self._apply_cursor_filter(query, cursor_data, direction)

        # 应用排序
        reverse = direction == CursorDirection.PREV
        query = self._apply_sort(query, reverse=reverse)

        # 多取一条用于判断是否有更多数据
        items = query.limit(limit + 1).all()

        # 判断是否有更多数据
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]

        # 如果是向前翻页，需要反转结果
        if reverse:
            items = list(reversed(items))

        # 生成游标
        next_cursor = None
        prev_cursor = None
        has_next = False
        has_prev = False

        if items:  # 下一页游标
            if direction == CursorDirection.NEXT:
                has_next = has_more
                has_prev = cursor is not None
            else:
                has_next = cursor is not None
                has_prev = has_more

            if has_next:
                next_cursor = self._create_cursor(items[-1], "next")
            if has_prev:
                prev_cursor = self._create_cursor(items[0], "prev")

        return CursorPaginationResponse(
            items=items,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_next,
            has_prev=has_prev,
            limit=limit,
        )


def cursor_paginate(
    query: Query,
    model_class: Any,
    cursor: Optional[str] = None,
    limit: int = 20,
    direction: CursorDirection = CursorDirection.NEXT,
    sort_field: str = "id",
    sort_desc: bool = True,
) -> CursorPaginationResponse:
    """
    便捷的游标分页函数

    Args:
        query: SQLAlchemy查询对象
        model_class: 模型类
        cursor: 游标字符串
        limit: 返回数量
        direction: 分页方向
        sort_field: 排序字段
        sort_desc: 是否降序

    Returns:
        CursorPaginationResponse: 分页结果

    用法:
        result = cursor_paginate(
            db.query(Village),
            Village,
            cursor=request.cursor,
            limit=20,
            sort_field="created_at",
            sort_desc=True
        )
    """
    paginator = CursorPaginator(
        model_class=model_class,
        sort_field=sort_field,
        sort_desc=sort_desc,
    )
    return paginator.paginate(query, cursor, limit, direction)


class KeysetPaginator:
    """
    键集分页器（Keyset Pagination）

    另一种高效分页实现，基于WHERE条件而非OFFSET。
    适用于需要精确控制分页条件的场景。
    """

    @staticmethod
    def paginate_by_id(
        query: Query,
        model_class: Any,
        last_id: Optional[int] = None,
        limit: int = 20,
        ascending: bool = True,
    ) -> Tuple[List[Any], Optional[int]]:
        """
        基于ID的键集分页

        Args:
            query: 查询对象
            model_class: 模型类
            last_id: 上一页最后一条记录的ID
            limit: 返回数量
            ascending: 是否升序

        Returns:
            Tuple[List, Optional[int]]: (数据列表, 下一页起始ID)
        """
        id_col = getattr(model_class, "id")

        if last_id is not None:
            if ascending:
                query = query.filter(id_col > last_id)
            else:
                query = query.filter(id_col < last_id)

        if ascending:
            query = query.order_by(asc(id_col))
        else:
            query = query.order_by(desc(id_col))

        items = query.limit(limit + 1).all()

        next_id = None
        if len(items) > limit:
            items = items[:limit]
            if items:
                next_id = getattr(items[-1], "id")

        return items, next_id

    @staticmethod
    def paginate_by_timestamp(
        query: Query,
        model_class: Any,
        timestamp_field: str = "created_at",
        last_timestamp: Optional[datetime] = None,
        last_id: Optional[int] = None,
        limit: int = 20,
        ascending: bool = False,
    ) -> Tuple[List[Any], Optional[datetime], Optional[int]]:
        """
        基于时间戳的键集分页

        Args:
            query: 查询对象
            model_class: 模型类
            timestamp_field: 时间戳字段名
            last_timestamp: 上一页最后一条记录的时间戳
            last_id: 上一页最后一条记录的ID（用于相同时间戳的排序）
            limit: 返回数量
            ascending: 是否升序

        Returns:
            Tuple[List, Optional[datetime], Optional[int]]:
                (数据列表, 下一页起始时间戳, 下一页起始ID)
        """
        ts_col = getattr(model_class, timestamp_field)
        id_col = getattr(model_class, "id")

        if last_timestamp is not None:
            if ascending:
                condition = or_(
                    ts_col > last_timestamp,
                    and_(ts_col == last_timestamp, id_col > last_id),
                )
            else:
                condition = or_(
                    ts_col < last_timestamp,
                    and_(ts_col == last_timestamp, id_col < last_id),
                )
            query = query.filter(condition)

        if ascending:
            query = query.order_by(asc(ts_col), asc(id_col))
        else:
            query = query.order_by(desc(ts_col), desc(id_col))

        items = query.limit(limit + 1).all()

        next_ts = None
        next_id = None
        if len(items) > limit:
            items = items[:limit]
            if items:
                next_ts = getattr(items[-1], timestamp_field)
                next_id = getattr(items[-1], "id")

        return items, next_ts, next_id
