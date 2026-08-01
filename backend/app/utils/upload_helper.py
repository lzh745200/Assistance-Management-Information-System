"""统一文件上传/下载工具 — 消除各模块重复的附件处理逻辑。

所有模块（经费、学校、帮扶村、政策等）的附件上传下载统一使用此模块，
确保安全校验、路径处理、审计日志的一致性。

使用方式：
    from app.utils.upload_helper import save_upload_file, get_attachment_response

    # 上传
    file_info = await save_upload_file(
        file=upload_file,
        sub_dir="funds/123",
        allowed_extensions=["pdf", "doc", "docx"],
    )
    # file_info = {"file_name": ..., "file_path": ..., "file_size": ..., "file_type": ...}

    # 下载
    return get_attachment_response(file_path=file_info["file_path"], filename=file_info["file_name"])
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Optional, Set

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── 默认允许的文件扩展名 ──
DEFAULT_ALLOWED_EXTENSIONS: Set[str] = {
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
    "txt", "zip", "rar", "jpg", "jpeg", "png", "gif", "bmp",
}


async def save_upload_file(
    file: UploadFile,
    sub_dir: str,
    *,
    allowed_extensions: Optional[Set[str]] = None,
    max_size: Optional[int] = None,
) -> dict:
    """统一的文件上传保存逻辑。

    Args:
        file: FastAPI UploadFile 对象
        sub_dir: 上传子目录（如 "funds/123", "schools/456"）
        allowed_extensions: 允许的文件扩展名集合，None 则使用默认集合
        max_size: 最大文件大小（字节），None 则使用 settings.MAX_FILE_SIZE

    Returns:
        dict: {"file_name": str, "file_path": str, "file_size": int, "file_type": str}

    Raises:
        HTTPException: 文件大小超限 / 类型不允许 / 写入失败
    """
    # 1. 读取文件内容
    content = await file.read()

    # 2. 检查文件大小
    _max_size = max_size or settings.MAX_FILE_SIZE
    if len(content) > _max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制({_max_size // 1048576}MB)",
        )

    # 3. 检查文件类型
    ext = ""
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()

    _allowed = allowed_extensions or (settings.allowed_file_types_list + list(DEFAULT_ALLOWED_EXTENSIONS))
    if ext and ext not in _allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: .{ext}",
        )

    # 4. 创建存储目录（使用绝对路径，防止路径遍历攻击）
    base_upload = os.path.abspath(settings.UPLOAD_DIR)
    upload_dir = os.path.join(base_upload, sub_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # 5. 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex[:12]}_{file.filename or 'unknown'}"
    file_path = os.path.join(upload_dir, unique_name)

    # 6. 写入文件
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as e:
        logger.error("文件写入失败: %s, 原因: %s", file_path, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件上传失败，请重试",
        )

    return {
        "file_name": file.filename or "unknown",
        "file_path": file_path,
        "file_size": len(content),
        "file_type": file.content_type or "application/octet-stream",
    }


def get_attachment_response(
    file_path: str,
    filename: str,
    media_type: Optional[str] = None,
    *,
    inline: bool = False,
) -> FileResponse:
    """统一的文件下载响应。

    Args:
        file_path: 文件绝对路径
        filename: 下载时显示的文件名
        media_type: MIME 类型，None 则自动推断
        inline: True 则使用 inline 模式（浏览器内预览），False 则 attachment 下载

    Returns:
        FileResponse

    Raises:
        HTTPException: 文件不存在
    """
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件文件不存在",
        )

    import mimetypes
    if not media_type:
        media_type, _ = mimetypes.guess_type(file_path)
        if not media_type:
            media_type = "application/octet-stream"

    headers = {}
    if inline:
        headers["Content-Disposition"] = f"inline; filename*=UTF-8''{filename}"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers=headers if headers else None,
    )


def delete_attachment_file(file_path: str) -> bool:
    """安全删除磁盘文件。

    放在 DB commit 之后调用，即使文件删除失败也不影响数据库操作。

    Returns:
        True 如果删除成功，False 如果文件不存在或删除失败
    """
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        os.remove(file_path)
        return True
    except OSError as e:
        logger.warning("删除文件失败: %s, 原因: %s", file_path, e)
        return False
