"""Tests for concurrency safety and atomic operations."""

import threading
import time
import pytest
from pathlib import Path
from unittest import mock

from warifuri.utils.atomic import (
    AtomicWriter,
    FileLock,
    FileLockError,
    atomic_write_text,
    safe_copy_with_lock,
    safe_rmtree,
)


class TestAtomicWriter:
    """Test atomic file writing."""

    def test_atomic_write_success(self, tmp_path: Path):
        """Test successful atomic write."""
        target = tmp_path / "test.txt"
        content = "test content"

        with AtomicWriter(target) as f:
            f.write(content)

        assert target.exists()
        assert target.read_text() == content

    def test_atomic_write_failure_cleanup(self, tmp_path: Path):
        """Test cleanup on write failure."""
        target = tmp_path / "test.txt"

        try:
            with AtomicWriter(target) as f:
                f.write("partial content")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Target file should not exist after error
        assert not target.exists()

        # No temp files should remain
        temp_files = list(tmp_path.glob(".*test.txt*.tmp"))
        assert len(temp_files) == 0

    def test_atomic_write_creates_parent_dirs(self, tmp_path: Path):
        """Test that parent directories are created."""
        target = tmp_path / "nested" / "dirs" / "test.txt"

        with AtomicWriter(target) as f:
            f.write("content")

        assert target.exists()
        assert target.read_text() == "content"


class TestFileLock:
    """Test file locking mechanism."""

    def test_file_lock_success(self, tmp_path: Path):
        """Test successful file locking."""
        lock_path = tmp_path / "test.lock"

        with FileLock(lock_path):
            assert lock_path.exists()

        # Lock should be released and file removed
        assert not lock_path.exists()

    def test_file_lock_timeout(self, tmp_path: Path):
        """Test lock timeout behavior."""
        lock_path = tmp_path / "test.lock"

        def hold_lock():
            with FileLock(lock_path, timeout=1.0):
                time.sleep(2.0)  # Hold longer than timeout

        # Start lock holder in background
        thread = threading.Thread(target=hold_lock)
        thread.start()

        # Wait for lock to be acquired
        time.sleep(0.1)

        # Try to acquire same lock with short timeout
        with pytest.raises(FileLockError):
            with FileLock(lock_path, timeout=0.5):
                pass

        thread.join()

    def test_concurrent_file_access(self, tmp_path: Path):
        """Test concurrent access to same file is serialized."""
        target_file = tmp_path / "concurrent.txt"
        lock_path = tmp_path / "concurrent.lock"
        results = []

        def write_with_lock(content: str, delay: float):
            with FileLock(lock_path):
                # Simulate some work
                time.sleep(delay)
                with open(target_file, "a") as f:
                    f.write(f"{content}\n")
                results.append(content)

        # Start multiple threads
        threads = []
        for i, delay in enumerate([0.1, 0.05, 0.15], 1):
            thread = threading.Thread(target=write_with_lock, args=(f"thread-{i}", delay))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check that file was written correctly (serialized access)
        assert target_file.exists()
        lines = target_file.read_text().strip().split("\n")
        assert len(lines) == 3
        assert len(results) == 3


class TestAtomicUtilities:
    """Test atomic utility functions."""

    def test_atomic_write_text(self, tmp_path: Path):
        """Test atomic text writing utility."""
        target = tmp_path / "atomic.txt"
        content = "atomic content"

        atomic_write_text(target, content)

        assert target.exists()
        assert target.read_text() == content

    def test_safe_copy_with_lock(self, tmp_path: Path):
        """Test safe file copying with locking."""
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("source content")

        safe_copy_with_lock(src, dst)

        assert dst.exists()
        assert dst.read_text() == "source content"

    def test_safe_rmtree_success(self, tmp_path: Path):
        """Test safe directory removal."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        safe_rmtree(test_dir)

        assert not test_dir.exists()

    def test_safe_rmtree_with_retries(self, tmp_path: Path):
        """Test safe directory removal with retry logic."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Mock rmtree to fail first few times
        original_rmtree = __import__("shutil").rmtree
        call_count = 0

        def mock_rmtree(path, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 times
                raise OSError("Simulated failure")
            return original_rmtree(path, *args, **kwargs)

        with mock.patch("shutil.rmtree", side_effect=mock_rmtree):
            safe_rmtree(test_dir)

        assert not test_dir.exists()
        assert call_count == 3  # Should have retried


class TestConcurrencyIntegration:
    """Integration tests for concurrency scenarios."""

    def test_concurrent_task_execution_simulation(self, tmp_path: Path):
        """Simulate concurrent task execution scenarios."""
        task_dir = tmp_path / "task"
        task_dir.mkdir()

        done_file = task_dir / "done.md"
        lock_path = task_dir / ".execution.lock"

        results = []

        def simulate_task_completion(task_id: str):
            """Simulate task completion with atomic done.md creation."""
            try:
                with FileLock(lock_path, timeout=2.0):
                    # Check if already done
                    if done_file.exists():
                        results.append(f"{task_id}: already done")
                        return

                    # Simulate work
                    time.sleep(0.1)

                    # Atomically create done.md
                    atomic_write_text(done_file, f"Completed by {task_id}\n")
                    results.append(f"{task_id}: completed")

            except FileLockError:
                results.append(f"{task_id}: lock timeout")

        # Start multiple "task runners"
        threads = []
        for i in range(3):
            thread = threading.Thread(target=simulate_task_completion, args=(f"runner-{i}",))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Only one should have completed the task
        completed_count = sum(1 for r in results if "completed" in r)
        already_done_count = sum(1 for r in results if "already done" in r)

        assert completed_count == 1  # Only one should complete
        assert already_done_count == 2  # Others should see it's done
        assert done_file.exists()
