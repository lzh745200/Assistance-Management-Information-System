"""b3 攻坚：覆盖 app.models.__init__ 懒加载 __getattr__ 的 AttributeError 分支"""
import pytest

import app.models as models_pkg


class TestModelsInitGetattr:
    def test_getattr_lazy_load_success(self):
        from app.models.rbac import RbacRole

        assert models_pkg.__getattr__("RbacRole") is RbacRole

    def test_getattr_unknown_name_raises(self):
        with pytest.raises(AttributeError, match="has no attribute"):
            models_pkg.__getattr__("NoSuchModelB3")
