"""Tests for app/utils/runtime_secrets.py — 100% coverage."""
import json
import os
import logging
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


# ---------------------------------------------------------------------------
# ensure_runtime_secrets
# ---------------------------------------------------------------------------


class TestEnsureRuntimeSecretsEnvProvided:
    def test_both_env_vars_set_returns_immediately(self):
        with patch.dict(os.environ, {"SECRET_KEY": "sk123", "CSRF_SECRET_KEY": "csrf456"}, clear=True):
            from app.utils.runtime_secrets import ensure_runtime_secrets
            ensure_runtime_secrets()
            assert os.environ["SECRET_KEY"] == "sk123"
            assert os.environ["CSRF_SECRET_KEY"] == "csrf456"

    def test_missing_csrf_generates_and_writes(self, tmp_path):
        secrets_file = tmp_path / "runtime_secrets.json"
        with patch.dict(os.environ, {"SECRET_KEY": "sk123", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import ensure_runtime_secrets
            ensure_runtime_secrets()
            assert os.environ["CSRF_SECRET_KEY"] != ""
            assert secrets_file.exists()
            data = json.loads(secrets_file.read_text(encoding="utf-8"))
            assert data["CSRF_SECRET_KEY"] == os.environ["CSRF_SECRET_KEY"]


class TestEnsureRuntimeSecretsFromFile:
    def test_loads_from_file_when_env_missing(self, tmp_path):
        secrets_file = tmp_path / "runtime_secrets.json"
        secrets_file.write_text(json.dumps({"SECRET_KEY": "file_sk", "CSRF_SECRET_KEY": "file_csrf"}), encoding="utf-8")
        with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import ensure_runtime_secrets
            ensure_runtime_secrets()
            assert os.environ["SECRET_KEY"] == "file_sk"
            assert os.environ["CSRF_SECRET_KEY"] == "file_csrf"

    def test_partial_from_file_combined_with_env(self, tmp_path):
        secrets_file = tmp_path / "runtime_secrets.json"
        secrets_file.write_text(json.dumps({"SECRET_KEY": "file_sk"}), encoding="utf-8")
        with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import ensure_runtime_secrets
            ensure_runtime_secrets()
            assert os.environ["SECRET_KEY"] == "file_sk"
            assert os.environ["CSRF_SECRET_KEY"] != ""

    def test_file_not_found_generates_new(self, tmp_path):
        secrets_file = tmp_path / "nonexistent.json"
        with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import ensure_runtime_secrets
            ensure_runtime_secrets()
            assert os.environ["SECRET_KEY"] != ""
            assert os.environ["CSRF_SECRET_KEY"] != ""

    def test_json_decode_error_logs_warning_and_generates(self, tmp_path, caplog):
        secrets_file = tmp_path / "corrupt.json"
        secrets_file.write_text("{bad json", encoding="utf-8")
        caplog.set_level(logging.WARNING)
        with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import ensure_runtime_secrets
            ensure_runtime_secrets()
            assert "JSON 格式损坏" in caplog.text
            assert os.environ["SECRET_KEY"] != ""

    def test_permission_error_reading_logs_warning(self, tmp_path, caplog):
        secrets_file = tmp_path / "noperm.json"
        secrets_file.write_text(json.dumps({"SECRET_KEY": "sk", "CSRF_SECRET_KEY": "csr"}), encoding="utf-8")
        caplog.set_level(logging.WARNING)
        with patch("builtins.open", side_effect=PermissionError("access denied")):
            with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
                from app.utils.runtime_secrets import ensure_runtime_secrets
                ensure_runtime_secrets()
                assert "无读取权限" in caplog.text

    def test_generic_exception_reading_logs_warning(self, tmp_path, caplog):
        secrets_file = tmp_path / "runtime_secrets.json"
        caplog.set_level(logging.WARNING)
        with patch("builtins.open", side_effect=OSError("disk error")):
            with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
                from app.utils.runtime_secrets import ensure_runtime_secrets
                ensure_runtime_secrets()
                assert "读取运行时密钥文件失败" in caplog.text

    def test_write_permission_error_logs_warning(self, tmp_path, caplog):
        secrets_file = tmp_path / "runtime_secrets.json"
        caplog.set_level(logging.WARNING)
        with patch("app.utils.runtime_secrets._atomic_write_json", side_effect=PermissionError("no write")):
            with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
                from app.utils.runtime_secrets import ensure_runtime_secrets
                ensure_runtime_secrets()
                assert "无写入权限" in caplog.text

    def test_write_generic_exception_logs_warning(self, tmp_path, caplog):
        secrets_file = tmp_path / "runtime_secrets.json"
        caplog.set_level(logging.WARNING)
        with patch("app.utils.runtime_secrets._atomic_write_json", side_effect=OSError("write fail")):
            with patch.dict(os.environ, {"SECRET_KEY": "", "CSRF_SECRET_KEY": "", "RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
                from app.utils.runtime_secrets import ensure_runtime_secrets
                ensure_runtime_secrets()
                assert "落盘失败" in caplog.text


# ---------------------------------------------------------------------------
# get_or_create_secret
# ---------------------------------------------------------------------------


class TestGetOrCreateSecret:
    def test_existing_key_returned(self, tmp_path):
        secrets_file = tmp_path / "runtime_secrets.json"
        secrets_file.write_text(json.dumps({"MY_KEY": "existing_value"}), encoding="utf-8")
        with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import get_or_create_secret
            val = get_or_create_secret("MY_KEY")
            assert val == "existing_value"

    def test_missing_key_generates_and_persists(self, tmp_path):
        secrets_file = tmp_path / "runtime_secrets.json"
        secrets_file.write_text(json.dumps({}), encoding="utf-8")
        with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import get_or_create_secret
            val = get_or_create_secret("NEW_KEY")
            assert val != ""
            data = json.loads(secrets_file.read_text(encoding="utf-8"))
            assert data["NEW_KEY"] == val

    def test_custom_generate_function(self, tmp_path):
        secrets_file = tmp_path / "runtime_secrets.json"
        secrets_file.write_text(json.dumps({}), encoding="utf-8")
        with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import get_or_create_secret
            val = get_or_create_secret("CUSTOM", generate=lambda: "custom_val_42")
            assert val == "custom_val_42"
            data = json.loads(secrets_file.read_text(encoding="utf-8"))
            assert data["CUSTOM"] == "custom_val_42"

    def test_file_not_found_generates_new(self, tmp_path):
        secrets_file = tmp_path / "runtime_secrets.json"
        with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import get_or_create_secret
            val = get_or_create_secret("FALLBACK")
            assert val != ""
            data = json.loads(secrets_file.read_text(encoding="utf-8"))
            assert data["FALLBACK"] == val

    def test_json_decode_error_logs_and_generates(self, tmp_path, caplog):
        secrets_file = tmp_path / "runtime_secrets.json"
        secrets_file.write_text("{bad", encoding="utf-8")
        caplog.set_level(logging.WARNING)
        with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
            from app.utils.runtime_secrets import get_or_create_secret
            val = get_or_create_secret("RECOVER")
            assert val != ""
            assert "读取运行时密钥文件失败" in caplog.text

    def test_permission_error_logs_and_generates(self, tmp_path, caplog):
        caplog.set_level(logging.WARNING)
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": str(tmp_path / "runtime_secrets.json")}, clear=True):
                from app.utils.runtime_secrets import get_or_create_secret
                val = get_or_create_secret("PERM")
                assert val != ""

    def test_write_exception_still_returns_value(self, tmp_path, caplog):
        secrets_file = tmp_path / "runtime_secrets.json"
        secrets_file.write_text(json.dumps({}), encoding="utf-8")
        caplog.set_level(logging.WARNING)
        with patch("app.utils.runtime_secrets._atomic_write_json", side_effect=OSError("write fail")):
            with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": str(secrets_file)}, clear=True):
                from app.utils.runtime_secrets import get_or_create_secret
                val = get_or_create_secret("NO_PERSIST")
                assert val != ""
                assert "无法持久化" in caplog.text

    def test_default_generate_is_token_urlsafe(self):
        from app.utils.runtime_secrets import get_or_create_secret
        gen = get_or_create_secret.__wrapped__ if hasattr(get_or_create_secret, '__wrapped__') else get_or_create_secret
        import inspect
        source = inspect.getsource(get_or_create_secret)
        assert "token_urlsafe" in source


# ---------------------------------------------------------------------------
# _resolve_secrets_file
# ---------------------------------------------------------------------------


class TestResolveSecretsFile:
    def test_uses_env_var(self):
        with patch.dict(os.environ, {"RUNTIME_SECRETS_FILE": "/custom/path/secrets.json"}, clear=True):
            from app.utils.runtime_secrets import _resolve_secrets_file
            result = _resolve_secrets_file()
            assert result == Path("/custom/path/secrets.json")

    def test_falls_back_to_data_path(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("app.utils.runtime_secrets.get_data_path", return_value=Path("/data/runtime_secrets.json")):
                from app.utils.runtime_secrets import _resolve_secrets_file
                result = _resolve_secrets_file()
                assert result == Path("/data/runtime_secrets.json")


# ---------------------------------------------------------------------------
# _atomic_write_json
# ---------------------------------------------------------------------------


class TestAtomicWriteJson:
    def test_writes_successfully(self, tmp_path):
        dest = tmp_path / "secrets.json"
        from app.utils.runtime_secrets import _atomic_write_json
        _atomic_write_json(dest, {"key": "value"})
        assert dest.exists()
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert data == {"key": "value"}

    def test_cleans_up_temp_on_failure(self, tmp_path):
        dest = tmp_path / "secrets.json"
        with patch("json.dump", side_effect=ValueError("serialization failed")):
            from app.utils.runtime_secrets import _atomic_write_json
            with pytest.raises(ValueError):
                _atomic_write_json(dest, {"key": "value"})
        assert not dest.exists()
        temps = list(tmp_path.glob("secrets.json.*.tmp"))
        assert len(temps) == 0

    def test_cleans_up_fd_on_error(self, tmp_path):
        dest = tmp_path / "secrets.json"
        with patch("os.fdopen", side_effect=OSError("fdopen failed")):
            from app.utils.runtime_secrets import _atomic_write_json
            with pytest.raises(OSError):
                _atomic_write_json(dest, {"key": "value"})
        assert not dest.exists()

    def test_chmod_skipped_on_windows(self, tmp_path):
        dest = tmp_path / "secrets.json"
        from app.utils.runtime_secrets import _atomic_write_json
        with patch("app.utils.runtime_secrets.os.chmod") as mock_chmod:
            _atomic_write_json(dest, {"key": "value"})
            mock_chmod.assert_not_called()

    def test_os_replace_failure_cleans_up_temp(self, tmp_path):
        dest = tmp_path / "secrets.json"
        with patch("os.replace", side_effect=OSError("replace failed")):
            from app.utils.runtime_secrets import _atomic_write_json
            with pytest.raises(OSError):
                _atomic_write_json(dest, {"key": "value"})
        assert not dest.exists()
        temps = list(tmp_path.glob("secrets.json.*.tmp"))
        assert len(temps) == 0

    def test_os_remove_failure_in_cleanup_handled(self, tmp_path):
        dest = tmp_path / "secrets.json"
        with patch("os.replace", side_effect=OSError("replace failed")), \
             patch("os.remove", side_effect=OSError("remove failed")):
            from app.utils.runtime_secrets import _atomic_write_json
            with pytest.raises(OSError):
                _atomic_write_json(dest, {"key": "value"})
        assert not dest.exists()
