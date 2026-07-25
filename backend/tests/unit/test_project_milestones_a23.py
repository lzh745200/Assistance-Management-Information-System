"""补齐 app.api.v1.project_milestones 覆盖率缺口（a23）。

缺口：
- update_milestone 完成时自动填充 actual_date (165)
- transition_status 请求字段预写入分支 (254-257, 259-262, 264)
- get_change_logs 项目不存在/无权访问 404 (318)、change_type 过滤 (322)
- _auto_update_project_progress 有里程碑时的进度回写 (451-453)

端点直接 async 调用；db 用链式 MagicMock；Query 默认值显式传真实值。
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

import app.api.v1.project_milestones as mod
from app.api.v1.project_milestones import (
    MilestoneUpdate,
    StatusTransitionRequest,
    StatusTransitionResponse,
)


def _user():
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.is_superuser = True
    user.role = "admin"
    return user


def _chain_db(first=None, all_=None):
    """db mock：query 链全部返回同一 q，多次 db.query 也返回 q。"""
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.order_by.return_value = q
    q.offset.return_value = q
    q.limit.return_value = q
    q.first.return_value = first
    q.all.return_value = all_ if all_ is not None else []
    db = MagicMock()
    db.query.return_value = q
    return db, q


def _milestone(**kw):
    m = MagicMock()
    m.id = kw.get("id", 1)
    m.project_id = kw.get("project_id", 1)
    m.name = kw.get("name", "基础施工")
    m.status = kw.get("status", "in_progress")
    m.actual_date = kw.get("actual_date", None)
    return m


class TestUpdateMilestoneAutoFillActualDate:
    @pytest.mark.asyncio
    async def test_completed_status_fills_actual_date_and_progress(self):
        # 覆盖 165（自动填充 actual_date）与 451-453（有里程碑时回写项目进度）
        milestone = _milestone(status="in_progress", actual_date=None)
        db, q = _chain_db(first=milestone, all_=[milestone])

        result = await mod.update_milestone(
            1, 1, MilestoneUpdate(status="completed"),
            current_user=_user(), db=db,
        )

        assert result is milestone
        assert milestone.status == "completed"
        assert milestone.actual_date == date.today()
        q.update.assert_called_once_with({"progress": 100})

    @pytest.mark.asyncio
    async def test_completed_status_keeps_existing_actual_date(self):
        existing = date(2025, 3, 1)
        milestone = _milestone(status="in_progress", actual_date=existing)
        db, q = _chain_db(first=milestone, all_=[milestone])

        await mod.update_milestone(
            1, 1, MilestoneUpdate(status="completed"),
            current_user=_user(), db=db,
        )

        assert milestone.actual_date == existing


class TestTransitionStatusPrefillFields:
    @pytest.mark.asyncio
    async def test_valid_date_fields_and_achievements_written(self):
        # 覆盖 253-256、258-260、263-264
        project = MagicMock()
        project.id = 1
        project.status = "in_progress"
        db, _ = _chain_db(first=project)

        data = StatusTransitionRequest(
            new_status="completed",
            reason="完工",
            actual_start_date="2025-01-01",
            actual_end_date="2025-06-30",
            achievements="全部验收通过",
        )
        with patch.object(
            mod, "validate_status_transition", return_value={"valid": True}
        ):
            resp = await mod.transition_status(1, data, current_user=_user(), db=db)

        assert isinstance(resp, StatusTransitionResponse)
        assert resp.valid is True
        assert resp.new_status == "completed"
        assert project.actual_start_date == date(2025, 1, 1)
        assert project.actual_end_date == date(2025, 6, 30)
        assert project.achievements == "全部验收通过"
        db.add.assert_called_once()  # 变更日志

    @pytest.mark.asyncio
    async def test_invalid_date_formats_logged_and_ignored(self):
        # 覆盖 257、261-262（ValueError → warning，不写入字段）
        project = MagicMock()
        project.id = 1
        project.status = "in_progress"
        db, _ = _chain_db(first=project)

        data = StatusTransitionRequest(
            new_status="completed",
            actual_start_date="not-a-date",
            actual_end_date="2025/06/30",
        )
        with patch.object(
            mod, "validate_status_transition", return_value={"valid": True}
        ):
            resp = await mod.transition_status(1, data, current_user=_user(), db=db)

        assert resp.valid is True
        # 非法日期未被写入（仍为 MagicMock 默认值，不是 date 实例）
        assert not isinstance(project.actual_start_date, date)
        assert not isinstance(project.actual_end_date, date)


class TestGetChangeLogsGaps:
    @pytest.mark.asyncio
    async def test_project_not_found_raises_404(self):
        # 覆盖 317-318
        db, _ = _chain_db(first=None)
        with pytest.raises(HTTPException) as exc_info:
            await mod.get_change_logs(
                project_id=999, change_type=None, page=1, page_size=50,
                current_user=_user(), db=db,
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_change_type_filter_applied(self):
        # 覆盖 321-322
        project = MagicMock()
        project.id = 1
        db, q = _chain_db(first=project, all_=[])
        result = await mod.get_change_logs(
            project_id=1, change_type="status", page=1, page_size=50,
            current_user=_user(), db=db,
        )
        assert result == []
        # project 校验 1 次 filter + change_type 过滤 1 次 filter
        assert q.filter.call_count >= 2
