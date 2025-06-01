"""Unit tests for atomic file operations."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from warifuri.utils.atomic import (
    AtomicWriter,
    FileLock,
    FileLockError,
    atomic_write_text,
    safe_copy_with_lock,
    safe_rmtree,
)


def test_safe_rmtree_success():
    """Test successful safe_rmtree operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        safe_rmtree(test_dir)

        assert not test_dir.exists()


def test_safe_rmtree_nonexistent_path():
    """Test safe_rmtree with non-existent path."""
    non_existent = Path("/tmp/non_existent_dir")

    # Should not raise exception
    safe_rmtree(non_existent)


@patch("warifuri.utils.atomic.shutil.rmtree")
@patch("warifuri.utils.atomic.Path.exists")
def test_safe_rmtree_retry_on_failure(mock_exists, mock_rmtree):
    """Test safe_rmtree retries on failure."""
    mock_exists.return_value = True
    mock_rmtree.side_effect = [OSError("Busy"), OSError("Busy"), None]

    test_path = Path("/tmp/test_dir")

    safe_rmtree(test_path, max_retries=3)

    assert mock_rmtree.call_count == 3


def test_atomic_write_text_success():
    """Test successful atomic_write_text operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "test.txt"
        content = "test content"

        atomic_write_text(target_file, content)

        assert target_file.exists()
        assert target_file.read_text() == content


def test_atomic_write_text_with_encoding():
    """Test atomic_write_text with specific encoding."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "test.txt"
        content = "test content with unicode: ñáéíóú"

        atomic_write_text(target_file, content, encoding="utf-8")

        assert target_file.exists()
        assert target_file.read_text(encoding="utf-8") == content


def test_safe_copy_with_lock_success():
    """Test successful safe_copy_with_lock operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        src = Path(temp_dir) / "source.txt"
        dst = Path(temp_dir) / "dest.txt"
        src.write_text("test content")

        safe_copy_with_lock(src, dst)

        assert dst.exists()
        assert dst.read_text() == "test content"
        assert src.exists()  # Source should still exist


def test_safe_copy_with_lock_custom_lock_dir():
    """Test safe_copy_with_lock with custom lock directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        src = Path(temp_dir) / "source.txt"
        dst = Path(temp_dir) / "dest.txt"
        lock_dir = Path(temp_dir) / "locks"
        lock_dir.mkdir()

        src.write_text("test content")

        safe_copy_with_lock(src, dst, lock_dir)

        assert dst.exists()
        assert dst.read_text() == "test content"


def test_atomic_writer_success():
    """Test successful AtomicWriter operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "test.txt"

        with AtomicWriter(target_file) as f:
            f.write("test content")

        assert target_file.exists()
        assert target_file.read_text() == "test content"


def test_atomic_writer_with_failure():
    """Test AtomicWriter cleanup on failure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "test.txt"

        try:
            with AtomicWriter(target_file) as f:
                f.write("partial content")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Target file should not exist due to rollback
        assert not target_file.exists()


def test_atomic_writer_custom_mode():
    """Test AtomicWriter with custom mode."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "test.txt"

        with AtomicWriter(target_file, mode="w", encoding="utf-8") as f:
            f.write("test content with ñáéíóú")

        assert target_file.exists()
        assert target_file.read_text(encoding="utf-8") == "test content with ñáéíóú"


def test_file_lock_success():
    """Test successful FileLock operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        lock_file = Path(temp_dir) / "test.lock"

        with FileLock(lock_file):
            assert lock_file.exists()

        # Lock should be released
        assert not lock_file.exists()


def test_file_lock_timeout():
    """Test FileLock timeout."""
    import threading
    import time

    with tempfile.TemporaryDirectory() as temp_dir:
        lock_file = Path(temp_dir) / "test.lock"

        def hold_lock():
            with FileLock(lock_file, timeout=2.0):  # Hold lock for 2 seconds
                time.sleep(1.5)  # Keep lock held

        # Start thread to hold the lock
        thread = threading.Thread(target=hold_lock)
        thread.start()

        time.sleep(0.1)  # Give thread time to acquire lock

        try:
            # This should timeout quickly
            with pytest.raises(FileLockError):
                with FileLock(lock_file, timeout=0.1):
                    pass
        finally:
            thread.join()  # Clean up thread


def test_file_lock_cleanup_on_error():
    """Test FileLock cleanup on error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        lock_file = Path(temp_dir) / "test.lock"

        try:
            with FileLock(lock_file):
                assert lock_file.exists()
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Lock should be cleaned up
        assert not lock_file.exists()


@patch("warifuri.utils.atomic.shutil.copy2")
def test_safe_copy_with_lock_copy_failure(mock_copy):
    """Test safe_copy_with_lock when copy operation fails."""
    mock_copy.side_effect = OSError("Copy failed")

    with tempfile.TemporaryDirectory() as temp_dir:
        src = Path(temp_dir) / "source.txt"
        dst = Path(temp_dir) / "dest.txt"
        src.write_text("content")

        with pytest.raises(OSError, match="Copy failed"):
            safe_copy_with_lock(src, dst)


@patch("warifuri.utils.atomic.AtomicWriter.__enter__")
def test_atomic_write_text_failure(mock_enter):
    """Test atomic_write_text when write operation fails."""
    mock_file = Mock()
    mock_file.write.side_effect = OSError("Write failed")
    mock_enter.return_value = mock_file

    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "test.txt"

        with pytest.raises(OSError, match="Write failed"):
            atomic_write_text(target_file, "content")


def test_file_lock_multiple_locks():
    """Test FileLock with multiple lock attempts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        lock_file = Path(temp_dir) / "test.lock"

        # First lock should succeed
        with FileLock(lock_file):
            # Second lock should fail quickly
            with pytest.raises(FileLockError):
                with FileLock(lock_file, timeout=0.1):
                    pass

        # After first lock is released, second should succeed
        with FileLock(lock_file):
            assert lock_file.exists()


def test_atomic_writer_creates_parent_directories():
    """Test AtomicWriter creates parent directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "subdir" / "test.txt"

        with AtomicWriter(target_file) as f:
            f.write("test content")

        assert target_file.exists()
        assert target_file.read_text() == "test content"
        assert target_file.parent.exists()


def test_safe_rmtree_with_readonly_files():
    """Test safe_rmtree with readonly files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()
        readonly_file = test_dir / "readonly.txt"
        readonly_file.write_text("content")
        readonly_file.chmod(0o444)  # Make readonly

        safe_rmtree(test_dir)

        assert not test_dir.exists()


def test_file_lock_with_custom_timeout():
    """Test FileLock with custom timeout."""
    import threading

    with tempfile.TemporaryDirectory() as temp_dir:
        lock_file = Path(temp_dir) / "test.lock"

        def hold_lock():
            with FileLock(lock_file, timeout=2.0):  # Hold lock for 2 seconds
                time.sleep(1.5)  # Keep lock held

        # Start thread to hold the lock
        thread = threading.Thread(target=hold_lock)
        thread.start()

        time.sleep(0.1)  # Give thread time to acquire lock

        try:
            start_time = time.time()
            with pytest.raises(FileLockError):
                with FileLock(lock_file, timeout=0.5):
                    pass
            end_time = time.time()

            # Should have waited approximately the timeout duration
            assert 0.4 < (end_time - start_time) < 0.8
        finally:
            thread.join()  # Clean up thread
