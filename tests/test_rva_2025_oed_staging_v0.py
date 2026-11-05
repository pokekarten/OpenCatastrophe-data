# SPDX-License-Identifier: Apache-2.0
"""Offline exporter-only synthetic tests; original 400-Kreis gate is upstream."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research_runners'))
from rva_2025_oed_staging_v0 import allocate_sample, export, StagingError, NATIONAL, GWP_CENTS


def fixture():
    cells=[]
    base,rem=divmod(NATIONAL,4000)
    for i in range(400):
        for j in range(10):
            k=i*10+j
            cells.append({'ags':f'{i:05d}','age':j,'count':base+(k<rem),'published_2022':1000+j})
    return cells

class TestStage(unittest.TestCase):
    def test_conserves_all_4000_cells_and_is_deterministic(self):
        cells=fixture()
        a=allocate_sample(cells,10000)
        self.assertEqual(a,allocate_sample(cells,10000))
        self.assertEqual(len(a),4000)
        self.assertEqual(sum(a),10000)
        self.assertTrue(all(x<=c['count'] for x,c in zip(a,cells)))
        self.assertEqual(sum(allocate_sample(cells,0)),NATIONAL)

    def test_original_controls_never_inferred_from_sample(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'test'
            rec=export(fixture(),out,'PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY','central',10000,{'test':'00'*32})
            self.assertEqual(rec['exported_fictional_locations_and_policies'],10000)
            self.assertEqual(rec['exported_fictional_building_tiv_eur'],4_500_000_000)
            self.assertEqual(rec['company_2025_national_annual_building_gwp_eur_cents_observed'],GWP_CENTS)
            self.assertFalse(rec['germany_peril_model_lookup_allowed'])
            self.assertFalse(rec['full_fictional_2025_book_exported'])
            self.assertFalse(rec['physical_site_coordinates_observed'])
            with (out/'location.csv').open(newline='',encoding='utf8') as f:
                loc=list(csv.DictReader(f))
            with (out/'account.csv').open(newline='',encoding='utf8') as f:
                acc=list(csv.DictReader(f))
            with (out/'cohort_receipt.csv').open(newline='',encoding='utf8') as f:
                cells=list(csv.DictReader(f))
            self.assertEqual((len(loc),len(acc),len(cells)),(10000,10000,4000))
            self.assertEqual(len({r['LocNumber'] for r in loc}),10000)
            self.assertEqual({r['AccNumber'] for r in acc},{r['AccNumber'] for r in loc})
            self.assertEqual({r['Latitude'] for r in loc},{''})
            self.assertEqual({r['Longitude'] for r in loc},{''})
            self.assertEqual({r['LocPerilsCovered'] for r in loc},{'WW2'})
            self.assertEqual({r['BuildingTIV'] for r in loc},{'450000'})
            self.assertEqual(sum(int(r['Fictional2025FullContractCount']) for r in cells),NATIONAL)
            self.assertEqual(sum(int(r['Fictional2025ExportedContractCount']) for r in cells),10000)
            for name,sha in rec['output_sha256'].items():
                self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),sha)
            self.assertEqual(json.loads((out/'manifest.json').read_text())['status'],'NOT_GEOLOCATED_NOT_MODEL_READY')

    def test_fail_closed(self):
        cells=fixture()
        for size in (-1,NATIONAL+1):
            with self.assertRaises(StagingError): allocate_sample(cells,size)
        bad=list(cells);bad[0]=dict(bad[0],count=-1)
        with self.assertRaises(StagingError):allocate_sample(bad,100)
        bad=list(cells);bad[0]=dict(bad[0],count=1)
        with self.assertRaises(StagingError):allocate_sample(bad,100)
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'made';out.mkdir()
            with self.assertRaises(StagingError):export(cells,out,'PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY','central',100,{'test':'00'*32})
            with self.assertRaises(StagingError):export(cells,Path(td)/'notmade','PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY','unknown',100,{'test':'00'*32})
            self.assertFalse((Path(td)/'notmade').exists())

if __name__=='__main__': unittest.main()
