"""app/utils/paths.py 单元测试。

覆盖所有路径函数的平台/环境分支与安全检查（_safe_join 路径遍历防护）。
通过 monkeypatch 控制 sys.frozen / platform.system / 环境变量 / Path.home / cwd，
绝不用 patch.dict(os.environ, clear=True)。
"""
import platform
import sys
from pathlib import Path

import pytest

from app.utils.paths import (
    PathTraversalError,
    _safe_join,
    get_app_data_dir,
    get_backup_directory,
    get_backup_path,
    get_cache_path,
    get_database_path,
    get_data_path,
    get_log_path,
    get_uploads_path,
    is_bundled,
    is_linux,
)


# ── 公共 fixture：每次测试前清理"打包态"属性 ──
@pytest.fixture(autouse=True)
def _clear_bundled_attrs(monkeypatch):
    """每个测试默认清除 sys.frozen / sys._MEIPASS，保证 is_bundled() 默认 False。"""
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


# ─────────────────────────────────────────────────────────────
# _safe_join
# ─────────────────────────────────────────────────────────────
class TestSafeJoin:
    def test_empty_sub_path_returns_base_unchanged(self, tmp_path):
        assert _safe_join(tmp_path, "") == tmp_path

    def test_valid_sub_path_resolves_within_base(self, tmp_path):
        result = _safe_join(tmp_path, "subdir/file.txt")
        assert result == (tmp_path / "subdir" / "file.txt").resolve()
        # 仍在 base 内
        assert str(result).startswith(str(tmp_path.resolve()))

    def test_valid_sub_path_with_nested_dirs(self, tmp_path):
        result = _safe_join(tmp_path, "a/b/c/d.txt")
        assert result.parent == (tmp_path / "a" / "b" / "c").resolve()

    def test_traversal_outside_base_raises(self, tmp_path):
        with pytest.raises(PathTraversalError) as exc:
            _safe_join(tmp_path, "../escape.txt")
        assert "路径遍历被拒绝" in str(exc.value)
        assert "../escape.txt" in str(exc.value)

    def test_traversal_deep_outside_base_raises(self, tmp_path):
        with pytest.raises(PathTraversalError):
            _safe_join(tmp_path, "a/../../../escape")

    def test_traversal_error_is_value_error_subclass(self):
        assert issubclass(PathTraversalError, ValueError)


