"""
完整测试 - app.services.sentiment.analysis_service
覆盖率目标: 100%
"""
import pytest
from unittest.mock import patch

class TestSentimentResult:
    """测试 SentimentResult 数据类"""

    def test_sentiment_result_creation(self):
        """测试创建情感分析结果"""
        from app.services.sentiment.analysis_service import SentimentResult

        result = SentimentResult(
            sentiment="positive",
            score=0.8,
            confidence=0.9,
            keywords=["好", "优秀"]
        )
        assert result.sentiment == "positive"
        assert result.score == 0.8
        assert result.confidence == 0.9
        assert result.keywords == ["好", "优秀"]

class TestSentimentAnalysisService:
    """测试 SentimentAnalysisService 类"""

    def test_service_creation(self):
        """测试创建服务"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        assert service.model is None
        assert service.initialized is False

    def test_analyze_text_positive(self):
        """测试分析正面情感文本"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        result = service.analyze_text("这个产品很好，非常满意")

        assert result.sentiment == "positive"
        assert result.score > 0
        assert result.confidence == 0.8
        assert len(result.keywords) > 0

    def test_analyze_text_negative(self):
        """测试分析负面情感文本"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        result = service.analyze_text("这个产品很差，非常糟糕")

        assert result.sentiment == "negative"
        assert result.score < 0

    def test_analyze_text_neutral(self):
        """测试分析中性情感文本"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        result = service.analyze_text("这是一个普通的产品")

        assert result.sentiment == "neutral"
        assert -0.1 <= result.score <= 0.1

    def test_analyze_batch(self):
        """测试批量分析"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        texts = ["很好", "很差", "一般"]
        results = service.analyze_batch(texts)

        assert len(results) == 3
        assert results[0].sentiment == "positive"
        assert results[1].sentiment == "negative"

    def test_analyze_batch_empty(self):
        """测试批量分析空列表"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        results = service.analyze_batch([])

        assert results == []

    def test_get_sentiment_score_multiple_positive(self):
        """测试获取情感分数 - 多个正面词"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        score = service.get_sentiment_score("好优秀棒喜欢满意")

        assert score > 0.5
        assert score <= 1.0

    def test_get_sentiment_score_multiple_negative(self):
        """测试获取情感分数 - 多个负面词"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        score = service.get_sentiment_score("差糟糕失败问题困难")

        assert score < -0.5
        assert score >= -1.0

    def test_get_sentiment_score_mixed(self):
        """测试获取情感分数 - 混合情感"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        score = service.get_sentiment_score("好但差")

        # Mixed should be close to neutral or one side depending on implementation
        assert -1.0 <= score <= 1.0

    def test_get_sentiment_score_neutral(self):
        """测试获取情感分数 - 中性文本"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        score = service.get_sentiment_score("abcdefg")

        assert score == 0.0

    def test_get_sentiment_score_clamping_max(self):
        """测试获取情感分数 - 上限截断"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        # Use many positive words to exceed max
        score = service.get_sentiment_score("好优秀棒喜欢满意成功提升增长增长")

        assert score == 1.0

    def test_get_sentiment_score_clamping_min(self):
        """测试获取情感分数 - 下限截断"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        # Use many negative words to exceed min
        score = service.get_sentiment_score("差糟糕失败问题困难下降减少不满")

        assert score == -1.0

    def test_classify_sentiment_positive(self):
        """测试分类情感 - 正面"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        assert service.classify_sentiment(0.5) == "positive"
        assert service.classify_sentiment(0.11) == "positive"
        assert service.classify_sentiment(1.0) == "positive"

    def test_classify_sentiment_negative(self):
        """测试分类情感 - 负面"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        assert service.classify_sentiment(-0.5) == "negative"
        assert service.classify_sentiment(-0.11) == "negative"
        assert service.classify_sentiment(-1.0) == "negative"

    def test_classify_sentiment_neutral(self):
        """测试分类情感 - 中性"""
        from app.services.sentiment.analysis_service import SentimentAnalysisService

        service = SentimentAnalysisService()
        assert service.classify_sentiment(0.0) == "neutral"
        assert service.classify_sentiment(0.05) == "neutral"
        assert service.classify_sentiment(-0.05) == "neutral"
        assert service.classify_sentiment(0.1) == "neutral"
        assert service.classify_sentiment(-0.1) == "neutral"

