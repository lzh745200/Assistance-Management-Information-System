"""Model column tests."""
import pytest

class TestUserColumns:
    def test_has_username(self):
        from app.models.user import User; assert hasattr(User, 'username')
    def test_has_email(self):
        from app.models.user import User; assert hasattr(User, 'email')
    def test_has_password(self):
        from app.models.user import User; assert hasattr(User, 'hashed_password')

class TestVillageColumns:
    def test_has_name(self):
        from app.models.supported_village import SupportedVillage; assert hasattr(SupportedVillage, 'village_name')
    def test_has_department(self):
        from app.models.supported_village import SupportedVillage; assert hasattr(SupportedVillage, 'department')

class TestProjectColumns:
    def test_has_name(self):
        from app.models.project import Project; assert hasattr(Project, 'name')

class TestFundColumns:
    def test_has_amount(self):
        from app.models.fund import Fund; assert hasattr(Fund, 'amount')
    def test_has_name(self):
        from app.models.fund import Fund; assert hasattr(Fund, 'name')

class TestSchoolColumns:
    def test_has_name(self):
        from app.models.school import School; assert hasattr(School, 'name')

class TestPolicyColumns:
    def test_has_title(self):
        from app.models.policy import Policy; assert hasattr(Policy, 'title')

class TestOrgColumns:
    def test_has_name(self):
        from app.models.organization import Organization; assert hasattr(Organization, 'name')

class TestAuditColumns:
    def test_has_action(self):
        from app.models.audit import AuditLog; assert hasattr(AuditLog, 'action')

class TestRBACColumns:
    def test_has_name(self):
        from app.models.rbac import RbacRole; assert hasattr(RbacRole, 'name')

class TestApprovalColumns:
    def test_has_name(self):
        from app.models.approval import ApprovalWorkflow; assert hasattr(ApprovalWorkflow, 'name')

class TestFundLifecycleCols:
    def test_phase_has_id(self):
        from app.models.fund_lifecycle import ProjectFundPhase; assert hasattr(ProjectFundPhase, 'id')
    def test_baseline_has_amount(self):
        from app.models.fund_lifecycle import BudgetBaseline; assert hasattr(BudgetBaseline, 'baseline_amount')

class TestMessageCols:
    def test_has_content(self):
        from app.models.message import Message; assert hasattr(Message, 'content')

class TestTodoCols:
    def test_has_title(self):
        from app.models.todo import Todo; assert hasattr(Todo, 'title')

class TestMachineCodeCols:
    def test_has_code(self):
        from app.models.machine_code import MachineCode; assert hasattr(MachineCode, 'machine_code')

class TestVillageCols:
    def test_has_name(self):
        from app.models.village import Village; assert hasattr(Village, 'name')

class TestRBACCols:
    def test_user_role_cols(self):
        from app.models.rbac import UserRole; assert hasattr(UserRole, 'user_id')
    def test_role_perm_cols(self):
        from app.models.rbac import RolePermission; assert hasattr(RolePermission, 'role_id')

class TestFundBudgetCols:
    def test_has_amount(self):
        from app.models.fund_budget import FundBudget; assert hasattr(FundBudget, 'budget_amount')

class TestProjectMilestoneCols:
    def test_has_name(self):
        from app.models.project_milestone import ProjectMilestone; assert hasattr(ProjectMilestone, 'name')
