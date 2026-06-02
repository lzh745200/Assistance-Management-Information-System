"""依赖注入模块

提供应用所需的各类依赖项

注意：大多数依赖项应直接从 app.core.database 导入 get_db()
此模块保留用于未来的自定义依赖项
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.core.database import get_db


def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话依赖项

    注意：这是 get_db() 的简单包装，建议直接使用 get_db()
    """
    yield from get_db()
