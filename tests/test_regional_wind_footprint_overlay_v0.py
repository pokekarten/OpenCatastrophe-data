# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import copy
import importlib.util
import unittest

from research_runners.regional_wind_footprint_overlay_v0 import overlay, OverlayError


SHA = 'a'*64


def rect(x1,y1,x2,y2):
    return {'type':'Polygon','coordinates':[[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]]}


def example():
    return (
        {'schema_version':'nuts2-polygons-v0', 'nuts_version':'2021',
         'crs':'EPSG:3035','source_sha256':SHA,
         'features':[{'nuts2':'DE21','geometry':rect(0,0,2000,1000)},
                     {'nuts2':'DE22','geometry':rect(2000,0,3000,1000)}]},
        {'schema_version':'storm-grid-v0','crs':'EPSG:3035',
         'source_id':'SYNTHETIC-NOT-C3S','source_sha256':SHA,
         'event_id':'SYNTH-EVENT-1','event_date':'2021-10-23',
         'peril':'extratropical_windstorm',
         'grid_cells':[{'cell_id':'c1','geometry':rect(0,0,1000,1000),'max_gust_mps':10},
                       {'cell_id':'c2','geometry':rect(1000,0,2000,1000),'max_gust_mps':30}]},
    )


@unittest.skipUnless(importlib.util.find_spec('shapely'), 'optional spatial profile requires shapely')
class OverlayTest(unittest.TestCase):
    def test_cover_and_uncovered_region(self):
        a,b=example();result=overlay(a,b)
        p,q=result['region_metrics']
        self.assertEqual((p['nuts2'],p['region_area_km2'],p['covered_area_km2']),('DE21',2.0,2.0))
        self.assertEqual(p['max_10m_gust_mps_in_covered_area'],30)
        self.assertEqual(p['area_mean_10m_gust_mps_in_covered_area'],20)
        self.assertEqual(p['covered_area_fraction'],1)
        self.assertIsNone(q['max_10m_gust_mps_in_covered_area'])
        self.assertTrue(q['uncovered_area_weather_unknown'])
        self.assertFalse(result['insured_losses_calculated'])
    def test_partial_coverage_unknown_not_zero(self):
        a,b=example();b['grid_cells'].pop()
        p=overlay(a,b)['region_metrics'][0]
        self.assertEqual(p['covered_area_fraction'],0.5)
        self.assertEqual(p['area_mean_10m_gust_mps_in_covered_area'],10)
        self.assertTrue(p['uncovered_area_weather_unknown'])
    def test_hole_excludes_weather_area(self):
        a,b=example();a['features']=[{'nuts2':'DE21','geometry':{
            'type':'Polygon','coordinates':[
                [[0,0],[2000,0],[2000,1000],[0,1000],[0,0]],
                [[600,200],[600,800],[1400,800],[1400,200],[600,200]]
            ]}}]
        p=overlay(a,b)['region_metrics'][0]
        self.assertEqual(p['region_area_km2'],1.52)
        self.assertEqual(p['covered_area_km2'],1.52)
        self.assertEqual(p['covered_area_fraction'],1)
        self.assertEqual(p['area_mean_10m_gust_mps_in_covered_area'],20)
    def test_overlapping_cells_are_blocked(self):
        a,b=example();b['grid_cells'][1]['geometry']=rect(500,0,1500,1000)
        with self.assertRaisesRegex(OverlayError,'overlapping grid'):
            overlay(a,b)
    def test_duplicate_region_blocked(self):
        a,b=example();a['features'].append(copy.deepcopy(a['features'][0]))
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_duplicate_grid_id_blocked(self):
        a,b=example();b['grid_cells'][1]['cell_id']='c1'
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_points_are_not_regions(self):
        a,b=example();a['features'][0]['geometry']={'type':'Point','coordinates':[0,0]}
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_bad_projection_is_blocked(self):
        a,b=example();b['crs']='EPSG:4326'
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_bad_vintage_is_blocked(self):
        a,b=example();a['nuts_version']='2016'
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_bad_source_digest_is_blocked(self):
        a,b=example();a['source_sha256']='not-a-checksum'
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_bad_gust_rejected(self):
        for val in [-1,float('nan'),float('inf'),True,'50']:
            with self.subTest(val=val):
                a,b=example();b['grid_cells'][0]['max_gust_mps']=val
                with self.assertRaises(OverlayError):overlay(a,b)
    def test_wrong_peril_blocked(self):
        a,b=example();b['peril']='hail'
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_invalid_geometry_not_repaired(self):
        a,b=example();a['features'][0]['geometry']={'type':'Polygon',
            'coordinates':[[[0,0],[2000,1000],[2000,0],[0,1000],[0,0]]]}
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_invalid_event_date_rejected(self):
        a,b=example();b['event_date']='2021-02-30'
        with self.assertRaises(OverlayError):overlay(a,b)
    def test_multigeometry_rings(self):
        a,b=example();a['features']=[{'nuts2':'DE21',
            'geometry':{'type':'MultiPolygon','coordinates':[
                [rect(0,0,1000,1000)['coordinates'][0]],
                [rect(1500,0,2000,1000)['coordinates'][0]]
            ]}}]
        p=overlay(a,b)['region_metrics'][0]
        self.assertEqual(p['covered_area_fraction'],1)
        self.assertAlmostEqual(p['area_mean_10m_gust_mps_in_covered_area'],16.666667,places=5)
    def test_determinism(self):
        a,b=example();self.assertEqual(overlay(a,b),overlay(copy.deepcopy(a),copy.deepcopy(b)))

if __name__ == '__main__':
    unittest.main()
