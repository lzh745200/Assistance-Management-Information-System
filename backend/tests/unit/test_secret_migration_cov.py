"""app.utils.secret_migration 覆盖率攻坚测试

覆盖点：
- verify：解密值为空 → False
- main：全流程成功 / 验证失败退出 / 迁移错误退出
"""

import json

import pytest

import app.utils.secret_migration as sm
from app.utils.encryption import DataPackageEncryption


def _migration(tmp_path):
    env_file = tmp_path / ".env"
    secrets_dir = tmp_path / "secrets"
    return sm.SecretMigration(str(env_file), str(secrets_dir))


class TestVerify:
    def test_empty_decrypted_value_returns_false(self, tmp_path):
        m = _migration(tmp_path)
        master_key = m._get_or_create_master_key()
        encryptor = DataPackageEncryption.from_key_string(master_key)
        # 加密一个空字节串 → 解密后为 falsy → 验证失败
        encrypted = encryptor.encrypt_data(b"")
        with open(m.secrets_file, "w") as f:
            json.dump({"SECRET_KEY": encrypted.decode("utf-8")}, f)
        assert m.verify() is False


class TestMain:
    def _patch_root(self, monkeypatch, tmp_path):
        fake_file = tmp_path / "backend" / "app" / "utils" / "secret_migration.py"
        monkeypatch.setattr(sm, "__file__", str(fake_file))

    def test_success_flow(self, monkeypatch, tmp_path, capsys):
        self._patch_root(monkeypatch, tmp_path)
        (tmp_path / ".env").write_text(
            "SECRET_KEY=abc\nCSRF_SECRET_KEY=def\n# 注释\nSMTP_PASSWORD=\n", encoding="utf-8"
        )
        sm.main()
        out = capsys.readouterr().out
        assert "验证通过" in out
        assert "迁移完成" in out
        assert "SECRET_KEY" in out
        # 空值密钥被跳过
        assert "SMTP_PASSWORD" in out

    def test_verify_failure_exits(self, monkeypatch, tmp_path, capsys):
        self._patch_root(monkeypatch, tmp_path)
        # 无 .env → 全部跳过 → 不生成加密配置 → verify 失败
        with pytest.raises(SystemExit) as exc_info:
            sm.main()
        assert exc_info.value.code == 1
        assert "验证失败" in capsys.readouterr().out

    def test_migrate_error_exits(self, monkeypatch, tmp_path, capsys):
        self._patch_root(monkeypatch, tmp_path)
        # .env 为目录 → 读取报错 → errors 非空 → 退出
        (tmp_path / ".env").mkdir()
        with pytest.raises(SystemExit) as exc_info:
            sm.main()
        assert exc_info.value.code == 1
        assert "错误" in capsys.readouterr().out

    def test_invalid_json_returns_false(self, tmp_path):
        """加密配置非法 JSON → 异常降级 False（154-157 行）"""
        m = _migration(tmp_path)
        m._get_or_create_master_key()
        m.secrets_file.write_text("not json", encoding="utf-8")
        assert m.verify() is False
