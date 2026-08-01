"""补齐 app.services.encryption_service 覆盖率缺口。

目标行：219-221 —— 运行时密钥存储不可用 → 抛出 RuntimeError（密钥初始化失败）。
"""

from unittest.mock import patch

import pytest

import app.services.encryption_service as enc_mod


class TestGetCipherRuntimeSecretFailure:
    def test_runtime_secret_failure_raises_runtime_error(self):
        enc_mod._reset_cipher_cache()
        try:
            with patch("app.core.config.settings") as mock_settings, patch(
                "app.utils.runtime_secrets.get_or_create_secret",
                side_effect=OSError("disk full"),
            ):
                mock_settings.ENCRYPTION_KEY = None
                with pytest.raises(RuntimeError, match="加密密钥初始化失败"):
                    enc_mod._get_cipher()
        finally:
            enc_mod._reset_cipher_cache()
