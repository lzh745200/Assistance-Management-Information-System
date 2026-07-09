"""
密钥迁移工具
将 .env 文件中的敏感密钥迁移到加密存储
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict

from .encryption import DataPackageEncryption


class SecretMigration:
    """密钥迁移工具"""

    # 需要加密的敏感配置项
    SENSITIVE_KEYS = [
        "SECRET_KEY",
        "CSRF_SECRET_KEY",
        "SMTP_PASSWORD",
        "DB_ENCRYPTION_KEY",
    ]

    def __init__(self, env_file: str = ".env", secrets_dir: str = "./backend/secrets"):
        """
        初始化迁移工具

        Args:
            env_file: .env 文件路径
            secrets_dir: 加密密钥存储目录
        """
        self.env_file = env_file
        self.secrets_dir = Path(secrets_dir)
        self.secrets_file = self.secrets_dir / "encrypted_config.json"
        self.master_key_file = self.secrets_dir / "master.key"

        # 确保目录存在
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

    def _get_or_create_master_key(self) -> str:
        """获取或创建主密钥"""
        if self.master_key_file.exists():
            with open(self.master_key_file, "r") as f:
                return f.read().strip()
        else:
            # 生成新的主密钥
            from .encryption import generate_encryption_key

            master_key = generate_encryption_key()
            with open(self.master_key_file, "w") as f:
                f.write(master_key)
            # 设置文件权限（仅所有者可读写）
            os.chmod(self.master_key_file, 0o600)
            return master_key

    def _read_env_file(self) -> Dict[str, str]:
        """读取 .env 文件"""
        env_vars = {}
        if not os.path.exists(self.env_file):
            return env_vars

        with open(self.env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                # 解析键值对
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        return env_vars

    def migrate(self) -> Dict[str, any]:
        """
        执行迁移

        Returns:
            迁移报告
        """
        report = {
            "success": False,
            "migrated_keys": [],
            "skipped_keys": [],
            "errors": [],
        }

        try:
            # 读取 .env 文件
            env_vars = self._read_env_file()

            # 获取主密钥
            master_key = self._get_or_create_master_key()
            encryptor = DataPackageEncryption.from_key_string(master_key)

            # 加密敏感配置
            encrypted_config = {}
            for key in self.SENSITIVE_KEYS:
                if key in env_vars and env_vars[key]:
                    # 加密值
                    encrypted_value = encryptor.encrypt_data(env_vars[key].encode())
                    encrypted_config[key] = encrypted_value.decode("utf-8")
                    report["migrated_keys"].append(key)
                else:
                    report["skipped_keys"].append(key)

            # 保存加密配置
            if encrypted_config:
                with open(self.secrets_file, "w") as f:
                    json.dump(encrypted_config, f, indent=2)
                # 设置文件权限
                os.chmod(self.secrets_file, 0o600)

            report["success"] = True
            report["secrets_file"] = str(self.secrets_file)
            report["master_key_file"] = str(self.master_key_file)

        except Exception as e:
            report["errors"].append(str(e))

        return report

    def verify(self) -> bool:
        """
        验证加密配置是否可以正确解密

        Returns:
            是否验证通过
        """
        try:
            if not self.secrets_file.exists():
                return False

            # 读取主密钥
            master_key = self._get_or_create_master_key()
            encryptor = DataPackageEncryption.from_key_string(master_key)

            # 读取加密配置
            with open(self.secrets_file, "r") as f:
                encrypted_config = json.load(f)

            # 尝试解密所有值
            for key, encrypted_value in encrypted_config.items():
                decrypted_value = encryptor.decrypt_data(encrypted_value.encode())
                # 验证解密后的值不为空
                if not decrypted_value:
                    return False

            return True

        except Exception:
            logger = logging.getLogger(__name__)
            logger.error("密钥迁移验证失败", exc_info=True)
            return False


def main():
    """主函数 - 执行迁移"""
    import sys

    # 确定项目根目录
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / ".env"
    secrets_dir = project_root / "backend" / "secrets"

    print("=" * 60)
    print("密钥迁移工具")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print(f".env 文件: {env_file}")
    print(f"密钥存储目录: {secrets_dir}")
    print()

    # 创建迁移工具
    migration = SecretMigration(str(env_file), str(secrets_dir))

    # 执行迁移
    print("开始迁移...")
    report = migration.migrate()

    # 打印报告
    print()
    print("=" * 60)
    print("迁移报告")
    print("=" * 60)
    print(f"状态: {'成功' if report['success'] else '失败'}")
    print(f"已迁移密钥: {', '.join(report['migrated_keys']) if report['migrated_keys'] else '无'}")
    print(f"跳过密钥: {', '.join(report['skipped_keys']) if report['skipped_keys'] else '无'}")

    if report.get("secrets_file"):
        print(f"加密配置文件: {report['secrets_file']}")
    if report.get("master_key_file"):
        print(f"主密钥文件: {report['master_key_file']}")

    if report["errors"]:
        print(f"错误: {', '.join(report['errors'])}")
        sys.exit(1)

    # 验证
    print()
    print("验证加密配置...")
    if migration.verify():
        print("[OK] 验证通过")
    else:
        print("[FAIL] 验证失败")
        sys.exit(1)

    print()
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 在 .env 文件中添加: USE_ENCRYPTED_SECRETS=true")
    print("2. 重启应用以使用加密密钥")
    print("3. 确保 backend/secrets/ 目录的安全性")
    print()


if __name__ == "__main__":
    main()
