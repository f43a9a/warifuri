"""Atomic file operations for concurrency safety."""

import fcntl
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import IO, Optional

logger = logging.getLogger(__name__)


class FileLockError(Exception):
    """File locking error."""

    pass


class AtomicWriter:
    """Context manager for atomic file writes."""

    def __init__(self, target_path: Path, mode: str = "w", encoding: str = "utf-8"):
        self.target_path = target_path
        self.mode = mode
        self.encoding = encoding
        self.temp_path: Optional[Path] = None
        self.temp_file: Optional[IO[str]] = None

    def __enter__(self) -> IO[str]:
        """Create temporary file for atomic write."""
        self.target_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temp file in same directory as target for atomic move
        fd, temp_name = tempfile.mkstemp(
            dir=self.target_path.parent, prefix=f".{self.target_path.name}.", suffix=".tmp"
        )

        self.temp_path = Path(temp_name)
        self.temp_file = os.fdopen(fd, self.mode, encoding=self.encoding)
        return self.temp_file

    def __exit__(
        self, exc_type: Optional[type], _exc_val: Optional[BaseException], _exc_tb: Optional[object]
    ) -> None:
        """Complete atomic write or cleanup on error."""
        if self.temp_file:
            self.temp_file.close()

        if exc_type is None:
            # Success: atomically move temp file to target
            try:
                shutil.move(str(self.temp_path), str(self.target_path))
                logger.debug(f"Atomic write completed: {self.target_path}")
            except OSError as e:
                logger.error(f"Atomic write failed: {e}")
                self._cleanup_temp()
                raise
        else:
            # Error: cleanup temp file
            self._cleanup_temp()

    def _cleanup_temp(self) -> None:
        """Clean up temporary file."""
        if self.temp_path and self.temp_path.exists():
            try:
                self.temp_path.unlink()
            except OSError:
                pass  # Best effort cleanup


class FileLock:
    """File-based locking mechanism."""

    def __init__(self, lock_path: Path, timeout: float = 10.0):
        self.lock_path = lock_path
        self.timeout = timeout
        self.lock_file: Optional[IO[str]] = None

    def __enter__(self) -> "FileLock":
        """Acquire file lock."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                # Open lock file exclusively
                self.lock_file = open(self.lock_path, "w")
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Write process info for debugging
                self.lock_file.write(f"pid={os.getpid()}\ntime={time.time()}\n")
                self.lock_file.flush()

                logger.debug(f"Acquired lock: {self.lock_path}")
                return self

            except (OSError, IOError):
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None
                time.sleep(0.1)

        raise FileLockError(f"Could not acquire lock: {self.lock_path}")

    def __exit__(
        self, exc_type: Optional[type], _exc_val: Optional[BaseException], _exc_tb: Optional[object]
    ) -> None:
        """Release file lock."""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                self.lock_path.unlink(missing_ok=True)
                logger.debug(f"Released lock: {self.lock_path}")
            except OSError as e:
                logger.warning(f"Error releasing lock {self.lock_path}: {e}")


def atomic_write_text(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    """Atomically write text content to file."""
    with AtomicWriter(file_path, "w", encoding) as f:
        f.write(content)


def safe_copy_with_lock(src: Path, dst: Path, lock_dir: Optional[Path] = None) -> None:
    """Copy file with locking to prevent race conditions."""
    if lock_dir is None:
        lock_dir = dst.parent

    lock_path = lock_dir / f".{dst.name}.lock"

    with FileLock(lock_path):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def safe_rmtree(path: Path, max_retries: int = 3) -> None:
    """Safely remove directory tree with retries."""
    for attempt in range(max_retries):
        try:
            if path.exists():
                shutil.rmtree(path)
            return
        except OSError as e:
            logger.warning(f"Cleanup attempt {attempt + 1} failed for {path}: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.1 * (2**attempt))  # Exponential backoff
            else:
                logger.error(f"Failed to cleanup {path} after {max_retries} attempts")
                raise
