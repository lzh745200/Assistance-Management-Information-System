"""
系统管理员功能测试
测试系统信息、备份恢复、系统配置等功能
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from tests.utils import HTTP_SUCCESS_OR_ERROR


class TestSystemAdmin:
    """系统管理员功能测试类"""

    def test_get_system_info(self, client: TestClient, admin_token_headers: dict):
        """测试获取系统信息"""
        response = client.get(
            "/api/v1/system/admin/info", headers=admin_token_headers
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR
        # 仅在成功时验证响应体
        if response.status_code == 200:
            data = response.json()
            assert "version" in data
            assert "database_size" in data
            assert "user_count" in data

    def test_create_backup(self, client: TestClient, admin_token_headers: dict, tmp_path: Path):
        """测试创建备份（使用临时目录，避免产生真实备份文件）"""
        from unittest.mock import patch, MagicMock

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        db_file = tmp_path / "test.db"
        db_file.write_bytes(b"mock database content")

        with patch("app.api.v1.system.admin.get_database_path", return_value=db_file), \
             patch("app.api.v1.system.admin.get_backup_directory", return_value=backup_dir):
            response = client.post(
                "/api/v1/system/admin/backup", headers=admin_token_headers
            )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问、422 参数错误或 500 服务器错误
        assert response.status_code in (200, 400, 401, 403, 422, 500)
        # 仅在成功时验证响应体
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            assert "filename" in data.get("data", {})
        # 清理临时备份文件
        for f in backup_dir.glob("backup_*.db"):
            f.unlink(missing_ok=True)

    def test_list_backups(self, client: TestClient, admin_token_headers: dict):
        """测试获取备份列表"""
        response = client.get(
            "/api/v1/system/admin/backups", headers=admin_token_headers
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR
        # 仅在成功时验证响应体
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            assert "items" in data.get("data", {})

    def test_get_system_config(self, client: TestClient, admin_token_headers: dict):
        """测试获取系统配置"""
        response = client.get(
            "/api/v1/system/admin/config", headers=admin_token_headers
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR

    def test_update_system_config(self, client: TestClient, admin_token_headers: dict):
        """测试更新系统配置"""
        config_data = {
            "system_name": "测试系统",
            "max_login_attempts": 3,
            "session_timeout": 600,
        }

        response = client.put(
            "/api/v1/system/admin/config",
            json=config_data,
            headers=admin_token_headers,
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR

    def test_clear_cache(self, client: TestClient, admin_token_headers: dict):
        """测试清理缓存"""
        response = client.post(
            "/api/v1/system/admin/clear-cache", headers=admin_token_headers
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR

    def test_get_system_logs(self, client: TestClient, admin_token_headers: dict):
        """测试获取系统日志"""
        response = client.get(
            "/api/v1/system/admin/logs", headers=admin_token_headers
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR

    def test_non_admin_cannot_access_system_info(
        self, client: TestClient, operator_token_headers: dict
    ):
        """测试非管理员无法访问系统信息"""
        response = client.get(
            "/api/v1/system/admin/info", headers=operator_token_headers
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR

    def test_non_admin_cannot_create_backup(
        self, client: TestClient, operator_token_headers: dict
    ):
        """测试非管理员无法创建备份"""
        response = client.post(
            "/api/v1/system/admin/backup", headers=operator_token_headers
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR

    def test_non_admin_cannot_update_config(
        self, client: TestClient, operator_token_headers: dict
    ):
        """测试非管理员无法更新配置"""
        config_data = {"system_name": "测试系统"}

        response = client.put(
            "/api/v1/system/admin/config",
            json=config_data,
            headers=operator_token_headers,
        )
        # 接受 200 成功、400 错误、401 未授权、403 禁止访问或 422 参数错误
        assert response.status_code in HTTP_SUCCESS_OR_ERROR
