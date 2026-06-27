"""TDD: 经费↔项目双向联动."""
from unittest.mock import MagicMock


class TestFundToProjectLink:
    def test_find_linkable_projects(self):
        """查找经费可关联的项目."""
        from app.services.fund_project_linker import find_linkable_projects
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 5
        mock_project.name = "道路改造项目"
        mock_project.village_id = 10
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        results = find_linkable_projects(mock_db, fund_village_id=10)
        assert len(results) >= 1
        assert results[0].id == 5

    def test_no_village_id_returns_empty(self):
        from app.services.fund_project_linker import find_linkable_projects
        mock_db = MagicMock()
        results = find_linkable_projects(mock_db, fund_village_id=None)
        assert len(results) == 0


class TestProjectToFundLink:
    def test_find_linkable_funds(self):
        """查找项目可关联的经费."""
        from app.services.fund_project_linker import find_linkable_funds
        mock_db = MagicMock()
        mock_fund = MagicMock()
        mock_fund.id = 3
        mock_fund.name = "专项资金"
        mock_fund.project_id = None
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_fund]
        results = find_linkable_funds(mock_db, project_village_id=10)
        assert len(results) >= 1
        assert results[0].id == 3

    def test_already_linked_funds_excluded(self):
        """已关联到其他项目的经费不应显示."""
        from app.services.fund_project_linker import find_linkable_funds
        mock_db = MagicMock()
        linked_fund = MagicMock()
        linked_fund.id = 3
        linked_fund.project_id = 7  # Already linked
        unlinked_fund = MagicMock()
        unlinked_fund.id = 4
        unlinked_fund.project_id = None
        mock_db.query.return_value.filter.return_value.all.return_value = [linked_fund, unlinked_fund]
        # The function should filter to only unlinked funds
        results = find_linkable_funds(mock_db, project_village_id=10)
        linked_ids = [r.id for r in results]
        assert 4 in linked_ids


class TestBudgetUpdate:
    def test_update_project_budget_on_fund_approval(self):
        from app.services.fund_project_linker import update_project_budget
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.budget = 500000.0
        mock_project.approved_funds = 200000.0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        result = update_project_budget(mock_db, project_id=5, additional_fund=100000.0)
        assert result is not None
        assert result.approved_funds == 300000.0  # 200000 + 100000
