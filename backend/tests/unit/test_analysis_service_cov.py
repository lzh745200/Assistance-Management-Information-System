"""app.services.sentiment.analysis_service 覆盖率攻坚测试

补齐缺口：
- analyze_news_batch（119-138）：批量分析未处理新闻并回写，含提交/空结果分支
- generate_hot_keywords（147-171）：热词聚合（标题提取 + 已存 keywords + 多数派情感）

db 使用 MagicMock 链式查询，新闻对象用 SimpleNamespace 模拟。
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.sentiment.analysis_service import SentimentAnalysisService


def _db_with_rows(rows):
    """构造链式查询 Mock：query().filter().order_by().limit().all() -> rows"""
    db = MagicMock()
    q = db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.all.return_value = rows
    return db


def _news(title, keywords=""):
    return SimpleNamespace(
        title=title,
        keywords=keywords,
        sentiment_label=None,
        sentiment_score=None,
        is_alert=False,
        processed=False,
    )


class TestAnalyzeNewsBatch:
    def test_processes_news_and_commits(self):
        # 3 个负面词 → score=-0.6 ≤ -0.4 → 舆情预警
        news_alert = _news("差 糟糕 失败")
        # 正面 → 不预警；keywords 被新提取结果覆盖
        news_ok = _news("优秀 满意", keywords="stale")
        db = _db_with_rows([news_alert, news_ok])

        count = SentimentAnalysisService.analyze_news_batch(db, limit=10)

        assert count == 2
        assert news_alert.sentiment_label == "negative"
        assert news_alert.sentiment_score <= SentimentAnalysisService.ALERT_SCORE_THRESHOLD
        assert news_alert.is_alert is True
        assert news_alert.processed is True
        assert "糟糕" in news_alert.keywords  # 提取的关键词已回写
        assert news_ok.sentiment_label == "positive"
        assert news_ok.is_alert is False
        assert news_ok.keywords != "stale"
        db.commit.assert_called_once()

    def test_empty_result_skips_commit(self):
        db = _db_with_rows([])
        count = SentimentAnalysisService.analyze_news_batch(db)
        assert count == 0
        db.commit.assert_not_called()

    def test_title_none_keeps_existing_keywords(self):
        # title=None → analyze_text("") → 无关键词 → 保留原 keywords
        news = _news(None, keywords="old_kw")
        db = _db_with_rows([news])

        count = SentimentAnalysisService.analyze_news_batch(db)

        assert count == 1
        assert news.keywords == "old_kw"
        assert news.sentiment_label == "neutral"
        assert news.is_alert is False
        db.commit.assert_called_once()


class TestGenerateHotKeywords:
    def test_aggregates_title_and_stored_keywords(self):
        rows = [
            ("苹果 苹果 香蕉", "苹果, 梨子", "positive"),
            ("苹果 橙子", None, None),          # 无已存关键词、无情感标签 → neutral
            (None, " , 葡萄 ,", "negative"),     # 标题为 None、空白片段被跳过
        ]
        db = _db_with_rows(rows)

        result = SentimentAnalysisService.generate_hot_keywords(db, days=7, top_k=10)

        assert len(result) == 5
        by_word = {item["word"]: item for item in result}
        assert by_word["苹果"]["count"] == 2  # 两行标题各出现一次（set 去重）
        assert by_word["苹果"]["sentiment"] == "positive"
        assert by_word["梨子"]["count"] == 1
        assert by_word["橙子"]["sentiment"] == "neutral"
        assert by_word["葡萄"]["sentiment"] == "negative"
        assert "" not in by_word
        # 按词频降序，苹果居首
        assert result[0]["word"] == "苹果"
        assert all(set(item) == {"word", "count", "sentiment"} for item in result)

    def test_top_k_truncates(self):
        rows = [("苹果 香蕉 橙子", "葡萄, 梨子", "positive")]
        db = _db_with_rows(rows)

        result = SentimentAnalysisService.generate_hot_keywords(db, days=3, top_k=2)

        assert len(result) == 2
