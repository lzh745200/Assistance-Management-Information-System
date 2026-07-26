"""b3 攻坚：覆盖 app.models.data_package 的 is_importable / is_editable 属性"""
from app.models.data_package import DataPackage, PackageStatus


class TestDataPackageProperties:
    def test_repr(self):
        pkg = DataPackage(id=1, package_code="PK001", status=PackageStatus.draft)
        assert "PK001" in repr(pkg)

    def test_is_importable_true(self):
        pkg = DataPackage(status=PackageStatus.validated)
        assert pkg.is_importable is True

    def test_is_importable_false(self):
        pkg = DataPackage(status=PackageStatus.draft)
        assert pkg.is_importable is False

    def test_is_editable_draft(self):
        assert DataPackage(status=PackageStatus.draft).is_editable is True

    def test_is_editable_pending(self):
        assert DataPackage(status=PackageStatus.pending).is_editable is True

    def test_is_editable_false(self):
        assert DataPackage(status=PackageStatus.validated).is_editable is False
