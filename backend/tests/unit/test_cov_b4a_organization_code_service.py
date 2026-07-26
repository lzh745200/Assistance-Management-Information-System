"""覆盖率攻坚: app/services/organization_code_service.py 缺口行 33-34（编码碰撞重试循环）."""
from unittest.mock import MagicMock, patch


class TestGenerateCodeCollision:
    def test_collision_triggers_retry_loop(self):
        """生成的编码已存在时进入 while 重试体（第 33-34 行），追加随机数字后退出."""
        from app.services.organization_code_service import OrganizationCodeService

        svc = OrganizationCodeService()
        svc.register_code("ABCDEF12", {"org": "已存在"})

        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "abcdef1234567890"  # [:8].upper() == "ABCDEF12"

        with patch("hashlib.sha256", return_value=mock_hash):
            code = svc.generate_code("某组织")

        assert code.startswith("ABCDEF12")
        assert len(code) == 9  # 追加了一位随机数字
