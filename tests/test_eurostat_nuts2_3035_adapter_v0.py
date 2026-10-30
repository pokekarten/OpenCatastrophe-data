# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic source-fixture tests; no Eurostat geometry bytes in Git."""
import copy
import json
import unittest
from research_runners.eurostat_nuts2_3035_adapter_v0 import AdapterError, convert
from research_runners.regional_wind_footprint_overlay_v0 import overlay


def box(x1, y1, x2, y2):
    return {'type': 'Polygon', 'coordinates': [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]]}


def geo(codes=('DE21', 'FR10'), projected=True):
    # Geographically synthetic rectangles but plausible metre-scale positions.
    return {'type':'FeatureCollection', 'features': [
        {'type':'Feature', 'properties':{'id':code, 'na':'Synthetic region'},
         'geometry':box(4300000+100000*i, 2600000, 4350000+100000*i, 2650000)
         if projected else box(10+i, 45, 11+i, 46)}
        for i, code in enumerate(codes)
    ]}


def encode(x):
    return json.dumps(x, sort_keys=True).encode()


class ConvertTest(unittest.TestCase):
    def test_normalizes_to_overlay_schema(self):
        out, receipt = convert(encode(geo()), encode(geo(projected=False)), '2021', ('DE', 'FR'))
        self.assertEqual(set(out), {'schema_version','nuts_version','crs','features','source_sha256'})
        self.assertEqual(out['crs'], 'EPSG:3035')
        self.assertEqual(receipt['selected_regions_count'],2)
        self.assertEqual(receipt['selected_source_area_km2'],5000)
        self.assertEqual(len(out['features']),2)
        self.assertFalse(receipt['real_insurer_exposure_inferred'])
    def test_select_one_country(self):
        a,b=convert(encode(geo()),encode(geo(projected=False)),'2024',('DE',))
        self.assertEqual([f['nuts2'] for f in a['features']],['DE21'])
        self.assertEqual(b['countries'],['DE'])
        self.assertTrue(b['other_countries_not_audited'])
    def test_reproducible(self):
        p=encode(geo());q=encode(geo(projected=False))
        self.assertEqual(convert(p,q,'2021',('DE',)),convert(p,q,'2021',('DE',)))
    def test_2021_3035_missing_azores_must_fail(self):
        with self.assertRaisesRegex(AdapterError,'missing='):
            convert(encode(geo(('PT11',))),encode(geo(('PT11','PT20'),False)),'2021',('PT',))
    def test_2021_3035_extra_canary_must_fail(self):
        with self.assertRaisesRegex(AdapterError,'unexpected='):
            convert(encode(geo(('ES70','ES11'))),encode(geo(('ES11',),False)),'2021',('ES',))
    def test_bad_geometry_point(self):
        p=geo();p['features'][0]['geometry']={'type':'Point','coordinates':[11,42]}
        with self.assertRaises(AdapterError):convert(encode(p),encode(geo(projected=False)),'2021',('DE',))
    def test_bad_geometry_ring(self):
        p=geo();p['features'][0]['geometry']= {'type':'Polygon','coordinates':[[[4300000,2600000],[4350000,2650000],[4350000,2600000],[4300000,2650000],[4300000,2600000]]]}
        with self.assertRaises(AdapterError):convert(encode(p),encode(geo(projected=False)),'2021',('DE',))
    def test_no_false_unprojected_source(self):
        with self.assertRaisesRegex(AdapterError,'unprojected'):
            convert(encode(geo(projected=False)), encode(geo(projected=False)), '2021', ('DE',))
    def test_duplicate_code(self):
        p=geo(('DE21','DE21'))
        with self.assertRaises(AdapterError):convert(encode(p),encode(geo(('DE21',),False)),'2021',('DE',))
    def test_bad_nuts_version(self):
        with self.assertRaises(AdapterError):convert(encode(geo()),encode(geo(projected=False)),'2016',('DE',))
    def test_ambiguous_countries(self):
        for countries in ((),('DE','DE'),('de',),('DE1',)):
            with self.subTest(countries=countries),self.assertRaises(AdapterError):
                convert(encode(geo()),encode(geo(projected=False)),'2021',countries)
    def test_missing_country_regions(self):
        with self.assertRaises(AdapterError):convert(encode(geo()),encode(geo(projected=False)),'2021',('PT',))
    def test_source_crs_metadata_refused(self):
        p=geo();p['crs']={'type':'name','properties':{'name':'EPSG:4326'}}
        with self.assertRaises(AdapterError):convert(encode(p),encode(geo(projected=False)),'2021',('DE',))
    def test_input_not_geojson(self):
        with self.assertRaises(AdapterError):convert(b'wrong',encode(geo(projected=False)),'2021',('DE',))
    def test_output_connects_to_actual_overlay(self):
        normalized,_=convert(encode(geo(('DE21',))),encode(geo(('DE21',),False)),'2021',('DE',))
        footprint={
            'schema_version':'storm-grid-v0','source_id':'SYNTHETIC-NOT-C3S',
            'source_sha256':'a'*64,'crs':'EPSG:3035','event_id':'SYNTH-001',
            'event_date':'2021-01-15','peril':'extratropical_windstorm',
            'grid_cells':[{'cell_id':'synthetic-grid','geometry':box(4300000,2600000,4325000,2650000),'max_gust_mps':18}]
        }
        result=overlay(normalized,footprint)
        region=result['region_metrics'][0]
        self.assertEqual(region['nuts2'],'DE21')
        self.assertEqual(region['covered_area_fraction'],0.5)
        self.assertEqual(region['covered_area_km2'],1250)
        self.assertEqual(region['area_mean_10m_gust_mps_in_covered_area'],18)
        self.assertFalse(result['insured_losses_calculated'])
    def test_reference_only_has_codes_not_in_primary(self):
        with self.assertRaisesRegex(AdapterError,'missing='):
            convert(encode(geo(('DE21',))),encode(geo(('DE21','DE22'),False)),'2024',('DE',))

