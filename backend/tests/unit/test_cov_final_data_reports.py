"""app.api.v1.data.data.reports 覆盖补全 — 更新订阅时 village_ids JSON 序列化分支 (line 494).

注：ReportSubscriptionUpdate schema 未暴露 village_ids 字段，HTTP 层无法到达该分支，
因此直接调用端点函数并构造含 village_ids 的 model_dump 结果。
"""
from unittest.mock import MagicMock, patch

from app.api.v1.data.data.reports import update_subscription


class TestUpdateSubscription:
    async def test_village_ids_serialized_to_json(self):
        subscription = MagicMock(name="subscription")
        subscription.id = 1
        subscription.village_ids = None
        subscription.include_sections = None

        db = MagicMock(name="db")
        q = MagicMock(name="query")
        q.filter.return_value = q
        q.first.return_value = subscription
        db.query.return_value = q

        update_data = MagicMock(name="update_data")
        update_data.model_dump.return_value = {"village_ids": [1, 2]}

        user = MagicMock(name="user")
        user.id = 9

        with patch("app.api.v1.data.data.reports.safe_commit"):
            result = await update_subscription(1, update_data, user, db)

        # line 494: village_ids 被 JSON 序列化后写入模型
        assert subscription.village_ids == "[1, 2]"
        # 响应中又被反序列化回列表
        assert result["village_ids"] == [1, 2]
