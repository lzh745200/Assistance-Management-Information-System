import pytest
import os
import hashlib
from pathlib import Path
import tempfile


# =========== ensure_dir ===========

class TestEnsureDir:
    def test_creates_directory(self):
        from app.core.file_utils import ensure_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_subdir"
            result = ensure_dir(new_dir)
            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_existing_directory(self):
        from app.core.file_utils import ensure_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert result == Path(tmpdir)
            assert Path(tmpdir).exists()

    def test_returns_path_object(self):
        from app.core.file_utils import ensure_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert isinstance(result, Path)


# =========== safe_path ===========

class TestSafePath:
    def test_within_base_dir(self):
        from app.core.file_utils import safe_path
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "sub" / "file.txt"
            nested.parent.mkdir(parents=True)
            nested.touch()
            result = safe_path(tmpdir, "sub", "file.txt")
            assert result == nested.resolve()

    def test_path_traversal_raises(self):
        from app.core.file_utils import safe_path
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="路径越界"):
                safe_path(tmpdir, "..", "outside.txt")

    def test_path_equality_to_base(self):
        from app.core.file_utils import safe_path
        with tempfile.TemporaryDirectory() as tmpdir:
            result = safe_path(tmpdir)
            assert result == Path(tmpdir).resolve()


# =========== is_safe_path ===========

class TestIsSafePath:
    def test_within_base_returns_true(self):
        from app.core.file_utils import is_safe_path
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_safe_path(tmpdir, Path(tmpdir) / "file.txt") is True

    def test_outside_base_returns_false(self):
        from app.core.file_utils import is_safe_path
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_safe_path(tmpdir, tmpdir + "/../outside") is False


# =========== read_file ===========

class TestReadFile:
    def test_read_text(self):
        from app.core.file_utils import read_file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("hello world")
            f.flush()
            fname = f.name
        try:
            content = read_file(fname)
            assert content == "hello world"
        finally:
            os.unlink(fname)

    def test_read_binary(self):
        from app.core.file_utils import read_file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".bin") as f:
            f.write(b"\x00\x01\x02")
            f.flush()
            fname = f.name
        try:
            content = read_file(fname, binary=True)
            assert content == b"\x00\x01\x02"
        finally:
            os.unlink(fname)


# =========== write_file ===========

class TestWriteFile:
    def test_write_text(self):
        from app.core.file_utils import write_file
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "test.txt"
            write_file(fpath, "hello")
            assert fpath.read_text() == "hello"

    def test_write_binary(self):
        from app.core.file_utils import write_file
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "test.bin"
            write_file(fpath, b"\x00\x01", binary=True)
            assert fpath.read_bytes() == b"\x00\x01"

    def test_write_atomic(self):
        from app.core.file_utils import write_file
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "atomic.txt"
            write_file(fpath, "atomic content", atomic=True)
            assert fpath.read_text() == "atomic content"
            tmp_file = fpath.with_suffix(fpath.suffix + ".tmp")
            assert not tmp_file.exists()

    def test_write_creates_parent_dirs(self):
        from app.core.file_utils import write_file
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "subdir" / "nested" / "test.txt"
            write_file(fpath, "nested")
            assert fpath.read_text() == "nested"


# =========== copy_file ===========

class TestCopyFile:
    def test_copy_successfully(self):
        from app.core.file_utils import copy_file
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "sub" / "dst.txt"
            src.write_text("source content")
            copy_file(src, dst)
            assert dst.read_text() == "source content"

    def test_copy_creates_parent_dirs(self):
        from app.core.file_utils import copy_file
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src.txt"
            dst = Path(tmpdir) / "deep" / "nested" / "dst.txt"
            src.write_text("content")
            copy_file(src, dst)
            assert dst.read_text() == "content"


# =========== delete_file ===========

class TestDeleteFile:
    def test_delete_existing_file(self):
        from app.core.file_utils import delete_file
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "del.txt"
            fpath.write_text("to delete")
            delete_file(fpath)
            assert not fpath.exists()

    def test_delete_missing_file_missing_ok_true(self):
        from app.core.file_utils import delete_file
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "missing.txt"
            delete_file(fpath, missing_ok=True)

    def test_delete_missing_file_missing_ok_false(self):
        from app.core.file_utils import delete_file
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "missing.txt"
            with pytest.raises(FileNotFoundError):
                delete_file(fpath, missing_ok=False)


