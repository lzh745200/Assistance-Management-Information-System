# -*- coding: utf-8 -*-
"""project_milestone 状态流转引擎与进度计算覆盖率测试"""

from types import SimpleNamespace

from app.models.project_milestone import calculate_milestone_progress, validate_status_transition


def _project(**kw):
    base = dict(
        status="draft",
        name="路",
        type="基建",
        budget=100,
        start_date="2024-01-01",
        end_date="2024-12-31",
        responsible_person="张三",
        actual_start_date=None,
        actual_end_date=None,
        achievements=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_invalid_transition_from_completed():
    r = validate_status_transition(_project(status="completed"), "draft")
    assert r["valid"] is False
    assert "无" in r["error"]
    assert r["missing_fields"] == []


def test_invalid_transition_lists_allowed():
    r = validate_status_transition(_project(status="draft"), "completed")
    assert r["valid"] is False
    assert "pending" in r["error"]


def test_status_none_defaults_to_draft():
    r = validate_status_transition(_project(status=None), "cancelled")
    assert r["valid"] is True


def test_valid_transition_with_requirements_satisfied():
    assert validate_status_transition(_project(), "pending") == {"valid": True}


def test_transition_missing_required_fields():
    p = _project(name="  ", budget=None)
    r = validate_status_transition(p, "pending")
    assert r["valid"] is False
    assert set(r["missing_fields"]) == {"name", "budget"}
    assert "提交审批" in r["error"]


def test_transition_no_requirements_path():
    assert validate_status_transition(_project(status="pending"), "approved") == {"valid": True}


def test_transition_in_progress_completed_requirements():
    p = _project(status="in_progress", actual_end_date="2024-06-01", achievements=None)
    r = validate_status_transition(p, "completed")
    assert r["valid"] is False
    assert r["missing_fields"] == ["achievements"]


def test_progress_empty():
    assert calculate_milestone_progress([]) == 0


def test_progress_mixed():
    ms = [SimpleNamespace(status="completed"), SimpleNamespace(status="pending"), SimpleNamespace(status="completed")]
    assert calculate_milestone_progress(ms) == 67
