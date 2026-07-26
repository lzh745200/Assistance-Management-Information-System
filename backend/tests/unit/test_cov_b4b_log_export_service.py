"""补齐 app.services.log_export_service 覆盖率缺口（26-27 行 mkdir 失败、244-246 行依赖包写入）."""
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

from app.services.log_export_service import LogExportService


class TestInitExportDirFailure:
    def test_mkdir_failure_is_tolerated(self):
        with patch.object(Path, "mkdir", side_effect=OSError("denied")):
            svc = LogExportService()
        assert svc.export_dir.name == "error_reports"


class TestWriteDependencies:
    def test_writes_installed_packages(self):
        fake_pkg_resources = ModuleType("pkg_resources")
        fake_pkg_resources.working_set = [MagicMock(key="demo-pkg", version="1.0")]
        svc = LogExportService()
        f = MagicMock()
        with patch.dict(sys.modules, {"pkg_resources": fake_pkg_resources}):
            svc._write_dependencies(f)
        written = "".join(c.args[0] for c in f.write.call_args_list)
        assert "demo-pkg==1.0" in written
