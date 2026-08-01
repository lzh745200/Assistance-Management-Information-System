"""覆盖 app.core.data_permission 缺口：未知 scope 的防御性兜底返回。"""
from unittest.mock import MagicMock, patch

import app.core.data_permission as dp


class TestUnknownScopeFallback:
    """get_data_scope 返回未知值时（防御性分支，正常枚举不会到达）。"""

    def test_apply_scope_to_query_returns_query_unchanged(self):
        query = MagicMock(name="query")
        model = MagicMock(name="model")
        user = MagicMock(name="user")
        with patch.object(dp, "get_data_scope", return_value="unknown_scope"):
            result = dp.apply_scope_to_query(query, model, user)
        assert result is query
        query.filter.assert_not_called()

    def test_check_record_access_returns_false(self):
        record = MagicMock(name="record")
        user = MagicMock(name="user")
        with patch.object(dp, "get_data_scope", return_value="unknown_scope"):
            assert dp.check_record_access(record, user) is False
