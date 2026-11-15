# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.eiopa_country_coverage import compare

class CoverageTest(unittest.TestCase):
    def test_overlap_does_not_authorize_ratio(self):
        exposure=[{'Peril':'Windstorm','As of date':2020,'Country':'Germany','NUTS':'DE11'}]
        losses=[{'Category':'Storm','Country':c} for c in ['DE','CH','Other']]
        r={x['loss_country_label']:x for x in compare(exposure,losses)}
        self.assertEqual(r['DE']['exposure_rows'],1)
        self.assertFalse(r['DE']['loss_ratio_computable'])
        self.assertEqual(r['CH']['coverage_status'],'no_matching_country')
        self.assertIsNone(r['Other']['mapped_exposure_country'])
        with self.assertRaises(ValueError):compare(exposure*2,losses)
