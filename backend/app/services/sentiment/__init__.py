"""
情感分析服务模块

提供情感数据采集和分析功能
"""

from .crawler_service import SentimentCrawlerService, SentimentData
from .analysis_service import (
    SentimentAnalysisService,
    SentimentResult,
    normalize_text,
    extract_keywords,
    calculate_weighted_score,
)

__all__ = [
    "SentimentCrawlerService",
    "SentimentData",
    "SentimentAnalysisService",
    "SentimentResult",
    "normalize_text",
    "extract_keywords",
    "calculate_weighted_score",
]
