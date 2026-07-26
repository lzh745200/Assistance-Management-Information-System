"""b3 攻坚：覆盖 app.schemas.__init__ 的 _register_schema 中模块带 __all__ 的分支"""
import sys
import types

import app.schemas as schemas_pkg
from app.schemas import _register_schema


class TestRegisterSchemaWithAll:
    def test_register_module_with___all__(self, monkeypatch):
        fake = types.ModuleType("app.schemas.b3_fake_mod")

        class _B3FakeSchema:
            pass

        fake.__all__ = ["_B3FakeSchema"]
        fake._B3FakeSchema = _B3FakeSchema
        monkeypatch.setitem(sys.modules, "app.schemas.b3_fake_mod", fake)
        try:
            _register_schema("b3_fake_mod")
            assert schemas_pkg._B3FakeSchema is _B3FakeSchema
            assert "_B3FakeSchema" in schemas_pkg.__all__
        finally:
            # 恢复：清除注册进 app.schemas 的名称，避免污染其他测试
            schemas_pkg.__dict__.pop("_B3FakeSchema", None)
            while "_B3FakeSchema" in schemas_pkg.__all__:
                schemas_pkg.__all__.remove("_B3FakeSchema")
