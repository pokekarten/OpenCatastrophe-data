from __future__ import annotations
import csv
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'reserve_underwriting_realised_cdr_panel.py'
spec = importlib.util.spec_from_file_location('cdr_panel', SCRIPT)
mod = importlib.util.module_from_spec(spec); assert spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def synthetic_cells():
    cells = {}
    # Two companies, AY 2000..2005, calendar through 2005. Paid follows
    # deterministic age factors 2.0, 1.5; incurred/premium define UW separately.
    for g in (1, 2):
        for ay in range(2000, 2006):
            base = (100 + 10*(ay-2000)) * g
            paid_by_age = {1: base, 2: base*2.0, 3: base*3.0}
            for age, paid in paid_by_age.items():
                cal = ay + age - 1
                if cal > 2005:
                    continue
                cells[(g, ay, cal)] = mod.Cell(
                    g, f'C{g}', 'x', ay, cal,
                    incurred=(120 + 5*(ay-2000))*g,
                    paid=paid,
                    prem_net=200*g,
                )
    return cells

class CdrPanelTests(unittest.TestCase):
    def test_volume_factors_use_cutoff_only(self):
        cells = synthetic_cells()
        f = mod.fit_factors(cells, 1, 2004, 3, 'volume')
        self.assertAlmostEqual(f[1], 2.0)
        self.assertAlmostEqual(f[2], 1.5)
        # Mutate a future 2005 cell; opening-2004 factors must not change.
        old = cells[(1, 2003, 2005)]
        cells[(1, 2003, 2005)] = mod.Cell(old.grcode, old.grname, old.lob, old.ay, old.calendar, old.incurred, old.paid*9, old.prem_net)
        f2 = mod.fit_factors(cells, 1, 2004, 3, 'volume')
        self.assertEqual(f, f2)

    def test_same_opening_population_and_cdr_identity(self):
        row = mod.build_row(synthetic_cells(), 1, 'x', 2005, 2000, 3, 'volume')
        self.assertEqual(row['opening_ays'], [2003, 2004])
        self.assertAlmostEqual(
            row['cdr'], row['paid_during_year'] + row['closing_reserve'] - row['opening_reserve']
        )
        self.assertAlmostEqual(row['cdr'], row['closing_ultimate'] - row['opening_ultimate'])

    def test_refit_changes_cdr_when_new_diagonal_changes(self):
        cells = synthetic_cells()
        base = mod.build_row(cells, 1, 'x', 2005, 2000, 3, 'volume')['cdr']
        # Perturb an age2 closing-diagonal paid value. It changes the closing
        # factor fit and cash emergence but not the opening fit.
        old = cells[(1, 2004, 2005)]
        cells[(1, 2004, 2005)] = mod.Cell(old.grcode, old.grname, old.lob, old.ay, old.calendar, old.incurred, old.paid*1.2, old.prem_net)
        changed = mod.build_row(cells, 1, 'x', 2005, 2000, 3, 'volume')['cdr']
        self.assertNotEqual(base, changed)

    def test_volume_and_median_are_distinct_challengers(self):
        cells = synthetic_cells()
        # Perturb one development ratio to make weighting matter.
        old = cells[(1, 2002, 2003)]
        cells[(1, 2002, 2003)] = mod.Cell(old.grcode, old.grname, old.ay, old.calendar, old.incurred, old.paid*1.25, old.prem_net)
        fv = mod.fit_factors(cells, 1, 2004, 3, 'volume')
        fm = mod.fit_factors(cells, 1, 2004, 3, 'median')
        self.assertNotEqual(fv[1], fm[1])

    def test_preflight_panel_schema(self):
        cells = synthetic_cells()
        rows = mod.build_panel(cells, 'x', (1,2), 2000, 2005, 3, 'volume')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'panel.csv'; mod.write_preflight_panel(p, rows)
            with p.open() as h:
                r=csv.DictReader(h)
                self.assertEqual(r.fieldnames, ['company','lob','year','uw','cdr','shared_driver'])
                self.assertEqual(len(list(r)), len(rows))

    def test_source_identity_gate_rejects_arbitrary_file(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.csv'; p.write_text('x\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'source identity mismatch'):
                mod.verify_source(p)

if __name__ == '__main__': unittest.main()
