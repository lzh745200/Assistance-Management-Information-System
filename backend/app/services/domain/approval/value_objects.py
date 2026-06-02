"""
Approval domain value objects
"""


class ApprovalStatus:
    """Approval status value object"""

    VALID_STATUSES = ["draft", "pending", "submitted", "in_review", "approved", "rejected", "returned", "cancelled"]

    def __init__(self, status: str = "draft"):
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        self.status = status

    def can_transition_to(self, new_status: str) -> bool:
        """Check if status can transition to new status"""
        valid_transitions = {
            "draft": ["submitted", "pending", "cancelled"],
            "submitted": ["in_review", "returned", "cancelled"],
            "pending": ["approved", "rejected", "returned"],
            "in_review": ["approved", "rejected", "returned"],
            "returned": ["submitted", "cancelled"],
            "approved": [],
            "rejected": [],
            "cancelled": [],
        }
        return new_status in valid_transitions.get(self.status, [])

    def __repr__(self) -> str:
        return f"ApprovalStatus({self.status})"
