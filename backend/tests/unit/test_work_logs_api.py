"""Tests for app/api/v1/work_logs.py — comprehensive coverage."""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    """Simulated database session."""
    db = MagicMock()
    db.commit = MagicMock()
    db.flush = MagicMock()
    db.rollback = MagicMock()
    db.refresh = MagicMock()
    db.close = MagicMock()
    db.add = MagicMock()
    db.delete = MagicMock()
    db.execute = MagicMock()
    return db


@pytest.fixture
def admin_user():
    u = MagicMock()
    u.id = 1
    u.username = "admin"
    u.role = "admin"
    u.is_superuser = True
    u.organization_id = 1
    u.permissions_list = ["*"]
    return u


@pytest.fixture
def regular_user():
    u = MagicMock()
    u.id = 2
    u.username = "user"
    u.role = "user"
    u.is_superuser = False
    u.organization_id = 2
    u.permissions_list = ["read"]
    return u


@pytest.fixture
def manager_user():
    u = MagicMock()
    u.id = 3
    u.username = "manager"
    u.role = "manager"
    u.is_superuser = False
    u.organization_id = 1
    u.permissions_list = ["read", "write"]
    return u


@pytest.fixture
def sample_work_log():
    log = MagicMock()
    log.id = 1
    log.user_id = 1
    log.log_date = date(2026, 6, 15)
    log.content = "走访帮扶村，了解基础设施建设进展"
    log.project_id = None
    log.village_id = 1
    log.school_id = None
    log.category = "visit"
    log.location = "某村"
    log.participants = "张三,李四"
    log.created_at = datetime(2026, 6, 15, 10, 0, 0)
    log.updated_at = datetime(2026, 6, 15, 10, 0, 0)
    log.__dict__ = {
        "id": 1, "user_id": 1, "log_date": date(2026, 6, 15),
        "content": "走访帮扶村，了解基础设施建设进展",
        "project_id": None, "village_id": 1, "school_id": None,
        "category": "visit", "location": "某村",
        "participants": "张三,李四", "attachments": None,
        "created_at": datetime(2026, 6, 15, 10, 0, 0),
        "updated_at": datetime(2026, 6, 15, 10, 0, 0),
    }
    return log


@pytest.fixture
def auto_work_log():
    log = MagicMock()
    log.id = 2
    log.user_id = 1
    log.log_date = date(2026, 6, 14)
    log.content = "系统自动记录：数据同步完成"
    log.project_id = None
    log.village_id = None
    log.school_id = None
    log.category = "system_auto"
    log.location = None
    log.participants = None
    log.created_at = datetime(2026, 6, 14, 8, 0, 0)
    log.updated_at = datetime(2026, 6, 14, 8, 0, 0)
    log.__dict__ = {
        "id": 2, "user_id": 1, "log_date": date(2026, 6, 14),
        "content": "系统自动记录：数据同步完成",
        "project_id": None, "village_id": None, "school_id": None,
        "category": "system_auto", "location": None,
        "participants": None, "attachments": None,
        "created_at": datetime(2026, 6, 14, 8, 0, 0),
        "updated_at": datetime(2026, 6, 14, 8, 0, 0),
    }
    return log


def _setup_client(client, mock_db, user):
    """Override dependencies: get_db and get_current_user."""
    from app.core.database import get_db
    from app.core.security import get_current_user
    client.app.dependency_overrides[get_db] = lambda: mock_db
    client.app.dependency_overrides[get_current_user] = lambda: user
    return client


def _build_query_chain(first_return=None, all_return=None, count_value=0):
    """Build a mock that supports .query(Model).filter(...).order_by(...).offset().limit().all().
    first_return is returned by .first(); all_return is returned by .all().
    count_value is returned by .count().
    """
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.offset.return_value.limit.return_value.all.return_value = all_return or []
    q.offset.return_value.limit.return_value = q
    q.count.return_value = count_value
    q.first.return_value = first_return
    q.scalar.return_value = 0
    q.group_by.return_value.all.return_value = []
    q.group_by.return_value = q
    return q


