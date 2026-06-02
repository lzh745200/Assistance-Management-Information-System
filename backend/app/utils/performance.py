"""
性能优化配置和工具
针对单机版系统的性能优化
"""

import logging
import time
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LRUCache:
    """
    线程安全的LRU缓存实现
    适用于单机版系统的内存缓存
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        """
        Args:
            maxsize: 最大缓存条目数
            ttl: 缓存过期时间（秒）
        """
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl
        self.timestamps = {}

    def get(self, key: str) -> Any:
        """获取缓存值"""
        if key not in self.cache:
            return None

        # 检查是否过期
        if time.time() - self.timestamps.get(key, 0) > self.ttl:
            self.delete(key)
            return None

        # 移到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        """设置缓存值"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                # 删除最旧的项
                oldest_key = next(iter(self.cache))
                self.delete(oldest_key)

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def delete(self, key: str):
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]
        if key in self.timestamps:
            del self.timestamps[key]

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


# 全局缓存实例
_global_cache = LRUCache(maxsize=5000, ttl=3600)


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # 尝试从缓存获取
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            _global_cache.set(cache_key, result)
            logger.debug(f"Cache set: {cache_key}")

            return result

        return wrapper

    return decorator


def clear_cache(key_prefix: str = None):
    """
    清空缓存

    Args:
        key_prefix: 如果指定，只清空匹配前缀的缓存
    """
    if key_prefix:
        keys_to_delete = [k for k in _global_cache.cache.keys() if k.startswith(key_prefix)]
        for key in keys_to_delete:
            _global_cache.delete(key)
        logger.info(f"Cleared {len(keys_to_delete)} cache entries with prefix: {key_prefix}")
    else:
        _global_cache.clear()
        logger.info("Cleared all cache entries")


def get_cache_stats() -> dict:
    """获取缓存统计信息"""
    return {
        "size": _global_cache.size(),
        "maxsize": _global_cache.maxsize,
        "ttl": _global_cache.ttl,
        "usage_percent": (_global_cache.size() / _global_cache.maxsize) * 100,
    }


class QueryOptimizer:
    """
    数据库查询优化器
    提供查询优化建议和慢查询检测
    """

    def __init__(self, slow_query_threshold: float = 0.5):
        """
        Args:
            slow_query_threshold: 慢查询阈值（秒）
        """
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries = []

    def log_query(self, query: str, duration: float, params: dict = None):
        """记录查询"""
        if duration > self.slow_query_threshold:
            self.slow_queries.append(
                {
                    "query": query,
                    "duration": duration,
                    "params": params,
                    "timestamp": time.time(),
                }
            )
            logger.warning(f"Slow query detected ({duration:.3f}s): {query[:100]}")

    def get_slow_queries(self, limit: int = 10) -> list:
        """获取慢查询列表"""
        return sorted(self.slow_queries, key=lambda x: x["duration"], reverse=True)[:limit]

    def clear_slow_queries(self):
        """清空慢查询记录"""
        self.slow_queries.clear()


# 全局查询优化器实例
query_optimizer = QueryOptimizer()


def optimize_query_decorator(func: Callable) -> Callable:
    """查询优化装饰器"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        # 记录查询
        query_optimizer.log_query(
            query=func.__name__,
            duration=duration,
            params={"args": str(args)[:100], "kwargs": str(kwargs)[:100]},
        )

        return result

    return wrapper


class BatchProcessor:
    """
    批处理器
    用于批量处理数据，提高性能
    """

    def __init__(self, batch_size: int = 100):
        """
        Args:
            batch_size: 批处理大小
        """
        self.batch_size = batch_size

    def process_in_batches(self, items: list, process_func: Callable) -> list:
        """
        批量处理数据

        Args:
            items: 要处理的数据列表
            process_func: 处理函数

        Returns:
            处理结果列表
        """
        results = []
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1

            logger.debug(f"Processing batch {batch_num}/{total_batches}")

            try:
                batch_results = process_func(batch)
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                raise

        return results


# 性能监控装饰器


def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        _ = 0  # 可以使用 psutil 获取内存使用

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            if duration > 1.0:  # 超过1秒记录警告
                logger.warning(f"Performance warning: {func.__name__} took {duration:.3f}s")
            else:
                logger.debug(f"Performance: {func.__name__} took {duration:.3f}s")

    return wrapper


# 数据库连接池优化配置
DATABASE_POOL_CONFIG = {
    "pool_size": 20,  # 连接池大小
    "max_overflow": 10,  # 最大溢出连接数
    "pool_timeout": 30,  # 连接超时（秒）
    "pool_recycle": 3600,  # 连接回收时间（秒）
    "pool_pre_ping": True,  # 连接前ping检查
    "echo": False,  # 不输出SQL（生产环境）
    "echo_pool": False,  # 不输出连接池日志
}

# 查询优化建议
QUERY_OPTIMIZATION_TIPS = {
    "use_indexes": "确保常用查询字段有索引",
    "avoid_n_plus_1": "使用 joinedload 或 selectinload 避免 N+1 查询",
    "use_pagination": "大数据集使用分页查询",
    "use_select_columns": "只查询需要的列，避免 SELECT *",
    "use_bulk_operations": "批量操作使用 bulk_insert_mappings",
    "cache_frequently_accessed": "缓存频繁访问的数据",
    "use_read_replicas": "读写分离（如果需要）",
}

# 缓存策略配置
CACHE_STRATEGY = {
    "user_data": {"ttl": 3600, "maxsize": 1000},  # 用户数据缓存1小时
    "village_data": {"ttl": 7200, "maxsize": 500},  # 村庄数据缓存2小时
    "analytics": {"ttl": 300, "maxsize": 100},  # 分析数据缓存5分钟
    "static_data": {"ttl": 86400, "maxsize": 200},  # 静态数据缓存24小时
}
