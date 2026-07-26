"""补齐 app.services.policy_fts_service 覆盖率缺口（FTS5 失败降级 LIKE 分支，80-84 行）."""
from unittest.mock import MagicMock

from app.services import policy_fts_service as fts


class TestSearchPoliciesFtsFallback:
    def test_fts_failure_falls_back_to_like(self):
        db = MagicMock()
        exists = MagicMock()
        exists.fetchone.return_value = ("policies_fts",)  # ensure_fts_table 早退
        rows = MagicMock()
        rows.fetchall.return_value = [
            (1, "标题", "摘要", "关键词", "省级", "产业", "摘要片段", 0.0),
        ]
        db.execute.side_effect = [exists, Exception("fts5 broken"), rows]

        result = fts.search_policies_fts(db, "乡村振兴")

        assert db.execute.call_count == 3
        assert result[0]["id"] == 1
        assert result[0]["title"] == "标题"
        assert result[0]["rank"] == 0.0
