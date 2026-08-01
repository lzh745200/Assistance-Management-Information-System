"""补齐 app.services.analytics_service 覆盖率缺口。

目标行：620、622、624 —— filter_villages 的 department / is_three_regions /
is_key_county 三个筛选分支。
"""

from unittest.mock import MagicMock

from app.services.analytics_service import AnalyticsService


def _make_query_mock():
    q = MagicMock()
    q.filter.return_value = q
    q.offset.return_value = q
    q.limit.return_value = q
    return q


class TestFilterVillagesExtendedFilters:
    def test_department_and_region_flags_filters(self):
        db = MagicMock()
        q = _make_query_mock()
        q.count.return_value = 2
        q.all.return_value = [MagicMock(id=1), MagicMock(id=2)]
        db.query.return_value = q

        svc = AnalyticsService(db)
        items, total = svc.filter_villages(
            {
                "department": "某部",
                "is_three_regions": True,
                "is_key_county": False,
            },
            page=1,
            page_size=10,
        )

        assert total == 2
        assert len(items) == 2
