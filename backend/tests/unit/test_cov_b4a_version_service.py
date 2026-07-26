"""覆盖率攻坚: app/services/version_service.py 缺口行 26-27（版本历史目录创建失败降级）."""
from unittest.mock import patch

from app.services.version_service import VersionService


class TestVersionServiceMkdirFailure:
    def test_history_dir_mkdir_failure_logs_warning(self):
        """history_file.parent.mkdir 抛异常时记录 warning 并继续初始化（第 26-27 行）."""
        with patch("pathlib.Path.mkdir", side_effect=OSError("read-only fs")):
            with patch.object(VersionService, "_load_current_version", return_value={"version": "9.9.9"}):
                svc = VersionService()

        assert svc.current_version == {"version": "9.9.9"}
        assert svc.version_file.name == "version.json"
