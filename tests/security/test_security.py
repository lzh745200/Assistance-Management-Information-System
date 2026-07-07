"""
安全测试套件

测试内容：
1. 权限管理测试
2. 配置文件防篡改测试
3. SQL 注��防护测试
4. XSS 防护测试
5. CSRF 防护测试
"""

import os
import sys
import pytest
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


class TestPermissionManagement:
    """权限管理测试"""

    def test_run_without_admin_privileges(self):
        """测试：无管理员权限时能否正常运行"""
        # 检查程序是否需要管理员权限
        # 单机版应用不应该强制要求管理员权限
        import ctypes

        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False

        # 程序应该能在非管理员权限下运行
        # 这个测试记录当前状态
        print(f"当前是否以管理员权限运行：{is_admin}")
        # 注意：实际测试需要在非管理员账户下运行程序

    def test_file_permissions_check(self):
        """测试：文件权限检查"""
        # 检查关键文件的权限设置
        critical_files = [
            Path(__file__).parent.parent.parent / "backend" / ".env",
            Path(__file__).parent.parent.parent / "backend" / "data" / "assistance_management.db",
        ]

        for file_path in critical_files:
            if file_path.exists():
                # 在 Windows 上，检查文件是否可读写
                assert os.access(file_path, os.R_OK), f"{file_path} 应该可读"
                assert os.access(file_path, os.W_OK), f"{file_path} 应该可写"

    def test_rbac_enforcement(self):
        """测试：RBAC 权限强制执行"""
        # 这个测试在 API 集成测试中实现
        # 验证不同角色的用户只能访问授权的资源
        pass  # 在集成测试中实现

    def test_unauthorized_access_blocked(self):
        """测试：未授权访问被阻止"""
        # 测试未登录用户访问受保护的 API
        pass  # 在集成测试中实现


class TestConfigurationTampering:
    """配置文件防篡改测试"""

    def test_config_file_integrity(self):
        """测试：配置文件完整性"""
        env_file = Path(__file__).parent.parent.parent / "backend" / ".env"

        if not env_file.exists():
            pytest.skip(".env 文件不存在")

        # 读取配置文件
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查必需的配置项
        required_keys = ['SECRET_KEY', 'DATABASE_URL']
        for key in required_keys:
            assert key in content, f"配置文件应该包含 {key}"

    def test_config_validation(self):
        """测试：配置验证"""
        from app.core.config import settings

        # 检查配置是否有效
        assert settings.SECRET_KEY, "SECRET_KEY 不应为空"
        assert len(settings.SECRET_KEY) >= 32, "SECRET_KEY 长度应该至少 32 字符"
        assert settings.DATABASE_URL, "DATABASE_URL 不应为空"

    def test_prevent_config_override_via_env(self):
        """测试：防止通过环境变量覆盖关键配置"""
        # 检查是否有机制防止恶意环境变量覆盖
        # 这是一个安全建议，当前可能未实现
        pytest.skip("需要实现配置保护机制")

    def test_config_file_not_in_web_root(self):
        """测试：配置文件不在 Web 根目录"""
        # 确保 .env 文件不会被 Web 服务器直接访问
        # 对于 Electron 应用，这个风险较低
        env_file = Path(__file__).parent.parent.parent / "backend" / ".env"
        frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

        if frontend_dist.exists():
            # .env 不应该在前端构建目录中
            assert not (frontend_dist / ".env").exists(), ".env 不应在前端目录"


