# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline mock of original-fetch wiring; NOT a provider-native byte read."""
from __future__ import annotations

from hashlib import sha256
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from scripts import climk_era5_conditional_damage_live_receipt_v0 as mod
from scripts.climk_era5_synthetic_damage_preview_v0 import preview_conditional_damage


FAKE = b'synthetic-fake-not-a-real-netcdf'


def sample():
    result = {
        'schema_version':'oc-climk-era5-synthetic-native-point-sample-v0',
        'status':'SOURCE_VERIFIED_SYNTHETIC_HAZARD_SAMPLE_NOT_LOSS',
        'peril':'WINDSTORM','source_dataset':'CLIMK-WINDS v2 / ERA5',
        'source_sha256':mod.PINNED_SHA256,'source_sha_pinned':True,
        'event_key':'climk-winds:v2:ERA5:storm-index:0',
        'storm_index_zero_based':0,'source_storm_name':'SYNTH TEST STORM',
        'source_storm_date_label':'1999-12-26',
        'source_storm_date_parsed_as_utc':False,
        'grid_coordinate_system':'source_native_lat_lon_degrees',
        'spatial_sampling':'nearest_native_grid_center_no_extrapolation',
        'physical_intensity_measure':'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT',
        'physical_intensity_unit':'m s**-1',
        'relative_intensity_measure':'MAX_GUST_DIVIDED_BY_98TH_PERCENTILE_CLIMATOLOGY',
        'relative_intensity_unit':'dimensionless',
        'site_count':2,'site_samples':[],
        'site_asset_ownership_admitted':False,
        'source_event_frequency_inferred':False,'full_grid_republished':False,
        'damage_or_insured_loss_computed':False,'scientifically_admitted':False,
    }
    result['site_samples'] = [
        {'site_id':site_id,'native_cell_x':100+i,'native_cell_y':60,
         'selected_cell_center_lon':5.75+0.25*i,
         'selected_cell_center_lat':52.5,
         'absolute_max_gust_m_s':20.0 if i==0 else 30.0,
         'relative_max_gust_dimensionless':1.0}
        for i,(site_id,*_) in enumerate(mod.SITES)]
    return result


class LiveOriginalReceiptOfflineTests(unittest.TestCase):
    def test_fixed_synthetic_input_roster_and_law(self):
        sites, assets, vlt=mod.synthetic_inputs()
        self.assertEqual(len(assets['rows']),24)
        self.assertEqual(sum(x['replacement_cost_eur'] for x in assets['rows']),240_000_000)
        self.assertEqual(len(set(x['asset_id'] for x in assets['rows'])),24)
        self.assertEqual(set(x['site_id'] for x in assets['rows']),set(s[0] for s in mod.SITES))
        self.assertEqual(json.loads(sites)['synthetic_only'],True)
        self.assertEqual(vlt['model_evidence'],'USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION')

    def test_offline_provider_fake_wiring_yields_13p2m_conditional_not_annual(self):
        sample_fake=sample()
        native_fake=SimpleNamespace(sample_climk_era5=lambda **kwargs: copy.deepcopy(sample_fake))
        with patch.object(mod,'PINNED_SHA256',sha256(FAKE).hexdigest()),\
             patch.dict(sys.modules,{'climk_era5_synthetic_native_sample_v0':native_fake}):
            report=mod.run_live(original=lambda:FAKE,
                                sampler=lambda **kwargs: copy.deepcopy(sample_fake),
                                previewer=preview_conditional_damage)
        self.assertEqual(report['conditional_physical_ground_up_eur_exact'],
                         {'numerator':13_200_000,'denominator':1})
        self.assertEqual(report['synthetic_total_replacement_cost_eur'],240_000_000)
        self.assertTrue(report['point_reextract_exact_original'])
        for key in ('annual_AAL','annual_OEP','annual_AEP','insurer_original_gross','insurer_retained_net'):
            self.assertIsNone(report[key])
        self.assertFalse(report['model_calibrated'])
        self.assertEqual(report['source_sha256'],sha256(FAKE).hexdigest())

    def test_provider_sha_drift_cannot_claim_original_source(self):
        sample_fake=sample()
        native_fake=SimpleNamespace(sample_climk_era5=lambda **kwargs:copy.deepcopy(sample_fake))
        with patch.dict(sys.modules,{'climk_era5_synthetic_native_sample_v0':native_fake}):
            with self.assertRaisesRegex(ValueError,'pinned SHA256'):
                mod.run_live(original=lambda:FAKE,
                             sampler=lambda **kwargs:copy.deepcopy(sample_fake),
                             previewer=preview_conditional_damage)

    def test_synthetic_wrong_reverification_flag_and_tiv_rejected(self):
        sample_fake=sample()
        def bad_preview(**kwargs):
            v=preview_conditional_damage(sample=kwargs['sample'],
                                         synthetic_assets=kwargs['synthetic_assets'],
                                         vulnerabilities=kwargs['vulnerabilities'])
            return v
        with self.assertRaisesRegex(ValueError,'scope'):
            mod.run_live(original=lambda:FAKE, sampler=lambda **kwargs:sample_fake,
                         previewer=bad_preview)
        with self.assertRaisesRegex(ValueError,'bounded bytes'):
            mod.run_live(original=lambda:None, sampler=lambda **kwargs:sample_fake,
                         previewer=bad_preview)


if __name__ == '__main__':
    unittest.main()
