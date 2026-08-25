# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import signal
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as subject


@unittest.skipUnless(hasattr(os, "killpg"), "requires POSIX process groups")
class ResidualStderrProcessGroupTests(unittest.TestCase):
    def _run_parent_with_residual_child(
        self,
        *,
        ignore_sigterm: bool,
    ) -> tuple[int, float]:
        child_setup = (
            "import signal,time; "
            + (
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                if ignore_sigterm
                else ""
            )
            + "time.sleep(60)"
        )
        parent = (
            "import subprocess,sys; "
            "subprocess.Popen([sys.executable, '-c', "
            + repr(child_setup)
            + "]); "
            "raise SystemExit(0)"
        )
        env = os.environ.copy()
        started = time.monotonic()
        with (
            mock.patch.object(subject, "NATIVE_EXECUTION_TIMEOUT_SECONDS", 5),
            mock.patch.object(subject, "NATIVE_TERMINATION_GRACE_SECONDS", 0.25),
        ):
            returncode = subject._execute_native([sys.executable, "-c", parent], env)
        return int(returncode), time.monotonic() - started

    def test_residual_stderr_writer_is_terminated_after_direct_process_exit(self) -> None:
        returncode, elapsed = self._run_parent_with_residual_child(ignore_sigterm=False)
        self.assertEqual(returncode, 0)
        self.assertLess(elapsed, 3.0)

    def test_sigterm_resistant_residual_writer_is_killed_boundedly(self) -> None:
        returncode, elapsed = self._run_parent_with_residual_child(ignore_sigterm=True)
        self.assertEqual(returncode, 0)
        self.assertLess(elapsed, 3.0)

    def test_success_tolerates_detached_new_session_stderr_holder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid_path = Path(directory, "detached.pid")
            child_setup = "import time; time.sleep(60)"
            parent = (
                "import pathlib,subprocess,sys; "
                "child=subprocess.Popen([sys.executable, '-c', "
                + repr(child_setup)
                + "], start_new_session=True); "
                + f"pathlib.Path({str(pid_path)!r}).write_text(str(child.pid)); "
                + "raise SystemExit(0)"
            )
            env = os.environ.copy()
            started = time.monotonic()
            try:
                with (
                    mock.patch.object(subject, "NATIVE_EXECUTION_TIMEOUT_SECONDS", 5),
                    mock.patch.object(
                        subject, "NATIVE_TERMINATION_GRACE_SECONDS", 0.1
                    ),
                ):
                    returncode = subject._execute_native(
                        [sys.executable, "-c", parent], env
                    )
            finally:
                if pid_path.exists():
                    detached_pid = int(pid_path.read_text(encoding="utf-8"))
                    try:
                        os.kill(detached_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

        self.assertEqual(returncode, 0)
        self.assertLess(time.monotonic() - started, 2.0)


if __name__ == "__main__":
    unittest.main()
