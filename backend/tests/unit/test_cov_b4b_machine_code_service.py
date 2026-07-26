"""补齐 app.services.machine_code_service 覆盖率缺口（68-69/74/80-84 行：wmic 采集异常分支）."""
from unittest.mock import MagicMock, patch

from app.services.machine_code_service import MachineCodeService

_MOD = "app.services.machine_code_service"


class TestCollectWmicInfo:
    def test_popen_failure_appends_none_and_skips(self):
        with patch(f"{_MOD}.platform.system", return_value="Windows"), patch(
            "subprocess.Popen", side_effect=OSError("no wmic")
        ):
            assert MachineCodeService._collect_wmic_info() == []

    def test_communicate_failure_and_kill_failure(self):
        proc = MagicMock()
        proc.communicate.side_effect = TimeoutError("slow")
        proc.kill.side_effect = OSError("cannot kill")
        with patch(f"{_MOD}.platform.system", return_value="Windows"), patch(
            "subprocess.Popen", return_value=proc
        ):
            assert MachineCodeService._collect_wmic_info() == []
        assert proc.kill.call_count == 3
