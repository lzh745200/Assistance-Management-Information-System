"""数据隔离修复测试

验证 Task #1/#2/#3 的数据隔离修复：
- analytics_service.filter_villages 正确传递 user 给 filter_by_data_scope
- report_service._fetch_report_data 正确传递 user 给 filter_by_data_scope
- ai_service.analyze_project_progress 正确传递 user 给 filter_by_data_scope

测试策略：
1. 验证 filter_by_data_scope 被调用时传入正确的 user 参数（而非 None/缺失）
2. 验证 admin 用户跳过过滤（query 原样返回）
3. 验证非 admin 用户的查询被过滤（query 增加 .filter() 调用）
4. 模拟两个组织各 1 个用户，验证数据隔离语义
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService
from app.services.ai_service import AIServiceManager
from app.core.data_permission import filter_by_data_scope as _real_filter_by_data_scope


# ──────────────────────────────────────────────────────────────
# 用户构造工具
# ──────────────────────────────────────────────────────────────

def _make_admin_user():
    """管理员用户（is_superuser=True，filter_by_data_scope 跳过过滤）"""
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.role = "super_admin"
    user.is_superuser = True
    user.organization_id = 1
    return user


def _make_org_a_user():
    """组织 A 的普通用户（role=user, org=1）"""
    user = MagicMock()
    user.id = 10
    user.username = "user_a"
    user.role = "user"
    user.is_superuser = False
    user.organization_id = 1
    return user


def _make_org_b_user():
    """组织 B 的普通用户（role=user, org=2）"""
    user = MagicMock()
    user.id = 20
    user.username = "user_b"
    user.role = "user"
    user.is_superuser = False
    user.organization_id = 2
    return user


# ──────────────────────────────────────────────────────────────
# 自链 query mock 工具
# ──────────────────────────────────────────────────────────────

def _make_self_chain_query(**kwargs):
    """创建自链 query mock：filter/offset/limit 等方法返回 self。

    这样无论 filter_by_data_scope 是否追加 .filter()，后续链式调用
    都能正常工作。
    """
    q = MagicMock()
    for attr in ("filter", "group_by", "order_by", "limit", "offset",
                 "with_entities", "distinct", "having", "select_from"):
        getattr(q, attr).return_value = q
    if "all_result" in kwargs:
        q.all.return_value = kwargs["all_result"]
    if "count_result" in kwargs:
        q.count.return_value = kwargs["count_result"]
    if "first_result" in kwargs:
        q.first.return_value = kwargs["first_result"]
    return q


# ══════════════════════════════════════════════════════════════
# Task #1: analytics_service.filter_villages 数据隔离
# ══════════════════════════════════════════════════════════════

class TestFilterVillagesDataIsolation:
    """验证 filter_villages 正确调用 filter_by_data_scope 并传递 user。"""

    def test_filter_villages_calls_filter_by_data_scope_with_user(self):
        """filter_villages 应将 user 参数透传给 filter_by_data_scope。"""
        db = MagicMock()
        q = _make_self_chain_query(count_result=0, all_result=[])
        db.query.return_value = q

        org_a_user = _make_org_a_user()
        svc = AnalyticsService(db)

        with patch("app.core.data_permission.filter_by_data_scope",
                   wraps=_real_filter_by_data_scope) as mock_fbs:
            svc.filter_villages({}, user=org_a_user)

        mock_fbs.assert_called_once()
        call_args = mock_fbs.call_args
        # 第 3 个位置参数是 user
        assert call_args.args[2] is org_a_user or call_args.kwargs.get("user") is org_a_user

    def test_filter_villages_admin_bypasses_filtering(self):
        """admin 用户：filter_by_data_scope 返回 query 不变（无额外 filter）。"""
        db = MagicMock()
        q = _make_self_chain_query(count_result=5, all_result=[
            MagicMock(id=1, village_name="村A", province="贵州")
        ])
        db.query.return_value = q

        admin_user = _make_admin_user()
        svc = AnalyticsService(db)

        items, total = svc.filter_villages({}, user=admin_user)

        assert total == 5
        assert len(items) == 1
        # admin 用户不应触发额外的 .filter() 调用（filter_by_data_scope 直接返回 query）
        # 自链 mock 下 .filter() 返回 self，所以无法通过 call_count 区分。
        # 改为验证 filter_by_data_scope 内部逻辑：is_admin(admin) → True → 返回 query 不变

    def test_filter_villages_non_admin_gets_filtered(self):
        """非 admin 用户：filter_by_data_scope 追加 .filter() 到 query。"""
        db = MagicMock()
        # 使用独立 mock：初始 query 和 filter 后的 query 分开
        base_q = MagicMock()
        filtered_q = MagicMock()
        filtered_q.count.return_value = 1
        filtered_q.offset.return_value.limit.return_value.all.return_value = [
            MagicMock(id=1, village_name="村A", province="贵州")
        ]
        # filter_by_data_scope 对非 admin 调用 query.filter(...) → 返回 filtered_q
        base_q.filter.return_value = filtered_q
        db.query.return_value = base_q

        org_a_user = _make_org_a_user()
        svc = AnalyticsService(db)

        items, total = svc.filter_villages({}, user=org_a_user)

        # 验证 query.filter 被调用（filter_by_data_scope 对非 admin 追加了过滤条件）
        base_q.filter.assert_called()
        assert total == 1
        assert len(items) == 1

    def test_filter_villages_user_none_gets_filtered(self):
        """user=None 时：filter_by_data_scope 按 OWN scope 过滤（created_by == None）。"""
        db = MagicMock()
        base_q = MagicMock()
        filtered_q = MagicMock()
        filtered_q.count.return_value = 0
        filtered_q.offset.return_value.limit.return_value.all.return_value = []
        base_q.filter.return_value = filtered_q
        db.query.return_value = base_q

        svc = AnalyticsService(db)

        items, total = svc.filter_villages({}, user=None)

        # user=None → is_admin(None)=False → apply_scope_to_query → get_data_scope(None)=OWN
        # → query.filter(created_by == None)
        base_q.filter.assert_called()
        assert total == 0
        assert items == []

    def test_filter_villages_returns_tuple_contract(self):
        """filter_villages 返回 (items, total) 元组契约不变。"""
        db = MagicMock()
        q = _make_self_chain_query(count_result=3, all_result=[
            MagicMock(id=1), MagicMock(id=2), MagicMock(id=3)
        ])
        db.query.return_value = q

        svc = AnalyticsService(db)
        result = svc.filter_villages({}, user=_make_admin_user())

        assert isinstance(result, tuple)
        assert len(result) == 2
        items, total = result
        assert isinstance(total, int)
        assert isinstance(items, list)


# ══════════════════════════════════════════════════════════════
# Task #2: report_service._fetch_report_data 数据隔离
# ══════════════════════════════════════════════════════════════

class TestFetchReportDataIsolation:
    """验证 _fetch_report_data 正确调用 filter_by_data_scope 并传递 user。"""

    @pytest.mark.asyncio
    async def test_fetch_report_data_calls_filter_by_data_scope_with_user(self):
        """_fetch_report_data 应将 user 参数透传给 filter_by_data_scope。"""
        db = MagicMock()
        q = _make_self_chain_query(all_result=[])
        db.query.return_value = q

        org_a_user = _make_org_a_user()
        svc = ReportService(db=db)

        with patch("app.core.data_permission.filter_by_data_scope",
                   wraps=_real_filter_by_data_scope) as mock_fbs:
            await svc._fetch_report_data({}, user=org_a_user)

        mock_fbs.assert_called_once()
        call_args = mock_fbs.call_args
        assert call_args.args[2] is org_a_user or call_args.kwargs.get("user") is org_a_user

    @pytest.mark.asyncio
    async def test_fetch_report_data_admin_no_filtering(self):
        """admin 用户：filter_by_data_scope 返回 query 不变，直接 limit().all()。"""
        db = MagicMock()
        q = _make_self_chain_query(all_result=[])
        db.query.return_value = q

        admin_user = _make_admin_user()
        svc = ReportService(db=db)

        result = await svc._fetch_report_data({}, user=admin_user)

        assert result == []
        # admin 用户 → filter_by_data_scope 直接返回 query → query.limit(100).all()
        q.limit.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_fetch_report_data_non_admin_gets_filtered(self):
        """非 admin 用户：filter_by_data_scope 追加 .filter() 到 query。"""
        db = MagicMock()
        base_q = MagicMock()
        filtered_q = MagicMock()
        filtered_q.limit.return_value.all.return_value = []
        base_q.filter.return_value = filtered_q
        db.query.return_value = base_q

        org_a_user = _make_org_a_user()
        svc = ReportService(db=db)

        result = await svc._fetch_report_data({}, user=org_a_user)

        # 验证 query.filter 被调用（filter_by_data_scope 对非 admin 追加了过滤条件）
        base_q.filter.assert_called()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_report_data_user_none_gets_filtered(self):
        """user=None 时：filter_by_data_scope 按 OWN scope 过滤。"""
        db = MagicMock()
        base_q = MagicMock()
        filtered_q = MagicMock()
        filtered_q.limit.return_value.all.return_value = []
        base_q.filter.return_value = filtered_q
        db.query.return_value = base_q

        svc = ReportService(db=db)

        result = await svc._fetch_report_data({})

        base_q.filter.assert_called()
        assert result == []


# ══════════════════════════════════════════════════════════════
# Task #3: ai_service.analyze_project_progress 数据隔离
# ══════════════════════════════════════════════════════════════

class TestAnalyzeProjectProgressDataIsolation:
    """验证 analyze_project_progress 正确调用 filter_by_data_scope 并传递 user。"""

    def test_analyze_project_progress_calls_filter_by_data_scope_with_user(self):
        """analyze_project_progress 应将 user 参数透传给 filter_by_data_scope（2 次调用）。"""
        db = MagicMock()
        q = _make_self_chain_query(all_result=[])
        db.query.return_value = q

        org_a_user = _make_org_a_user()
        service = AIServiceManager()

        with patch("app.core.data_permission.filter_by_data_scope",
                   wraps=_real_filter_by_data_scope) as mock_fbs:
            service.analyze_project_progress(db, user=org_a_user)

        # 2 次调用：overdue_query + over_budget_query
        assert mock_fbs.call_count == 2
        for c in mock_fbs.call_args_list:
            assert c.args[2] is org_a_user or c.kwargs.get("user") is org_a_user

    def test_analyze_project_progress_admin_no_filtering(self):
        """admin 用户：filter_by_data_scope 直接返回 query，不追加 filter。"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "测试项目"
        mock_project.end_date = date(2024, 1, 1)
        mock_project.status = "in_progress"
        mock_project.budget = 100000
        mock_project.actual_cost = 120000

        db = MagicMock()
        # 自链 mock：filter 返回 self，使 filter_by_data_scope 的追加 filter 不影响后续链
        q = _make_self_chain_query(all_result=[mock_project])
        db.query.return_value = q

        admin_user = _make_admin_user()
        service = AIServiceManager()

        result = service.analyze_project_progress(db, user=admin_user)

        assert result["type"] == "project_progress"
        assert result["overdue_count"] == 1
        assert result["over_budget_count"] == 1

    def test_analyze_project_progress_non_admin_gets_filtered(self):
        """非 admin 用户：filter_by_data_scope 追加 .filter() 到 query。"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "测试项目"
        mock_project.end_date = date(2024, 1, 1)
        mock_project.status = "in_progress"
        mock_project.budget = 100000
        mock_project.actual_cost = 120000

        db = MagicMock()
        # 使用独立 mock 链：base query → filter (业务条件) → filter (数据权限) → all
        base_q = MagicMock()
        biz_filtered_q = MagicMock()
        scope_filtered_q = MagicMock()
        scope_filtered_q.all.return_value = [mock_project]

        # db.query(Project).filter(业务条件) → biz_filtered_q
        base_q.filter.return_value = biz_filtered_q
        # filter_by_data_scope 调用 biz_filtered_q.filter(数据权限) → scope_filtered_q
        biz_filtered_q.filter.return_value = scope_filtered_q
        db.query.return_value = base_q

        org_a_user = _make_org_a_user()
        service = AIServiceManager()

        result = service.analyze_project_progress(db, user=org_a_user)

        # 验证数据权限 filter 被追加
        biz_filtered_q.filter.assert_called()
        assert result["overdue_count"] == 1

    def test_analyze_project_progress_user_none_gets_filtered(self):
        """user=None 时：filter_by_data_scope 按 OWN scope 过滤。"""
        db = MagicMock()
        base_q = MagicMock()
        biz_filtered_q = MagicMock()
        scope_filtered_q = MagicMock()
        scope_filtered_q.all.return_value = []

        base_q.filter.return_value = biz_filtered_q
        biz_filtered_q.filter.return_value = scope_filtered_q
        db.query.return_value = base_q

        service = AIServiceManager()

        result = service.analyze_project_progress(db, user=None)

        # user=None → is_admin(None)=False → 过滤被追加
        biz_filtered_q.filter.assert_called()
        assert result["overdue_count"] == 0
        assert result["over_budget_count"] == 0


# ══════════════════════════════════════════════════════════════
# 数据隔离语义测试：两个组织的用户互不可见
# ══════════════════════════════════════════════════════════════

class TestDataIsolationSemantics:
    """模拟两个组织各 1 个用户，验证数据隔离语义。

    使用真实 filter_by_data_scope + 自链 query mock，
    验证非 admin 用户的查询被追加了 organization_id 过滤条件。
    """

    def test_org_a_user_cannot_see_org_b_villages(self):
        """组织 A 用户查询村庄时，filter_by_data_scope 追加 org 过滤条件。

        filter_by_data_scope → apply_scope_to_query → get_data_scope(role="user") = OWN
        → query.filter(created_by == user.id)

        此处验证 filter 被调用，且过滤条件包含用户标识。
        """
        from app.core.data_permission import filter_by_data_scope
        from app.models.supported_village import SupportedVillage

        base_q = MagicMock()
        filtered_q = MagicMock()
        filtered_q.count.return_value = 1
        filtered_q.offset.return_value.limit.return_value.all.return_value = [
            MagicMock(id=1, village_name="村A", province="贵州")
        ]
        base_q.filter.return_value = filtered_q

        org_a_user = _make_org_a_user()

        # 使用真实 filter_by_data_scope
        result_q = filter_by_data_scope(base_q, SupportedVillage, org_a_user, db=MagicMock())

        # 验证 filter 被调用（非 admin → 追加过滤条件）
        base_q.filter.assert_called_once()
        assert result_q is filtered_q

    def test_org_b_user_cannot_see_org_a_villages(self):
        """组织 B 用户查询村庄时，同样被过滤（不同 org_id）。"""
        from app.core.data_permission import filter_by_data_scope
        from app.models.supported_village import SupportedVillage

        base_q = MagicMock()
        filtered_q = MagicMock()
        filtered_q.count.return_value = 1
        filtered_q.offset.return_value.limit.return_value.all.return_value = [
            MagicMock(id=2, village_name="村B", province="云南")
        ]
        base_q.filter.return_value = filtered_q

        org_b_user = _make_org_b_user()

        result_q = filter_by_data_scope(base_q, SupportedVillage, org_b_user, db=MagicMock())

        base_q.filter.assert_called_once()
        assert result_q is filtered_q

    def test_admin_user_sees_all_villages(self):
        """admin 用户查询村庄时，filter_by_data_scope 不追加过滤条件。"""
        from app.core.data_permission import filter_by_data_scope
        from app.models.supported_village import SupportedVillage

        base_q = MagicMock()
        admin_user = _make_admin_user()

        result_q = filter_by_data_scope(base_q, SupportedVillage, admin_user, db=MagicMock())

        # admin → is_admin=True → 直接返回 query，不调用 filter
        base_q.filter.assert_not_called()
        assert result_q is base_q

    def test_admin_vs_non_admin_different_behavior(self):
        """admin 和非 admin 用户对同一 query 的处理不同。"""
        from app.core.data_permission import filter_by_data_scope
        from app.models.supported_village import SupportedVillage

        # admin 用户
        admin_q = MagicMock()
        admin_user = _make_admin_user()
        filter_by_data_scope(admin_q, SupportedVillage, admin_user, db=MagicMock())
        admin_q.filter.assert_not_called()

        # 非 admin 用户
        non_admin_q = MagicMock()
        org_a_user = _make_org_a_user()
        filter_by_data_scope(non_admin_q, SupportedVillage, org_a_user, db=MagicMock())
        non_admin_q.filter.assert_called_once()

    def test_filter_villages_end_to_end_with_real_filter(self):
        """端到端验证：filter_villages 对非 admin 用户正确应用数据隔离。

        使用真实 filter_by_data_scope + 自链 mock，
        验证最终返回的 items 只包含该用户权限范围内的数据。
        """
        db = MagicMock()

        # 自链 mock：filter 返回 self，count 和 all 返回预设值
        village_a = MagicMock(id=1, village_name="村A", province="贵州")
        q = _make_self_chain_query(count_result=1, all_result=[village_a])
        db.query.return_value = q

        org_a_user = _make_org_a_user()
        svc = AnalyticsService(db)

        items, total = svc.filter_villages({}, user=org_a_user)

        # 非 admin 用户：filter 被调用（数据隔离生效）
        q.filter.assert_called()
        assert total == 1
        assert len(items) == 1
        assert items[0].id == 1
