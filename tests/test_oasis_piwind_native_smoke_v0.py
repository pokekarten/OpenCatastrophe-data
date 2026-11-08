# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Independent synthetic-only tests; never invoke the native Oasis CLI."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from research_runners.oasis_piwind_native_smoke_v0 import (
    EXPECTED_FILES,
    MODEL_COMMIT,
    PiWindNativeSmokeError,
    attest_output_csv,
    blob_sha256,
    inspect_piwind_outputs,
    main,
    native_run,
    verify_model_checkout,
)


def fake_outputs(root: Path) -> Path:
    output = root / "ProgOasis-fictional" / "output"
    output.mkdir(parents=True)
    for file in EXPECTED_FILES:
        (output / file).write_text(
            "SummaryId,SampleType,MeanLoss\n1,2,0.0\n",
            encoding="utf-8",
        )
    return output


class NativePiWindReceiptTests(unittest.TestCase):
    def test_contract_only_requires_six_core_gul_il_ri_files(self) -> None:
        self.assertEqual(len(EXPECTED_FILES), 6)
        self.assertEqual(
            set(EXPECTED_FILES),
            {"gul_S1_palt.csv", "gul_S1_psept.csv",
             "il_S1_palt.csv", "il_S1_psept.csv",
             "ri_S1_palt.csv", "ri_S1_psept.csv"},
        )
        self.assertEqual(len(MODEL_COMMIT), 40)

    def test_synthetic_output_sha_and_counts(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            output = fake_outputs(root)
            report = inspect_piwind_outputs(root)
            self.assertEqual(set(report), set(EXPECTED_FILES))
            for file in EXPECTED_FILES:
                raw = (output / file).read_bytes()
                self.assertEqual(report[file]["data_rows"], 1)
                self.assertEqual(report[file]["bytes"], len(raw))
                self.assertEqual(report[file]["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(blob_sha256(b"unit-test"), hashlib.sha256(b"unit-test").hexdigest())

    def test_absent_stream_fails_closed(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            output = fake_outputs(root)
            (output / "ri_S1_palt.csv").unlink()
            with self.assertRaisesRegex(PiWindNativeSmokeError, "exactly one"):
                inspect_piwind_outputs(root)

    def test_empty_csv_does_not_attest_native_engine(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            output = fake_outputs(root)
            (output / "il_S1_psept.csv").write_bytes(b"")
            with self.assertRaisesRegex(PiWindNativeSmokeError, "invalid size"):
                inspect_piwind_outputs(root)

    def test_header_only_and_missing_columns_fail(self) -> None:
        with TemporaryDirectory() as d:
            path = Path(d) / "bad.csv"
            path.write_text("SummaryId,SampleType,MeanLoss\n", encoding="utf-8")
            with self.assertRaisesRegex(PiWindNativeSmokeError, "empty or has no valid header"):
                attest_output_csv(path)
            path.write_text("SummaryId,SampleType\n1,2\n", encoding="utf-8")
            with self.assertRaisesRegex(PiWindNativeSmokeError, "inconsistent row fields"):
                attest_output_csv(path)

    def test_inconsistent_csv_body_fails(self) -> None:
        with TemporaryDirectory() as d:
            path = Path(d) / "inconsistent.csv"
            path.write_text("SummaryId,SampleType,MeanLoss\n1,2\n", encoding="utf-8")
            with self.assertRaisesRegex(PiWindNativeSmokeError, "inconsistent row fields"):
                attest_output_csv(path)

    def test_ambiguous_result_roots_fail(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            fake_outputs(root / "run-a")
            fake_outputs(root / "run-b")
            with self.assertRaisesRegex(PiWindNativeSmokeError, "exactly one"):
                inspect_piwind_outputs(root)

    def test_missing_model_checkout_fails_without_using_network_or_cli(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaisesRegex(PiWindNativeSmokeError, "verify model git commit"):
                verify_model_checkout(root)
            with self.assertRaisesRegex(PiWindNativeSmokeError, "verify model git commit"):
                native_run(root, timeout_seconds=600)

    def test_invalid_timeout_blocks_before_running(self) -> None:
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(PiWindNativeSmokeError, "runtime limit"):
                native_run(Path(d), timeout_seconds=10)

    def test_dangling_native_output_and_log_symlinks_block_before_cli(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            model = root / "model"
            model.mkdir()
            with (
                patch("research_runners.oasis_piwind_native_smoke_v0.verify_model_checkout", return_value=MODEL_COMMIT),
                patch("research_runners.oasis_piwind_native_smoke_v0.metadata.version", return_value="2.5.8"),
                patch("research_runners.oasis_piwind_native_smoke_v0.shutil.which", return_value="/not-called"),
                patch("research_runners.oasis_piwind_native_smoke_v0.subprocess.run", side_effect=AssertionError("native CLI invoked")),
            ):
                output = model / "runs"
                output.symlink_to(root / "missing-runs", target_is_directory=True)
                with self.assertRaisesRegex(PiWindNativeSmokeError, "already contains run outputs"):
                    native_run(model, timeout_seconds=600)
                output.unlink()
                log = root / "native-piwind-output.log"
                log.symlink_to(root / "missing-log")
                with self.assertRaisesRegex(PiWindNativeSmokeError, "overwrite existing native log"):
                    native_run(model, timeout_seconds=600)
                self.assertFalse((root / "missing-log").exists())
                log.unlink()
                log.write_text("untouched", encoding="utf-8")
                with self.assertRaisesRegex(PiWindNativeSmokeError, "overwrite existing native log"):
                    native_run(model, timeout_seconds=600)
                self.assertEqual(log.read_text(encoding="utf-8"), "untouched")

    def test_dangling_receipt_symlink_refused_before_native_run(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            receipt = root / "receipt.json"
            receipt.symlink_to(root / "missing-receipt")
            with patch("research_runners.oasis_piwind_native_smoke_v0.native_run", side_effect=AssertionError("native run invoked")):
                self.assertEqual(main([str(root), "--receipt", str(receipt)]), 2)
            self.assertFalse((root / "missing-receipt").exists())

    def test_fresh_receipt_exclusive_creation_and_existing_file_preserved(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            receipt = root / "receipt.json"
            with patch("research_runners.oasis_piwind_native_smoke_v0.native_run", return_value={"status": "fictional"}):
                self.assertEqual(main([str(root), "--receipt", str(receipt)]), 0)
            self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["status"], "fictional")
            with patch("research_runners.oasis_piwind_native_smoke_v0.native_run", side_effect=AssertionError("native run invoked")):
                self.assertEqual(main([str(root), "--receipt", str(receipt)]), 2)
            self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["status"], "fictional")


if __name__ == "__main__":
    unittest.main()
