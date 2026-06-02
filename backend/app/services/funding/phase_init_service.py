"""Phase 1: 论证立项 — 项目资金阶段初始化。

从 fund_lifecycle.py Phase 1 提取的业务逻辑。
使用 PHASE_LABELS 作为权威的阶段名称来源。
"""
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.fund_lifecycle import (
    PHASE_LABELS,
    PhaseStatus,
    ProjectFundPhase,
)

logger = logging.getLogger(__name__)


class PhaseInitService:
    """项目资金阶段初始化服务。

    从 fund_lifecycle.py 的 _init_phases() 内联函数提取。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_phases(self, project_id: int) -> List[ProjectFundPhase]:
        result = await self.db.execute(
            select(ProjectFundPhase)
            .where(ProjectFundPhase.project_id == project_id)
            .order_by(ProjectFundPhase.phase)
        )
        return list(result.scalars().all())

    async def get_phase(self, phase_id: int) -> Optional[ProjectFundPhase]:
        result = await self.db.execute(
            select(ProjectFundPhase).where(ProjectFundPhase.id == phase_id)
        )
        return result.scalar_one_or_none()

    async def init_phases(self, project_id: int, fund_id: Optional[int] = None) -> List[ProjectFundPhase]:
        """为指定项目初始化全部7个阶段记录。

        Args:
            project_id: 项目ID（必填，对应 ProjectFundPhase.project_id FK）
            fund_id: 经费ID（可选，对应 ProjectFundPhase.fund_id FK）

        Returns:
            创建的7个阶段记录列表
        """
        phases = []
        for i in range(1, 8):
            phase = ProjectFundPhase(
                project_id=project_id,
                fund_id=fund_id,
                phase=i,
                status=PhaseStatus.NOT_STARTED.value if i > 1 else PhaseStatus.IN_PROGRESS.value,
                remarks=PHASE_LABELS.get(i, f"阶段{i}"),
            )
            self.db.add(phase)
            phases.append(phase)
        await self.db.commit()
        logger.info(
            "Initialized 7 phases for project %d (fund=%s)",
            project_id,
            fund_id or "N/A",
        )
        return phases
