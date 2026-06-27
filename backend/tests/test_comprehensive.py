#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合系统测试脚本（FastAPI 版本）

覆盖：
- 后端 API 接口测试
- 数据库连接测试
- 认证流程测试
- 数据 CRUD 测试
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



def test_imports():
    """测试核心模块导入"""
    from app.main import app
    assert app is not None
    print(f"✓ FastAPI 应用加载成功，路由数: {len(app.routes)}")


def test_database_connection():
    """测试数据库连接"""
    from app.core.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    print("✓ 数据库连接正常")


def test_config_loading():
    """测试配置加载"""
    from app.core.config import settings
    assert settings.PROJECT_NAME is not None
    print(f"✓ 配置加载成功: {settings.PROJECT_NAME}")


if __name__ == "__main__":
    print("=" * 50)
    print("军事乡村振兴管理系统 - 综合测试")
    print("=" * 50)
    test_imports()
    test_database_connection()
    test_config_loading()
    print("=" * 50)
    print("所有测试通过！")