# ─────────────────────────────────────────────────────────────
# is_bundled / is_linux
# ─────────────────────────────────────────────────────────────
class TestPlatformHelpers:
    def test_is_bundled_false_by_default(self):
        assert is_bundled() is False

    def test_is_bundled_true_when_frozen_with_meipass(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake/meipass", raising=False)
        assert is_bundled() is True

    def test_is_bundled_true_when_frozen_without_meipass(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        # _MEIPASS 已被 autouse fixture 删除；onedir 模式 frozen 但无 _MEIPASS 仍判定为打包环境
        assert is_bundled() is True

    def test_is_linux_true(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        assert is_linux() is True

    def test_is_linux_false_on_windows(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        assert is_linux() is False

    def test_is_linux_false_on_darwin(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        assert is_linux() is False


# ─────────────────────────────────────────────────────────────
# get_app_data_dir —— 所有平台/环境分支
# ─────────────────────────────────────────────────────────────
class TestGetAppDataDir:
    def test_dev_windows_uses_cwd(self, monkeypatch, tmp_path):
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.chdir(tmp_path)
        result = get_app_data_dir()
        assert result == tmp_path

    def test_dev_linux_with_dev_mode_uses_cwd(self, monkeypatch, tmp_path):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setenv("BUMOFU_DEV_MODE", "1")
        monkeypatch.chdir(tmp_path)
        assert get_app_data_dir() == tmp_path

    def test_prod_linux_without_dev_mode_uses_home(self, monkeypatch, tmp_path):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.delenv("BUMOFU_DEV_MODE", raising=False)
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        result = get_app_data_dir()
        assert result == fake_home / ".bumofu"
        assert result.exists()

    def test_bundled_linux_uses_home(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        result = get_app_data_dir()
        assert result == fake_home / ".bumofu"

    def test_bundled_windows_with_localappdata(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        local = tmp_path / "local"
        monkeypatch.setenv("LOCALAPPDATA", str(local))
        monkeypatch.delenv("APPDATA", raising=False)
        result = get_app_data_dir()
        assert result == local / "bumofu-assistance"

    def test_bundled_windows_appdata_fallback_when_no_localappdata(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        roaming = tmp_path / "roaming"
        monkeypatch.setenv("APPDATA", str(roaming))
        result = get_app_data_dir()
        assert result == roaming / "bumofu-assistance"

    def test_bundled_windows_no_env_uses_home(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.delenv("APPDATA", raising=False)
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        result = get_app_data_dir()
        assert result == fake_home / ".bumofu"

    def test_directory_is_created(self, monkeypatch, tmp_path):
        """无论走哪个分支，最终目录必须存在。"""
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.chdir(tmp_path)
        result = get_app_data_dir()
        assert result.exists()
        assert result.is_dir()


# ─────────────────────────────────────────────────────────────
# 通用辅助：在 dev mode 下测试各路径函数
# ─────────────────────────────────────────────────────────────
def _setup_dev_mode(monkeypatch, tmp_path):
    """统一设置 dev mode（Windows 开发环境 + cwd=tmp_path）。"""
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.chdir(tmp_path)


# ─────────────────────────────────────────────────────────────
# get_data_path
# ─────────────────────────────────────────────────────────────
class TestGetDataPath:
    def test_empty_sub_path_returns_base(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_data_path("")
        assert result == tmp_path / "data"

    def test_default_arg_returns_base(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_data_path()
        assert result == tmp_path / "data"

    def test_flat_filename_parent_equals_base_no_mkdir(
        self, monkeypatch, tmp_path
    ):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_data_path("file.db")
        assert result == (tmp_path / "data" / "file.db").resolve()
        # base 目录由 get_app_data_dir 创建；data 目录不应被本函数创建
        # 但 file.db 的父目录是 data，等价于 base —— 不应抛错

    def test_nested_sub_path_creates_parent_dirs(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_data_path("subdir/deep/file.txt")
        assert result.parent.exists()
        assert result.parent == (tmp_path / "data" / "subdir" / "deep").resolve()

    def test_traversal_raises(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        with pytest.raises(PathTraversalError):
            get_data_path("../../escape")


# ─────────────────────────────────────────────────────────────
# get_backup_path / get_backup_directory
# ─────────────────────────────────────────────────────────────
class TestGetBackupPath:
    def test_empty_sub_path_returns_base(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        assert get_backup_path("") == tmp_path / "backups"

    def test_default_arg_returns_base(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        assert get_backup_path() == tmp_path / "backups"

    def test_flat_filename_returns_path(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_backup_path("backup.zip")
        assert result == (tmp_path / "backups" / "backup.zip").resolve()

    def test_nested_sub_path_creates_parent(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_backup_path("daily/2025/backup.zip")
        assert result.parent.exists()

    def test_traversal_raises(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        with pytest.raises(PathTraversalError):
            get_backup_path("../escape")


class TestBackupDirectoryAlias:
    def test_alias_is_same_function(self):
        assert get_backup_directory is get_backup_path

    def test_alias_returns_same_result(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        assert get_backup_directory("x.zip") == get_backup_path("x.zip")


# ─────────────────────────────────────────────────────────────
# get_cache_path —— 包含独立的平台分支
# ─────────────────────────────────────────────────────────────
class TestGetCachePath:
    def test_dev_mode_empty_returns_data_cache(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        assert get_cache_path("") == tmp_path / "data" / "cache"

    def test_dev_mode_with_sub_path(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_cache_path("tmp.json")
        assert result == (tmp_path / "data" / "cache" / "tmp.json").resolve()

    def test_dev_mode_nested_creates_parent(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_cache_path("sub/dir/cache.json")
        assert result.parent.exists()

    def test_dev_mode_traversal_raises(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        with pytest.raises(PathTraversalError):
            get_cache_path("../escape")

    def test_bundled_linux_uses_home_cache(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        assert get_cache_path("") == fake_home / ".bumofu" / "cache"

    def test_bundled_linux_with_sub_path(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        result = get_cache_path("a/b.json")
        assert result == (fake_home / ".bumofu" / "cache" / "a" / "b.json").resolve()

    def test_bundled_windows_with_localappdata(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        local = tmp_path / "local"
        monkeypatch.setenv("LOCALAPPDATA", str(local))
        monkeypatch.delenv("APPDATA", raising=False)
        assert get_cache_path("") == local / "bumofu-assistance" / "cache"

    def test_bundled_windows_appdata_fallback(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        roaming = tmp_path / "roaming"
        monkeypatch.setenv("APPDATA", str(roaming))
        assert get_cache_path("") == roaming / "bumofu-assistance" / "cache"

    def test_bundled_windows_no_env_uses_home(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", "/fake", raising=False)
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.delenv("APPDATA", raising=False)
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        assert get_cache_path("") == fake_home / ".bumofu" / "cache"

    def test_prod_linux_without_dev_mode_uses_home_cache(
        self, monkeypatch, tmp_path
    ):
        """非 bundled 但 Linux 生产（无 BUMOFU_DEV_MODE）也走 home 分支。"""
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.delenv("BUMOFU_DEV_MODE", raising=False)
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        assert get_cache_path("") == fake_home / ".bumofu" / "cache"


# ─────────────────────────────────────────────────────────────
# get_uploads_path
# ─────────────────────────────────────────────────────────────
class TestGetUploadsPath:
    def test_empty_returns_base(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        assert get_uploads_path("") == tmp_path / "uploads"

    def test_default_arg_returns_base(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        assert get_uploads_path() == tmp_path / "uploads"

    def test_flat_filename(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_uploads_path("avatar.png")
        assert result == (tmp_path / "uploads" / "avatar.png").resolve()

    def test_nested_creates_parent(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_uploads_path("users/123/avatar.png")
        assert result.parent.exists()

    def test_traversal_raises(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        with pytest.raises(PathTraversalError):
            get_uploads_path("../escape")


# ─────────────────────────────────────────────────────────────
# get_database_path
# ─────────────────────────────────────────────────────────────
class TestGetDatabasePath:
    def test_returns_data_path_with_db_filename(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_database_path()
        assert result == (tmp_path / "data" / "rural_revitalization.db").resolve()


# ─────────────────────────────────────────────────────────────
# get_log_path —— 总是创建 base 目录
# ─────────────────────────────────────────────────────────────
class TestGetLogPath:
    def test_empty_returns_base_and_creates_dir(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_log_path("")
        assert result == tmp_path / "logs"
        assert result.exists()
        assert result.is_dir()

    def test_default_arg_returns_base(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        assert get_log_path() == tmp_path / "logs"

    def test_with_sub_path_returns_file_path(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_log_path("app.log")
        assert result == (tmp_path / "logs" / "app.log").resolve()
        # base 应被创建
        assert (tmp_path / "logs").exists()

    def test_nested_sub_path_creates_parents(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        result = get_log_path("subdir/run.log")
        assert result.parent.exists()

    def test_traversal_raises(self, monkeypatch, tmp_path):
        _setup_dev_mode(monkeypatch, tmp_path)
        with pytest.raises(PathTraversalError):
            get_log_path("../../escape")
