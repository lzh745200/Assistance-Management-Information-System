"""异步导出服务 — 委托给 ChunkedUploadService。"""
from app.services.chunked_upload_service import ChunkedUploadService


class AsyncExportService:
    @staticmethod
    async def create_export_session(db, filename: str, total_size: int, total_chunks: int):
        service = ChunkedUploadService(db)
        return await service.create_session(filename, total_size, total_chunks)
