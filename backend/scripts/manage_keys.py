#!/usr/bin/env python3
"""
密钥管理 CLI 工具
用于生成主密钥、加密配置文件和管理密钥轮换

使用方法:
    # 生成新主密钥
    python -m scripts.manage_keys generate-key

    # 加密配置文件
    python -m scripts.manage_keys encrypt-config .env.production

    # 解密配置文件（验证用）
    python -m scripts.manage_keys decrypt-config encrypted_config.json

    # 密钥轮换
    python -m scripts.manage_keys rotate-key old_key.txt new_key.txt encrypted_config.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def generate_key():
    """生成新的加密主密钥"""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()
    key_str = key.decode()

    print("=" * 60)
    print("🔐 新主密钥已生成")
    print("=" * 60)
    print(f"\n{key_str}\n")
    print("=" * 60)
    print("⚠️  安全提示:")
    print("   1. 请将此密钥保存到安全位置（如密码管理器）")
    print("   2. 不要将此密钥提交到版本控制")
    print("   3. 建议启用 USE_ENCRYPTED_SECRETS 前备份现有配置")
    print("=" * 60)

    # 保存到文件
    output_file = f"master_key_{datetime.now().strftime('%Y%m%d')}.key"
    with open(output_file, "w") as f:
        f.write(key_str)
    print(f"\n✅ 密钥已保存到: {output_file}")

    return key_str


def encrypt_config(env_file: str, master_key_file: str = None):
    """
    将 .env 文件加密为配置文件

    Args:
        env_file: 环境变量文件路径
        master_key_file: 主密钥文件路径（如果不提供，从环境变量读取）
    """
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.utils.encryption import DataPackageEncryption

    # 读取主密钥
    if master_key_file:
        with open(master_key_file, "r") as f:
            master_key = f.read().strip()
    else:
        master_key = os.environ.get("MASTER_KEY")
        if not master_key:
            print("❌ 错误: 未提供主密钥文件，且环境变量 MASTER_KEY 未设置")
            sys.exit(1)

    # 读取环境文件
    env_path = Path(env_file)
    if not env_path.exists():
        print(f"❌ 错误: 文件不存在: {env_file}")
        sys.exit(1)

    # 解析环境变量
    secrets_to_encrypt = [
        "SECRET_KEY",
        "CSRF_SECRET_KEY",
        "SMTP_PASSWORD",
        "DB_ENCRYPTION_KEY",
        "DATABASE_URL",
        "REDIS_URL",
    ]

    encrypted_config = {}
    encryptor = DataPackageEncryption.from_key_string(master_key)

    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"\'')

                if key in secrets_to_encrypt and value:
                    encrypted_value = encryptor.encrypt_data(value.encode())
                    encrypted_config[key] = encrypted_value.decode()
                    print(f"🔒 已加密: {key}")

    # 保存加密配置
    output_file = "encrypted_config.json"
    with open(output_file, "w") as f:
        json.dump(encrypted_config, f, indent=2)

    print(f"\n✅ 加密配置已保存到: {output_file}")
    print(f"📊 共加密 {len(encrypted_config)} 个密钥")

    # 生成配置指南
    print("\n" + "=" * 60)
    print("📋 启用加密密钥的配置步骤:")
    print("=" * 60)
    print("""
1. 将加密配置文件移动到项目目录:
   mv encrypted_config.json backend/secrets/

2. 将主密钥文件移动到安全位置:
   mv master_key_*.key backend/secrets/master.key

3. 修改 backend/app/core/config.py:
   USE_ENCRYPTED_SECRETS = True
   SECRETS_FILE_PATH = "./backend/secrets/encrypted_config.json"
   MASTER_KEY_PATH = "./backend/secrets/master.key"

4. 确保主密钥文件权限正确（仅限所有者读取）:
   chmod 600 backend/secrets/master.key

