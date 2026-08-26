# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from scripts import classify_oq313_native_stderr as classifier
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313 as subject


@unittest.skipUnless(hasattr(os, "pread"), "requires POSIX positional reads")
class OQ313NativeCleanupNonblockingTests(unittest.TestCase):
    def test_snapshot_hashes_only_frozen_prefix_without_moving_file_offset(self) -> None:
        frozen = b"engine-owned stderr\n"
        later = b"detached-dbserver-later-append\n"
        with tempfile.TemporaryFile(mode="w+b") as capture:
            capture.write(frozen + later)
            capture.flush()
            capture.seek(len(frozen + later))
            original_offset = capture.tell()

            with mock.patch.object(
                subject.os,
                "fstat",
                return_value=SimpleNamespace(st_size=len(frozen)),
            ):
                diagnostic = subject._stderr_diagnostic_snapshot(capture)

            self.assertEqual(capture.tell(), original_offset)

        self.assertEqual(
            diagnostic,
            {
                "byte_count": len(frozen),
                "sha256": hashlib.sha256(frozen).hexdigest(),
                "content_exposed": False,
                "exception_class": classifier.UNCLASSIFIED_EXCEPTION_CLASS,
                "traceback_origin": classifier.UNCLASSIFIED_TRACEBACK_ORIGIN,
            },
        )

    def test_snapshot_fails_closed_if_frozen_prefix_cannot_be_read(self) -> None:
        with tempfile.TemporaryFile(mode="w+b") as capture:
            capture.write(b"abc")
            capture.flush()
            with mock.patch.object(
                subject.os,
                "fstat",
                return_value=SimpleNamespace(st_size=4),
            ):
                with self.assertRaisesRegex(
                    subject.KosovoResidentialOQ313RunError,
                    "ended before its frozen boundary",
                ):
                    subject._stderr_diagnostic_snapshot(capture)

    def test_snapshot_rejects_non_integer_size(self) -> None:
        with tempfile.TemporaryFile(mode="w+b") as capture:
            with mock.patch.object(
                subject.os,
                "fstat",
                return_value=SimpleNamespace(st_size=True),
            ):
                with self.assertRaisesRegex(
                    subject.KosovoResidentialOQ313RunError,
                    "snapshot size drifted",
                ):
                    subject._stderr_diagnostic_snapshot(capture)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
