"""覆盖 app.core.transaction 缺口：非 SQLite 环境下的事务隔离/只读设置。"""
from unittest.mock import MagicMock

import app.core.transaction as tx


class TestApplyTxSettings:
    def test_non_sqlite_applies_isolation_and_readonly(self, monkeypatch):
        monkeypatch.setattr(tx, "IS_SQLITE", False)
        sess = MagicMock()

        tx._apply_tx_settings(sess, "SERIALIZABLE", True)

        assert sess.execute.call_count == 2
        statements = [str(call.args[0]) for call in sess.execute.call_args_list]
        assert any("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE" in s for s in statements)
        assert any("SET TRANSACTION READ ONLY" in s for s in statements)

    def test_non_sqlite_isolation_only(self, monkeypatch):
        monkeypatch.setattr(tx, "IS_SQLITE", False)
        sess = MagicMock()

        tx._apply_tx_settings(sess, "READ COMMITTED", False)

        assert sess.execute.call_count == 1
