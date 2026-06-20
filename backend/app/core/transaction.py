"""
事务管理工具
提供声明式和编程式事务管理
"""

import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import DatabaseError

# 合法的事务隔离级别白名单
_VALID_ISOLATION_LEVELS = frozenset(
    {
        "READ UNCOMMITTED",
        "READ COMMITTED",
        "REPEATABLE READ",
        "SERIALIZABLE",
    }
)


@contextmanager
def get_db_context():
    """将 get_db 生成器包装为上下文管理器"""
    gen = get_db()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


logger = logging.getLogger(__name__)


class TransactionManager:
    """事务管理器"""

    @staticmethod
    @contextmanager
    def transaction(db: Session):
        """
        事务上下文管理器

        使用方法:
            with transaction(db) as session:
                # 执行数据库操作
                session.add(user)
                # 如果发生异常，自动回滚
                # 否则自动提交
        """
        try:
            yield db
            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed and rolled back: {e}")
            raise DatabaseError(f"事务执行失败: {str(e)}") from e

    @staticmethod
    def transactional(func: Callable) -> Callable:
        """
        事务装饰器

        使用方法:
            @transactional
            def create_user(db: Session, user_data: dict):
                user = User(**user_data)
                db.add(user)
                return user
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 查找数据库会话参数
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break

            if db is None:
                # 从关键字参数中查找
                db = kwargs.get("db")

            if db is None:
                # 自动创建会话
                with get_db_context() as session:
                    try:
                        return func(session, *args, **kwargs)
                    except Exception as e:
                        session.rollback()
                        raise DatabaseError(f"事务执行失败: {str(e)}") from e
            else:
                # 使用现有会话
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    db.rollback()
                    raise DatabaseError(f"事务执行失败: {str(e)}") from e

        return wrapper

    @staticmethod
    def run_in_transaction(func: Callable, db: Session, *args, **kwargs) -> Any:
        """
        在事务中执行函数

        Args:
            func: 要执行的函数
            db: 数据库会话
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        try:
            result = func(db, *args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed and rolled back: {e}")
            raise DatabaseError(f"事务执行失败: {str(e)}") from e

    @staticmethod
    @contextmanager
    def nested_transaction(db: Session):
        """
        嵌套事务上下文管理器

        使用方法:
            with nested_transaction(db) as session:
                # 执行数据库操作
                session.add(user)
        """
        # 开始嵌套事务
        nested = db.begin_nested()
        try:
            yield nested
            nested.commit()
        except Exception as e:
            nested.rollback()
            logger.error(f"Nested transaction failed and rolled back: {e}")
            raise DatabaseError(f"嵌套事务执行失败: {str(e)}") from e

    @staticmethod
    @contextmanager
    def savepoint(db: Session, name: Optional[str] = None):
        """
        保存点上下文管理器

        Args:
            db: 数据库会话
            name: 保存点名称（可选）

        使用方法:
            with savepoint(db, 'user_savepoint') as sp:
                # 执行数据库操作
                db.add(user)
                # 可以回滚到这个保存点
                # sp.rollback()
        """
        sp = db.begin_nested()
        if name:
            sp.name = name
        try:
            yield sp
            sp.commit()
        except Exception as e:
            sp.rollback()
            logger.error(f"Savepoint failed and rolled back: {e}")
            raise DatabaseError(f"保存点执行失败: {str(e)}") from e


# 便捷函数
transaction = TransactionManager.transaction
transactional = TransactionManager.transactional
run_in_transaction = TransactionManager.run_in_transaction
nested_transaction = TransactionManager.nested_transaction
savepoint = TransactionManager.savepoint


# 事务装饰器（更详细的版本）
def with_transaction(isolation_level: Optional[str] = None, readonly: bool = False):
    """
    高级事务装饰器

    Args:
        isolation_level: 隔离级别（READ COMMITTED, REPEATABLE READ, SERIALIZABLE）
        readonly: 是否只读事务

    使用方法:
        @with_transaction(isolation_level="READ COMMITTED")
        def create_user(db: Session, user_data: dict):
            user = User(**user_data)
            db.add(user)
            return user
    """
    # 在装饰器定义期间（而非运行时）校验隔离级别，防止 SQL 注入
    if isolation_level and isolation_level.upper() not in _VALID_ISOLATION_LEVELS:
        raise ValueError(f"无效的隔离级别: {isolation_level}，" f"允许值: {', '.join(sorted(_VALID_ISOLATION_LEVELS))}")
    _safe_isolation = isolation_level.upper() if isolation_level else None

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 查找数据库会话参数
            db = None
            for arg in args:
                if isinstance(arg, Session):
                    db = arg
                    break

            if db is None:
                db = kwargs.get("db")

            def _apply_tx_settings(sess: Session):
                if _safe_isolation:
                    sess.execute(text(f"SET TRANSACTION ISOLATION LEVEL {_safe_isolation}"))
                if readonly:
                    sess.execute(text("SET TRANSACTION READ ONLY"))

            if db is None:
                with get_db_context() as session:
                    try:
                        _apply_tx_settings(session)
                        result = func(session, *args, **kwargs)
                        session.commit()
                        return result
                    except Exception as e:
                        session.rollback()
                        raise DatabaseError(f"事务执行失败: {str(e)}") from e
            else:
                try:
                    _apply_tx_settings(db)
                    result = func(*args, **kwargs)
                    db.commit()
                    return result
                except Exception as e:
                    db.rollback()
                    raise DatabaseError(f"事务执行失败: {str(e)}") from e

        return wrapper

    return decorator


# 重试装饰器
def retry_on_deadlock(max_retries: int = 3, delay: float = 0.1):
    """
    死锁重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）

    使用方法:
        @retry_on_deadlock(max_retries=3)
        def update_user(db: Session, user_id: int, data: dict):
            user = db.query(User).filter(User.id == user_id).first()
            for key, value in data.items():
                setattr(user, key, value)
            return user
    """
    import time

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except SQLAlchemyError as e:
                    last_exception = e
                    if "deadlock" in str(e).lower() or "lock" in str(e).lower():
                        if attempt < max_retries - 1:
                            logger.warning(f"Deadlock detected, retrying ({attempt + 1}/{max_retries})...")
                            time.sleep(delay)
                            continue
                    raise

            raise DatabaseError(f"事务执行失败（重试{max_retries}次后）: {str(last_exception)}") from last_exception

        return wrapper

    return decorator


# 批量操作工具
class BatchOperation:
    """批量操作工具"""

    @staticmethod
    def batch_insert(db: Session, model_class: type, items: list[dict], batch_size: int = 1000) -> int:
        """
        批量插入

        Args:
            db: 数据库会话
            model_class: 模型类
            items: 要插入的数据列表
            batch_size: 批次大小

        Returns:
            插入的记录数
        """
        total_inserted = 0

        try:
            for i in range(0, len(items), batch_size):
                batch = items[i: i + batch_size]
                db.bulk_insert_mappings(model_class, batch)
                total_inserted += len(batch)

                # 每个批次后刷新，避免内存占用过大
                db.flush()

            db.commit()
            return total_inserted
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"批量插入失败: {str(e)}") from e

    @staticmethod
    def batch_update(db: Session, model_class: type, updates: list[dict], batch_size: int = 1000) -> int:
        """
        批量更新

        Args:
            db: 数据库会话
            model_class: 模型类
            updates: 更新数据列表（每个字典必须包含id）
            batch_size: 批次大小

        Returns:
            更新的记录数
        """
        total_updated = 0

        try:
            for i in range(0, len(updates), batch_size):
                batch = updates[i: i + batch_size]
                db.bulk_update_mappings(model_class, batch)
                total_updated += len(batch)
                db.flush()

            db.commit()
            return total_updated
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"批量更新失败: {str(e)}") from e

    @staticmethod
    def batch_delete(db: Session, model_class: type, ids: list, batch_size: int = 1000) -> int:
        """
        批量删除

        Args:
            db: 数据库会话
            model_class: 模型类
            ids: 要删除的ID列表
            batch_size: 批次大小

        Returns:
            删除的记录数
        """
        total_deleted = 0

        try:
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i: i + batch_size]
                db.query(model_class).filter(model_class.id.in_(batch_ids)).delete(synchronize_session=False)
                total_deleted += len(batch_ids)
                db.flush()

            db.commit()
            return total_deleted
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"批量删除失败: {str(e)}") from e
