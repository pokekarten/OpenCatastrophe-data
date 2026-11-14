# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Dependency-free synthetic HURDAT2 structural and negative tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.profile_hurdat2_atlantic_original_v0 import (
    Hurdat2StructureError,
    profile_original,
)

ROOT = Path(__file__).resolve().parents[1]


def original(fixes: list[str] | None = None, header: str | None = None) -> bytes:
    if fixes is None:
        fixes = [
            "20220919, 0000, , TS, 18.4N, 68.5W, 40, 1000, " + ", ".join(["-999"] * 12) + ", -999,",
            "20220919, 0600, L, HU, 19.0N, 69.0W, 75, 975, " + ", ".join(["50"] * 12) + ", 20,",
        ]
    if header is None:
        header = f"AL092022, SYNTHETIC, {len(fixes)},"
    return ("\n".join([header, *fixes]) + "\n").encode("ascii")


class Hurdat2OriginalProfileTests(unittest.TestCase):
    def test_receipt_tracks_original_bytes_and_no_download(self):
        raw = original()
        result = profile_original(raw)
        self.assertEqual(result["original_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["original_bytes"], len(raw))
        self.assertEqual((result["storm_count"], result["track_fix_count"]), (1, 2))
        self.assertIn("syntactic_preflight_only", result["verification"])
        self.assertEqual(result["first_fix_utc"], "2022-09-19T00:00:00+00:00")
        self.assertNotIn("model_use", result)

    def test_older_twenty_column_fix_is_supported_without_imputation(self):
        fields = original().decode().splitlines()[1].split(",")
        raw = original([",".join(fields[:20]) + ","])
        self.assertEqual(profile_original(raw)["track_fix_count"], 1)

    def test_rejects_corrupt_or_ambiguous_provider_rows(self):
        first = original().decode().splitlines()[1]
        second = original().decode().splitlines()[2]
        mutations = {
            "missing comma": first.replace("18.4N, 68.5W", "18.4N 68.5W"),
            "missing hemisphere": first.replace("18.4N", "18.4"),
            "unwrapped longitude": first.replace("68.5W", "358.0W"),
            "invalid latitude": first.replace("18.4N", "91.0N"),
            "invalid date": first.replace("20220919", "20221319"),
            "bad status": first.replace(", TS,", ", ZZ,"),
            "non synoptic without marker": first.replace("0000", "0300"),
            "negative radius": first.replace(", -999,", ", -4,", 1),
            "wrong field count": ",".join(first.split(",")[:-4]),
        }
        for name, changed in mutations.items():
            with self.subTest(name=name), self.assertRaises(Hurdat2StructureError):
                profile_original(original([changed]))
        with self.assertRaisesRegex(Hurdat2StructureError, "duplicate/out-of-order"):
            profile_original(original([first, first]))
        with self.assertRaisesRegex(Hurdat2StructureError, "truncated"):
            profile_original(original([first], header="AL092022, SYNTHETIC, 2,"))
        with self.assertRaisesRegex(Hurdat2StructureError, "invalid Atlantic storm header"):
            profile_original(original([first], header="EP092022, SYNTHETIC, 1,"))
        with self.assertRaisesRegex(Hurdat2StructureError, "duplicate storm id"):
            profile_original(original([first])+original([second]))

    def test_missing_bytes_oversize_non_ascii_and_blank_line_fail(self):
        for raw in [b"", b"x" * (12 * 1024 * 1024 + 1), b"\xff", original() + b"\n"]:
            with self.subTest(size=len(raw)), self.assertRaises(Hurdat2StructureError):
                profile_original(raw)

    def test_cli_emits_receipt_without_echoing_raw_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "synthetic-source.txt"
            source.write_bytes(original())
            result = subprocess.run(
                [sys.executable, "-m", "scripts.profile_hurdat2_atlantic_original_v0", "--input", str(source)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["storm_count"], 1)
            self.assertNotIn("SYNTHETIC", result.stdout)
            self.assertNotIn("18.4N", result.stdout)


if __name__ == "__main__":
    unittest.main()
