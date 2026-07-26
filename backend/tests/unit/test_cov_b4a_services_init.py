"""覆盖率攻坚: app/services/__init__.py 缺口行 37-38（encryption_service 导入失败回退）."""
import importlib
import sys
from unittest.mock import patch

import app.services


class TestEncryptionServiceImportFallback:
    def test_import_error_sets_encryption_service_none(self):
        """encryption_service 不可导入时 EncryptionService 置为 None（第 37-38 行）."""
        try:
            with patch.dict(sys.modules, {"app.services.encryption_service": None}):
                importlib.reload(app.services)
                assert app.services.EncryptionService is None
        finally:
            # 无论断言成败都恢复正常导入状态
            importlib.reload(app.services)

        assert app.services.EncryptionService is not None
