"""补齐 app.services.secrets_manager 覆盖率缺口（39-46 行：默认密钥生成/降级分支）."""
import sys
from unittest.mock import patch

from app.services.secrets_manager import SecretsManager


class TestInitDefaultKey:
    def test_generates_and_persists_key_file(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        mgr = SecretsManager()
        key_file = tmp_path / "bumofu-assistance" / "data" / ".secrets_manager_key"
        assert key_file.exists()
        assert mgr.get_secret("default") == key_file.read_text(encoding="utf-8").strip()

    def test_fernet_import_error_falls_back_to_token(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        with patch.dict(sys.modules, {"cryptography.fernet": None}):
            mgr = SecretsManager()
        assert mgr.get_secret("default")

    def test_os_error_falls_back_to_token(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        with patch("os.makedirs", side_effect=OSError("denied")):
            mgr = SecretsManager()
        assert mgr.get_secret("default")
