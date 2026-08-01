"""补齐 app.utils.database_init 覆盖率缺口。

目标行：_mask_password 的短口令分支（原 init_default_users 内嵌 _mask，已提升为
模块级函数以便直接测试）。
"""

from app.utils.database_init import _mask_password


class TestMaskPassword:
    def test_short_password_fully_masked(self):
        assert _mask_password("abcd") == "****"
        assert _mask_password("ab") == "**"

    def test_long_password_edges_visible(self):
        assert _mask_password("abcdefgh") == "ab****gh"
