import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.utils.paths import get_uploads_path


def find_frontend_dir() -> str | None:
    """查找前端构建产物目录，返回包含 index.html 的目录路径或 None。"""
    # PyInstaller 打包后 _MEIPASS 才可用，否则跳过以免匹配到相对路径
    _meipass = getattr(sys, '_MEIPASS', '')
    candidates = [
        os.environ.get("FRONTEND_DIST_PATH", ""),
        # PyInstaller 打包后：资源在 _MEIPASS 中（仅冻结环境启用）
        str(Path(_meipass) / "resources" / "frontend") if _meipass else "",
        str(Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"),
        str(Path(__file__).resolve().parent.parent.parent.parent / "resources" / "frontend"),
        # 项目根目录下的 resources/frontend（从任意 CWD 启动均可靠）
        str(Path(__file__).resolve().parent.parent.parent.parent / ".." / "resources" / "frontend"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, "index.html")):
            return candidate
    return None


def setup_static_files(app: FastAPI) -> str | None:
    """挂载上传目录静态文件并返回前端目录路径（或 None）。

    前端路由和 SPA fallback 由 main.py 负责注册。
    """
    uploads_dir = settings.UPLOAD_DIR

    if not os.path.isabs(uploads_dir) or (
        getattr(sys, "frozen", False) and uploads_dir.startswith(os.path.dirname(sys.executable))
    ):
        uploads_dir = str(get_uploads_path())

    try:
        os.makedirs(uploads_dir, exist_ok=True)
    except PermissionError:
        uploads_dir = str(get_uploads_path())
        os.makedirs(uploads_dir, exist_ok=True)

    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    return find_frontend_dir()
