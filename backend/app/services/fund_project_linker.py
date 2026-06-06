"""经费↔项目双向联动."""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.fund import Fund
from app.models.project import Project

logger = logging.getLogger(__name__)


def find_linkable_projects(db: Session, fund_village_id: Optional[int]) -> List[Project]:
    """查找经费可关联的项目（同帮扶村下的项目）."""
    if fund_village_id is None:
        return []
    return (
        db.query(Project)
        .filter(Project.village_id == fund_village_id)
        .all()
    )


def find_linkable_funds(db: Session, project_village_id: Optional[int]) -> List[Fund]:
    """查找项目可关联的经费（同帮扶村下且未关联到其他项目）."""
    if project_village_id is None:
        return []
    return (
        db.query(Fund)
        .filter(
            Fund.village_id == project_village_id,
            (Fund.project_id.is_(None)) | (Fund.project_id == 0),
        )
        .all()
    )


def update_project_budget(
    db: Session,
    project_id: int,
    additional_fund: float,
) -> Optional[Project]:
    """经费审批通过后更新关联项目预算."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    current = getattr(project, "approved_funds", None)
    if current is None:
        current = 0.0
    project.approved_funds = current + additional_fund
    db.commit()
    return project
