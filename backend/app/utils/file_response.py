"""安全的文件响应工具 — 替换裸 StreamingResponse 防止句柄泄漏。

使用方式：
    # 从内存 BytesIO 构建下载
    return bytesio_response(output, filename="data.xlsx")

    # 从文件路径构建下载
    return filepath_response(path, filename="data.xlsx")

    # 从 open() 文件对象构建（自动关闭句柄）
    return file_response(fp, filename="data.pdf")

所有函数返回 FileResponse（Starlette 会在响应后调用 close()），
确保文件句柄/内存缓冲区被正确清理。
"""

from __future__ import annotations

import os
import tempfile
from io import BytesIO
from typing import IO, Optional

from fastapi.responses import FileResponse


def bytesio_response(
    buf: BytesIO,
    *,
    filename: str = "download",
    media_type: str = "application/octet-stream",
) -> FileResponse:
    """将 BytesIO 写入临时文件后返回 FileResponse。

    临时文件在响应完成后自动删除（Starlette FileResponse 行为）。
    """
    buf.seek(0)
    # 写入临时文件（保留后缀以帮助浏览器识别）
    _, ext = os.path.splitext(filename)
    tmp = tempfile.NamedTemporaryFile(suffix=ext or ".tmp", delete=False)
    try:
        tmp.write(buf.read())
        tmp.close()
        return FileResponse(
            tmp.name,
            media_type=media_type,
            filename=filename,
            background=None,  # Starlette handles cleanup
        )
    except Exception:
        # 出错时主动清理临时文件
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        raise


def filepath_response(
    path: str,
    *,
    filename: Optional[str] = None,
    media_type: str = "application/octet-stream",
) -> FileResponse:
    """从磁盘路径返回 FileResponse（安全，无句柄泄漏）。"""
    return FileResponse(
        path,
        media_type=media_type,
        filename=filename or os.path.basename(path),
    )


def file_response(
    fp: IO[bytes],
    *,
    filename: str = "download",
    media_type: str = "application/octet-stream",
) -> FileResponse:
    """从已打开的 file-like 对象写入临时文件，关闭原文件，返回 FileResponse。"""
    try:
        fp.seek(0)
        _, ext = os.path.splitext(filename)
        tmp = tempfile.NamedTemporaryFile(suffix=ext or ".tmp", delete=False)
        try:
            tmp.write(fp.read())
            tmp.close()
            return FileResponse(
                tmp.name,
                media_type=media_type,
                filename=filename,
            )
        except Exception:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
            raise
    finally:
        try:
            fp.close()
        except Exception:
            pass
