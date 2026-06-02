"""
应用路径工具模块

解决不同平台的数据目录权限问题：
- 开发环境：使用项目目录（./data, ./backups, ./cache）
- Windows 生产环境：使用用户数据目录（%APPDATA%/bumofu-assistance/）
- Linux 生产环境（麒麟V10 ARM64）：使用家目录隐藏文件夹（~/.bumofu/）
"""

import os
import platform
import sys
from pathlib import Path


class PathTraversalError(ValueError):
    """路径遍历安全异常"""


def _safe_join(base: Path, sub_path: str) -> Path:
    """
    安全地拼接路径，防止路径遍历攻击。

    Args:
        base: 基础目录
        sub_path: 子路径

    Returns:
        Path: 拼接后的路径

    Raises:
        PathTraversalError: 如果子路径试图逃逸基础目录
    """
    if not sub_path:
        return base

    resolved = (base / sub_path).resolve()
    base_resolved = base.resolve()

    # 确保解析后的路径仍在基础目录内
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        raise PathTraversalError(
            f"路径遍历被拒绝: '{sub_path}' 试图逃逸 '{base}'"
        )

    return resolved


def is_bundled() -> bool:
    """检测是否在 PyInstaller 打包环境中运行"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def is_linux() -> bool:
    """检测是否在 Linux 平台上运行"""
    return platform.system() == "Linux"


def get_app_data_dir() -> Path:
    """
    获取应用数据目录

    返回:
        Path: 可写的应用数据目录路径
    """
    if is_bundled() or (is_linux() and not os.environ.get("BUMOFU_DEV_MODE")):
        if is_linux():
            # Linux（麒麟V10 ARM64）：使用家目录隐藏文件夹
            data_dir = Path.home() / ".bumofu"
        else:
            # Windows：使用 AppData/Local
            base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            if base_dir:
                data_dir = Path(base_dir) / "bumofu-assistance"
            else:
                data_dir = Path.home() / ".bumofu"
    else:
        # 开发环境：使用项目目录
        data_dir = Path.cwd()

    # 确保目录存在
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_data_path(sub_path: str = "") -> Path:
    """
    获取数据文件路径

    Args:
        sub_path: 相对于数据目录的子路径

    返回:
        Path: 完整的数据文件路径

    Raises:
        PathTraversalError: 如果子路径试图逃逸基础目录
    """
    base = get_app_data_dir() / "data"
    if sub_path:
        path = _safe_join(base, sub_path)
        # 如果子路径包含目录部分，确保目录存在
        if path.parent != base:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return base


def get_backup_path(sub_path: str = "") -> Path:
    """
    获取备份文件路径

    Args:
        sub_path: 相对于备份目录的子路径

    返回:
        Path: 完整的备份文件路径

    Raises:
        PathTraversalError: 如果子路径试图逃逸基础目录
    """
    base = get_app_data_dir() / "backups"
    if sub_path:
        path = _safe_join(base, sub_path)
        if path.parent != base:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return base


# 向后兼容的别名
get_backup_directory = get_backup_path


def get_cache_path(sub_path: str = "") -> Path:
    """
    获取缓存文件路径

    Args:
        sub_path: 相对于缓存目录的子路径

    返回:
        Path: 完整的缓存文件路径
    """
    # 缓存使用 Local 目录（不漫游）
    if is_bundled() or (is_linux() and not os.environ.get("BUMOFU_DEV_MODE")):
        if is_linux():
            base = Path.home() / ".bumofu" / "cache"
        else:
            base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            if base_dir:
                base = Path(base_dir) / "bumofu-assistance" / "cache"
            else:
                base = Path.home() / ".bumofu" / "cache"
    else:
        # 开发环境：与其他路径函数保持一致
        base = get_app_data_dir() / "data" / "cache"

    if sub_path:
        path = _safe_join(base, sub_path)
        if path.parent != base:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return base


def get_uploads_path(sub_path: str = "") -> Path:
    """
    获取上传文件路径

    Args:
        sub_path: 相对于上传目录的子路径

    返回:
        Path: 完整的上传文件路径

    Raises:
        PathTraversalError: 如果子路径试图逃逸基础目录
    """
    base = get_app_data_dir() / "uploads"
    if sub_path:
        path = _safe_join(base, sub_path)
        if path.parent != base:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return base


def get_database_path() -> Path:
    """
    获取数据库文件路径

    返回:
        Path: 数据库文件的完整路径
    """
    return get_data_path("rural_revitalization.db")


def get_log_path(sub_path: str = "") -> Path:
    """
    获取日志文件路径

    Args:
        sub_path: 相对于日志目录的子路径

    返回:
        Path: 完整的日志文件路径

    Raises:
        PathTraversalError: 如果子路径试图逃逸基础目录
    """
    base = get_app_data_dir() / "logs"
    base.mkdir(parents=True, exist_ok=True)
    if sub_path:
        path = _safe_join(base, sub_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return base
