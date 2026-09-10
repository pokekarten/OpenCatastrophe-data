from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reserve_underwriting_clrd_empirical_probe.py"

spec = importlib.util.spec_from_file_location("clrd_probe", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class ClrdEmpiricalProbeBasisTests(unittest.TestCase):
    def _write_csv(self, rows: list[str]) -> Path:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name) / "clrd.csv"
        header = (
            "GRCODE,GRNAME,AccidentYear,DevelopmentYear,"
            "IncurLoss,EarnedPremDIR,EarnedPremNet,LOB\n"
        )
        path.write_text(header + "".join(rows), encoding="utf-8")
        return path

    def test_load_rows_requires_and_preserves_net_premium(self):
        path = self._write_csv(
            ["337,Example,1988,1988,100,120,80,wkcomp\n"]
        )
        rows, names = mod.load_rows(path, "wkcomp", (337,))
        self.assertEqual(names[337], "Example")
        self.assertEqual(
            rows[(337, 1988, 1988)],
            {"incurred": 100.0, "prem_net": 80.0, "prem_dir": 120.0},
        )

    def test_duplicate_coordinate_fails_closed(self):
        path = self._write_csv(
            [
                "337,Example,1988,1988,100,120,80,wkcomp\n",
                "337,Example,1988,1988,101,120,80,wkcomp\n",
            ]
        )
        with self.assertRaisesRegex(ValueError, "duplicate CLRD coordinate"):
            mod.load_rows(path, "wkcomp", (337,))

    def test_primary_panel_uses_net_net_basis_and_keeps_direct_mismatch_explicit(self):
        rows = {
            (337, 1988, 1988): {
                "incurred": 100.0,
                "prem_net": 80.0,
                "prem_dir": 100.0,
            },
            (337, 1988, 1989): {
                "incurred": 110.0,
                "prem_net": 80.0,
                "prem_dir": 100.0,
            },
            (337, 1989, 1989): {
                "incurred": 50.0,
                "prem_net": 40.0,
                "prem_dir": 100.0,
            },
        }
        panel = mod.build_panel(rows, {337: "Example"}, (337,), 1988, 1989)
        self.assertEqual(len(panel), 1)
        row = panel[0]
        self.assertEqual(row["uw"], 1.25)
        self.assertEqual(row["uw_direct_mismatched"], 0.5)
        self.assertEqual(row["legacy_incurred_norm"], 0.1)
        self.assertEqual(row["legacy_premium_norm"], 0.125)
        self.assertEqual(row["legacy_direct_premium_norm_mismatched"], 0.1)


if __name__ == "__main__":
    unittest.main()
