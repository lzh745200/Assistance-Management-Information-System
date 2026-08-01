"""补齐 app.services.policy_fts_service 覆盖率缺口。

目标行：
- 138：sync_policy_to_fts 政策行不存在 → 早退
- 151-152：sync 异常 → 吞掉并记 debug 日志（不抛出）
- 160-161：remove 异常 → 吞掉并记 debug 日志（不抛出）
"""

from unittest.mock import MagicMock

from app.services.policy_fts_service import remove_policy_from_fts, sync_policy_to_fts


class TestSyncPolicyToFts:
    def test_missing_row_returns_early(self):
        db = MagicMock()
        db.execute.return_value.fetchone.return_value = None

        sync_policy_to_fts(db, 1)

        # 只执行了 SELECT，未执行 DELETE/INSERT
        assert db.execute.call_count == 1

    def test_exception_swallowed(self):
        db = MagicMock()
        db.execute.side_effect = RuntimeError("fts down")

        sync_policy_to_fts(db, 1)  # 不应抛出


class TestRemovePolicyFromFts:
    def test_exception_swallowed(self):
        db = MagicMock()
        db.execute.side_effect = RuntimeError("fts down")

        remove_policy_from_fts(db, 1)  # 不应抛出
