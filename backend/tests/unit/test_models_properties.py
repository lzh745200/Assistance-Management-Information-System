"""Model property and method tests."""
import pytest

class TestModelProperties:
    def test_user_tablename(self):
        from app.models.user import User; assert User.__tablename__ == 'users'
    def test_supported_village_tablename(self):
        from app.models.supported_village import SupportedVillage; assert SupportedVillage.__tablename__ == 'supported_villages'
    def test_project_tablename(self):
        from app.models.project import Project; assert Project.__tablename__ == 'projects'
    def test_fund_tablename(self):
        from app.models.fund import Fund; assert Fund.__tablename__ == 'funds'
    def test_school_tablename(self):
        from app.models.school import School; assert School.__tablename__ == 'schools'
    def test_policy_tablename(self):
        from app.models.policy import Policy; assert Policy.__tablename__ == 'policies'
    def test_org_tablename(self):
        from app.models.organization import Organization; assert Organization.__tablename__ == 'organizations'
    def test_village_tablename(self):
        from app.models.village import Village; assert Village.__tablename__ == 'villages'
    def test_audit_tablename(self):
        from app.models.audit import AuditLog; assert AuditLog.__tablename__ == 'audit_logs'
    def test_message_tablename(self):
        from app.models.message import Message; assert Message.__tablename__ == 'messages'
    def test_machine_code_tablename(self):
        from app.models.machine_code import MachineCode; assert MachineCode.__tablename__ == 'machine_codes'
    def test_rbac_role_tablename(self):
        from app.models.rbac import RbacRole; assert RbacRole.__tablename__ == 'rbac_roles'
    def test_approval_workflow_tablename(self):
        from app.models.approval import ApprovalWorkflow; assert ApprovalWorkflow.__tablename__ == 'approval_workflows'
    def test_data_sync_log_tablename(self):
        from app.models.data_sync import DataSyncLog; assert DataSyncLog.__tablename__ == 'data_sync_logs'
    def test_system_config_tablename(self):
        from app.models.system_config import SystemConfig; assert SystemConfig.__tablename__ == 'system_configs'
    def test_user_session_tablename(self):
        from app.models.user_session import UserSession; assert UserSession.__tablename__ == 'user_sessions'
    def test_todo_tablename(self):
        from app.models.todo import Todo; assert Todo.__tablename__ == 'todos'
    def test_work_log_tablename(self):
        from app.models.work_log import WorkLog; assert WorkLog.__tablename__ == 'work_logs'

class TestModelBaseClasses:
    def test_base_exists(self):
        from app.models.base import Base, BaseModel, TimestampMixin; assert Base is not None
    def test_base_model_has_to_dict(self):
        from app.models.base import BaseModel; assert hasattr(BaseModel, 'to_dict')
    def test_timestamp_mixin_has_created_at(self):
        from app.models.base import TimestampMixin; assert hasattr(TimestampMixin, 'created_at')

class TestFundLifecycleProps:
    def test_phase_labels_count(self):
        from app.models.fund_lifecycle import PHASE_LABELS; assert len(PHASE_LABELS) == 7
    def test_phase_status_values(self):
        from app.models.fund_lifecycle import PhaseStatus
        assert hasattr(PhaseStatus, 'NOT_STARTED')
        assert hasattr(PhaseStatus, 'IN_PROGRESS')
    def test_contract_status_values(self):
        from app.models.fund_lifecycle import ContractStatus
        assert hasattr(ContractStatus, 'DRAFT')