class TestNormalizeText:
    """测试 normalize_text 函数"""

    def test_normalize_text_basic(self):
        """测试基本标准化"""
        from app.services.sentiment.analysis_service import normalize_text

        result = normalize_text("  Hello   WORLD  ")
        assert result == "hello world"

    def test_normalize_text_empty(self):
        """测试空文本"""
        from app.services.sentiment.analysis_service import normalize_text

        assert normalize_text("") == ""

    def test_normalize_text_none(self):
        """测试None文本"""
        from app.services.sentiment.analysis_service import normalize_text

        assert normalize_text(None) == ""

    def test_normalize_text_multiple_spaces(self):
        """测试多个空格"""
        from app.services.sentiment.analysis_service import normalize_text

        result = normalize_text("a    b    c")
        assert result == "a b c"

    def test_normalize_text_tabs_and_newlines(self):
        """测试制表符和换行"""
        from app.services.sentiment.analysis_service import normalize_text

        result = normalize_text("a\t\tb\n\nc")
        assert result == "a b c"

class TestExtractKeywords:
    """测试 extract_keywords 函数"""

    def test_extract_keywords_basic(self):
        """测试基本关键词提取"""
        from app.services.sentiment.analysis_service import extract_keywords

        text = "苹果 香蕉 苹果 橙子 香蕉 苹果"
        result = extract_keywords(text)

        # Most frequent words should be first
        assert "苹果" in result
        assert len(result) <= 5

    def test_extract_keywords_limit(self):
        """测试关键词数量限制"""
        from app.services.sentiment.analysis_service import extract_keywords

        text = "a b c d e f g h i j"
        result = extract_keywords(text, top_n=3)

        assert len(result) <= 3

    def test_extract_keywords_single_char_ignored(self):
        """测试单字符被忽略"""
        from app.services.sentiment.analysis_service import extract_keywords

        text = "a bb ccc dddd"
        result = extract_keywords(text)

        assert "a" not in result
        assert "bb" in result

    def test_extract_keywords_empty(self):
        """测试空文本"""
        from app.services.sentiment.analysis_service import extract_keywords

        result = extract_keywords("")
        assert result == []

    def test_extract_keywords_no_words(self):
        """测试无单词文本"""
        from app.services.sentiment.analysis_service import extract_keywords

        result = extract_keywords("!@#$%")
        assert result == []

class TestCalculateWeightedScore:
    """测试 calculate_weighted_score 函数"""

    def test_calculate_weighted_score_basic(self):
        """测试基本加权分数"""
        from app.services.sentiment.analysis_service import calculate_weighted_score

        scores = [1.0, 0.5, 0.0]
        weights = [1.0, 1.0, 1.0]
        result = calculate_weighted_score(scores, weights)

        expected = (1.0 + 0.5 + 0.0) / 3.0
        assert result == expected

    def test_calculate_weighted_score_with_weights(self):
        """测试不同权重"""
        from app.services.sentiment.analysis_service import calculate_weighted_score

        scores = [1.0, 0.5]
        weights = [2.0, 1.0]
        result = calculate_weighted_score(scores, weights)

        expected = (1.0 * 2.0 + 0.5 * 1.0) / 3.0
        assert result == expected

    def test_calculate_weighted_score_empty(self):
        """测试空分数列表"""
        from app.services.sentiment.analysis_service import calculate_weighted_score

        result = calculate_weighted_score([])
        assert result == 0.0

    def test_calculate_weighted_score_no_weights(self):
        """测试无权重（默认等权重）"""
        from app.services.sentiment.analysis_service import calculate_weighted_score

        scores = [0.5, 0.5, 0.5]
        result = calculate_weighted_score(scores)

        assert result == 0.5

    def test_calculate_weighted_score_zero_weights(self):
        """测试零权重"""
        from app.services.sentiment.analysis_service import calculate_weighted_score

        scores = [1.0, 0.5]
        weights = [0.0, 0.0]
        result = calculate_weighted_score(scores, weights)

        assert result == 0.0

    def test_calculate_weighted_score_mismatched_length(self):
        """测试长度不匹配"""
        from app.services.sentiment.analysis_service import calculate_weighted_score

        scores = [1.0, 0.5]
        weights = [1.0]

        with pytest.raises(ValueError, match="must have the same length"):
            calculate_weighted_score(scores, weights)

    def test_calculate_weighted_score_single_score(self):
        """测试单分数"""
        from app.services.sentiment.analysis_service import calculate_weighted_score

        result = calculate_weighted_score([0.8])
        assert result == 0.8
