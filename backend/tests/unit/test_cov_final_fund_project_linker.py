"""补齐 app.services.fund_project_linker 覆盖率缺口。

目标行：
- 28：find_linkable_funds 的 village_id 为 None → 返回空列表
- 47：update_project_budget 项目不存在 → 返回 None
- 50：approved_funds 为 None → 按 0 累加
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services import fund_project_linker as linker


class TestFindLinkableFunds:
    def test_none_village_returns_empty(self):
        assert linker.find_linkable_funds(MagicMock(), None) == []


class TestUpdateProjectBudget:
    def test_project_not_found_returns_none(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        assert linker.update_project_budget(db, 999, 100.0) is None

    def test_none_approved_funds_treated_as_zero(self):
        project = SimpleNamespace(approved_funds=None)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project

        out = linker.update_project_budget(db, 1, 50.0)

        assert out is project
        assert project.approved_funds == 50.0
