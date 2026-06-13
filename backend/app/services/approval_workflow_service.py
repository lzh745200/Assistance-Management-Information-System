"""
审批工作流服务

完整的审批引擎实现，替代之前的空壳桩代码。
使用 ApprovalWorkflow/ApprovalNode/ApprovalTask/ApprovalRecord 数据模型。

Requirements: 3.1, 3.2, 3.4 - Multi-level approval workflow
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.approval import (
    ApprovalAction,
    ApprovalNode,
    ApprovalRecord,
    ApprovalStatus,
    ApprovalTask,
    ApprovalWorkflow,
)

logger = logging.getLogger(__name__)


class ApprovalWorkflowService:
    """审批工作流服务 —— 管理审批流程、任务、记录的完整生命周期"""

    def __init__(self, db: Session):
        self.db = db

    # ══════════════════════════════════════════════════════════════
    #  Workflow CRUD
    # ══════════════════════════════════════════════════════════════

    def create_workflow(
        self,
        name: str,
        entity_type: str,
        nodes: List[Dict],
        description: str = "",
        created_by: Optional[int] = None,
    ) -> ApprovalWorkflow:
        """创建审批流程

        Args:
            name: 流程名称
            entity_type: 实体类型
            nodes: [{"name": "", "approver_type": "user|role", "approver_id": 1, "timeout_hours": 24}, ...]
            description: 流程描述
            created_by: 创建人ID

        Raises:
            ValueError: 节点超过5级
        """
        if len(nodes) > 5:
            raise ValueError("最多支持5级审批")
        if len(nodes) == 0:
            raise ValueError("至少需要1个审批节点")

        workflow = ApprovalWorkflow(
            name=name,
            entity_type=entity_type,
            description=description,
            created_by=created_by,
            is_active=True,
        )
        self.db.add(workflow)
        self.db.flush()

        for i, node_data in enumerate(nodes, 1):
            node = ApprovalNode(
                workflow_id=workflow.id,
                level=i,
                name=node_data.get("name", f"第{i}级审批"),
                approver_type=node_data.get("approver_type", "user"),
                approver_id=node_data.get("approver_id"),
                timeout_hours=node_data.get("timeout_hours", 24),
            )
            self.db.add(node)

        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_workflow(self, workflow_id: int) -> Optional[ApprovalWorkflow]:
        """获取审批流程"""
        return (
            self.db.query(ApprovalWorkflow)
            .options(joinedload(ApprovalWorkflow.nodes))
            .filter(ApprovalWorkflow.id == workflow_id)
            .first()
        )

    def list_workflows(
        self,
        entity_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ApprovalWorkflow]:
        """列出审批流程"""
        query = self.db.query(ApprovalWorkflow).options(joinedload(ApprovalWorkflow.nodes))
        if entity_type:
            query = query.filter(ApprovalWorkflow.entity_type == entity_type)
        if is_active is not None:
            query = query.filter(ApprovalWorkflow.is_active == is_active)
        return query.order_by(ApprovalWorkflow.id.desc()).offset(skip).limit(limit).all()

    def update_workflow(
        self,
        workflow_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[ApprovalWorkflow]:
        """更新审批流程（原子操作，所有变更在同一事务中提交）"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if is_active is not None:
            workflow.is_active = is_active
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def delete_workflow(self, workflow_id: int) -> bool:
        """删除审批流程（级联删除节点）"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        self.db.delete(workflow)
        self.db.commit()
        return True

    def ensure_default_workflow(self, entity_type: str, user_id: Optional[int] = None) -> ApprovalWorkflow:
        """确保默认审批流程存在（单机版自动创建单节点流程）"""
        existing = (
            self.db.query(ApprovalWorkflow)
            .filter(ApprovalWorkflow.entity_type == entity_type, ApprovalWorkflow.is_active.is_(True))
            .first()
        )
        if existing:
            return existing

        return self.create_workflow(
            name=f"{entity_type}默认审批流程",
            entity_type=entity_type,
            nodes=[{"name": "直接审批", "approver_type": "user", "approver_id": user_id, "timeout_hours": 48}],
            description="系统自动创建的默认审批流程",
            created_by=user_id,
        )

    # ══════════════════════════════════════════════════════════════
    #  Task Operations
    # ══════════════════════════════════════════════════════════════

    def submit_approval(
        self,
        entity_type: str,
        entity_id: int,
        submitter_id: int,
        change_data: Optional[Dict] = None,
        original_data: Optional[Dict] = None,
        title: str = "",
    ) -> Optional[ApprovalTask]:
        """提交审批申请

        自动匹配实体类型的活跃工作流，创建审批任务。
        若无匹配工作流，返回None。
        """
        workflow = (
            self.db.query(ApprovalWorkflow)
            .options(joinedload(ApprovalWorkflow.nodes))
            .filter(
                ApprovalWorkflow.entity_type == entity_type,
                ApprovalWorkflow.is_active.is_(True),
            )
            .first()
        )

        if not workflow or not workflow.nodes:
            return None

        first_node = workflow.nodes[0]
        task = ApprovalTask(
            workflow_id=workflow.id,
            entity_type=entity_type,
            entity_id=entity_id,
            submitter_id=submitter_id,
            current_level=1,
            current_approver_id=first_node.approver_id,
            status=ApprovalStatus.PENDING.value,
            change_data=change_data,
            original_data=original_data,
            title=title,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # ── 审批消息推送 ──
        try:
            from app.models.message import Message
            msg = Message(
                user_id=task.current_approver_id,
                title=f"新的审批任务: {title or entity_type}",
                content=f"您有一个待审批的{entity_type}申请需要处理（任务ID: {task.id}）",
                message_type="approval",
                is_read=False,
            )
            self.db.add(msg)
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.warning("审批消息推送失败（非致命）", exc_info=True)

        return task

    def get_task(self, task_id: int) -> Optional[ApprovalTask]:
        """获取审批任务"""
        return (
            self.db.query(ApprovalTask)
            .options(joinedload(ApprovalTask.records), joinedload(ApprovalTask.workflow))
            .filter(ApprovalTask.id == task_id)
            .first()
        )

    def get_pending_tasks(self, approver_id: int, skip: int = 0, limit: int = 100) -> List[ApprovalTask]:
        """获取待审批任务列表"""
        return (
            self.db.query(ApprovalTask)
            .options(joinedload(ApprovalTask.workflow))
            .filter(
                ApprovalTask.current_approver_id == approver_id,
                ApprovalTask.status == ApprovalStatus.PENDING.value,
            )
            .order_by(desc(ApprovalTask.priority), desc(ApprovalTask.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_tasks_with_count(
        self,
        entity_type: Optional[str] = None,
        status: Optional[str] = None,
        submitter_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """获取任务列表及总数"""
        query = self.db.query(ApprovalTask).options(
            joinedload(ApprovalTask.workflow), joinedload(ApprovalTask.records)
        )
        if entity_type:
            query = query.filter(ApprovalTask.entity_type == entity_type)
        if status:
            query = query.filter(ApprovalTask.status == status)
        if submitter_id:
            query = query.filter(ApprovalTask.submitter_id == submitter_id)

        total = query.count()
        items = query.order_by(desc(ApprovalTask.created_at)).offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def approve_task(
        self,
        task_id: int,
        approver_id: int,
        opinion: str = "",
        standalone: bool = False,
    ) -> Optional[ApprovalTask]:
        """审批通过当前级别

        standalone=True: 单机模式，跳过审批人验证

        当前级别通过后：
        - 若还有下一级 → 推进到下一级
        - 若已是最后一级 → 标记为APPROVED
        """
        task = self.get_task(task_id)
        if not task or task.status != ApprovalStatus.PENDING.value:
            return None

        if not standalone and task.current_approver_id != approver_id:
            return None

        # 创建审批记录
        record = ApprovalRecord(
            task_id=task.id,
            level=task.current_level,
            approver_id=approver_id,
            action=ApprovalAction.APPROVE.value,
            opinion=opinion,
        )
        self.db.add(record)

        # 检查是否有下一级
        workflow_nodes = sorted(task.workflow.nodes, key=lambda n: n.level)
        next_level = task.current_level + 1

        if next_level <= len(workflow_nodes):
            next_node = workflow_nodes[next_level - 1]
            task.current_level = next_level
            task.current_approver_id = next_node.approver_id
        else:
            # 所有级别通过
            task.status = ApprovalStatus.APPROVED.value
            task.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(task)
        return task

    def reject_task(
        self,
        task_id: int,
        approver_id: int,
        opinion: str = "",
        standalone: bool = False,
    ) -> Optional[ApprovalTask]:
        """拒绝审批"""
        task = self.get_task(task_id)
        if not task or task.status != ApprovalStatus.PENDING.value:
            return None

        if not standalone and task.current_approver_id != approver_id:
            return None

        record = ApprovalRecord(
            task_id=task.id,
            level=task.current_level,
            approver_id=approver_id,
            action=ApprovalAction.REJECT.value,
            opinion=opinion,
        )
        self.db.add(record)

        task.status = ApprovalStatus.REJECTED.value
        task.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(task)
        return task

    def withdraw_task(self, task_id: int, submitter_id: int) -> Optional[ApprovalTask]:
        """撤回审批申请（仅提交人可操作）"""
        task = self.get_task(task_id)
        if not task or task.status != ApprovalStatus.PENDING.value:
            return None
        if task.submitter_id != submitter_id:
            return None

        task.status = ApprovalStatus.WITHDRAWN.value
        task.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task

    def resubmit_approval(
        self,
        task_id: int,
        submitter_id: int,
        change_data: Optional[Dict] = None,
    ) -> Optional[ApprovalTask]:
        """重新提交被拒绝的审批"""
        task = self.get_task(task_id)
        if not task:
            return None
        if task.status not in (ApprovalStatus.REJECTED.value, ApprovalStatus.WITHDRAWN.value):
            return None
        if task.submitter_id != submitter_id:
            return None

        task.status = ApprovalStatus.PENDING.value
        task.current_level = 1
        task.completed_at = None
        if change_data is not None:
            task.change_data = change_data

        # 重置到第一级审批人
        workflow_nodes = sorted(task.workflow.nodes, key=lambda n: n.level)
        if workflow_nodes:
            task.current_approver_id = workflow_nodes[0].approver_id

        self.db.commit()
        self.db.refresh(task)
        return task

    def submit_and_auto_approve(
        self,
        entity_type: str,
        entity_id: int,
        submitter_id: int,
        change_data: Optional[Dict] = None,
        original_data: Optional[Dict] = None,
    ) -> Optional[ApprovalTask]:
        """提交并自动通过所有级别（单机版快捷操作）

        如果entity_type没有活跃工作流，自动创建默认单节点工作流。
        """
        task = self.submit_approval(
            entity_type=entity_type,
            entity_id=entity_id,
            submitter_id=submitter_id,
            change_data=change_data,
            original_data=original_data,
        )
        if not task:
            # 自动创建默认工作流并重试
            self.ensure_default_workflow(entity_type, user_id=submitter_id)
            task = self.submit_approval(
                entity_type=entity_type,
                entity_id=entity_id,
                submitter_id=submitter_id,
                change_data=change_data,
                original_data=original_data,
            )
        if not task:
            return None

        workflow_nodes = sorted(task.workflow.nodes, key=lambda n: n.level)
        for _node in workflow_nodes:
            task = self.approve_task(
                task_id=task.id,
                approver_id=submitter_id,
                opinion="系统自动审批（单机模式）",
                standalone=True,
            )
            if task is None or task.status == ApprovalStatus.REJECTED.value:
                break

        return task

    def transfer_task(
        self,
        task_id: int,
        approver_id: int,
        transfer_to_id: int,
        reason: str = "",
    ) -> Optional[ApprovalTask]:
        """转交审批任务给其他审批人"""
        task = self.get_task(task_id)
        if not task or task.status != ApprovalStatus.PENDING.value:
            return None
        if task.current_approver_id != approver_id:
            return None

        record = ApprovalRecord(
            task_id=task.id,
            level=task.current_level,
            approver_id=approver_id,
            action=ApprovalAction.TRANSFER.value,
            opinion=f"转交给用户{transfer_to_id}",
            transfer_to_id=transfer_to_id,
            transfer_reason=reason,
        )
        self.db.add(record)

        task.current_approver_id = transfer_to_id
        self.db.commit()
        self.db.refresh(task)
        return task

    def batch_approve(
        self,
        task_ids: List[int],
        approver_id: int,
        opinion: str = "批量同意",
    ) -> Dict[str, Any]:
        """批量审批"""
        success = []
        failed = []
        for tid in task_ids:
            try:
                result = self.approve_task(tid, approver_id, opinion, standalone=True)
                if result:
                    success.append(tid)
                else:
                    failed.append({"id": tid, "reason": "任务状态不允许审批"})
            except Exception as e:
                logger.warning(f"批量审批失败 task_id={tid}: {e}")
                failed.append({"id": tid, "reason": str(e)})
        return {"success": success, "failed": failed}

    def auto_approve_all_pending(self, approver_id: int) -> Dict[str, int]:
        """自动通过所有待审批任务（单机版操作）"""
        pending = (
            self.db.query(ApprovalTask)
            .filter(ApprovalTask.status == ApprovalStatus.PENDING.value)
            .all()
        )
        approved = 0
        for task in pending:
            result = self.approve_task(task.id, approver_id, "自动批量审批", standalone=True)
            if result and result.status == ApprovalStatus.APPROVED.value:
                approved += 1
        return {"total_pending": len(pending), "approved": approved}

    # ══════════════════════════════════════════════════════════════
    #  History & Diff
    # ══════════════════════════════════════════════════════════════

    def get_approval_history(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        submitter_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ApprovalRecord]:
        """获取审批历史记录（过滤在DB层执行，保证分页正确）"""
        query = self.db.query(ApprovalRecord).options(
            joinedload(ApprovalRecord.task), joinedload(ApprovalRecord.approver)
        )
        # JOIN ApprovalTask for entity/submitter/status filtering
        need_join = bool(entity_type and entity_id is not None) or submitter_id or status
        if need_join:
            query = query.join(ApprovalTask)
        if entity_type and entity_id is not None:
            query = query.filter(
                ApprovalTask.entity_type == entity_type,
                ApprovalTask.entity_id == entity_id,
            )
        if submitter_id:
            query = query.filter(ApprovalTask.submitter_id == submitter_id)
        if status:
            query = query.filter(ApprovalTask.status == status)
        return query.order_by(desc(ApprovalRecord.created_at)).offset(skip).limit(limit).all()

    def get_task_diff(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务的变更对比"""
        task = self.get_task(task_id)
        if not task:
            return None
        return {
            "changed": task.change_data or {},
            "original": task.original_data or {},
            "task_id": task.id,
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
        }
