"""
管理员密码重置工具（支持任意数据库文件）

用法：
    python -m app.utils.reset_admin_password --password <新密码> [--db 数据库文件路径]

密码为必填参数（不接受默认弱密码 admin123），且需通过复杂度校验：
长度 ≥ 8，包含大写、小写、数字、特殊字符。

未指定 --db 时使用开发环境默认数据库。
重置后清除 must_change_password 标记（--no-clear-flag 保留）。

生产环境（Electron 打包）数据库通常位于：
    %LOCALAPPDATA%\\bumofu-assistance\\data\\rural_revitalization.db

示例：
    python -m app.utils.reset_admin_password --password "MyNewPass123!"
    python -m app.utils.reset_admin_password --password "MyNewPass123!" ^
        --db "%LOCALAPPDATA%\\bumofu-assistance\\data\\rural_revitalization.db"
"""

import argparse
import os
import re
import sqlite3
import sys


class PasswordTooWeakError(ValueError):
    """密码不满足复杂度要求"""


def validate_password_strength(password: str) -> None:
    """校验密码复杂度，弱密码直接抛错（避免生产库被重置为弱口令）。"""
    if len(password) < 8:
        raise PasswordTooWeakError("密码长度至少 8 位")
    checks = {
        "大写字母": r"[A-Z]",
        "小写字母": r"[a-z]",
        "数字": r"\d",
        "特殊字符": r"[^A-Za-z0-9]",
    }
    missing = [name for name, pattern in checks.items() if not re.search(pattern, password)]
    if missing:
        raise PasswordTooWeakError("密码需包含" + "、".join(missing))


def _default_db_path() -> str:
    """开发环境默认数据库路径"""
    return os.path.join(os.getcwd(), "data", "rural_revitalization.db")


def _resolve_env(path: str) -> str:
    """展开环境变量（如 %LOCALAPPDATA%）"""
    return os.path.expandvars(os.path.expanduser(path))


def reset_admin_password(db_path: str, new_password: str, clear_flag: bool = True) -> bool:
    """重置指定数据库中 admin 用户的密码

    Args:
        db_path: SQLite 数据库文件路径
        new_password: 新密码（必填，需满足复杂度要求）
        clear_flag: 是否清除 must_change_password 强制改密标记

    Returns:
        bool: 是否重置成功
    """
    validate_password_strength(new_password)
    db_path = _resolve_env(db_path)
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    # 使用与后端一致的 bcrypt 哈希（passlib + bcrypt 兼容层）
    from app.core.security import get_password_hash

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, username, role FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        if not row:
            print(f"数据库 {db_path} 中未找到 admin 用户")
            # 列出存在的用户供参考
            users = conn.execute("SELECT username FROM users LIMIT 10").fetchall()
            if users:
                print("现有用户:", ", ".join(u[0] for u in users))
            return False

        new_hash = get_password_hash(new_password)
        if clear_flag:
            conn.execute(
                "UPDATE users SET hashed_password = ?, must_change_password = 0 WHERE username = ?",
                (new_hash, "admin"),
            )
        else:
            conn.execute(
                "UPDATE users SET hashed_password = ? WHERE username = ?",
                (new_hash, "admin"),
            )
        conn.commit()
        print(f"已重置数据库 {db_path} 中 admin 的密码: {new_password}")
        if clear_flag:
            print("must_change_password 标记已清除（可直接登录）")
        else:
            print("must_change_password 标记保留（首次登录将强制改密）")
        return True
    except Exception as e:
        conn.rollback()
        print(f"重置失败: {e}")
        return False
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="管理员密码重置工具")
    parser.add_argument("--password", required=True,
                        help="新密码（必填，需含大小写字母、数字、特殊字符且长度≥8）")
    parser.add_argument("--db", default=None, help="数据库文件路径（默认开发环境数据库）")
    parser.add_argument("--no-clear-flag", action="store_true", help="保留 must_change_password 标记")
    args = parser.parse_args()

    db_path = args.db if args.db else _default_db_path()
    try:
        ok = reset_admin_password(
            db_path,
            new_password=args.password,
            clear_flag=not args.no_clear_flag,
        )
    except PasswordTooWeakError as e:
        print(f"密码不符合复杂度要求: {e}")
        sys.exit(2)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
