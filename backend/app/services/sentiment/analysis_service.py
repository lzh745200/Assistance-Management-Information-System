"""
情感分析服务

提供文本情感分析功能
"""

import heapq
import re
from dataclasses import dataclass
from typing import List, Optional

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
    word_freq = {}
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
