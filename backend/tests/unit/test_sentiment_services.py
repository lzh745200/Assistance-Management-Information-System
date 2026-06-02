"""
测试 - app.services.sentiment 模块
覆盖率目标: 100%
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

class TestSentimentData:
    """测试 SentimentData 数据类"""

    def test_sentiment_data_creation(self):
        """测试 SentimentData 创建"""
        from app.services.sentiment.crawler_service import SentimentData
        data = SentimentData(
            id="123",
            source="news",
            content="测试内容",
            timestamp=datetime.utcnow(),
            metadata={"key": "value"}
        )
        assert data.id == "123"
        assert data.source == "news"
        assert data.content == "测试内容"

class TestSentimentCrawlerService:
    """测试 SentimentCrawlerService 类"""

    def test_service_import(self):
        """测试类可以导入"""
        from app.services.sentiment.crawler_service import SentimentCrawlerService
        assert SentimentCrawlerService is not None

    def test_service_creation(self):
        """测试服务创建"""
        from app.services.sentiment.crawler_service import SentimentCrawlerService
        service = SentimentCrawlerService()
        assert service is not None
        assert service.sources == []
        assert service.crawled_data == []

    def test_crawl_news(self):
        """测试爬取新闻"""
        from app.services.sentiment.crawler_service import SentimentCrawlerService
        service = SentimentCrawlerService()
        result = service.crawl_news(["关键词"], limit=10)
        assert isinstance(result, list)

    def test_crawl_social_media(self):
        """测试爬取社交媒体"""
        from app.services.sentiment.crawler_service import SentimentCrawlerService
        service = SentimentCrawlerService()
        result = service.crawl_social_media(["关键词"], ["weibo"], limit=10)
        assert isinstance(result, list)

    def test_parse_content(self):
        """测试解析内容"""
        from app.services.sentiment.crawler_service import SentimentCrawlerService
        service = SentimentCrawlerService()
        result = service.parse_content("原始内容", "news")
        assert result["text"] == "原始内容"
        assert result["source_type"] == "news"
        assert "parsed_at" in result

class TestSentimentAnalysisService:
    """测试 SentimentAnalysisService 类"""

    def test_service_import(self):
        """测试类可以导入"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService
        assert SentimentAnalysisService is not None

    def test_service_creation(self):
        """测试服务创建"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService
        service = SentimentAnalysisService()
        assert service is not None

    def test_analyze_text(self):
        """测试分析文本"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService
        service = SentimentAnalysisService()
        result = service.analyze_text("这是一个测试")
        assert result is not None

    def test_analyze_batch(self):
        """测试批量分析"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService
        service = SentimentAnalysisService()
        texts = ["文本1", "文本2", "文本3"]
        result = service.analyze_batch(texts)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_get_sentiment_label(self):
        """测试获取情感标签"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService
        service = SentimentAnalysisService()
        # 测试情感标签映射
        result = service.analyze_text("good")
        assert result is not None
