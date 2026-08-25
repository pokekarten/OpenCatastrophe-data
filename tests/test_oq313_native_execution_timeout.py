# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import signal
import subprocess
import threading
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as subject


class _ChunkedStderr:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = iter(chunks)
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        if size != subject.NATIVE_STDERR_HASH_CHUNK_BYTES:
            raise AssertionError(f"unexpected stderr read size: {size}")
        return next(self._chunks, b"")

    def close(self) -> None:
        self.closed = True


class _BlockingStderr:
    def __init__(self) -> None:
        self._closed = threading.Event()

    def read(self, size: int = -1) -> bytes:
        if size != subject.NATIVE_STDERR_HASH_CHUNK_BYTES:
            raise AssertionError(f"unexpected stderr read size: {size}")
        self._closed.wait()
        return b""

    def close(self) -> None:
        self._closed.set()


class _FakeProcess:
    def __init__(self, stderr: object, wait_results: list[object]) -> None:
        self.stderr = stderr
        self.pid = 4242
        self.wait_results = list(wait_results)
        self.wait_timeouts: list[float | None] = []
        self.returncode: int | None = None
        self.kill_calls = 0

    def wait(self, timeout: float | None = None) -> int:
        self.wait_timeouts.append(timeout)
        if not self.wait_results:
            if self.returncode is None:
                raise AssertionError("unexpected extra process.wait call")
            return self.returncode
        result = self.wait_results.pop(0)
        if isinstance(result, BaseException):
            raise result
        if type(result) is not int:
            raise AssertionError(f"unexpected fake wait result: {result!r}")
        self.returncode = result
        return result

    def poll(self) -> int | None:
        return self.returncode

    def kill(self) -> None:
        self.kill_calls += 1
        self.returncode = -signal.SIGKILL


class OQ313NativeExecutionTimeoutTests(unittest.TestCase):
    def test_timeout_terminates_process_group_and_returns_bounded_failure(self) -> None:
        secret = b"private runtime stderr must remain opaque\n"
        process = _FakeProcess(
            _ChunkedStderr([secret]),
            [
                subprocess.TimeoutExpired(subject.COMMAND, 1),
                subprocess.TimeoutExpired(subject.COMMAND, 1),
                -signal.SIGKILL,
            ],
        )

        with (
            mock.patch.object(subject.subprocess, "Popen", return_value=process) as popen,
            mock.patch.object(subject.os, "killpg") as killpg,
        ):
            returncode = subject._execute_native(subject.COMMAND, {"PATH": "/fixed"})

        self.assertEqual(int(returncode), subject.NATIVE_TIMEOUT_EXIT_CODE)
        self.assertEqual(subject.NATIVE_TIMEOUT_EXIT_CODE, 124)
        self.assertIs(getattr(returncode, "timed_out"), True)
        self.assertEqual(subject._native_failure_code(returncode), "openquake_run_timeout")
        self.assertEqual(
            getattr(returncode, "diagnostic"),
            {
                "byte_count": len(secret),
                "sha256": hashlib.sha256(secret).hexdigest(),
                "content_exposed": False,
            },
        )
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(process.pid, signal.SIGTERM),
                mock.call(process.pid, signal.SIGKILL),
            ],
        )
        self.assertEqual(
            process.wait_timeouts[:3],
            [
                subject.NATIVE_EXECUTION_TIMEOUT_SECONDS,
                subject.NATIVE_TERMINATION_GRACE_SECONDS,
                subject.NATIVE_TERMINATION_GRACE_SECONDS,
            ],
        )

        popen.assert_called_once()
        _args, kwargs = popen.call_args
        self.assertTrue(kwargs["start_new_session"])
        self.assertIs(kwargs["stdout"], subject.subprocess.DEVNULL)
        self.assertIs(kwargs["stderr"], subject.subprocess.PIPE)

    def test_termination_signal_failure_is_bounded_independently_of_stderr_eof(self) -> None:
        stderr = _BlockingStderr()
        process = _FakeProcess(
            stderr,
            [
                subprocess.TimeoutExpired(subject.COMMAND, 1),
                -signal.SIGKILL,
            ],
        )

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

            self.assertEqual(process.kill_calls, 1)
            self.assertFalse(stderr._closed.is_set())
            self.assertEqual(
                process.wait_timeouts,
                [
                    subject.NATIVE_EXECUTION_TIMEOUT_SECONDS,
                    0.01,
                ],
            )
        finally:
            stderr._closed.set()

    def test_native_exit_124_is_not_controller_timeout(self) -> None:
        diagnostic = {
            "byte_count": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
            "content_exposed": False,
        }
        returncode = subject._NativeExitCode(
            subject.NATIVE_TIMEOUT_EXIT_CODE,
            diagnostic,
        )

        self.assertEqual(int(returncode), 124)
        self.assertIs(returncode.timed_out, False)
        self.assertEqual(subject._native_failure_code(returncode), "openquake_run_failed")
        self.assertEqual(subject._native_failure_code(124), "openquake_run_failed")

    def test_inner_budget_leaves_terminalization_margin_under_outer_job_limit(self) -> None:
        outer_job_timeout_seconds = 355 * 60
        self.assertLess(
            subject.NATIVE_EXECUTION_TIMEOUT_SECONDS
            + (2 * subject.NATIVE_TERMINATION_GRACE_SECONDS),
            outer_job_timeout_seconds,
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
