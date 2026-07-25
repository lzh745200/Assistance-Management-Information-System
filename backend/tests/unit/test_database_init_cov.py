"""app.utils.database_init 覆盖率攻坚测试

覆盖缺口：
- 226-227：init_default_users 中管理员关联顶级组织失败的 except 降级
- 307-349：main() 的 --reset / --info / 正常全流程 / --init-only /
  连接失败提前返回 / 异常 sys.exit(1) 全部分支
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import app.utils.database_init as di


class TestInitDefaultUsersOrgLink:
    def test_org_link_failure_degrades(self, capsys):
        """用户初始化主流程成功，但关联组织查询抛异常 → warning 降级继续提交（226-227）"""
        db = MagicMock()
        q_users = MagicMock()
        q_users.count.return_value = 0
        # 第一次 db.query（User count）正常；第二次（Organization）抛异常
        db.query.side_effect = [q_users, Exception("org table gone")]

        di.init_default_users(db)

        db.add_all.assert_called_once()
        db.commit.assert_called_once()
        # 控制台一次性口令提示仍输出
        out = capsys.readouterr().out
        assert "初始登录口令" in out


class TestMain:
    def _run_main(self, argv, **mock_cfg):
        """在隔离 mock 环境下执行 main()，返回各 mock 以便断言"""
        with patch.object(sys, "argv", ["database_init.py"] + argv), \
             patch.object(di, "reset_database") as m_reset, \
             patch.object(di, "get_database_info") as m_info, \
             patch.object(di, "check_database_connection", return_value=mock_cfg.get("conn_ok", True)) as m_conn, \
             patch.object(di, "create_database_if_not_exists") as m_create, \
             patch.object(di, "init_database_tables") as m_tables, \
             patch.object(di, "init_default_roles") as m_roles, \
             patch.object(di, "init_default_users") as m_users, \
             patch.object(di, "SessionLocal") as m_session:
            di.main()
        return SimpleNamespace(
            reset=m_reset, info=m_info, conn=m_conn, create=m_create,
            tables=m_tables, roles=m_roles, users=m_users, session=m_session,
        )

    def test_reset_branch(self):
        m = self._run_main(["--reset"])
        m.reset.assert_called_once()
        m.info.assert_called_once()  # 尾部统计仍执行
        m.roles.assert_called_once()
        m.users.assert_called_once()

    def test_info_branch_returns_early(self):
        m = self._run_main(["--info"])
        m.info.assert_called_once()
        m.create.assert_not_called()
        m.roles.assert_not_called()

    def test_normal_full_flow(self):
        m = self._run_main([])
        m.create.assert_called_once()
        m.tables.assert_called_once()
        m.roles.assert_called_once()
        m.users.assert_called_once()

    def test_init_only_skips_default_data(self):
        m = self._run_main(["--init-only"])
        m.tables.assert_called_once()
        m.roles.assert_not_called()
        m.users.assert_not_called()

    def test_connection_failure_returns(self):
        m = self._run_main([], conn_ok=False)
        m.create.assert_not_called()
        m.roles.assert_not_called()

    def test_exception_exits_1(self):
        with patch.object(sys, "argv", ["database_init.py"]), \
             patch.object(di, "reset_database", side_effect=Exception("boom")), \
             pytest.raises(SystemExit) as exc:
            di.main()
        assert exc.value.code == 1
