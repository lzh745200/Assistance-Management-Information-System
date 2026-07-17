"""
全局 Date 类型安全防护

自动扫描所有 SQLAlchemy 模型中的 Column(Date) 列，注册 before_insert / before_update
事件监听器，在写入数据库前将 datetime / str 值自动转换为 date 对象。

这解决了 SQLite "SQLite Date type only accepts Python date objects as input" 错误，
无需在每个 API 端点或 Service 方法中手动转换。

设计原则：
- 零侵入：业务代码无需修改，监听器自动在 ORM 事件中执行
- 安全：仅处理 Date 类型列，不影响 DateTime 类型列
- 幂等：已经是 date 对象的值不做转换
- 可扩展：新的模型只要声明了 Column(Date) 就自动被覆盖
"""

import logging
from datetime import date, datetime
from typing import Any, Type

from sqlalchemy import Date, event
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# 全局标记，防止重复注册
_registered_models: set[str] = set()


def _coerce_to_date(value: Any) -> Any:
    """将值转换为 date 对象。如果无法转换则原样返回（让数据库驱动处理或报错）。"""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        # 已经是 date（但不是 datetime），直接返回
        return value
    if isinstance(value, datetime):
        # datetime → 取 date 部分
        return value.date()
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # 尝试 ISO 格式解析
        try:
            return datetime.fromisoformat(s).date()
        except ValueError:
            pass
        # 尝试 YYYY-MM-DD 格式（取前 10 个字符）
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
        # 无法解析，原样返回让数据库处理
        logger.warning("无法将字符串 %r 转换为 date 对象", value)
        return value
    return value


def _get_date_columns(model: Type[Any]) -> list[str]:
    """获取模型中所有 Date 类型列的名称。"""
    date_cols = []
    if not hasattr(model, "__table__"):
        return date_cols
    for col in model.__table__.columns:
        if isinstance(col.type, Date):
            date_cols.append(col.name)
    return date_cols


def _make_before_listener(date_col_names: list[str]):
    """为指定 Date 列名列表创建 before_insert / before_update 事件监听器。"""

    def _listener(mapper, connection, target):
        for col_name in date_col_names:
            val = getattr(target, col_name, None)
            if val is not None:
                coerced = _coerce_to_date(val)
                if coerced is not val:
                    setattr(target, col_name, coerced)

    return _listener


def register_date_type_handlers(base_class: Type[DeclarativeBase]) -> int:
    """
    扫描所有继承自 base_class 的模型，为含有 Column(Date) 列的模型注册
    before_insert / before_update 事件监听器，自动将 datetime/str 转为 date。

    Args:
        base_class: SQLAlchemy 声明式基类（如 app.models.base.Base）

    Returns:
        注册了监听器的模型数量
    """
    # 导入所有模型以确保它们被映射到 base_class.metadata
    try:
        import app.models  # noqa: F401
    except ImportError:
        logger.warning("无法导入 app.models 包，跳过 Date 类型监听器注册")

    registered_count = 0

    # 遍历所有已映射的模型
    for mapper in base_class.registry.mappers:
        model_class = mapper.class_
        if not hasattr(model_class, "__table__"):
            continue
        if not hasattr(model_class, "__tablename__"):
            continue

        # 防止重复注册
        model_key = f"{model_class.__module__}.{model_class.__name__}"
        if model_key in _registered_models:
            continue

        date_cols = _get_date_columns(model_class)
        if not date_cols:
            continue

        listener = _make_before_listener(date_cols)
        event.listen(model_class, "before_insert", listener)
        event.listen(model_class, "before_update", listener)

        _registered_models.add(model_key)
        registered_count += 1
        logger.debug(
            "已注册 Date 类型监听器: %s.%s → 列: %s",
            model_class.__module__,
            model_class.__name__,
            date_cols,
        )

    if registered_count > 0:
        logger.info("Date 类型安全防护已启用：%d 个模型注册了自动转换监听器", registered_count)

    return registered_count