5. 重启应用程序
""")


def decrypt_config(encrypted_file: str, master_key_file: str = None):
    """解密配置文件（用于验证）"""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.utils.encryption import DataPackageEncryption

    # 读取主密钥
    if master_key_file:
        with open(master_key_file, "r") as f:
            master_key = f.read().strip()
    else:
        master_key = os.environ.get("MASTER_KEY")
        if not master_key:
            print("❌ 错误: 未提供主密钥文件，且环境变量 MASTER_KEY 未设置")
            sys.exit(1)

    # 读取加密配置
    with open(encrypted_file, "r") as f:
        encrypted_config = json.load(f)

    # 解密
    encryptor = DataPackageEncryption.from_key_string(master_key)

    print("🔓 解密验证:")
    print("=" * 60)

    for key, encrypted_value in encrypted_config.items():
        try:
            decrypted = encryptor.decrypt_data(encrypted_value.encode())
            value_preview = decrypted.decode()[:20] + "..." if len(decrypted) > 20 else decrypted.decode()
            print(f"✅ {key}: {value_preview}")
        except Exception as e:
            print(f"❌ {key}: 解密失败 ({e})")

    print("=" * 60)


def rotate_key(old_key_file: str, new_key_file: str, encrypted_config_file: str):
    """
    密钥轮换：使用新密钥重新加密所有配置

    Args:
        old_key_file: 旧主密钥文件
        new_key_file: 新主密钥文件（如果不存在则生成）
        encrypted_config_file: 加密配置文件
    """
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.utils.encryption import DataPackageEncryption

    # 读取旧密钥
    with open(old_key_file, "r") as f:
        old_key = f.read().strip()

    # 获取/生成新密钥
    if Path(new_key_file).exists():
        with open(new_key_file, "r") as f:
            new_key = f.read().strip()
        print("📝 使用现有新密钥")
    else:
        from cryptography.fernet import Fernet
        new_key = Fernet.generate_key().decode()
        with open(new_key_file, "w") as f:
            f.write(new_key)
        print(f"🆕 已生成新密钥并保存到: {new_key_file}")

    # 读取加密配置
    with open(encrypted_config_file, "r") as f:
        config = json.load(f)

    # 解密并重新加密
    old_encryptor = DataPackageEncryption.from_key_string(old_key)
    new_encryptor = DataPackageEncryption.from_key_string(new_key)

    new_config = {}
    print("\n🔄 执行密钥轮换:")

    for key, encrypted_value in config.items():
        try:
            # 解密
            decrypted = old_encryptor.decrypt_data(encrypted_value.encode())
            # 重新加密
            new_encrypted = new_encryptor.encrypt_data(decrypted)
            new_config[key] = new_encrypted.decode()
            print(f"  ✅ {key}")
        except Exception as e:
            print(f"  ❌ {key}: 失败 ({e})")
            new_config[key] = encrypted_value  # 保留原值

    # 备份旧配置
    backup_file = f"{encrypted_config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    Path(encrypted_config_file).rename(backup_file)
    print(f"\n📦 旧配置已备份到: {backup_file}")

    # 保存新配置
    with open(encrypted_config_file, "w") as f:
        json.dump(new_config, f, indent=2)

    print(f"✅ 新配置已保存到: {encrypted_config_file}")
    print("\n⚠️  重要: 请验证新密钥正常工作后再删除备份！")


def main():
    parser = argparse.ArgumentParser(
        description="密钥管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s generate-key
  %(prog)s encrypt-config .env.production --key master.key
  %(prog)s decrypt-config encrypted_config.json --key master.key
  %(prog)s rotate-key old.key new.key encrypted_config.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # generate-key
    gen_parser = subparsers.add_parser("generate-key", help="生成新主密钥")

    # encrypt-config
    enc_parser = subparsers.add_parser("encrypt-config", help="加密配置文件")
    enc_parser.add_argument("env_file", help="环境变量文件路径")
    enc_parser.add_argument("--key", dest="master_key_file", help="主密钥文件路径")

    # decrypt-config
    dec_parser = subparsers.add_parser("decrypt-config", help="解密配置文件（验证用）")
    dec_parser.add_argument("encrypted_file", help="加密配置文件路径")
    dec_parser.add_argument("--key", dest="master_key_file", help="主密钥文件路径")

    # rotate-key
    rot_parser = subparsers.add_parser("rotate-key", help="执行密钥轮换")
    rot_parser.add_argument("old_key_file", help="旧主密钥文件")
    rot_parser.add_argument("new_key_file", help="新主密钥文件（不存在则生成）")
    rot_parser.add_argument("encrypted_config_file", help="加密配置文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate-key":
        generate_key()
    elif args.command == "encrypt-config":
        encrypt_config(args.env_file, args.master_key_file)
    elif args.command == "decrypt-config":
        decrypt_config(args.encrypted_file, args.master_key_file)
    elif args.command == "rotate-key":
        rotate_key(args.old_key_file, args.new_key_file, args.encrypted_config_file)


if __name__ == "__main__":
    main()
