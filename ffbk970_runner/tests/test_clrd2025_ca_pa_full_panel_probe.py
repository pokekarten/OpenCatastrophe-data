import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "clrd2025_ca_pa_full_panel_probe.py"
spec = importlib.util.spec_from_file_location("probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)


def write_fixture(path: Path) -> str:
    fields = [
        "GRCODE",
        "GRNAME",
        "AccidentYear",
        "DevelopmentYear",
        "DevelopmentLag",
        "IncurredLosses",
        "CumPaidLoss",
        "BulkLoss",
        "EarnedPremDIR",
        "EarnedPremCeded",
        "EarnedPremNet",
        "Single",
        "PostedReserves2007",
        "LOB",
    ]
    rows = []
    for company_i, grcode in enumerate(("101", "202", "303", "404"), start=1):
        for lob_i, lob in enumerate(("comauto", "ppauto"), start=1):
            for ay_i, ay in enumerate(range(2000, 2005), start=1):
                value = 100.0 + company_i * 30 + lob_i * 17 + ay_i * 11
                for lag in range(1, 5):
                    if lag > 1:
                        rate = (
                            1.02
                            + 0.012 * company_i
                            + 0.007 * lob_i
                            + 0.003 * ay_i
                            + 0.004 * lag
                            + (
                                0.002 * company_i * ay_i
                                if lob == "comauto"
                                else -0.001 * company_i * ay_i
                            )
                        )
                        value *= rate
                    rows.append(
                        {
                            "GRCODE": grcode,
                            "GRNAME": f"Company {grcode}",
                            "AccidentYear": ay,
                            "DevelopmentYear": ay + lag - 1,
                            "DevelopmentLag": lag,
                            "IncurredLosses": value,
                            "CumPaidLoss": value,
                            "BulkLoss": 0,
                            "EarnedPremDIR": 1,
                            "EarnedPremCeded": 0,
                            "EarnedPremNet": 1,
                            "Single": 0,
                            "PostedReserves2007": 0,
                            "LOB": lob,
                        }
                    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)
    return probe.git_blob_sha1(path.read_bytes())


class ProbeTests(unittest.TestCase):
    def test_git_blob_gate_rejects_wrong_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            path.write_text("not the pinned source\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source Git blob mismatch"):
                probe.verify_source(path)

    def test_full_pipeline_on_synthetic_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.csv"
            blob = write_fixture(path)
            result = probe.analyze(path, expected_blob=blob)
            self.assertEqual(result["source"]["git_blob"], blob)
            self.assertEqual(result["scope"]["companies_in_source_two_lobs"], 4)
            self.assertEqual(result["scope"]["max_adjacent_link_start"], 3)
            same = result["pooled"]["same_step"]
            self.assertGreater(same["raw"]["n_records"], 0)
            self.assertGreater(same["centered"]["n_records"], 0)
            self.assertGreater(same["normalized"]["n_records"], 0)
            self.assertIsNotNone(same["raw"]["pearson"])
            self.assertIsNotNone(same["centered"]["pearson"])
            self.assertIsNotNone(same["normalized"]["pearson"])
            self.assertEqual(same["leave_one_company_centered"]["n"], 4)

    def test_zero_and_missing_paid_cells_fail_closed_per_pair_not_globally(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.csv"
            write_fixture(path)
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                if (
                    row["GRCODE"] == "101"
                    and row["LOB"] == "ppauto"
                    and row["AccidentYear"] == "2000"
                    and row["DevelopmentLag"] == "2"
                ):
                    row["CumPaidLoss"] = "0"
            fields = rows[0].keys()
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\r\n")
                writer.writeheader()
                writer.writerows(rows)
            blob = probe.git_blob_sha1(path.read_bytes())
            result = probe.analyze(path, expected_blob=blob)
            link1 = result["pair_specific"]["same_step"]["1"]["raw"]
            link2 = result["pair_specific"]["same_step"]["2"]["raw"]
            self.assertEqual(link1["n_companies"], 4)
            self.assertEqual(link2["n_companies"], 4)
            self.assertEqual(link1["n_records"], 19)
            self.assertEqual(link2["n_records"], 19)


if __name__ == "__main__":
    unittest.main()
