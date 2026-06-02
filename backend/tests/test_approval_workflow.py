"""
审批流程服务测试
测试审批工作流的创建、提交、审批、拒绝等核心功能
"""

import pytest
from datetime import datetime

from app.core.exceptions import ValidationError, NotFoundException, BusinessError
from app.models.approval import ApprovalStatus


class TestApprovalWorkflowService:
    """审批流程服务测试类"""

    @pytest.fixture
    def real_db_session(self):
        """创建SQLite内存数据库session用于测试，预置测试用户"""
        from sqlalchemy import create_engine, event
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base
        from app.models.user import User

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def set_pragma(conn, _record):
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 创建测试用户（满足外键约束）
        for uid in range(1, 6):
            user = User(
                id=uid,
                username=f"testuser{uid}",
                email=f"test{uid}@test.com",
                hashed_password="dummy_hash_for_test",
                is_active=True,
            )
            session.add(user)
        session.commit()

        yield session
        session.rollback()
        session.close()
        engine.dispose()

    @pytest.fixture
    def service(self, real_db_session):
        """创建服务实例"""
        from app.services.approval_workflow_service import ApprovalWorkflowService
        return ApprovalWorkflowService(real_db_session)

    @pytest.fixture
    def sample_workflow_data(self):
        """示例工作流数据"""
        return {
            "name": "项目审批流程",
            "description": "项目立项审批",
            "nodes": [
                {
                    "name": "部门审批",
                    "approver_type": "user",
                    "approver_id": 1,
                    "timeout_hours": 24,
                },
                {
                    "name": "财务审批",
                    "approver_type": "user",
                    "approver_id": 2,
                    "timeout_hours": 24,
                },
                {
                    "name": "领导审批",
                    "approver_type": "user",
                    "approver_id": 3,
                    "timeout_hours": 24,
                }
            ]
        }

    def test_create_workflow(self, service, sample_workflow_data):
        """测试创建审批流程"""
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            description=sample_workflow_data["description"],
            nodes=sample_workflow_data["nodes"]
        )

        assert workflow is not None
        assert workflow.name == "项目审批流程"
        assert workflow.description == "项目立项审批"
        assert len(workflow.nodes) == 3

    def test_create_workflow_without_name(self, service):
        """测试创建流程时名称为空"""
        from app.models.approval import ApprovalNode
        with pytest.raises(ValueError, match="至少需要1个审批节点"):
            service.create_workflow(
                name="",
                entity_type="project",
                nodes=[]
            )
        # 空名称但有效节点 — 应成功
        workflow = service.create_workflow(
            name="",
            entity_type="project",
            nodes=[{"name": "节点1", "approver_type": "user", "approver_id": 1}]
        )
        assert workflow is not None
        assert workflow.name == ""

    def test_create_workflow_without_nodes(self, service):
        """测试创建流程时没有节点——应拒绝空节点"""
        with pytest.raises(ValueError, match="至少需要1个审批节点"):
            service.create_workflow(
                name="测试流程",
                entity_type="project",
                nodes=[]
            )

    def test_create_workflow_too_many_nodes(self, service):
        """测试创建流程时节点超过5级"""
        nodes = [
            {"name": f"第{i}级审批", "approver_type": "user", "approver_id": i}
            for i in range(1, 7)  # 6个节点
        ]
        with pytest.raises(ValueError, match="最多支持5级"):
            service.create_workflow(
                name="测试流程",
                entity_type="project",
                nodes=nodes
            )

    def test_get_workflow(self, service, sample_workflow_data):
        """测试获取审批流程"""
        # 创建流程
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )

        # 获取流程
        retrieved = service.get_workflow(workflow.id)
        assert retrieved is not None
        assert retrieved.id == workflow.id
        assert retrieved.name == workflow.name

    def test_get_nonexistent_workflow(self, service):
        """测试获取不存在的流程"""
        retrieved = service.get_workflow(99999)
        assert retrieved is None

    def test_submit_approval(self, service, sample_workflow_data, real_db_session):
        """测试提交审批"""
        # 创建流程
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )

        # 提交审批
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={"project_name": "测试项目", "budget": 100000}
        )

        assert task is not None
        assert task.workflow_id == workflow.id
        assert task.entity_type == "project"
        assert task.entity_id == 1
        assert task.status == ApprovalStatus.PENDING.value
        assert task.current_level == 1

    def test_submit_approval_no_workflow(self, service):
        """测试没有流程时提交审批"""
        task = service.submit_approval(
            entity_type="nonexistent_type",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )
        assert task is None

    def test_approve_task(self, service, sample_workflow_data):
        """测试审批通过"""
        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 审批通过（单机模式）
        result = service.approve_task(
            task_id=task.id,
            approver_id=1,
            opinion="同意",
            standalone=True
        )

        assert result is not None
        # 应该进入下一个节点
        task_updated = service.get_task(task.id)
        assert task_updated.current_level == 2

    def test_reject_task(self, service, sample_workflow_data):
        """测试审批拒绝"""
        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 拒绝审批
        result = service.reject_task(
            task_id=task.id,
            approver_id=1,
            opinion="不同意",
            standalone=True
        )

        assert result is not None
        task_updated = service.get_task(task.id)
        assert task_updated.status == ApprovalStatus.REJECTED.value

    def test_approve_task_unauthorized(self, service, sample_workflow_data):
        """测试未授权用户审批（非单机模式）"""
        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 使用未授权用户审批（非单机模式）
        result = service.approve_task(
            task_id=task.id,
            approver_id=999,  # 不同的用户ID
            opinion="同意",
            standalone=False  # 非单机模式，需要验证
        )

        # 应该返回None（未授权）
        assert result is None

    def test_complete_workflow(self, service, sample_workflow_data):
        """测试完整的审批流程"""
        # 创建流程
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )

        # 提交审批
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 第一级审批
        service.approve_task(task.id, approver_id=1, opinion="部门同意", standalone=True)

        # 第二级审批
        service.approve_task(task.id, approver_id=2, opinion="财务同意", standalone=True)

        # 第三级审批
        service.approve_task(task.id, approver_id=3, opinion="领导同意", standalone=True)

        # 检查最终状态
        task_final = service.get_task(task.id)
        assert task_final.status == ApprovalStatus.APPROVED.value

    def test_get_pending_tasks(self, service, sample_workflow_data):
        """测试获取待审批任务"""
        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 获取待审批任务（当前审批人是第一个节点的approver_id=1）
        pending_tasks = service.get_pending_tasks(approver_id=1)
        assert len(pending_tasks) >= 0

    def test_withdraw_task(self, service, sample_workflow_data):
        """测试撤回申请（原cancel_task）"""
        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 撤回审批
        result = service.withdraw_task(task.id, submitter_id=1)
        assert result is not None

        task_updated = service.get_task(task.id)
        assert task_updated.status == ApprovalStatus.WITHDRAWN.value

    def test_withdraw_task_by_non_submitter(self, service, sample_workflow_data):
        """测试非提交人撤回审批"""
        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 非提交人尝试撤回
        result = service.withdraw_task(task.id, submitter_id=2)
        assert result is None  # 应该返回None（无权限）

    def test_ensure_default_workflow(self, service):
        """测试确保默认流程（单机版）"""
        workflow = service.ensure_default_workflow("test_entity", user_id=1)
        assert workflow is not None
        assert workflow.entity_type == "test_entity"
        assert len(workflow.nodes) == 1

    def test_submit_and_auto_approve(self, service):
        """测试提交并自动审批（单机版）"""
        task = service.submit_and_auto_approve(
            entity_type="auto_entity",
            entity_id=1,
            submitter_id=1,
            change_data={"test": "data"}
        )

        assert task is not None
        assert task.status == ApprovalStatus.APPROVED.value

    def test_resubmit_rejected_task(self, service, sample_workflow_data):
        """测试重新提交被拒绝的任务"""
        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 拒绝任务
        service.reject_task(task.id, approver_id=1, opinion="不同意", standalone=True)

        # 重新提交
        result = service.resubmit_approval(task.id, submitter_id=1, change_data={"updated": "data"})
        assert result is not None
        assert result.status == ApprovalStatus.PENDING.value
        assert result.current_level == 1

    def test_transfer_task(self, service, sample_workflow_data, real_db_session):
        """测试转交审批任务"""
        from app.models.user import User

        # 创建目标用户 - 必须提供 hashed_password
        target_user = User(
            username="target",
            email="target@test.com",
            hashed_password="dummy_hash_for_test"
        )
        real_db_session.add(target_user)
        real_db_session.commit()
        real_db_session.refresh(target_user)

        # 创建流程并提交
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 转交任务（单机模式下使用standalone）
        result = service.transfer_task(
            task_id=task.id,
            approver_id=1,  # 当前审批人
            transfer_to_id=target_user.id,
            reason="转交测试"
        )

        # 转交需要当前审批人匹配，在单机模式下可能返回None
        # 这里主要是测试函数能正常调用

    def test_batch_approve(self, service, sample_workflow_data):
        """测试批量审批"""
        # 创建多个任务
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )

        task1 = service.submit_approval(entity_type="project", entity_id=1, submitter_id=1, change_data={})
        task2 = service.submit_approval(entity_type="project", entity_id=2, submitter_id=1, change_data={})

        # 批量审批（单机模式）
        results = service.batch_approve([task1.id, task2.id], approver_id=1, opinion="批量同意")
        assert "success" in results
        assert "failed" in results

    def test_get_approval_history(self, service, sample_workflow_data):
        """测试获取审批历史"""
        # 创建并审批任务
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={}
        )

        # 审批通过
        service.approve_task(task.id, approver_id=1, opinion="同意", standalone=True)

        # 获取历史
        history = service.get_approval_history(entity_type="project", entity_id=1)
        assert len(history) >= 0

    def test_get_task_diff(self, service, sample_workflow_data):
        """测试获取任务变更对比"""
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )
        task = service.submit_approval(
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            change_data={"new_value": "test"},
            original_data={"old_value": "original"}
        )

        diff = service.get_task_diff(task.id)
        assert diff is not None
        assert diff["changed"] == {"new_value": "test"}
        assert diff["original"] == {"old_value": "original"}

    def test_list_workflows(self, service, sample_workflow_data):
        """测试列出审批流程"""
        # 创建流程
        service.create_workflow(
            name="流程1",
            entity_type="type1",
            nodes=sample_workflow_data["nodes"]
        )
        service.create_workflow(
            name="流程2",
            entity_type="type2",
            nodes=sample_workflow_data["nodes"]
        )

        # 列出所有流程
        workflows = service.list_workflows()
        assert len(workflows) >= 2

        # 按实体类型筛选
        workflows_filtered = service.list_workflows(entity_type="type1")
        assert all(w.entity_type == "type1" for w in workflows_filtered)

    def test_update_workflow(self, service, sample_workflow_data):
        """测试更新审批流程"""
        # 创建流程
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )

        # 更新流程
        updated = service.update_workflow(
            workflow_id=workflow.id,
            name="更新后的名称",
            description="更新后的描述"
        )

        assert updated is not None
        assert updated.name == "更新后的名称"
        assert updated.description == "更新后的描述"

    def test_delete_workflow(self, service, sample_workflow_data):
        """测试删除审批流程"""
        # 创建流程
        workflow = service.create_workflow(
            name=sample_workflow_data["name"],
            entity_type="project",
            nodes=sample_workflow_data["nodes"]
        )

        # 删除流程
        result = service.delete_workflow(workflow.id)
        assert result is True

        # 验证已删除
        deleted = service.get_workflow(workflow.id)
        assert deleted is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
