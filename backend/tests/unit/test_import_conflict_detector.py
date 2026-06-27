"""TDD: 导入冲突检测引擎."""


class TestIdConflict:
    def test_same_id_different_fields_is_conflict(self):
        from app.services.import_conflict_detector import detect_id_conflicts
        local = [{"id": 1, "name": "幸福村", "population": 500}]
        imported = [{"id": 1, "name": "幸福村", "population": 600}]
        conflicts = detect_id_conflicts(local, imported)
        assert len(conflicts) >= 1
        c = conflicts[0]
        assert c["type"] == "id_conflict"
        assert "population" in str(c.get("diff_fields", []))

    def test_same_id_same_fields_no_conflict(self):
        from app.services.import_conflict_detector import detect_id_conflicts
        local = [{"id": 1, "name": "幸福村"}]
        imported = [{"id": 1, "name": "幸福村"}]
        conflicts = detect_id_conflicts(local, imported)
        assert len(conflicts) == 0

    def test_new_record_no_conflict(self):
        from app.services.import_conflict_detector import detect_id_conflicts
        local = [{"id": 1, "name": "幸福村"}]
        imported = [{"id": 2, "name": "新村庄"}]
        assert len(detect_id_conflicts(local, imported)) == 0


class TestUniqueKeyConflict:
    def test_same_village_name_county_is_conflict(self):
        from app.services.import_conflict_detector import detect_unique_key_conflicts
        local = [{"village_name": "幸福村", "county": "丹寨县"}]
        imported = [{"village_name": "幸福村", "county": "丹寨县"}]
        conflicts = detect_unique_key_conflicts(local, imported, keys=["village_name", "county"])
        assert len(conflicts) >= 1

    def test_different_county_no_conflict(self):
        from app.services.import_conflict_detector import detect_unique_key_conflicts
        local = [{"village_name": "幸福村", "county": "丹寨县"}]
        imported = [{"village_name": "幸福村", "county": "榕江县"}]
        conflicts = detect_unique_key_conflicts(local, imported, keys=["village_name", "county"])
        assert len(conflicts) == 0


class TestOrphanDetection:
    def test_fk_not_found_is_orphan(self):
        from app.services.import_conflict_detector import detect_orphan_records
        target_fk_set = {1, 2, 3}
        imported = [
            {"id": 10, "project_id": 5},
            {"id": 11, "project_id": 2},
        ]
        orphans = detect_orphan_records(imported, "project_id", target_fk_set)
        assert len(orphans) == 1
        assert orphans[0]["record"]["id"] == 10

    def test_all_fks_found_no_orphan(self):
        from app.services.import_conflict_detector import detect_orphan_records
        target_fk_set = {1, 2, 3}
        imported = [{"id": 10, "project_id": 1}, {"id": 11, "project_id": 2}]
        assert len(detect_orphan_records(imported, "project_id", target_fk_set)) == 0


class TestConflictResolution:
    def test_timestamp_newer_wins(self):
        from app.services.import_conflict_detector import resolve_by_timestamp
        local = {"id": 1, "name": "旧名", "updated_at": "2025-01-01"}
        imported = {"id": 1, "name": "新名", "updated_at": "2026-01-01"}
        result = resolve_by_timestamp(local, imported)
        assert result["name"] == "新名"

    def test_timestamp_local_newer_keeps_local(self):
        from app.services.import_conflict_detector import resolve_by_timestamp
        local = {"id": 1, "name": "最新名", "updated_at": "2026-06-01"}
        imported = {"id": 1, "name": "旧名", "updated_at": "2025-01-01"}
        result = resolve_by_timestamp(local, imported)
        assert result["name"] == "最新名"
