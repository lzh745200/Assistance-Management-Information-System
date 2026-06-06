"""TDD: 数据质量自动评分."""
import pytest


class TestQualityScorer:
    def test_score_perfect_data(self):
        from app.services.data_quality_scorer import score_village_data
        village = {
            "village_name": "幸福村", "department": "某部", "support_unit": "某单位",
            "province": "贵州省", "city": "黔东南州", "county": "丹寨县",
            "longitude": 107.5, "latitude": 26.2,
            "population": 800, "households": 200,
        }
        result = score_village_data(village)
        assert result["score"] >= 80
        assert result["level"] in ("good", "excellent")

    def test_score_incomplete_data(self):
        from app.services.data_quality_scorer import score_village_data
        village = {"village_name": "不完整村"}
        result = score_village_data(village)
        assert result["score"] < 60
        assert len(result["missing_fields"]) > 0

    def test_missing_fields_detected(self):
        from app.services.data_quality_scorer import score_village_data
        result = score_village_data({"village_name": "test"})
        assert "longitude" in result["missing_fields"] or "latitude" in result["missing_fields"]

    def test_batch_scoring(self):
        from app.services.data_quality_scorer import batch_score, score_village_data
        data = [
            {"village_name": "A村", "department": "某部", "support_unit": "某单位", "province": "贵州", "city": "黔东南", "county": "丹寨", "longitude": 107, "latitude": 26, "population": 800},
            {"village_name": "B村"},
        ]
        results = batch_score(data, score_village_data)
        assert len(results) == 2
        assert results[0]["score"] > results[1]["score"]

    def test_quality_level_labels(self):
        from app.services.data_quality_scorer import get_quality_level
        assert get_quality_level(95) == "excellent"
        assert get_quality_level(80) == "good"
        assert get_quality_level(60) == "fair"
        assert get_quality_level(40) == "poor"
        assert get_quality_level(10) == "critical"

    def test_overall_report(self):
        from app.services.data_quality_scorer import generate_quality_report
        results = [
            {"score": 90, "level": "excellent"},
            {"score": 50, "level": "fair"},
            {"score": 30, "level": "poor"},
        ]
        report = generate_quality_report(results, "帮扶村")
        assert report["entity_type"] == "帮扶村"
        assert report["total"] == 3
        assert report["average_score"] > 0
        assert "excellent" in report["distribution"]
