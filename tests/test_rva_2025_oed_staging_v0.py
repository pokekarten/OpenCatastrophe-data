# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
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
from rva_2025_oed_staging_v0 import allocate_sample, export, hypothetical_value, StagingError, NATIONAL, GWP_CENTS


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

    def test_nonuniform_age_archetype_sensitivity_is_explicit(self):
        self.assertEqual(hypothetical_value(450000,0,'SYN-01001-01-000001','flat'),(450000,'flat_one_building_per_contract'))
        with self.assertRaises(StagingError):
            hypothetical_value(450000,10,'SYN-01001-11-000001','age_archetype')
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'heterogeneous'
            receipt=export(fixture(),out,'PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY',
                           'central',10000,{'test':'00'*32},'age_archetype')
            self.assertEqual(receipt['fictional_valuation_pattern'],'age_archetype')
            self.assertEqual(sum(receipt['fictional_exported_archetype_counts'].values()),10000)
            self.assertGreater(len(receipt['fictional_exported_archetype_counts']),2)
            with (out/'location.csv').open(encoding='utf8',newline='') as f:
                loc=list(csv.DictReader(f))
            with (out/'cohort_receipt.csv').open(encoding='utf8',newline='') as f:
                cohort=list(csv.DictReader(f))
            tiv=sum(int(r['BuildingTIV']) for r in loc)
            self.assertEqual(tiv,receipt['exported_fictional_building_tiv_eur'])
            self.assertEqual(sum(int(r['FictionalExportedBuildingTIVEUR']) for r in cohort),tiv)
            self.assertGreater(len({int(r['BuildingTIV']) for r in loc}),15)
            self.assertNotEqual(tiv,4500000000)
            self.assertFalse(receipt['germany_peril_model_lookup_allowed'])

    def test_duplicate_and_malformed_cohorts_rejected_before_output(self):
        cells = fixture()
        defects = {
            'duplicate county/age': dict(cells[1], ags=cells[0]['ags'], age=cells[0]['age']),
            'non-numeric AGS': dict(cells[1], ags='00x01'),
            'non-ASCII AGS': dict(cells[1], ags='００００１'),
            'invalid age': dict(cells[1], age=10),
            'invalid physical count': dict(cells[1], published_2022=-1),
        }
        for name, replacement in defects.items():
            with self.subTest(defect=name), tempfile.TemporaryDirectory() as td:
                bad = list(cells)
                bad[1] = replacement  # unchanged national count, but invalid OED identity
                out = Path(td) / 'must_not_exist'
                with self.assertRaises(StagingError):
                    export(bad, out, 'PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY',
                           'central', 10000, {'test': '00'*32})
                self.assertFalse(out.exists())

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
