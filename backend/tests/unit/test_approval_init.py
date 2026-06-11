"""Tests for app/services/approval/__init__.py — 100% coverage."""


class TestApprovalInit:
    """Verify the re-export in approval/__init__.py works."""

    def test_approval_workflow_service_imported(self):
        from app.services.approval import ApprovalWorkflowService
        assert ApprovalWorkflowService is not None
        assert callable(ApprovalWorkflowService)

    def test_module_has_service(self):
        import app.services.approval as mod
        assert hasattr(mod, "ApprovalWorkflowService")
