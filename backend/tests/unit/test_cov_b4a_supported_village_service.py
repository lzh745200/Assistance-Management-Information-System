"""覆盖率攻坚: app/services/supported_village_service.py 缺口行 24-25（name 过滤分支）."""
from unittest.mock import AsyncMock, MagicMock

from app.services.supported_village_service import SupportedVillageService


class TestGetVillagesFilters:
    async def test_name_filter_applied(self):
        """传入 name 时追加 contains 过滤（第 24-25 行）."""
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        village = MagicMock()
        village.name = "幸福村"
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [village]
        db.execute.side_effect = [count_result, list_result]

        svc = SupportedVillageService(db)
        out = await svc.get_villages(name="幸福")

        assert out["total"] == 1
        assert out["items"] == [village]
        assert out["page"] == 1
        assert db.execute.await_count == 2

    async def test_organization_and_name_filters_applied(self):
        """organization_id + name 组合过滤（第 21-25 行）."""
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = []
        db.execute.side_effect = [count_result, list_result]

        svc = SupportedVillageService(db)
        out = await svc.get_villages(organization_id=3, name="不存在")

        assert out["total"] == 0
        assert out["items"] == []
