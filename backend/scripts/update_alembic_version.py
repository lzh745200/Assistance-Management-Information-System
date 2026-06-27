"""更新 Alembic 版本号"""
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/assistance_management.db')
with engine.connect() as conn:
    # 检查表是否存在
    result = conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
    ))
    if result.fetchone():
        conn.execute(text("UPDATE alembic_version SET version_num = '008'"))
        conn.commit()
        print('版本号已更新为 008')
    else:
        # 创建表并插入版本号
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('008')"))
        conn.commit()
        print('已创建 alembic_version 表并设置版本号为 008')
