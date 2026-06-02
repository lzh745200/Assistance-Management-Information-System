"""
Data routes - delegates to real implementations in data/data/ subpackage.

All actual route logic lives in data/data/ (analytics, statistics, reports,
data_reports, data_packages, dashboard, data_quality).
"""
from fastapi import APIRouter

from app.api.v1.data.data import router as data_router

router = APIRouter()
router.include_router(data_router)
