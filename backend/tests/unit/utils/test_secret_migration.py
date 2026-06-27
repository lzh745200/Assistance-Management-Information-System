"""
密钥迁移工具测试

测试 app/utils/secret_migration.py 模块
"""
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from app.utils.secret_migration import SecretMigration


@pytest.fixture
def migration(tmp_path):
    env_file = tmp_path / ".env"
    secrets_dir = tmp_path / "secrets"
    return SecretMigration(str(env_file), str(secrets_dir))


class TestSecretMigration:
    def test_init_creates_secrets_dir(self, tmp_path):
        env_file = tmp_path / ".env"
        secrets_dir = tmp_path / "custom_secrets"
        migration = SecretMigration(str(env_file), str(secrets_dir))
        assert Path(secrets_dir).exists()

    def test_read_env_file_not_found(self, migration):
        result = migration._read_env_file()
        assert result == {}

    def test_read_env_file_success(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=value2\n# comment\n\n")
        migration = SecretMigration(str(env_file), str(tmp_path / "secrets"))
        result = migration._read_env_file()
        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_read_env_file_skips_comments_and_empty(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\n\nKEY=val\n")
        migration = SecretMigration(str(env_file), str(tmp_path / "secrets"))
        result = migration._read_env_file()
        assert result == {"KEY": "val"}

    @patch("app.utils.encryption.generate_encryption_key", return_value="new_master_key")
    def test_get_or_create_master_key_new(self, mock_gen, tmp_path):
        env_file = tmp_path / ".env"
        secrets_dir = tmp_path / "secrets"
        migration = SecretMigration(str(env_file), str(secrets_dir))
        key = migration._get_or_create_master_key()
        assert key == "new_master_key"
        assert (secrets_dir / "master.key").exists()
        mock_gen.assert_called_once()

    def test_get_or_create_master_key_existing(self, tmp_path):
        env_file = tmp_path / ".env"
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        master_key_file = secrets_dir / "master.key"
        master_key_file.write_text("existing_master_key")
        migration = SecretMigration(str(env_file), str(secrets_dir))
        key = migration._get_or_create_master_key()
        assert key == "existing_master_key"

    def test_migrate_no_env_file(self, migration):
        report = migration.migrate()
        assert report["success"] is True
        assert report["migrated_keys"] == []
        assert report["skipped_keys"] == ["SECRET_KEY", "CSRF_SECRET_KEY", "SMTP_PASSWORD", "DB_ENCRYPTION_KEY"]

    def test_migrate_success(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=mysecret\nSMTP_PASSWORD=mypass\n")
        secrets_dir = tmp_path / "secrets"
        migration = SecretMigration(str(env_file), str(secrets_dir))
        report = migration.migrate()
        assert report["success"] is True
        assert "SECRET_KEY" in report["migrated_keys"]
        assert "SMTP_PASSWORD" in report["migrated_keys"]
        assert "CSRF_SECRET_KEY" in report["skipped_keys"]
        assert "DB_ENCRYPTION_KEY" in report["skipped_keys"]
        assert (secrets_dir / "encrypted_config.json").exists()
        assert (secrets_dir / "master.key").exists()

    def test_verify_no_secrets_file(self, migration):
        assert migration.verify() is False

    def test_verify_success(self, tmp_path):
        from app.utils.encryption import DataPackageEncryption, generate_encryption_key
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=mysecret\n")
        secrets_dir = tmp_path / "secrets"
        migration = SecretMigration(str(env_file), str(secrets_dir))
        migration.migrate()
        assert migration.verify() is True

    def test_verify_corrupted(self, tmp_path):
        secrets_dir = tmp_path / "secrets"
        secrets_dir.mkdir()
        master_key_file = secrets_dir / "master.key"
        master_key_file.write_text("master_key_12345")
        config_file = secrets_dir / "encrypted_config.json"
        config_file.write_text('{"SECRET_KEY": "not-valid-base64"}')
        env_file = tmp_path / ".env"
        migration = SecretMigration(str(env_file), str(secrets_dir))
        assert migration.verify() is False

    def test_migrate_error_reading_env(self, migration):
        with patch.object(migration, '_read_env_file', side_effect=Exception("Read error")):
            report = migration.migrate()
            assert report["success"] is False
            assert len(report["errors"]) > 0

    def test_migrate_updates_secrets_file_only_with_encrypted_keys(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=value1\nOTHER_KEY=value2\n")
        secrets_dir = tmp_path / "secrets"
        migration = SecretMigration(str(env_file), str(secrets_dir))
        report = migration.migrate()
        assert "SECRET_KEY" in report["migrated_keys"]
        assert "OTHER_KEY" not in report["migrated_keys"]
        secrets_file = secrets_dir / "encrypted_config.json"
        with open(secrets_file) as f:
            saved = json.load(f)
        assert "SECRET_KEY" in saved
        assert "OTHER_KEY" not in saved
