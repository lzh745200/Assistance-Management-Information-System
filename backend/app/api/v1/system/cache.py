"""Auto-generated stub."""

from fastapi import APIRouter


router = APIRouter()


@router.post("/clear")
async def clear_cache():
    return {"status": "ok"}
