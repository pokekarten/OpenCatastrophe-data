# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.climk_event_identity_diagnostics import diagnose

class IdentityTest(unittest.TestCase):
    def test_aliases_and_date_conflicts_are_not_merged(self):
        r=diagnose([{'provider_name':n,'provider_date_label':d} for n,d in
                    [('Storm','20000101'),('storm','20000102'),('Other','20000102')]])
        self.assertEqual(len(r['same_name_multiple_dates']),1)
        self.assertEqual(len(r['same_date_multiple_names']),1)
        self.assertEqual(r['automatic_physical_event_merges'],0)