# CLI verification is deliberately synthetic; provider raw files are not present.
class CommandLineTest(unittest.TestCase):
    def _run(self, valid=True):
        import hashlib
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            proj=encode(geo(('DE21',), True))
            ref=encode(geo(('DE21',), False))
            (p/'source.json').write_bytes(proj)
            (p/'reference.json').write_bytes(ref)
            sha_proj=hashlib.sha256(proj).hexdigest()
            sha_ref=hashlib.sha256(ref).hexdigest()
            cmd=[sys.executable, '-m', 'research_runners.eurostat_nuts2_3035_adapter_v0',
                 str(p/'source.json'),str(p/'reference.json'), '--vintage','2021',
                 '--country','DE','--expected-3035-sha256',sha_proj if valid else '0'*64,
                 '--expected-4326-sha256',sha_ref,'--out',str(p/'converted.json'),
                 '--receipt',str(p/'receipt.json')]
            response=subprocess.run(cmd,capture_output=True,text=True,check=False)
            if valid:
                self.assertEqual(response.returncode,0,response.stderr)
                result=json.loads((p/'converted.json').read_text())
                receipt=json.loads((p/'receipt.json').read_text())
                self.assertEqual(result['source_sha256'],sha_proj)
                self.assertEqual(receipt['reference_sha256'],sha_ref)
                self.assertEqual(receipt['selected_region_codes'],['DE21'])
            else:
                self.assertNotEqual(response.returncode,0)
                self.assertIn('SHA256 does not match',response.stderr)
                self.assertFalse((p/'converted.json').exists())
                self.assertFalse((p/'receipt.json').exists())
    def test_cli_pins_two_source_hashes(self):
        self._run(True)
    def test_cli_refuses_unreviewed_source_hash(self):
        self._run(False)

if __name__ == '__main__':
    unittest.main()
