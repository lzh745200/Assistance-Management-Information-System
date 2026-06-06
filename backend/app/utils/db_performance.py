"""数据库性能优化工具模块"""

import functools
import hashlib
import logging
import time
from typing import Any, Callable, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Query, Session

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """查询优化器"""

    @staticmethod
    def add_pagination(query: Query, page: int = 1, page_size: int = 20, max_page_size: int = 100) -> Query:
        """添加分页

        Args:
            query: SQLAlchemy查询
            page: 页码
            page_size: 每页数量
            max_page_size: 最大每页数量

        Returns:
            分页后的查询
        """
        page_size = min(page_size, max_page_size)
        page = max(page, 1)
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)

    @staticmethod
    def optimize_eager_loading(query: Query, relationships: List[str]) -> Query:
        """优化预加载

        Args:
            query: SQLAlchemy查询
            relationships: 关系列表

        Returns:
            优化后的查询
        """
        from sqlalchemy.orm import joinedload

        for relationship in relationships:
            query = query.options(joinedload(relationship))

        return query

    @staticmethod
    def get_query_count(query: Query) -> int:
        """高效获取查询结果数量

        Args:
            query: SQLAlchemy查询

        Returns:
            结果数量
        """

        return query.count()


class BatchOperator:
    """批量操作器"""

    @staticmethod
    def bulk_insert(
        db: Session,
        model_class: Any,
        data_list: List[dict],
        batch_size: int = 100,
        commit: bool = True,
    ) -> int:
        """批量插入

        Args:
            db: 数据库会话
            model_class: 模型类
            data_list: 数据列表
            batch_size: 批次大小
            commit: 是否提交

        Returns:
            插入的记录数
        """
        total = len(data_list)
        inserted = 0

        try:
            for i in range(0, total, batch_size):
                batch = data_list[i: i + batch_size]
                db.bulk_insert_mappings(model_class, batch)
                if commit:
                    db.commit()
                inserted += len(batch)
                logger.info(f"批量插入进度: {inserted}/{total}")

            return inserted

        except Exception as e:
            if commit:
                db.rollback()
            logger.error(f"批量插入失败: {str(e)}")
            raise

    @staticmethod
    def bulk_update(
        db: Session,
        model_class: Any,
        data_list: List[dict],
        batch_size: int = 100,
        commit: bool = True,
    ) -> int:
        """批量更新

        Args:
            db: 数据库会话
            model_class: 模型类
            data_list: 数据列表
            batch_size: 批次大小
            commit: 是否提交

        Returns:
            更新的记录数
        """
        total = len(data_list)
        updated = 0

        try:
            for i in range(0, total, batch_size):
                batch = data_list[i: i + batch_size]
                db.bulk_update_mappings(model_class, batch)
                if commit:
                    db.commit()
                updated += len(batch)
                logger.info(f"批量更新进度: {updated}/{total}")

            return updated

        except Exception as e:
            if commit:
                db.rollback()
            logger.error(f"批量更新失败: {str(e)}")
            raise


class SimpleCache:
    """简单缓存"""

    def __init__(self, ttl: int = 300):
        """初始化缓存

        Args:
            ttl: 缓存过期时间（秒）
        """
        self.cache = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或None
        """
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        self.cache[key] = (value, time.time())

    def delete(self, key: str) -> None:
        """删除缓存

        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()


query_cache = SimpleCache(ttl=300)


def cache_query(ttl: int = 300):
    """查询缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = hashlib.md5(
                f"{func.__name__}:{str(args)}:{str(kwargs)}".encode(),
                usedforsecurity=False,
            ).hexdigest()

            cached_value = query_cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {func.__name__}")
                return cached_value

            result = func(*args, **kwargs)
            query_cache.set(cache_key, result)

            return result

        return wrapper

    return decorator


def measure_query_time(func: Callable) -> Callable:
    """查询时间测量装饰器

    Args:
        func: 要测量的函数

    Returns:
        装饰后的函数
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        duration = (end_time - start_time) * 1000
        logger.info(f"查询 {func.__name__} 耗时: {duration:.2f}ms")

        return result

    return wrapper


def optimize_sqlite_connection(db: Session) -> None:
    """优化SQLite连接

    Args:
        db: 数据库会话
    """
    try:
        # 设置缓存大小
        db.execute(text("PRAGMA cache_size = 10000"))
        # 使用WAL模式
        db.execute(text("PRAGMA journal_mode = WAL"))
        # 设置同步模式
        db.execute(text("PRAGMA synchronous = NORMAL"))
        # 使用内存临时存储
        db.execute(text("PRAGMA temp_store = MEMORY"))
        # 设置页面大小
        db.execute(text("PRAGMA page_size = 4096"))

        db.commit()
        logger.info("SQLite连接优化完成")

    except Exception as e:
        logger.error(f"SQLite连接优化失败: {str(e)}")
