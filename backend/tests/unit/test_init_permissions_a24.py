"""app.utils.init_permissions.main() 覆盖补充测试（a24）

缺口：211-225（main 函数成功路径与异常回滚路径）
"""
import pytest
from unittest.mock import MagicMock, patch

from app.utils import init_permissions as ip_module


class TestMain:
    def test_main_success(self):
        mock_db = MagicMock()
        with patch("app.core.database.SessionLocal", return_value=mock_db) as mock_session, \
             patch.object(ip_module, "init_permissions") as mock_init_perms, \
             patch.object(ip_module, "init_roles") as mock_init_roles:
            ip_module.main()

        mock_session.assert_called_once_with()
        mock_init_perms.assert_called_once_with(mock_db)
        mock_init_roles.assert_called_once_with(mock_db)
        mock_db.rollback.assert_not_called()
        mock_db.close.assert_called_once_with()

    def test_main_failure_rolls_back_and_reraises(self):
        mock_db = MagicMock()
        with patch("app.core.database.SessionLocal", return_value=mock_db), \
             patch.object(ip_module, "init_permissions", side_effect=RuntimeError("boom")), \
             patch.object(ip_module, "init_roles") as mock_init_roles:
            with pytest.raises(RuntimeError, match="boom"):
                ip_module.main()

        mock_init_roles.assert_not_called()
        mock_db.rollback.assert_called_once_with()
        mock_db.close.assert_called_once_with()

    def test_main_init_roles_failure_also_rolls_back(self):
        mock_db = MagicMock()
        with patch("app.core.database.SessionLocal", return_value=mock_db), \
             patch.object(ip_module, "init_permissions"), \
             patch.object(ip_module, "init_roles", side_effect=ValueError("role error")):
            with pytest.raises(ValueError, match="role error"):
                ip_module.main()

        mock_db.rollback.assert_called_once_with()
        mock_db.close.assert_called_once_with()
