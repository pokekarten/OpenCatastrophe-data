# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline faked source tests: never claim original NetCDF execution here."""
from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
import sys
import unittest

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts')]
from climk_kyrill_two_cell_spatial_preview_v0 import (
    CONTRACT, PINNED_SHA256, SITES, SpatialPreviewError,
    synthetic_inputs,validate_spatial_preview,
)


def mocked():
    _,assets,_=synthetic_inputs()
    source={
        'schema_version':'oc-climk-era5-synthetic-native-point-sample-v0',
        'status':'SOURCE_VERIFIED_SYNTHETIC_HAZARD_SAMPLE_NOT_LOSS',
        'source_sha256':PINNED_SHA256,'source_sha_pinned':True,
        'source_storm_name':'KYRILL','source_storm_date_label':'20070118',
        'storm_index_zero_based':0,'event_key':'climk-winds:v2:ERA5:storm-index:0',
        'physical_intensity_measure':'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT',
        'physical_intensity_unit':'m s**-1',
        'event_identity_cross_model_matched':False,
        'source_event_frequency_inferred':False,'scientifically_admitted':False,
        'site_count':2,
        'site_samples':[{'site_id':SITES[0][0],'native_cell_x':100,'native_cell_y':80,
                         'absolute_max_gust_m_s':35.5},
                        {'site_id':SITES[1][0],'native_cell_x':130,'native_cell_y':75,
                         'absolute_max_gust_m_s':28.2}],
    }
    loss=[]
    for r in assets['rows']:
        wind=35500 if r['site_id']==SITES[0][0] else 28200
        value=2_000_000 if wind==35500 else 500_000
        loss.append({'asset_id':r['asset_id'],'site_id':r['site_id'],
                     'native_gust_mm_s':wind,'replacement_cost_eur':10_000_000,
                     'conditional_expected_ground_up_eur_exact':
                     {'numerator':value,'denominator':1}})
    damage={'schema_version':'oc-climk-era5-synthetic-conditional-damage-preview-v0',
            'source_storm_key':source['event_key'],'currency':'EUR',
            'synthetic_asset_count':24,'native_grid_sampled_site_count':2,
            'source_sample_gust_values_independently_reverified':True,
            'scientifically_calibrated':False,
            'promoted_to_financial_loss_model':False,
            'annual_AAL':None,'annual_AEP':None,'annual_OEP':None,
            'insured_original_gross':None,'insurer_retained_net':None,
            'external_re_inward_gross':None,'external_re_retained_net':None,
            'asset_conditional_damage':loss,
            'total_conditional_ground_up_eur_exact':{'numerator':30_000_000,'denominator':1},
            'synthetic_asset_roster_sha256':'fake-test-only',
            'uncalibrated_vlt_sha256':'fake-test-only'}
    return source,damage,assets


class SyntheticTwoCellPreview(unittest.TestCase):
    def test_different_city_markers_and_tiv(self):
        raw, assets, vlt=synthetic_inputs()
        sites=json.loads(raw)['sites']
        self.assertEqual(len(sites),2)
        self.assertNotEqual((sites[0]['longitude'],sites[0]['latitude']),
                            (sites[1]['longitude'],sites[1]['latitude']))
        self.assertEqual({r['site_id'] for r in assets['rows']}, {s[0] for s in SITES})
        self.assertEqual(sum(r['replacement_cost_eur'] for r in assets['rows']),240_000_000)
        self.assertEqual(vlt['model_evidence'],'USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION')

    def test_preserves_distinct_cells_and_loss_conservation(self):
        a,b,c=mocked()
        z=validate_spatial_preview(sample=a,damage=b,assets=c)
        self.assertEqual(z['contract'],CONTRACT)
        self.assertEqual(z['number_of_distinct_native_ERA5_cells'],2)
        self.assertEqual(z['conditional_expected_physical_loss_total_eur_exact'],
                         {'numerator':30_000_000,'denominator':1})
        self.assertEqual([x['conditional_expected_physical_loss_eur_exact'] for x in z['per_site']],
                         [{'numerator':24_000_000,'denominator':1},
                          {'numerator':6_000_000,'denominator':1}])
        self.assertIsNone(z['annual_AEP'])
        self.assertFalse(z['original_source_bytes_verified_in_this_pure_function'])

    def test_both_points_in_same_cell_rejected(self):
        a,b,c=mocked()
        a['site_samples'][1]['native_cell_x']=100
        a['site_samples'][1]['native_cell_y']=80
        with self.assertRaisesRegex(SpatialPreviewError,'SHARE ONE CELL'):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_missing_site_rejected(self):
        a,b,c=mocked()
        a['site_samples'].pop()
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_wrong_event_peril_identity_rejected(self):
        for key,value in [('event_key','made-up'),('source_storm_name','storm2'),
                          ('source_sha256','0'*64),('source_storm_date_label','20070117'),
                          ('source_event_frequency_inferred',True)]:
            a,b,c=mocked()
            a[key]=value
            with self.subTest(key=key),self.assertRaises(SpatialPreviewError):
                validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_tampered_asset_gust_rejected(self):
        a,b,c=mocked();b['asset_conditional_damage'][0]['native_gust_mm_s']+=1
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_duplicate_asset_rejected(self):
        a,b,c=mocked(); b['asset_conditional_damage'][1]=copy.deepcopy(b['asset_conditional_damage'][0])
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_incomplete_24_asset_site_roster_rejected(self):
        a,b,c=mocked();c['rows'][0]['site_id']=SITES[1][0]
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_loss_conservation_rejected(self):
        a,b,c=mocked(); b['total_conditional_ground_up_eur_exact']['numerator']+=1
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_annual_ep_rejected(self):
        a,b,c=mocked(); b['annual_AEP']=0
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_false_original_reread_rejected(self):
        a,b,c=mocked(); b['source_sample_gust_values_independently_reverified']=False
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_bad_rational_rejected(self):
        for invalid in [None,{'numerator':0,'denominator':0},
                        {'numerator':True,'denominator':1},
                        {'numerator':20,'denominator':-1}]:
            a,b,c=mocked()
            b['asset_conditional_damage'][0]['conditional_expected_ground_up_eur_exact']=invalid
            with self.subTest(invalid=invalid),self.assertRaises(SpatialPreviewError):
                validate_spatial_preview(sample=a,damage=b,assets=c)

    def test_nonphysical_loss_rejected(self):
        a,b,c=mocked()
        b['asset_conditional_damage'][0]['conditional_expected_ground_up_eur_exact']={'numerator':10_000_001,'denominator':1}
        with self.assertRaises(SpatialPreviewError):
            validate_spatial_preview(sample=a,damage=b,assets=c)


if __name__=='__main__':
    unittest.main()
