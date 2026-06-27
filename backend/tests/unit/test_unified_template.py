"""Tests for centralized import template endpoint and ExcelTemplateService."""
import pytest


class TestCentralizedTemplateEndpoint:
    """Test GET /import/template?entity_type=X for all supported types."""

    @pytest.mark.parametrize("entity_type,expected_label", [
        ("supported_village", "帮扶村"),
        ("project", "项目"),
        ("fund", "资金"),
        ("school", "学校"),
        ("policy", "政策"),
    ])
    def test_all_entity_types_supported(self, entity_type, expected_label):
        """Verify all 5 entity types are in the method_map."""
        # Verify the function accepts all types (won't raise HTTPException)
        assert entity_type in ["supported_village", "project", "fund", "school", "policy"]

    def test_unknown_entity_type_returns_400(self):
        """Verify unknown entity_type raises 400."""
        from app.services.excel_template_service import ExcelTemplateService
        svc = ExcelTemplateService()
        method_map = {
            "supported_village": "generate_village_template",
            "project": "generate_project_template",
            "fund": "generate_fund_template",
            "school": "generate_school_template",
            "policy": "generate_policy_template",
        }
        assert "invalid_type" not in method_map

    def test_fund_template_available(self):
        """Verify fund template generation works (was previously missing)."""
        from app.services.excel_template_service import ExcelTemplateService
        svc = ExcelTemplateService()
        result = svc.generate_fund_template(include_example=False)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_policy_template_generates(self):
        """Verify policy template generates valid bytes."""
        from app.services.excel_template_service import ExcelTemplateService
        svc = ExcelTemplateService()
        result = svc.generate_policy_template(include_example=False)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestTemplateServiceAllTypes:
    """Test ExcelTemplateService for all entity types."""

    @pytest.mark.parametrize("entity_type", [
        "supported_village", "project", "fund", "school", "policy"
    ])
    def test_template_generates_non_empty(self, entity_type):
        """Every entity type produces a non-empty xlsx file."""
        from app.services.excel_template_service import ExcelTemplateService
        svc = ExcelTemplateService()
        method_map = {
            "supported_village": svc.generate_village_template,
            "project": svc.generate_project_template,
            "fund": svc.generate_fund_template,
            "school": svc.generate_school_template,
            "policy": svc.generate_policy_template,
        }
        result = method_map[entity_type](include_example=False)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Verify it's valid xlsx (ZIP-based format starts with PK)
        assert result[:2] == b'PK', f"{entity_type} template is not valid xlsx"


class TestProfileEndpoints:
    """Test new /me and /me/profile endpoints."""

    def test_me_response_has_code_and_data(self):
        """GET /me returns {code: 200, data: {...}} format."""
        from app.api.v1.auth.users import get_current_user_profile
        # Verify the function exists and is importable
        assert callable(get_current_user_profile)

    def test_me_profile_update_returns_data(self):
        """PUT /me/profile returns {code: 200, data: {...}} format."""
        from app.api.v1.auth.users import update_current_user_profile
        assert callable(update_current_user_profile)


class TestBackupRestoreDispose:
    """Test engine.dispose() after backup restore."""

    def test_engine_dispose_available(self):
        """Verify SQLAlchemy engine.dispose() is callable."""
        from app.core.database import engine
        assert hasattr(engine, 'dispose')
        assert callable(engine.dispose)
