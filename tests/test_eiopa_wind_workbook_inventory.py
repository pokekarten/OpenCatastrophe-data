# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import tempfile
import unittest
from pathlib import Path
from research_runners.eiopa_wind_workbook_inventory import inventory

class WorkbookTest(unittest.TestCase):
    def test_formatting_rows_and_trimmed_labels(self):
        import openpyxl
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'synthetic.xlsx'
            w=openpyxl.Workbook();s=w.active
            s.append(['Event ','LoB']);s.append(['test','ALL']);s.append(['test','RES'])
            s.cell(100,5).number_format='0.00';w.save(p);w.close()
            r=inventory(p)['sheets'][0]
            self.assertEqual(r['nonempty_data_rows'],2)
            self.assertEqual(r['last_nonempty_row'],3)
            self.assertIn({'field':'Event','label':'test','rows':2},r['category_counts'])
