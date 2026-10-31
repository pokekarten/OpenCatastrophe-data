# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic fail-closed GHSL candidate tests with no provider raster bytes."""
import json
import tempfile
import unittest
from pathlib import Path
from research_runners.check_ghsl_source_metadata_v0 import test_current_catalogue

def sample(id, unit):
    return {'candidate_id':id,'resolution_or_granularity':'global '+unit+' raster',
            'admission_status':'not_admitted','rights_review_status':'not_reviewed',
            'scientific_review_status':'not_reviewed',
            'authoritative_url':'https://example.org/data',
            'note':'Not an insured property value'}

class SourceMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/'landscape').mkdir()
        self.a=sample('ec-jrc.ghsl.ghs-built-s.r2023a','m2')
        self.b=sample('ec-jrc.ghsl.ghs-built-v.r2023a','m3')
    def tearDown(self):
        self.tmp.cleanup()
    def run_case(self):
        for name,record in [('s',self.a),('v',self.b)]:
            (self.root/f'landscape/sources-ghsl-built-{name}-2026.json').write_text(
                json.dumps({'entries':[record]}))
        return test_current_catalogue(self.root)
    def test_valid_pair(self):
        self.assertEqual(self.run_case()['candidate_count'],2)
    def test_wrong_units(self):
        self.b['resolution_or_granularity']='m2'
        with self.assertRaises(ValueError):self.run_case()
    def test_unreviewed_status_cannot_be_promoted(self):
        self.a['admission_status']='approved'
        with self.assertRaises(ValueError):self.run_case()
    def test_duplicate_identity(self):
        self.b['candidate_id']=self.a['candidate_id']
        with self.assertRaises(ValueError):self.run_case()
    def test_source_url(self):
        self.b['authoritative_url']='invalid'
        with self.assertRaises(ValueError):self.run_case()

if __name__=='__main__':unittest.main()
