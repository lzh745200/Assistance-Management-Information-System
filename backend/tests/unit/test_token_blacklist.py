"""Tests for app.core.token_blacklist — 100% coverage target."""

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core import token_blacklist


# Clean up module-level state before every test
@pytest.fixture(autouse=True)
def _clean_blacklist():
    token_blacklist._blacklist.clear()
    token_blacklist._blacklist.update({"_pytest_sentinel": time.time() + 99999})
    yield
    token_blacklist._blacklist.clear()


# ==============================================================================
# add
# ==============================================================================


class TestAdd:
    def test_empty_jti_does_nothing(self):
        token_blacklist.add("")
        assert token_blacklist.count() == 1  # only sentinel

    def test_add_with_expires_at(self):
        exp = datetime.now(timezone.utc).replace(year=2099)
        token_blacklist.add("jti-1", expires_at=exp)
        assert token_blacklist.is_blacklisted("jti-1") is True

    def test_add_with_ttl_seconds(self):
        token_blacklist.add("jti-2", ttl_seconds=3600)
        assert token_blacklist.is_blacklisted("jti-2") is True

    def test_add_zero_ttl_uses_default_86400(self):
        token_blacklist.add("jti-3", ttl_seconds=0)
        assert token_blacklist.is_blacklisted("jti-3") is True

    def test_add_negative_ttl_is_clamped(self):
        token_blacklist.add("jti-4", ttl_seconds=-5)
        assert token_blacklist.is_blacklisted("jti-4") is True


# ==============================================================================
# remove
# ==============================================================================


class TestRemove:
    def test_remove_existing(self):
        token_blacklist.add("to-remove")
        assert token_blacklist.is_blacklisted("to-remove") is True
        token_blacklist.remove("to-remove")
        assert token_blacklist.is_blacklisted("to-remove") is False

    def test_remove_nonexistent_does_not_raise(self):
        token_blacklist.remove("does-not-exist")  # should not raise


# ==============================================================================
# is_blacklisted
# ==============================================================================


class TestIsBlacklisted:
    def test_blacklisted_returns_true(self):
        token_blacklist.add("bad-token")
        assert token_blacklist.is_blacklisted("bad-token") is True

    def test_not_blacklisted_returns_false(self):
        assert token_blacklist.is_blacklisted("good-token") is False

    def test_expired_entry_cleaned(self):
        token_blacklist._blacklist["expired-jti"] = time.time() - 10
        assert token_blacklist.is_blacklisted("expired-jti") is False


# ==============================================================================
# load_from_db
# ==============================================================================


class TestLoadFromDb:
    def test_loads_entries(self):
        mock_session = MagicMock()
        mock_entry = MagicMock()
        mock_entry.token_jti = "db-jti"
        mock_entry.expires_at = datetime.now(timezone.utc).replace(year=2099)
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_entry]

        count = token_blacklist.load_from_db(mock_session)
        assert count == 1
        assert token_blacklist.is_blacklisted("db-jti") is True

    def test_skips_duplicate_jti(self):
        token_blacklist.add("existing-jti")
        mock_session = MagicMock()
        mock_entry = MagicMock()
        mock_entry.token_jti = "existing-jti"
        mock_entry.expires_at = datetime.now(timezone.utc).replace(year=2099)
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_entry]

        count = token_blacklist.load_from_db(mock_session)
        assert count == 1

    def test_entry_with_no_expiry_uses_default_ttl(self):
        mock_session = MagicMock()
        mock_entry = MagicMock()
        mock_entry.token_jti = "no-expiry"
        mock_entry.expires_at = None
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_entry]

        count = token_blacklist.load_from_db(mock_session)
        assert count == 1
        assert token_blacklist.is_blacklisted("no-expiry") is True

    def test_empty_result(self):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        count = token_blacklist.load_from_db(mock_session)
        assert count == 0

    def test_exception_returns_zero(self):
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("db error")

        count = token_blacklist.load_from_db(mock_session)
        assert count == 0


# ==============================================================================
# clear / count
# ==============================================================================


class TestClearAndCount:
    def test_clear_removes_all(self):
        token_blacklist.add("some-jti")
        token_blacklist.clear()
        assert token_blacklist.count() == 0

    def test_count_excludes_expired(self):
        token_blacklist._blacklist["expired"] = time.time() - 5
        assert token_blacklist.is_blacklisted("expired") is False
        assert token_blacklist.count() == 1  # only sentinel

    def test_count_includes_active(self):
        token_blacklist.add("active")
        assert token_blacklist.count() == 2  # sentinel + active


# ==============================================================================
# add_to_db
# ==============================================================================


class TestAddToDb:
    @patch("app.models.token_blacklist.TokenBlacklist")
    def test_success(self, mock_model):
        mock_entry = MagicMock()
        mock_model.return_value = mock_entry
        mock_session = MagicMock()
        token_blacklist.add_to_db("jti-db", mock_session, reason="logout")
        mock_session.add.assert_called_once_with(mock_entry)
        mock_session.commit.assert_called_once()

    @patch("app.models.token_blacklist.TokenBlacklist")
    def test_default_reason(self, mock_model):
        mock_entry = MagicMock()
        mock_model.return_value = mock_entry
        mock_session = MagicMock()
        token_blacklist.add_to_db("jti-db-2", mock_session)
        mock_model.assert_called_once()
        args, kwargs = mock_model.call_args
        assert kwargs.get("reason") == "manual_revoke"

    @patch("app.models.token_blacklist.TokenBlacklist")
    def test_exception_rolls_back(self, mock_model):
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("commit fail")
        mock_session.add = MagicMock()

        token_blacklist.add_to_db("jti-fail", mock_session)
        mock_session.rollback.assert_called_once()

    @patch("app.models.token_blacklist.TokenBlacklist")
    def test_exception_rollback_also_fails(self, mock_model):
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("commit fail")
        mock_session.add = MagicMock()
        mock_session.rollback.side_effect = RuntimeError("rollback fail")

        token_blacklist.add_to_db("jti-fail2", mock_session)
        mock_session.rollback.assert_called_once()
