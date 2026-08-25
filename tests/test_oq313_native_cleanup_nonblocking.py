# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import signal
import subprocess
import threading
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as subject


class _CloseMustNotUnblockRead:
    def __init__(self) -> None:
        self.release_read = threading.Event()
        self.read_finished = threading.Event()
        self.close_calls = 0

    def read(self, size: int = -1) -> bytes:
        if size != subject.NATIVE_STDERR_HASH_CHUNK_BYTES:
            raise AssertionError(f"unexpected stderr read size: {size}")
        self.release_read.wait()
        self.read_finished.set()
        return b""

    def close(self) -> None:
        self.close_calls += 1
        raise AssertionError("controller must not close stderr before drain completion")


class _FakeProcess:
    def __init__(self, stderr: object) -> None:
        self.stderr = stderr
        self.pid = 4242
        self.returncode: int | None = None
        self.kill_calls = 0
        self.wait_timeouts: list[float | None] = []
        self._first_wait = True

    def wait(self, timeout: float | None = None) -> int:
        self.wait_timeouts.append(timeout)
        if self._first_wait:
            self._first_wait = False
            raise subprocess.TimeoutExpired(subject.COMMAND, timeout)
        if self.returncode is None:
            raise AssertionError("bounded cleanup wait happened before direct kill")
        return self.returncode

    def poll(self) -> int | None:
        return self.returncode

    def kill(self) -> None:
        self.kill_calls += 1
        self.returncode = -signal.SIGKILL


class OQ313NativeCleanupNonblockingTests(unittest.TestCase):
    def test_killpg_failure_does_not_close_stderr_while_drain_is_blocked(self) -> None:
        stderr = _CloseMustNotUnblockRead()
        process = _FakeProcess(stderr)

        try:
            with (
                mock.patch.object(subject.subprocess, "Popen", return_value=process),
                mock.patch.object(subject.os, "killpg", side_effect=OSError("denied")),
                mock.patch.object(subject, "NATIVE_TERMINATION_GRACE_SECONDS", 0.01),
            ):
                with self.assertRaisesRegex(
                    subject.KosovoResidentialOQ313RunError,
                    "timed-out process group could not be terminated",
                ):
                    subject._execute_native(subject.COMMAND, {"PATH": "/fixed"})

            self.assertEqual(stderr.close_calls, 0)
            self.assertEqual(process.kill_calls, 1)
            self.assertEqual(
                process.wait_timeouts,
                [subject.NATIVE_EXECUTION_TIMEOUT_SECONDS, 0.01],
            )
        finally:
            stderr.release_read.set()
            self.assertTrue(stderr.read_finished.wait(1.0))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
