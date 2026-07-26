"""覆盖率攻坚: app/services/project/__init__.py 缺口行 17-19（包初始化导入与 __all__）."""
import importlib


class TestProjectPackageInit:
    def test_package_imports_effectiveness_service(self):
        """导入 app.services.project 执行包初始化（第 17-19 行）."""
        import app.services.project as project_pkg

        importlib.reload(project_pkg)

        assert project_pkg.EffectivenessService is not None
        assert "EffectivenessService" in project_pkg.__all__
