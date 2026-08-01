"""app.api.v1.data_scope 覆盖补全 — filter_by_org_ids 有 org_ids 但未传列时的拒绝兜底 (line 77)."""
from unittest.mock import MagicMock

from app.api.v1.data_scope import DataScope


class TestFilterByOrgIdsNoColumns:
    def test_org_ids_without_columns_denies_all(self):
        ds = DataScope(is_admin=False, org_ids=[1, 2])
        q = MagicMock()
        result = ds.filter_by_org_ids(q)
        q.filter.assert_called_once_with(False)
        assert result == q.filter.return_value
