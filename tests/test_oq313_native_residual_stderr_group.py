# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import sys
import time
import unittest
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


if __name__ == "__main__":
    unittest.main()