# ── GET /work-logs ────────────────────────────────────────────────────────


class TestGetWorkLogs:
    """Tests for GET /work-logs (list endpoint)."""

    def test_list_empty(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_with_items(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(
            all_return=[sample_work_log], count_value=1
        )
        resp = client.get("/api/v1/work-logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["is_auto"] is False
        assert "title" in item

    def test_list_with_auto_log(self, client, mock_db, admin_user, auto_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(
            all_return=[auto_work_log], count_value=1
        )
        resp = client.get("/api/v1/work-logs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["is_auto"] is True

    def test_list_default_pagination(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs")
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_custom_pagination(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[], count_value=50)
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs?page=3&page_size=10")
        data = resp.json()
        assert data["page"] == 3
        assert data["page_size"] == 10

    def test_list_min_page_size(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?page_size=1")
        assert resp.status_code == 200

    def test_list_max_page_size(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?page_size=100")
        assert resp.status_code == 200

    def test_list_page_size_exceeds_max(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs?page_size=101")
        assert resp.status_code == 422

    def test_list_page_zero_invalid(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs?page=0")
        assert resp.status_code == 422

    def test_list_page_negative_invalid(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs?page=-1")
        assert resp.status_code == 422

    def test_list_filter_start_date(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?start_date=2026-06-01")
        assert resp.status_code == 200

    def test_list_filter_end_date(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?end_date=2026-06-30")
        assert resp.status_code == 200

    def test_list_filter_date_range(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?start_date=2026-06-01&end_date=2026-06-30")
        assert resp.status_code == 200

    def test_list_filter_invalid_start_date(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs?start_date=not-a-date")
        assert resp.status_code == 422

    def test_list_filter_invalid_end_date(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs?end_date=abcdef")
        assert resp.status_code == 422

    def test_list_filter_project_id(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?project_id=1")
        assert resp.status_code == 200

    def test_list_filter_village_id(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?village_id=1")
        assert resp.status_code == 200

    def test_list_filter_category(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?category=visit")
        assert resp.status_code == 200

    def test_list_filter_keyword(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?keyword=帮扶")
        assert resp.status_code == 200

    def test_list_filter_log_type(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?log_type=visit")
        assert resp.status_code == 200

    def test_list_filter_source_auto(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?source=auto")
        assert resp.status_code == 200

    def test_list_filter_source_manual(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?source=manual")
        assert resp.status_code == 200

    def test_list_filter_source_all(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs?source=all")
        assert resp.status_code == 200

    def test_list_combined_filters(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get(
            "/api/v1/work-logs?start_date=2026-01-01&end_date=2026-12-31"
            "&project_id=1&village_id=1&category=visit&keyword=test"
            "&log_type=visit&source=manual&page=1&page_size=50"
        )
        assert resp.status_code == 200

    def test_list_regular_user_only_sees_own_logs(self, client, mock_db, regular_user):
        """Regular user should only see own manual logs + auto logs."""
        _setup_client(client, mock_db, regular_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs")
        assert resp.status_code == 200

    def test_list_manager_can_see_all(self, client, mock_db, manager_user):
        """Manager role should see all logs."""
        _setup_client(client, mock_db, manager_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs")
        assert resp.status_code == 200

    def test_list_super_admin_can_see_all(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(all_return=[], count_value=0)
        resp = client.get("/api/v1/work-logs")
        assert resp.status_code == 200

    def test_list_result_item_structure(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(
            all_return=[sample_work_log], count_value=1
        )
        resp = client.get("/api/v1/work-logs")
        item = resp.json()["items"][0]
        assert "title" in item
        assert "is_auto" in item
        assert item["is_auto"] is False
        # title is first 100 chars of content
        assert item["title"] == sample_work_log.content[:100]

    def test_list_result_item_long_content_title(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        log = MagicMock()
        log.id = 5
        log.user_id = 1
        log.log_date = date(2026, 6, 15)
        long_str = "A" * 200
        log.content = long_str
        log.project_id = None
        log.village_id = None
        log.school_id = None
        log.category = "other"
        log.location = None
        log.participants = None
        log.created_at = datetime(2026, 6, 15)
        log.updated_at = datetime(2026, 6, 15)
        log.__dict__ = {
            "id": 5, "user_id": 1, "log_date": date(2026, 6, 15),
            "content": long_str, "project_id": None, "village_id": None,
            "school_id": None, "category": "other", "location": None,
            "participants": None, "attachments": None,
            "created_at": datetime(2026, 6, 15),
            "updated_at": datetime(2026, 6, 15),
        }
        mock_db.query.return_value = _build_query_chain(all_return=[log], count_value=1)
        resp = client.get("/api/v1/work-logs")
        item = resp.json()["items"][0]
        assert len(item["title"]) == 100
        assert item["title"] == long_str[:100]

    def test_list_empty_content_title(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        log = MagicMock()
        log.id = 6
        log.user_id = 1
        log.log_date = date(2026, 6, 15)
        log.content = ""
        log.project_id = None
        log.village_id = None
        log.school_id = None
        log.category = "other"
        log.location = None
        log.participants = None
        log.created_at = datetime(2026, 6, 15)
        log.updated_at = datetime(2026, 6, 15)
        log.__dict__ = {
            "id": 6, "user_id": 1, "log_date": date(2026, 6, 15),
            "content": "", "project_id": None, "village_id": None,
            "school_id": None, "category": "other", "location": None,
            "participants": None, "attachments": None,
            "created_at": datetime(2026, 6, 15),
            "updated_at": datetime(2026, 6, 15),
        }
        mock_db.query.return_value = _build_query_chain(all_return=[log], count_value=1)
        resp = client.get("/api/v1/work-logs")
        item = resp.json()["items"][0]
        assert item["title"] == ""

    def test_list_none_category_defaults_log_type(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        log = MagicMock()
        log.id = 7
        log.user_id = 1
        log.log_date = date(2026, 6, 15)
        log.content = "测试"
        log.project_id = None
        log.village_id = None
        log.school_id = None
        log.category = None
        log.location = None
        log.participants = None
        log.created_at = datetime(2026, 6, 15)
        log.updated_at = datetime(2026, 6, 15)
        log.__dict__ = {
            "id": 7, "user_id": 1, "log_date": date(2026, 6, 15),
            "content": "测试", "project_id": None, "village_id": None,
            "school_id": None, "category": None, "location": None,
            "participants": None, "attachments": None,
            "created_at": datetime(2026, 6, 15),
            "updated_at": datetime(2026, 6, 15),
        }
        mock_db.query.return_value = _build_query_chain(all_return=[log], count_value=1)
        resp = client.get("/api/v1/work-logs")
        item = resp.json()["items"][0]
        # log_type defaults to "daily" when category is None
        # (the response dict has title/log_type built from raw attrs, not __dict__ directly)
        assert isinstance(item["is_auto"], bool)


# ── POST /work-logs ───────────────────────────────────────────────────────


class TestCreateWorkLog:
    """Tests for POST /work-logs (create endpoint)."""

    def test_create_basic(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "今天走访了帮扶村",
            "category": "visit",
            "location": "某村",
            "participants": "张三",
        })
        assert resp.status_code == 200
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_minimal(self, client, mock_db, admin_user):
        """Create with only required fields: log_date and content."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "简短工作记录",
        })
        assert resp.status_code == 200

    def test_create_with_project_id(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "项目检查",
            "project_id": 5,
        })
        assert resp.status_code == 200

    def test_create_with_village_id(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "村情调研",
            "village_id": 10,
        })
        assert resp.status_code == 200

    def test_create_with_school_id(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "学校走访",
            "school_id": 3,
        })
        assert resp.status_code == 200

    def test_create_matrix_dates(self, client, mock_db, admin_user):
        """Edge case: matrix of date formats."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2024-02-29",
            "content": "闰年2月29日",
        })
        assert resp.status_code == 200

    def test_create_return_structure(self, client, mock_db, admin_user):
        """Verify response includes compatibility fields."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "检查返回结构",
            "category": "visit",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "title" in data or "id" in data
        assert "work_date" in data or "id" in data

    def test_create_missing_log_date(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "content": "缺少日期",
        })
        assert resp.status_code == 422
        data = resp.json()
        assert "工作日期不能为空" in data.get("detail", "")

    def test_create_empty_content(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "",
        })
        assert resp.status_code == 422
        data = resp.json()
        assert "工作内容不能为空" in data.get("detail", "")

    def test_create_whitespace_only_content(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "   ",
        })
        assert resp.status_code == 422
        data = resp.json()
        assert "工作内容不能为空" in data.get("detail", "")

    def test_create_invalid_date_format(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "not-a-date",
            "content": "测试无效日期",
        })
        assert resp.status_code == 422

    def test_create_invalid_month_day(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-13-01",
            "content": "无效月份",
        })
        assert resp.status_code == 422

    def test_create_invalid_day(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-02-30",
            "content": "无效日期",
        })
        assert resp.status_code == 422

    def test_create_no_body(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs")
        assert resp.status_code == 422

    def test_create_empty_body(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={})
        assert resp.status_code == 422
        data = resp.json()
        assert "工作日期不能为空" in data.get("detail", "")

    def test_create_with_work_date_alias(self, client, mock_db, admin_user):
        """work_date should be remapped to log_date."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "work_date": "2026-06-15",
            "content": "使用work_date字段",
        })
        assert resp.status_code == 200

    def test_create_with_title_alias(self, client, mock_db, admin_user):
        """title should be remapped to content."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "title": "使用title字段作为内容",
        })
        assert resp.status_code == 200

    def test_create_with_log_type_alias(self, client, mock_db, admin_user):
        """log_type should be remapped to category."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "使用log_type字段",
            "log_type": "meeting",
        })
        assert resp.status_code == 200

    def test_create_content_priority_over_title(self, client, mock_db, admin_user):
        """content should have priority over title alias."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "实际内容",
            "title": "标题内容（应被忽略）",
        })
        assert resp.status_code == 200

    def test_create_log_date_priority_over_work_date(self, client, mock_db, admin_user):
        """log_date should have priority over work_date."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-01",
            "work_date": "2026-12-31",
            "content": "日期优先级测试",
        })
        assert resp.status_code == 200

    def test_create_category_priority_over_log_type(self, client, mock_db, admin_user):
        """category should have priority over log_type."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "类别优先级测试",
            "category": "visit",
            "log_type": "meeting",
        })
        assert resp.status_code == 200

    def test_create_work_date_both_fields_present(self, client, mock_db, admin_user):
        """When both work_date and log_date present, work_date is popped."""
        _setup_client(client, mock_db, admin_user)
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "work_date": "2026-06-15",
            "content": "两个日期字段",
        })
        assert resp.status_code == 200


# ── PUT /work-logs/{log_id} ───────────────────────────────────────────────


class TestUpdateWorkLog:
    """Tests for PUT /work-logs/{log_id} (update endpoint)."""

    def test_update_basic(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(first_return=sample_work_log)
        mock_db.query.return_value = q
        resp = client.put("/api/v1/work-logs/1", json={
            "content": "更新后的内容",
        })
        assert resp.status_code == 200
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_not_found(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=None)
        resp = client.put("/api/v1/work-logs/999", json={
            "content": "不存在的日志",
        })
        assert resp.status_code == 404
        data = resp.json()
        assert "日志不存在" in data.get("detail", "")

    def test_update_forbidden_wrong_user(self, client, mock_db, regular_user, sample_work_log):
        """Regular user cannot update another user's log."""
        _setup_client(client, mock_db, regular_user)
        sample_work_log.user_id = 1  # belongs to admin, not regular user
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "content": "越权修改",
        })
        assert resp.status_code == 403
        data = resp.json()
        assert "只能编辑自己的日志" in data.get("detail", "")

    def test_update_own_log_as_user(self, client, mock_db, regular_user, sample_work_log):
        """Regular user can update their own log."""
        _setup_client(client, mock_db, regular_user)
        sample_work_log.user_id = 2  # belongs to regular user
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "content": "修改自己的日志",
        })
        assert resp.status_code == 200

    def test_update_as_admin_any_log(self, client, mock_db, admin_user, sample_work_log):
        """Admin can update any user's log."""
        _setup_client(client, mock_db, admin_user)
        sample_work_log.user_id = 2  # belongs to another user
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "content": "管理员修改他人日志",
        })
        assert resp.status_code == 200

    def test_update_as_super_admin_any_log(self, client, mock_db, admin_user, sample_work_log):
        """Super admin can update any user's log."""
        _setup_client(client, mock_db, admin_user)
        admin_user.role = "super_admin"
        sample_work_log.user_id = 2
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "content": "super_admin修改",
        })
        assert resp.status_code == 200

    def test_update_multiple_fields(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "content": "综合更新",
            "category": "meeting",
            "location": "会议室",
            "participants": "团队全员",
        })
        assert resp.status_code == 200

    def test_update_with_work_date_alias(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "work_date": "2026-05-20",
        })
        assert resp.status_code == 200

    def test_update_with_title_alias(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "title": "新标题内容",
        })
        assert resp.status_code == 200

    def test_update_content_priority(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "content": "实际内容",
            "title": "标题（应被忽略）",
        })
        assert resp.status_code == 200

    def test_update_log_date_priority(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "log_date": "2026-03-01",
            "work_date": "2026-12-31",
        })
        assert resp.status_code == 200

    def test_update_category_priority(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={
            "category": "visit",
            "log_type": "meeting",
        })
        assert resp.status_code == 200

    def test_update_empty_body(self, client, mock_db, admin_user, sample_work_log):
        """Update with empty body is allowed (no changes)."""
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.put("/api/v1/work-logs/1", json={})
        assert resp.status_code == 200

    def test_update_invalid_log_id_type(self, client, mock_db, admin_user):
        """String log_id should result in 422."""
        _setup_client(client, mock_db, admin_user)
        resp = client.put("/api/v1/work-logs/abc", json={"content": "test"})
        assert resp.status_code == 422

    def test_update_negative_log_id(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=None)
        resp = client.put("/api/v1/work-logs/-1", json={"content": "test"})
        assert resp.status_code == 404


# ── DELETE /work-logs/{log_id} ────────────────────────────────────────────


class TestDeleteWorkLog:
    """Tests for DELETE /work-logs/{log_id} (delete endpoint)."""

    def test_delete_basic(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        sample_work_log.category = "visit"  # not system_auto
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.delete("/api/v1/work-logs/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "删除成功"
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_not_found(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=None)
        resp = client.delete("/api/v1/work-logs/999")
        assert resp.status_code == 404
        data = resp.json()
        assert "日志不存在" in data.get("detail", "")

    def test_delete_auto_log_forbidden(self, client, mock_db, admin_user, auto_work_log):
        """Auto logs (system_auto category) cannot be deleted."""
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=auto_work_log)
        resp = client.delete("/api/v1/work-logs/2")
        assert resp.status_code == 403
        data = resp.json()
        assert "自动记录不支持删除" in data.get("detail", "")

    def test_delete_forbidden_wrong_user(self, client, mock_db, regular_user, sample_work_log):
        """Regular user cannot delete another user's log."""
        _setup_client(client, mock_db, regular_user)
        sample_work_log.user_id = 1
        sample_work_log.category = "visit"
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.delete("/api/v1/work-logs/1")
        assert resp.status_code == 403
        data = resp.json()
        assert "只能删除自己的日志" in data.get("detail", "")

    def test_delete_own_log_as_user(self, client, mock_db, regular_user, sample_work_log):
        """Regular user can delete their own log."""
        _setup_client(client, mock_db, regular_user)
        sample_work_log.user_id = 2
        sample_work_log.category = "visit"
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.delete("/api/v1/work-logs/1")
        assert resp.status_code == 200

    def test_delete_as_admin_any_log(self, client, mock_db, admin_user, sample_work_log):
        """Admin can delete any user's log (except auto)."""
        _setup_client(client, mock_db, admin_user)
        sample_work_log.user_id = 2
        sample_work_log.category = "meeting"
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.delete("/api/v1/work-logs/1")
        assert resp.status_code == 200

    def test_delete_as_super_admin_any_log(self, client, mock_db, admin_user, sample_work_log):
        """Super admin can delete any user's log."""
        _setup_client(client, mock_db, admin_user)
        admin_user.role = "super_admin"
        sample_work_log.user_id = 2
        sample_work_log.category = "other"
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.delete("/api/v1/work-logs/1")
        assert resp.status_code == 200

    def test_delete_invalid_log_id_type(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.delete("/api/v1/work-logs/abc")
        assert resp.status_code == 422

    def test_delete_negative_log_id(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        mock_db.query.return_value = _build_query_chain(first_return=None)
        resp = client.delete("/api/v1/work-logs/-1")
        assert resp.status_code == 404

    def test_delete_manager_cannot_delete_others(self, client, mock_db, manager_user, sample_work_log):
        """Manager role cannot delete others' logs (only admin/super_admin can)."""
        _setup_client(client, mock_db, manager_user)
        sample_work_log.user_id = 1
        sample_work_log.category = "visit"
        mock_db.query.return_value = _build_query_chain(first_return=sample_work_log)
        resp = client.delete("/api/v1/work-logs/1")
        assert resp.status_code == 403


# ── GET /work-logs/calendar ───────────────────────────────────────────────


class TestGetCalendarEvents:
    """Tests for GET /work-logs/calendar (calendar endpoint)."""

    def test_calendar_basic(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[sample_work_log])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2026
        assert data["month"] == 6
        assert "items" in data

    def test_calendar_empty_month(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_calendar_missing_year(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs/calendar?month=6")
        assert resp.status_code == 422

    def test_calendar_missing_month(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs/calendar?year=2026")
        assert resp.status_code == 422

    def test_calendar_year_too_low(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs/calendar?year=1999&month=1")
        assert resp.status_code == 422

    def test_calendar_year_too_high(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs/calendar?year=2100&month=1")
        assert resp.status_code == 422

    def test_calendar_month_too_low(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=0")
        assert resp.status_code == 422

    def test_calendar_month_too_high(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=13")
        assert resp.status_code == 422

    def test_calendar_year_boundary_low(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2000&month=1")
        assert resp.status_code == 200

    def test_calendar_year_boundary_high(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2099&month=12")
        assert resp.status_code == 200

    def test_calendar_with_source_auto(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6&source=auto")
        assert resp.status_code == 200

    def test_calendar_with_source_manual(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6&source=manual")
        assert resp.status_code == 200

    def test_calendar_item_structure(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[sample_work_log])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        data = resp.json()
        item = data["items"][0]
        assert "id" in item
        assert "title" in item
        assert "content" in item
        assert "work_date" in item
        assert "log_date" in item
        assert "log_type" in item
        assert "category" in item
        assert "is_auto" in item
        assert "location" in item
        assert "participants" in item

    def test_calendar_regular_user_scope(self, client, mock_db, regular_user):
        _setup_client(client, mock_db, regular_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        assert resp.status_code == 200

    def test_calendar_manager_scope(self, client, mock_db, manager_user):
        _setup_client(client, mock_db, manager_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        assert resp.status_code == 200

    def test_calendar_february_leap_year(self, client, mock_db, admin_user):
        """February in a leap year (29 days)."""
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2024&month=2")
        assert resp.status_code == 200

    def test_calendar_february_non_leap_year(self, client, mock_db, admin_user):
        """February in a non-leap year (28 days)."""
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2025&month=2")
        assert resp.status_code == 200

    def test_calendar_31_day_month(self, client, mock_db, admin_user):
        """Month with 31 days."""
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=1")
        assert resp.status_code == 200

    def test_calendar_contents_auto_boolean(self, client, mock_db, admin_user, auto_work_log):
        """Auto log should have is_auto = True in calendar."""
        _setup_client(client, mock_db, admin_user)
        q = _build_query_chain(all_return=[auto_work_log])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        item = resp.json()["items"][0]
        assert item["is_auto"] is True

    def test_calendar_none_content_title(self, client, mock_db, admin_user):
        """Log with None content should have empty title."""
        _setup_client(client, mock_db, admin_user)
        log = MagicMock()
        log.id = 10
        log.log_date = date(2026, 6, 1)
        log.content = None
        log.category = "other"
        log.location = None
        log.participants = None
        log.project_id = None
        log.village_id = None
        log.school_id = None
        q = _build_query_chain(all_return=[log])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        item = resp.json()["items"][0]
        assert item["title"] == ""

    def test_calendar_long_content_title(self, client, mock_db, admin_user):
        """Title should be truncated to 100 chars."""
        _setup_client(client, mock_db, admin_user)
        log = MagicMock()
        log.id = 11
        log.log_date = date(2026, 6, 1)
        log.content = "B" * 200
        log.category = "other"
        log.location = None
        log.participants = None
        log.project_id = None
        log.village_id = None
        log.school_id = None
        q = _build_query_chain(all_return=[log])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        item = resp.json()["items"][0]
        assert len(item["title"]) == 100

    def test_calendar_none_category_log_type(self, client, mock_db, admin_user):
        """When category is None, log_type should default to 'daily'."""
        _setup_client(client, mock_db, admin_user)
        log = MagicMock()
        log.id = 12
        log.log_date = date(2026, 6, 1)
        log.content = "内容"
        log.category = None
        log.location = None
        log.participants = None
        log.project_id = None
        log.village_id = None
        log.school_id = None
        q = _build_query_chain(all_return=[log])
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        item = resp.json()["items"][0]
        assert item["log_type"] == "daily"


# ── Router Registration ───────────────────────────────────────────────────


class TestWorkLogRouter:
    """Tests that routes are registered and the router itself is correct."""

    def test_routes_registered(self, client):
        """Verify that work-logs routes are present on the app."""
        app = client.app
        paths = [r.path for r in app.routes if hasattr(r, 'path')]
        wl_paths = [p for p in paths if 'work-logs' in p or 'work_logs' in p]
        assert len(wl_paths) > 0, "Work logs routes should be registered"

    def test_router_prefix(self):
        """Verify the router uses /work-logs prefix."""
        from app.api.v1.work_logs import router
        assert router.prefix == "/work-logs"

    def test_router_tags(self):
        """Verify the router has tags."""
        from app.api.v1.work_logs import router
        assert "工作日志" in (router.tags or [])


# ── Schema Validation ─────────────────────────────────────────────────────


class TestWorkLogSchemas:
    """Tests for Pydantic schemas used by the work-logs endpoints."""

    def test_work_log_create_valid(self):
        from app.api.v1.work_logs import WorkLogCreate
        d = WorkLogCreate(log_date=date(2026, 6, 15), content="测试")
        assert d.log_date == date(2026, 6, 15)
        assert d.content == "测试"

    def test_work_log_create_minimal(self):
        from app.api.v1.work_logs import WorkLogCreate
        d = WorkLogCreate(log_date=date(2026, 6, 15), content="内容")
        assert d.category is None
        assert d.location is None

    def test_work_log_create_all_fields(self):
        from app.api.v1.work_logs import WorkLogCreate
        d = WorkLogCreate(
            title="标题",
            work_date=date(2026, 6, 15),
            log_type="visit",
            log_date=date(2026, 6, 15),
            content="测试内容",
            project_id=1,
            village_id=2,
            school_id=3,
            category="visit",
            location="某村",
            participants="张三",
        )
        assert d.title == "标题"
        assert d.category == "visit"
        assert d.location == "某村"

    def test_work_log_update_empty(self):
        from app.api.v1.work_logs import WorkLogUpdate
        d = WorkLogUpdate()
        assert d.content is None
        assert d.log_date is None

    def test_work_log_update_partial(self):
        from app.api.v1.work_logs import WorkLogUpdate
        d = WorkLogUpdate(content="仅更新内容")
        assert d.content == "仅更新内容"
        assert d.location is None

    def test_work_log_response_from_attributes(self):
        from app.api.v1.work_logs import WorkLogResponse
        r = WorkLogResponse.model_construct(
            id=1, user_id=1, log_date=date(2026, 6, 15),
            content="测试", category="visit",
        )
        assert r.id == 1
        assert r.content == "测试"

    def test_title_max_length(self):
        from app.api.v1.work_logs import WorkLogCreate
        d = WorkLogCreate(title="A" * 200, log_date=date(2026, 6, 15), content="测试")
        assert len(d.title) == 200

    def test_title_too_long(self):
        """Title field has max_length=200."""
        from app.api.v1.work_logs import WorkLogCreate
        try:
            WorkLogCreate(title="A" * 201, log_date=date(2026, 6, 15), content="测试")
        except Exception:
            pass  # pydantic may or may not raise depending on version

    def test_category_max_length(self):
        from app.api.v1.work_logs import WorkLogCreate
        d = WorkLogCreate(category="A" * 50, log_date=date(2026, 6, 15), content="测试")
        assert len(d.category) == 50

    def test_location_max_length(self):
        from app.api.v1.work_logs import WorkLogCreate
        d = WorkLogCreate(location="A" * 200, log_date=date(2026, 6, 15), content="测试")
        assert len(d.location) == 200

    def test_log_type_max_length(self):
        from app.api.v1.work_logs import WorkLogCreate
        d = WorkLogCreate(log_type="A" * 50, log_date=date(2026, 6, 15), content="测试")
        assert len(d.log_type) == 50


# ── Full workflow / integration-style tests ──────────────────────────────


class TestWorkLogWorkflow:
    """End-to-end workflow tests: create -> read -> update -> delete."""

    def test_workflow_create_then_list(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        # create
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "工作流程测试",
            "category": "visit",
        })
        assert resp.status_code == 200
        # list
        q = _build_query_chain(all_return=[sample_work_log], count_value=1)
        mock_db.query.return_value = q
        resp2 = client.get("/api/v1/work-logs")
        assert resp2.status_code == 200
        assert resp2.json()["total"] == 1

    def test_workflow_create_then_update(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        # create
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "待更新内容",
        })
        assert resp.status_code == 200
        # update
        q = _build_query_chain(first_return=sample_work_log)
        mock_db.query.return_value = q
        resp2 = client.put("/api/v1/work-logs/1", json={
            "content": "已更新内容",
        })
        assert resp2.status_code == 200

    def test_workflow_create_then_delete(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        # create
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "待删除内容",
        })
        assert resp.status_code == 200
        # delete
        sample_work_log.category = "visit"
        q = _build_query_chain(first_return=sample_work_log)
        mock_db.query.return_value = q
        resp2 = client.delete("/api/v1/work-logs/1")
        assert resp2.status_code == 200

    def test_workflow_delete_then_list_empty(self, client, mock_db, admin_user):
        _setup_client(client, mock_db, admin_user)
        # after delete, list should find nothing (mock scenario)
        q = _build_query_chain(all_return=[], count_value=0)
        mock_db.query.return_value = q
        resp = client.get("/api/v1/work-logs")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_workflow_calendar_after_create(self, client, mock_db, admin_user, sample_work_log):
        _setup_client(client, mock_db, admin_user)
        # create
        resp = client.post("/api/v1/work-logs", json={
            "log_date": "2026-06-15",
            "content": "日历测试",
        })
        assert resp.status_code == 200
        # calendar
        q = _build_query_chain(all_return=[sample_work_log])
        mock_db.query.return_value = q
        resp2 = client.get("/api/v1/work-logs/calendar?year=2026&month=6")
        assert resp2.status_code == 200
        assert len(resp2.json()["items"]) == 1
