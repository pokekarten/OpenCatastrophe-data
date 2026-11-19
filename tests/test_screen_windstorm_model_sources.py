# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import json
import tempfile
import unittest
from pathlib import Path
from scripts.screen_windstorm_model_sources import build, classify

class SourceScreenTest(unittest.TestCase):
    def test_buildings_without_windstorm_are_included(self):
        result = classify({'categories': ['buildings']})
        self.assertIn('exposure', result['component_matches'])
        self.assertFalse(result['scientifically_admitted_by_screen'])

    def test_tropical_response_is_not_automatically_transferred(self):
        result = classify({'categories': ['tropical_cyclone', 'vulnerability']})
        self.assertTrue(result['tropical_cyclone_transfer_review_required'])
        self.assertFalse(result['scientifically_admitted_by_screen'])

    def test_all_records_preserved_even_without_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'landscape').mkdir()
            (root / 'landscape/a.json').write_text(json.dumps({'entries': [
                {'candidate_id': 'same', 'categories': ['buildings']},
                {'candidate_id': 'same', 'categories': ['unrecognised']},
            ]}))
            result = build(root)
            self.assertEqual(result['record_count'], 2)
            self.assertEqual(result['matched_record_count'], 1)
            self.assertEqual(result['records'][1]['entry_index'], 1)
            self.assertEqual(len(result['files'][0]['sha256']), 64)
            self.assertFalse(result['records'][1]['download_verified_by_screen'])

    def test_malformed_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'landscape').mkdir()
            (root / 'landscape/a.json').write_text('{"entries":[null]}')
            with self.assertRaises(ValueError):
                build(root)
