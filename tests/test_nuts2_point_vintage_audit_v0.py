# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import copy
import json
import unittest
from nuts2_point_vintage_audit_v0 import audit, VintageError


def payload(codes=('DE21', 'FRJ1'), null_area=False):
    return {
        'type': 'FeatureCollection', 'name': 'nutspt_2',
        'crs': {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}},
        'features': [
            {'type': 'Feature', 'properties': {'id': code, 'na': 'SYNTHETIC', 'ar': None if null_area else 100},
             'geometry': {'type': 'Point', 'coordinates': [11.0, 48.0]}}
            for code in codes
        ]
    }


def blob(x):
    return json.dumps(x, sort_keys=True).encode()


class AuditTest(unittest.TestCase):
    def test_code_drift_and_flags(self):
        r = audit(blob(payload()), blob(payload(('DE21', 'FRK1'), True)), '2021', '2024')
        self.assertEqual((r['baseline_nuts2_count'], r['successor_nuts2_count'], r['common_code_count']), (2,2,1))
        self.assertEqual(r['retired_codes'], ['FRJ1'])
        self.assertEqual(r['new_codes'], ['FRK1'])
        self.assertEqual(r['area_metadata_null_counts'], {'2021': 0, '2024': 2})
        self.assertFalse(r['unchanged_code_proves_boundary_equivalence'])
        self.assertFalse(r['real_exposure_or_losses_calculated'])
    def test_deterministic(self):
        a, b = blob(payload()), blob(payload(('DE21',)))
        self.assertEqual(audit(a,b,'2021','2024'), audit(a,b,'2021','2024'))
    def test_wrong_vintage_block(self):
        with self.assertRaises(VintageError):audit(blob(payload()),blob(payload()),'2020','2024')
    def test_duplicate_codes_blocked(self):
        with self.assertRaises(VintageError):audit(blob(payload(('DE21','DE21'))),blob(payload()),'2021','2024')
    def test_bad_crs_blocked(self):
        a=payload();a['crs']['properties']['name']='EPSG:3857'
        with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_no_geometry_polygons(self):
        a=payload();a['features'][0]['geometry']={'type':'Polygon','coordinates':[]}
        with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_missing_point_blocked(self):
        a=payload();a['features'][0]['geometry']['coordinates']=[10.0]
        with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_invalid_coordinates(self):
        for v in [float('nan'), float('inf'), True, 195, '10']:
            with self.subTest(v=v):
                a=payload();a['features'][0]['geometry']['coordinates'][0]=v
                with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_invalid_area(self):
        for v in [-1, float('inf'), True, '100']:
            with self.subTest(v=v):
                a=payload();a['features'][0]['properties']['ar']=v
                with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_missing_label(self):
        a=payload();a['features'][0]['properties']['na']=''
        with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_invalid_payload(self):
        with self.assertRaises(VintageError):audit(b'foo',blob(payload()),'2021','2024')
    def test_region_code(self):
        a=payload(('de21',))
        with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_missing_region_records(self):
        a=payload();a['features']=[]
        with self.assertRaises(VintageError):audit(blob(a),blob(payload()),'2021','2024')
    def test_live_dataset_null_areas_are_supported(self):
        r=audit(blob(payload(null_area=True)),blob(payload(null_area=True)),'2021','2024')
        self.assertEqual(r['area_metadata_null_counts']['2021'],2)

if __name__=='__main__':unittest.main()
