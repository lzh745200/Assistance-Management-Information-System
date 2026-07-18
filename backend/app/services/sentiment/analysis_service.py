"""
情感分析服务

提供文本情感分析功能
"""

import heapq
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# 情感词典（模块级常量，避免每次调用重建）
_POSITIVE_WORDS = ["好", "优秀", "棒", "喜欢", "满意", "成功", "提升", "增长"]
_NEGATIVE_WORDS = ["差", "糟糕", "失败", "问题", "困难", "下降", "减少", "不满"]


@dataclass
class SentimentResult:
    """情感分析结果"""

    sentiment: str  # positive, negative, neutral
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    keywords: List[str]


class SentimentAnalysisService:
    """
    情感分析服务

    分析文本情感倾向
    """

    def __init__(self):
        self.model = None
        self.initialized = False

    def analyze_text(self, text: str) -> SentimentResult:
        """
        分析单条文本的情感

        Args:
            text: 待分析的文本

        Returns:
            SentimentResult: 情感分析结果
        """
        # 简单的情感分析逻辑
        normalized = normalize_text(text)
        keywords = extract_keywords(normalized)
        score = self.get_sentiment_score(normalized)
        sentiment = self.classify_sentiment(score)

        return SentimentResult(sentiment=sentiment, score=score, confidence=0.8, keywords=keywords)

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        批量分析文本情感

        Args:
            texts: 待分析的文本列表

        Returns:
            List[SentimentResult]: 情感分析结果列表
        """
        return [self.analyze_text(text) for text in texts]

    def get_sentiment_score(self, text: str) -> float:
        """
        获取文本的情感分数

        Args:
            text: 待分析的文本

        Returns:
            float: 情感分数，范围 -1.0 到 1.0
        """
        score = 0.0
        for word in _POSITIVE_WORDS:
            if word in text:
                score += 0.2
        for word in _NEGATIVE_WORDS:
            if word in text:
                score -= 0.2

        return max(-1.0, min(1.0, score))

    def classify_sentiment(self, score: float) -> str:
        """
        根据分数分类情感

        Args:
            score: 情感分数

        Returns:
            str: 情感分类 (positive, negative, neutral)
        """
        if score > 0.1:
            return "positive"
        elif score < -0.1:
            return "negative"
        else:
            return "neutral"

    # 舆情预警阈值：负面且分数不高于该值时标记 is_alert
    ALERT_SCORE_THRESHOLD = -0.4

    @classmethod
    def analyze_news_batch(cls, db, limit: int = 100) -> int:
        """批量分析未处理新闻的情感并回写结果。

        Args:
            db: 数据库会话
            limit: 单次最多处理条数

        Returns:
            int: 本次处理的新闻数量
        """
        from app.models.sentiment import SentimentNews

        service = cls()
        news_list = (
            db.query(SentimentNews)
            .filter(SentimentNews.processed == False)  # noqa: E712
            .order_by(SentimentNews.published_at.desc())
            .limit(limit)
            .all()
        )
        for news in news_list:
            result = service.analyze_text(news.title or "")
            news.sentiment_label = result.sentiment
            news.sentiment_score = result.score
            news.keywords = ",".join(result.keywords) if result.keywords else (news.keywords or "")
            news.is_alert = result.sentiment == "negative" and result.score <= cls.ALERT_SCORE_THRESHOLD
            news.processed = True
        if news_list:
            db.commit()
        return len(news_list)

    @classmethod
    def generate_hot_keywords(cls, db, days: int = 7, top_k: int = 20) -> List[Dict[str, Any]]:
        """统计近 N 天新闻热词（标题关键词提取 + 已存 keywords 字段聚合）。

        Returns:
            [{"word": w, "count": n, "sentiment": 多数派情感标签}]，按词频降序
        """
        from collections import Counter
        from datetime import datetime, timedelta, timezone

        from app.models.sentiment import SentimentNews

        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            db.query(SentimentNews.title, SentimentNews.keywords, SentimentNews.sentiment_label)
            .filter(SentimentNews.published_at >= since)
            .all()
        )

        counter: Counter = Counter()
        sentiment_votes: Dict[str, Counter] = {}
        for title, stored_keywords, label in rows:
            words = set(extract_keywords(title or "", top_n=8))
            for kw in (stored_keywords or "").split(","):
                kw = kw.strip()
                if kw:
                    words.add(kw)
            for word in words:
                counter[word] += 1
                sentiment_votes.setdefault(word, Counter())[label or "neutral"] += 1

        return [
            {
                "word": word,
                "count": count,
                "sentiment": sentiment_votes[word].most_common(1)[0][0],
            }
            for word, count in counter.most_common(top_k)
        ]


def normalize_text(text: str) -> str:
    """
    标准化文本

    Args:
        text: 原始文本

    Returns:
        str: 标准化后的文本
    """
    if not text:
        return ""
    # 移除多余空白
    text = re.sub(r"\s+", " ", text)
    # 转换为小写
    return text.strip().lower()


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    提取关键词

    Args:
        text: 待分析的文本
        top_n: 返回的关键词数量

    Returns:
        List[str]: 关键词列表
    """
    # 简单的关键词提取（基于词频）
    words = re.findall(r"\b\w+\b", text)
    word_freq: dict[str, int] = {}
    for word in words:
        if len(word) > 1:
            word_freq[word] = word_freq.get(word, 0) + 1

    # 使用堆获取top_n，避免全量排序
    top_words = heapq.nlargest(top_n, word_freq.items(), key=lambda x: x[1])
    return [word for word, freq in top_words]


def calculate_weighted_score(scores: List[float], weights: Optional[List[float]] = None) -> float:
    """
    计算加权情感分数

    Args:
        scores: 分数列表
        weights: 权重列表

    Returns:
        float: 加权后的分数
    """
    if not scores:
        return 0.0

    if weights is None:
        weights = [1.0] * len(scores)

    if len(scores) != len(weights):
        raise ValueError("Scores and weights must have the same length")

    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    return weighted_sum / total_weight
