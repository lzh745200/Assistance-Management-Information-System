"""app.services.smart_conflict_resolver 覆盖率攻坚测试（补充既有测试未覆盖分支）

覆盖点：
- resolve_conflicts_with_strategy 的 AUTO 策略三分支（SKIP/OVERWRITE/MERGE）
- _determine_auto_strategy：少量差异→MERGE、时间戳比较（字符串/datetime/非法）→各策略
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.smart_conflict_resolver import (
    ConflictStrategy,
    DataConflict,
    SmartConflictResolver,
)


def _resolver():
    return SmartConflictResolver(MagicMock())


def _conflict(differences, import_record, local_record):
    return DataConflict(
        data_type="projects",
        business_key={"code": import_record.get("code", "C1")},
        local_record=local_record,
        import_record=import_record,
        differences=differences,
    )


class TestAutoStrategyResolution:
    def test_auto_skip(self):
        """导入时间更旧 → AUTO 选 SKIP"""
        local = SimpleNamespace(id=10, name="本地", updated_at=datetime(2026, 6, 1))
        imp = {"id": 99, "code": "C1", "name": "导入", "updated_at": datetime(2026, 1, 1)}
        conflict = _conflict(["name", "type", "budget"], imp, local)
        r = _resolver()
        mapping = r.resolve_conflicts_with_strategy([conflict], ConflictStrategy.AUTO)
        assert mapping == {"projects": {99: 10}}
        assert local.name == "本地"  # 未被覆盖

    def test_auto_overwrite(self):
        """导入时间更新（字符串时间戳）→ AUTO 选 OVERWRITE"""
        local = SimpleNamespace(id=10, name="本地", updated_at="2026-01-01T00:00:00")
        imp = {"id": 99, "code": "C1", "name": "导入", "updated_at": "2026-06-01T00:00:00"}
        conflict = _conflict(["name", "type", "budget"], imp, local)
        r = _resolver()
        mapping = r.resolve_conflicts_with_strategy([conflict], ConflictStrategy.AUTO)
        assert mapping == {"projects": {99: 10}}
        assert local.name == "导入"
        r.db.flush.assert_called()

    def test_auto_merge(self):
        """差异≤2 → AUTO 选 MERGE：本地空值用导入值，导入更新时覆盖"""
        local = SimpleNamespace(id=10, name=None, budget=100, updated_at=datetime(2026, 1, 1))
        imp = {
            "id": 99, "code": "C1", "name": "导入名", "budget": 200,
            "updated_at": datetime(2026, 6, 1),
        }
        conflict = _conflict(["name", "budget"], imp, local)
        mapping = _resolver().resolve_conflicts_with_strategy([conflict], ConflictStrategy.AUTO)
        assert mapping == {"projects": {99: 10}}
        assert local.name == "导入名"   # 本地为空 → 采用导入值
        assert local.budget == 200      # 导入更新 → 覆盖


class TestDetermineAutoStrategy:
    def test_few_differences_merge(self):
        conflict = _conflict(["a"], {"code": "C1"}, SimpleNamespace(id=1))
        assert _resolver()._determine_auto_strategy(conflict) == ConflictStrategy.MERGE

    def test_import_newer_overwrite(self):
        local = SimpleNamespace(updated_at=datetime(2026, 1, 1))
        conflict = _conflict(
            ["a", "b", "c"],
            {"code": "C1", "updated_at": datetime(2026, 6, 1)},
            local,
        )
        assert _resolver()._determine_auto_strategy(conflict) == ConflictStrategy.OVERWRITE

    def test_local_newer_skip(self):
        local = SimpleNamespace(updated_at=datetime(2026, 6, 1))
        conflict = _conflict(
            ["a", "b", "c"],
            {"code": "C1", "updated_at": "2026-01-01T00:00:00"},
            local,
        )
        assert _resolver()._determine_auto_strategy(conflict) == ConflictStrategy.SKIP

    def test_invalid_timestamp_falls_back_merge(self):
        local = SimpleNamespace(updated_at="not-a-date")
        conflict = _conflict(
            ["a", "b", "c"],
            {"code": "C1", "updated_at": "also-bad"},
            local,
        )
        assert _resolver()._determine_auto_strategy(conflict) == ConflictStrategy.MERGE

    def test_missing_timestamps_merge(self):
        conflict = _conflict(["a", "b", "c"], {"code": "C1"}, SimpleNamespace(updated_at=None))
        assert _resolver()._determine_auto_strategy(conflict) == ConflictStrategy.MERGE