# =========== delete_directory ===========

class TestDeleteDirectory:
    def test_delete_existing_directory(self):
        from app.core.file_utils import delete_directory
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "file.txt").write_text("content")
            delete_directory(subdir)
            assert not subdir.exists()

    def test_delete_missing_dir_missing_ok_true(self):
        from app.core.file_utils import delete_directory
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing"
            delete_directory(missing, missing_ok=True)

    def test_delete_missing_dir_missing_ok_false(self):
        from app.core.file_utils import delete_directory
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing"
            with pytest.raises(FileNotFoundError, match="目录不存在"):
                delete_directory(missing, missing_ok=False)

    def test_path_is_file_does_nothing(self):
        from app.core.file_utils import delete_directory
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "file.txt"
            fpath.write_text("content")
            delete_directory(fpath, missing_ok=True)
            assert fpath.exists()


# =========== file_md5 ===========

class TestFileMd5:
    def test_computes_md5(self):
        from app.core.file_utils import file_md5
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello")
            fname = f.name
        try:
            expected = hashlib.md5(b"hello").hexdigest()
            assert file_md5(fname) == expected
        finally:
            os.unlink(fname)

    def test_empty_file_md5(self):
        from app.core.file_utils import file_md5
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name
        try:
            expected = hashlib.md5(b"").hexdigest()
            assert file_md5(fname) == expected
        finally:
            os.unlink(fname)

    def test_large_file_md5(self):
        from app.core.file_utils import file_md5
        data = b"a" * 20000
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data)
            fname = f.name
        try:
            expected = hashlib.md5(data).hexdigest()
            assert file_md5(fname) == expected
        finally:
            os.unlink(fname)


# =========== file_sha256 ===========

class TestFileSha256:
    def test_computes_sha256(self):
        from app.core.file_utils import file_sha256
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello")
            fname = f.name
        try:
            expected = hashlib.sha256(b"hello").hexdigest()
            assert file_sha256(fname) == expected
        finally:
            os.unlink(fname)

    def test_empty_file_sha256(self):
        from app.core.file_utils import file_sha256
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name
        try:
            expected = hashlib.sha256(b"").hexdigest()
            assert file_sha256(fname) == expected
        finally:
            os.unlink(fname)


# =========== file_size ===========

class TestFileSize:
    def test_returns_correct_size(self):
        from app.core.file_utils import file_size
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"12345")
            fname = f.name
        try:
            assert file_size(fname) == 5
        finally:
            os.unlink(fname)

    def test_empty_file(self):
        from app.core.file_utils import file_size
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name
        try:
            assert file_size(fname) == 0
        finally:
            os.unlink(fname)


# =========== file_extension ===========

class TestFileExtension:
    def test_regular_file(self):
        from app.core.file_utils import file_extension
        assert file_extension("document.pdf") == ".pdf"

    def test_no_extension(self):
        from app.core.file_utils import file_extension
        assert file_extension("README") == ""

    def test_multiple_extensions(self):
        from app.core.file_utils import file_extension
        assert file_extension("archive.tar.gz") == ".gz"

    def test_lowercase_conversion(self):
        from app.core.file_utils import file_extension
        assert file_extension("Photo.JPG") == ".jpg"

    def test_dotfile(self):
        from app.core.file_utils import file_extension
        result = file_extension(".gitignore")
        assert result == ""

    def test_path_object(self):
        from app.core.file_utils import file_extension
        assert file_extension(Path("data.csv")) == ".csv"


# =========== temp_filename ===========

class TestTempFilename:
    def test_generates_unique(self):
        from app.core.file_utils import temp_filename
        names = {temp_filename() for _ in range(100)}
        assert len(names) == 100

    def test_with_suffix(self):
        from app.core.file_utils import temp_filename
        name = temp_filename(suffix=".txt")
        assert name.endswith(".txt")
        assert len(name) > 4

    def test_length(self):
        from app.core.file_utils import temp_filename
        name = temp_filename()
        assert len(name) == 32
