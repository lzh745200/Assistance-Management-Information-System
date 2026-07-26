"""b3 攻坚：覆盖 app.schemas.common 的 PaginationParams.skip / limit 属性"""
from app.schemas.common import PaginationParams


class TestPaginationParams:
    def test_skip_first_page(self):
        assert PaginationParams(page=1, page_size=10).skip == 0

    def test_skip_later_page(self):
        assert PaginationParams(page=3, page_size=15).skip == 30

    def test_limit(self):
        assert PaginationParams(page=2, page_size=25).limit == 25
