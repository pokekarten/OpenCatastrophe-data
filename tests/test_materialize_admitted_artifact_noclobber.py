# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import materialize_admitted_artifact as materializer

BYTES = b"abc"
SHA = hashlib.sha256(BYTES).hexdigest()
RACED = b"raced"


class MaterializeAdmittedArtifactNoClobberTests(unittest.TestCase):
    def _run_race(self, raced_bytes: bytes) -> tuple[Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        source = root / "source.bin"
        destination = root / "cache" / "artifact"
        destination.parent.mkdir()
        source.write_bytes(BYTES)

        real_replace = os.replace
        real_link = os.link

        def racing_replace(src: os.PathLike[str] | str, dst: os.PathLike[str] | str) -> None:
            Path(dst).write_bytes(raced_bytes)
            real_replace(src, dst)

        def racing_link(src: os.PathLike[str] | str, dst: os.PathLike[str] | str) -> None:
            Path(dst).write_bytes(raced_bytes)
            real_link(src, dst)

        patches = (
            mock.patch.object(materializer.os, "replace", side_effect=racing_replace),
            mock.patch.object(materializer.os, "link", side_effect=racing_link),
        )
        with patches[0], patches[1]:
            if raced_bytes == BYTES:
                materializer._copy_and_verify(
                    source,
                    destination,
                    expected_sha256=SHA,
                    expected_size=len(BYTES),
                )
            else:
                with self.assertRaisesRegex(
                    materializer.MaterializationError,
                    "existing cache destination does not match admitted artifact",
                ):
                    materializer._copy_and_verify(
                        source,
                        destination,
                        expected_sha256=SHA,
                        expected_size=len(BYTES),
                    )

        return root, destination

    def test_concurrent_mismatched_destination_is_rejected_without_clobber(self) -> None:
        root, destination = self._run_race(RACED)
        self.assertEqual(destination.read_bytes(), RACED)
        self.assertEqual(list(root.rglob(".oc-materialize-*")), [])

    def test_concurrent_exact_destination_is_accepted_without_clobber(self) -> None:
        root, destination = self._run_race(BYTES)
        self.assertEqual(destination.read_bytes(), BYTES)
        self.assertEqual(list(root.rglob(".oc-materialize-*")), [])


if __name__ == "__main__":
    unittest.main()
