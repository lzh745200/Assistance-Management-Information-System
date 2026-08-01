"""覆盖 app.main 缺口：_run_alembic_upgrade 的 upgrade head 分支（行 433-434）。"""
from unittest.mock import patch

import alembic.command  # noqa: F401  确保 patch("alembic.command") 目标属性存在

from app.main import _run_alembic_upgrade


class TestRunAlembicUpgrade:
    def test_upgrade_head_when_alembic_version_table_exists(self):
        # 已有 alembic_version 表 → 走 else 分支执行真正的 upgrade（行 433-434）
        with patch("alembic.command") as mock_cmd, patch("sqlalchemy.inspect") as mock_inspect:
            mock_inspect.return_value.get_table_names.return_value = [
                "users",
                "supported_villages",
                "alembic_version",
            ]
            _run_alembic_upgrade()

        mock_cmd.upgrade.assert_called_once()
        mock_cmd.stamp.assert_not_called()

    def test_stamp_head_when_business_tables_without_version(self):
        # 对照组：无 alembic_version 但有业务表 → stamp 分支
        with patch("alembic.command") as mock_cmd, patch("sqlalchemy.inspect") as mock_inspect:
            mock_inspect.return_value.get_table_names.return_value = [
                "users",
                "supported_villages",
            ]
            _run_alembic_upgrade()

        mock_cmd.stamp.assert_called_once()
        mock_cmd.upgrade.assert_not_called()
