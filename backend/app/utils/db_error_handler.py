"""
数据库操作错误处理装饰器

提供统一的数据库事务错误处理
"""

import functools
import logging
from typing import Any, Callable, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def handle_db_errors(func: F) -> F:
    """
    数据库操作错误处理装饰器

    自动处理常见的数据库错误并回滚事务
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 尝试从参数中获取db session
        db: Session | None = None

        # 检查位置参数
        for arg in args:
            if isinstance(arg, Session):
                db = arg
                break

        # 检查关键字参数
        if db is None and "db" in kwargs:
            db = kwargs["db"]

        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            if db:
                db.rollback()
            logger.error(f"Database integrity error in {func.__name__}: {e}")

            # 解析具体错误
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)

            if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
                raise HTTPException(status_code=409, detail="数据已存在，请检查唯一性约束")
            elif "FOREIGN KEY constraint failed" in error_msg:
                raise HTTPException(status_code=400, detail="关联数据不存在或已被删除")
            else:
                raise HTTPException(status_code=400, detail=f"数据完整性错误: {error_msg[:100]}")

        except OperationalError as e:
            if db:
                db.rollback()
            logger.error(f"Database operational error in {func.__name__}: {e}")
            raise HTTPException(status_code=503, detail="数据库操作失败，请稍后重试")

        except SQLAlchemyError as e:
            if db:
                db.rollback()
            logger.error(f"Database error in {func.__name__}: {e}")
            raise HTTPException(status_code=500, detail="数据库错误，请联系管理员")

        except HTTPException:
            # 重新抛出HTTP异常
            if db:
                db.rollback()
            raise

        except BusinessError:
            # 重新抛出业务异常
            if db:
                db.rollback()
            raise

        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"操作失败: {str(e)[:100]}")

    return wrapper  # type: ignore


def handle_db_errors_async(func: F) -> F:
    """
    异步数据库操作错误处理装饰器
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 尝试从参数中获取db session
        db: Session | None = None

        for arg in args:
            if isinstance(arg, Session):
                db = arg
                break

        if db is None and "db" in kwargs:
            db = kwargs["db"]

        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            if db:
                db.rollback()
            logger.error(f"Database integrity error in {func.__name__}: {e}")

            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)

            if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg.lower():
                raise HTTPException(status_code=409, detail="数据已存在，请检查唯一性约束")
            elif "FOREIGN KEY constraint failed" in error_msg:
                raise HTTPException(status_code=400, detail="关联数据不存在或已被删除")
            else:
                raise HTTPException(status_code=400, detail=f"数据完整性错误: {error_msg[:100]}")

        except OperationalError as e:
            if db:
                db.rollback()
            logger.error(f"Database operational error in {func.__name__}: {e}")
            raise HTTPException(status_code=503, detail="数据库操作失败，请稍后重试")

        except SQLAlchemyError as e:
            if db:
                db.rollback()
            logger.error(f"Database error in {func.__name__}: {e}")
            raise HTTPException(status_code=500, detail="数据库错误，请联系管理员")

        except HTTPException:
            if db:
                db.rollback()
            raise

        except BusinessError:
            # 重新抛出业务异常
            if db:
                db.rollback()
            raise

        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"操作失败: {str(e)[:100]}")

    return wrapper  # type: ignore


class DBTransaction:
    """
    数据库事务上下文管理器

    使用示例:
    ```python
    with DBTransaction(db):
        # 数据库操作
        db.add(obj)
        db.commit()
    ```
    """

    def __init__(self, db: Session, auto_commit: bool = False):
        self.db = db
        self.auto_commit = auto_commit

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 发生异常，回滚
            self.db.rollback()
            logger.error(f"Transaction rolled back due to {exc_type.__name__}: {exc_val}")
            return False

        if self.auto_commit:
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Commit failed: {e}")
                raise

        return True
