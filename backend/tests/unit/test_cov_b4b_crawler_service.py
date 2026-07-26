"""补齐 app.services.sentiment.crawler_service 覆盖率缺口（142-157 行：爬虫启用时的模拟 RSS 抓取）."""
from unittest.mock import patch

import app.services.sentiment.crawler_service as cs


class TestFetchRssFeedsEnabled:
    def test_returns_mock_news_when_crawler_enabled(self):
        with patch.object(cs, "_CRAWLER_ENABLED", True):
            items = cs.CrawlerService.fetch_rss_feeds(None, ["扶贫", "乡村振兴"])
        assert len(items) == 2
        assert items[0].title == "关于扶贫的新闻"
        assert items[0].source == "RSS Feed"
        assert items[0].keywords == ["扶贫"]
        assert items[0].published_at is not None
