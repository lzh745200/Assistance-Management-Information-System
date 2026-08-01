"""
通用文件上传 API
提供无业务绑定的文件上传端点，返回可直接访问的 /uploads 静态 URL。
"""

import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import settings
from app.core.security import get_current_user
from app.core.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["文件上传"])

# 允许的文件扩展名（按类别分组）
_ALLOWED_EXTS = {
    "image": {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico"},
    "document": {"pdf", "doc", "docx", "ppt", "pptx", "txt", "xls", "xlsx", "csv"},
    "archive": {"zip", "rar", "7z", "tar", "gz"},
    "audio": {"mp3", "wav", "ogg"},
    "video": {"mp4", "avi", "mov", "mkv", "webm"},
}


def _safe_extension(filename: str) -> str:
    """提取文件扩展名（小写、去点）"""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


@router.post("/upload", summary="通用文件上传")
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """上传任意业务模块的附件文件

    Args:
        file: 上传文件
        category: 存储子目录（可选，如 policies/villages/schools）

    Returns:
        url: 可通过 /uploads/... 静态访问的相对 URL
    """
    content = await file.read()

    # 大小限制
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制({settings.MAX_FILE_SIZE // 1048576}MB)",
        )

    # 类型校验（可选扩展名白名单）
    ext = _safe_extension(file.filename or "")
    if ext:
        allowed = set()
        for _exts in _ALLOWED_EXTS.values():
            allowed |= _exts
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

    # 存储目录：uploads/generic[/category]
    base_upload = os.path.abspath(settings.UPLOAD_DIR)
    sub_dir = "generic"
    if category:
        clean_category = category.strip().strip("/").replace("\\", "/")
        # 安全校验：仅允许字母/数字/下划线/连字符/斜杠，禁止路径遍历
        if (
            clean_category
            and ".." not in clean_category.split("/")
            and all(c.isalnum() or c in "-_/" for c in clean_category)
        ):
            sub_dir = os.path.join(sub_dir, *clean_category.split("/"))
    upload_dir = os.path.join(base_upload, sub_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # 唯一文件名（保留原始扩展名）
    unique_name = f"{uuid.uuid4().hex[:16]}{('.' + ext) if ext else ''}"
    file_path = os.path.join(upload_dir, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # 相对 URL（静态挂载在 /uploads 下）
    rel_path = os.path.relpath(file_path, base_upload).replace("\\", "/")
    url = f"/uploads/{rel_path}"

    logger.info(
        "文件上传成功: user=%s, file=%s, url=%s, size=%d",
        getattr(current_user, 'username', 'unknown'),
        file.filename or unique_name,
        url,
        len(content),
    )

    return success_response(
        data={
            "url": url,
            "file_name": file.filename or unique_name,
            "file_size": len(content),
            "file_type": file.content_type or "application/octet-stream",
        },
        message="上传成功",
    )