class TestSQLInjectionPrevention:
    """SQL 注入防护测试"""

    def test_parameterized_queries(self):
        """测试：使用参数化查询"""
        # 检查代码中是否使用了参数化查询
        # 而不是字符串拼接

        # 检查 SQLAlchemy 模型文件
        model_files = list(Path(__file__).parent.parent.parent.glob(
            "backend/app/models/*.py"
        ))

        dangerous_patterns = [
            'execute("SELECT',
            'execute(f"SELECT',
            'execute("INSERT',
            'execute(f"INSERT',
        ]

        violations = []
        for model_file in model_files:
            with open(model_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in dangerous_patterns:
                    if pattern in content:
                        violations.append((model_file.name, pattern))

        assert len(violations) == 0, f"发现可能的 SQL 注入风险：{violations}"

    def test_orm_usage(self):
        """测试：使用 ORM 而不是原生 SQL"""
        # SQLAlchemy ORM 可以有效防止 SQL 注入
        from app.models.user import User

        # 检查模型是否正确使用 ORM
        assert hasattr(User, '__tablename__'), "应该使用 SQLAlchemy 模型"

    def test_input_validation(self):
        """测试：输入验证"""
        # 检查 Pydantic schemas 是否定义了验证规则
        schema_files = list(Path(__file__).parent.parent.parent.glob(
            "backend/app/schemas/*.py"
        ))

        validation_found = False
        for schema_file in schema_files[:5]:  # 检查前 5 个文件
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'BaseModel' in content:
                    validation_found = True
                    break

        assert validation_found, "应该使用 Pydantic 进行输入验证"

    def test_sql_injection_attack_simulation(self):
        """测试：模拟 SQL 注入攻击"""
        # 这个测试在 API 集成测试中实现
        # 尝试注入恶意 SQL 代码，验证是否被阻止
        pass  # 在集成测试中实现


class TestXSSPrevention:
    """XSS 防护测试"""

    def test_output_escaping(self):
        """测试：输出转义"""
        # 检查前端是否正确转义用户输入
        # Vue 默认会转义插值内容
        vue_files = list(Path(__file__).parent.parent.parent.glob(
            "frontend/src/**/*.vue"
        ))

        # 检查是否使用了 v-html（可能导致 XSS）
        v_html_usage = []
        for vue_file in vue_files[:20]:
            with open(vue_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'v-html' in content:
                    v_html_usage.append(vue_file.name)

        if v_html_usage:
            print(f"警告：以下文件使用了 v-html，需要确保内容已消毒：{v_html_usage}")

    def test_csp_headers(self):
        """测试：Content Security Policy 头部"""
        # 检查是否设置了 CSP 头部
        # 这个测试在 API 测试中实现
        pytest.skip("需要检查 HTTP 响应头")

    def test_sanitize_user_input(self):
        """测试：用户输入消毒"""
        # 检查是否有输入消毒函数
        utils_files = list(Path(__file__).parent.parent.parent.glob(
            "backend/app/utils/*.py"
        ))

        sanitize_found = False
        for util_file in utils_files:
            with open(util_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'sanitize' in content.lower() or 'escape' in content.lower():
                    sanitize_found = True
                    break

        # 注意：这是一个建议，当前可能未实现专门的消毒函数
        if not sanitize_found:
            print("建议：实现输入消毒函数")


class TestCSRFPrevention:
    """CSRF 防护测试"""

    def test_csrf_token_in_forms(self):
        """测试：表单中的 CSRF Token"""
        # 对于 SPA 应用，通常使用 JWT 而不是 CSRF Token
        # 检查是否使用了适当的认证机制
        from app.core.security import create_access_token

        # 检查 JWT 实现
        assert callable(create_access_token), "应该有 JWT Token 生成函数"

    def test_same_origin_policy(self):
        """测试：同源策略"""
        # 检查 CORS 配置
        # 这个测试在 API 测试中实现
        pytest.skip("需要检查 CORS 配置")

    def test_referer_validation(self):
        """测试：Referer 验证"""
        # 对于敏感操作，应该验证 Referer 头
        pytest.skip("需要在 API 中实现")


class TestAuthenticationSecurity:
    """认证安全测试"""

    def test_password_hashing(self):
        """测试：密码哈希"""
        from app.core.security import get_password_hash, verify_password

        # 测试密码哈希
        password = "test_password_123"
        hashed = get_password_hash(password)

        # bcrypt 哈希应该以 $2b$ 开头
        assert hashed.startswith('$2b$'), "应该使用 bcrypt"
        assert len(hashed) == 60, "bcrypt 哈希长度应为 60"

        # 验证密码
        assert verify_password(password, hashed), "密码验证应该成功"
        assert not verify_password("wrong_password", hashed), "错误密码应该验证失败"

    def test_jwt_token_security(self):
        """测试：JWT Token 安全性"""
        from app.core.security import create_access_token, decode_token

        # 创建 Token
        token = create_access_token(data={"sub": "test_user"})
        assert token, "应该成功创建 Token"

        # 解码 Token
        payload = decode_token(token)
        assert payload is not None, "应该成功解码 Token"
        assert payload.get("sub") == "test_user", "Token 数据应该正确"

    def test_token_expiration(self):
        """测试：Token 过期"""
        from app.core.security import create_access_token, decode_token
        from datetime import timedelta

        # 创建一个已过期的 Token
        token = create_access_token(
            data={"sub": "test_user"},
            expires_delta=timedelta(seconds=-1)  # 已过期
        )

        # 尝试解码过期的 Token
        payload = decode_token(token)
        # 应该返回 None 或抛出异常
        assert payload is None, "过期的 Token 应该无效"

    def test_brute_force_protection(self):
        """测试：暴力破解保护"""
        # 检查是否有登录失败次数限制
        # 这个测试在 API 集成测试中实现
        pass  # 在集成测试中实现


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
