"""TDD: FTS5 全文搜索 + 关键词高亮."""


class TestPolicyFTSService:
    def test_search_returns_results(self, real_db_session):
        from app.services.policy_fts_service import search_policies_fts, ensure_fts_table
        from app.models.policy import Policy
        p1 = Policy(title="军人抚恤优待条例", content="关于军人抚恤优待的详细规定",
                     summary="抚恤优待", keywords="军人,抚恤", category="政策法规", level="国家级")
        p2 = Policy(title="乡村振兴实施意见", content="全面推进乡村振兴战略的实施意见",
                     summary="乡村振兴", keywords="乡村,振兴", category="政策法规", level="省级")
        real_db_session.add_all([p1, p2])
        real_db_session.commit()
        ensure_fts_table(real_db_session)
        results = search_policies_fts(real_db_session, "抚恤")
        assert len(results) >= 1

    def test_no_results_for_nonexistent_term(self, real_db_session):
        from app.services.policy_fts_service import search_policies_fts
        results = search_policies_fts(real_db_session, "不存在的关键词xyz123")
        assert len(results) == 0

    def test_fts_table_creatable(self, real_db_session):
        from app.services.policy_fts_service import ensure_fts_table
        ensure_fts_table(real_db_session)
        from sqlalchemy import text
        result = real_db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'")
        ).fetchall()
        assert len(result) >= 1


class TestKeywordHighlight:
    def test_highlight_single_match(self):
        from app.services.policy_fts_service import highlight_keywords
        result = highlight_keywords("这是军人抚恤优待条例", "抚恤")
        assert "<mark>" in result

    def test_highlight_multiple_matches(self):
        from app.services.policy_fts_service import highlight_keywords
        result = highlight_keywords("乡村振兴 乡村发展 乡村建设", "乡村")
        assert result.count("<mark>") == 3

    def test_highlight_no_match(self):
        from app.services.policy_fts_service import highlight_keywords
        result = highlight_keywords("普通文本", "不存在的词")
        assert result == "普通文本"
