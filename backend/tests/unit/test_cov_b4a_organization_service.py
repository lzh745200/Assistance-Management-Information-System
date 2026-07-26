"""覆盖率攻坚: app/services/organization_service.py 缺口行 289（get_ancestors 路径与 ID 不匹配）."""
from types import SimpleNamespace
from unittest.mock import MagicMock


def _make_service(org):
    from app.services.organization_service import OrganizationService

    svc = OrganizationService(db=MagicMock())
    svc.get_organization = lambda org_id: org
    return svc


class TestGetAncestorsPathMismatch:
    def test_path_tail_not_matching_org_id_returns_empty(self):
        """path 末段不等于 org_id 时返回空列表（第 289 行）."""
        org = SimpleNamespace(id=5, path="/1/2/")
        svc = _make_service(org)
        assert svc.get_ancestors(5) == []

    def test_empty_path_returns_empty(self):
        """path 为空串解析不出 ID 时同样返回空列表（第 289 行）."""
        org = SimpleNamespace(id=7, path="")
        svc = _make_service(org)
        assert svc.get_ancestors(7) == []
