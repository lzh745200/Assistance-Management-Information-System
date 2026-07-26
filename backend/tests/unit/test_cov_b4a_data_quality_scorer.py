"""覆盖率攻坚: app/services/data_quality_scorer.py 缺口行 27（score_fund_data）、87（空结果报告）。"""


class TestScoreFundData:
    def test_score_complete_fund(self):
        """完整经费数据评分（第 27 行）."""
        from app.services.data_quality_scorer import score_fund_data

        fund = {
            "name": "专项资金", "amount": 100000, "fund_type": "专项", "source": "财政",
            "project_id": 1, "village_id": 2, "organization_id": 3, "purpose": "修路",
        }
        result = score_fund_data(fund)
        assert result["score"] == 100
        assert result["level"] == "excellent"
        assert result["missing_fields"] == []

    def test_score_incomplete_fund(self):
        """缺失字段的经费数据扣分（第 27 行）."""
        from app.services.data_quality_scorer import score_fund_data

        result = score_fund_data({"name": "只有名字"})
        assert result["score"] < 100
        assert "amount" in result["missing_fields"]


class TestGenerateQualityReportEmpty:
    def test_empty_results_report(self):
        """空评分列表返回零值报告（第 87 行）."""
        from app.services.data_quality_scorer import generate_quality_report

        report = generate_quality_report([], "经费")
        assert report == {
            "entity_type": "经费",
            "total": 0,
            "average_score": 0,
            "distribution": {},
        }
