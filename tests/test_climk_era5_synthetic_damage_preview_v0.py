# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline numeric and scientific boundary challenges; NO raw provider data here."""
from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from climk_era5_synthetic_damage_preview_v0 import (
    DamagePreviewError, PINNED_ERA5_SHA256,
    _ratio, _load_json, preview_conditional_damage,
)


def fixtures():
    samples = []
    for sid, wind, x in [('A',20.0,100),('B',30.0,101)]:
        samples.append({
            'site_id':sid,'native_cell_x':x,'native_cell_y':60,
            'selected_cell_center_lon':10.0+(x-100)*.25,
            'selected_cell_center_lat':50.0,
            'absolute_max_gust_m_s':wind,
            'relative_max_gust_dimensionless':1.3,
        })
    sample = {
        'schema_version':'oc-climk-era5-synthetic-native-point-sample-v0',
        'status':'SOURCE_VERIFIED_SYNTHETIC_HAZARD_SAMPLE_NOT_LOSS',
        'peril':'WINDSTORM','source_dataset':'CLIMK-WINDS v2 / ERA5',
        'source_sha256':PINNED_ERA5_SHA256,'source_sha_pinned':True,
        'event_key':'climk-winds:v2:ERA5:storm-index:0',
        'storm_index_zero_based':0,'source_storm_name':'SYNTHETIC TEST STORM',
        'source_storm_date_label':'2000-01-01',
        'source_storm_date_parsed_as_utc':False,
        'event_identity_cross_model_matched':False,
        'grid_coordinate_system':'source_native_lat_lon_degrees',
        'spatial_sampling':'nearest_native_grid_center_no_extrapolation',
        'physical_intensity_measure':'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT',
        'physical_intensity_unit':'m s**-1',
        'relative_intensity_measure':'MAX_GUST_DIVIDED_BY_98TH_PERCENTILE_CLIMATOLOGY',
        'relative_intensity_unit':'dimensionless',
        'site_count':2,'site_samples':samples,'site_asset_ownership_admitted':False,
        'source_event_frequency_inferred':False,'full_grid_republished':False,
        'damage_or_insured_loss_computed':False,'scientifically_admitted':False,
    }
    assets = {
        'schema_version':'oc-climk-era5-synthetic-asset-roster-v0',
        'synthetic_only':True,'currency':'EUR','insurer_label':'ZURICH_RESEARCH_PROXY',
        'rows':[{'asset_id':f'synthetic-{sid}','site_id':sid,
                 'taxonomy':'COM','replacement_cost_eur':10_000_000}
                for sid in ('A','B')],
    }
    vlt = {
        'schema_version':'oc-climk-era5-synthetic-conditional-gust-vlt-v0',
        'physical_intensity_measure':'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT',
        'normalized_unit':'mm/s',
        'model_evidence':'USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION',
        'curves':[{'taxonomy':'COM',
                   'gust_knots_mm_s':[0,15000,25000,35000,200000],
                   'damage_ratio_bps':[0,0,100,2000,10000]}],
    }
    return sample, assets, vlt


def calculate():
    a,b,c=fixtures()
    return preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)


class SyntheticClimkConditionalDamage(unittest.TestCase):
    def test_two_sites_exact_expected_damage_and_source_receipts(self):
        result=calculate()
        self.assertEqual(result['synthetic_asset_count'],2)
        self.assertEqual(result['native_grid_sampled_site_count'],2)
        # 20 m/s interpolates to 50 bps => 50,000 EUR of a EUR10m asset.
        # 30 m/s interpolates to 1050 bps => 1,050,000 EUR.
        self.assertEqual(result['asset_conditional_damage'][0]['conditional_expected_ground_up_eur_exact'],
                         {'numerator':50_000,'denominator':1})
        self.assertEqual(result['asset_conditional_damage'][1]['conditional_expected_ground_up_eur_exact'],
                         {'numerator':1_050_000,'denominator':1})
        self.assertEqual(result['total_conditional_ground_up_eur_exact'],
                         {'numerator':1_100_000,'denominator':1})
        for name in ('annual_AAL','annual_AEP','annual_OEP','insured_original_gross',
                     'insurer_retained_net','external_re_inward_gross','external_re_retained_net'):
            self.assertIsNone(result[name],name)
        self.assertFalse(result['scientifically_calibrated'])
        self.assertFalse(result['source_sample_gust_values_independently_reverified'])
        self.assertFalse(result['promoted_to_financial_loss_model'])
        self.assertEqual(len(result['uncalibrated_vlt_sha256']),64)
        self.assertEqual(calculate(),result)

    def test_exact_linear_interpolation_boundaries_and_no_clipping(self):
        points=((0,0),(15000,0),(25000,100),(35000,2000),(200000,10000))
        self.assertEqual(_ratio(0,points),Fraction(0))
        self.assertEqual(_ratio(15000,points),Fraction(0))
        self.assertEqual(_ratio(20000,points),Fraction(50))
        self.assertEqual(_ratio(25000,points),Fraction(100))
        self.assertEqual(_ratio(30000,points),Fraction(1050))
        self.assertEqual(_ratio(200000,points),Fraction(10000))
        with self.assertRaises(DamagePreviewError): _ratio(200001,points)

    def test_tampered_source_hash_rejected(self):
        a,b,c=fixtures();a['source_sha256']='0'*64
        with self.assertRaisesRegex(DamagePreviewError,'source_sha256'):
            preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_misidentified_event_or_date_claim_rejected(self):
        for edit in ('event_key','storm_index_zero_based','source_storm_date_parsed_as_utc'):
            a,b,c=fixtures()
            a[edit]={'event_key':'fake-world-id','storm_index_zero_based':9,
                     'source_storm_date_parsed_as_utc':True}[edit]
            with self.subTest(edit=edit),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_source_sampling_not_implicitly_an_insurance_or_frequency_claim(self):
        for field in ('site_asset_ownership_admitted','source_event_frequency_inferred',
                      'scientifically_admitted','damage_or_insured_loss_computed'):
            a,b,c=fixtures();a[field]=True
            with self.subTest(field=field),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_source_model_cross_identity_must_remain_explicitly_unmatched(self):
        a,b,c=fixtures()
        a['event_identity_cross_model_matched']=True
        with self.assertRaisesRegex(DamagePreviewError,'cross_model|event_identity'):
            preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)
        a,b,c=fixtures()
        del a['event_identity_cross_model_matched']
        with self.assertRaisesRegex(DamagePreviewError,'exact schema'):
            preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_wrong_gust_measure_or_unit_rejected(self):
        for key,val in [('physical_intensity_measure','MAX_3_SECOND_10M_GUST_OVER_72_HOURS'),
                        ('physical_intensity_unit','mph')]:
            a,b,c=fixtures();a[key]=val
            with self.subTest(key=key),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_missing_site_duplicate_asset_and_real_assets_rejected(self):
        for change in ('missing-site','duplicate-asset','not-synthetic','foreign-site'):
            a,b,c=fixtures()
            if change=='missing-site':b['rows'].pop()
            if change=='duplicate-asset':b['rows'][1]['asset_id']=b['rows'][0]['asset_id']
            if change=='not-synthetic':b['synthetic_only']=False
            if change=='foreign-site':b['rows'][0]['site_id']='unknown-site'
            with self.subTest(change=change),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_malformed_gust_bool_nan_and_unsafe_axes_rejected(self):
        for value in (True,float('nan'),-1,201,10**400):
            a,b,c=fixtures();a['site_samples'][0]['absolute_max_gust_m_s']=value
            with self.subTest(value=repr(value)[:30]),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)
        a,b,c=fixtures();a['site_samples'][0]['native_cell_x']=269
        with self.assertRaises(DamagePreviewError):
            preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_loss_law_non_monotonic_or_out_of_range_rejected(self):
        for field,values in [('damage_ratio_bps',[0,2000,100,100,10000]),
                             ('damage_ratio_bps',[0,0,100,2000,10001]),
                             ('gust_knots_mm_s',[0,15000,25000,25000,200000]),
                             ('gust_knots_mm_s',[0,15000,25000,35000,12000])]:
            a,b,c=fixtures();c['curves'][0][field]=values
            with self.subTest(field=field,values=values),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_required_extrapolation_coverage_instead_of_silent_zero(self):
        a,b,c=fixtures();c['curves'][0]['gust_knots_mm_s']=[0,15000,25000,26000,28000]
        with self.assertRaisesRegex(DamagePreviewError,'no extrapolation'):
            preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_unknown_or_extra_schema_fields_and_bool_cost_rejected(self):
        for field in ('source','assets','vlt','cost'):
            a,b,c=fixtures()
            if field=='source':a['invented_frequency']=0.2
            if field=='assets':b['actual_insurer_tiv']=1000000
            if field=='vlt':c['curves'][0]['price']=1.0
            if field=='cost':b['rows'][0]['replacement_cost_eur']=False
            with self.subTest(field=field),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c)

    def test_duplicate_json_fields_nonfinite_constant_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'test.json'
            for raw in ('{"a":1,"a":2}', '{"loss":NaN}'):
                p.write_text(raw)
                with self.subTest(raw=raw),self.assertRaises(DamagePreviewError):
                    _load_json(p)

    def test_original_source_reverification_wiring_and_tamper_detection(self):
        # The *real* provider reader is imported only when both original inputs
        # are provided. A mocked reader validates wiring and exact JSON equality,
        # NOT NetCDF parsing or original source authenticity.
        a,b,c=fixtures()
        reader=SimpleNamespace(sample_climk_era5=lambda **kw:copy.deepcopy(a))
        with patch.dict(sys.modules,{'climk_era5_synthetic_native_sample_v0':reader}):
            receipt=preview_conditional_damage(sample=a,synthetic_assets=b,
                vulnerabilities=c,original_netcdf_bytes=b'header',
                original_sites_json_bytes=b'{"synthetic":true}')
            self.assertTrue(receipt['source_sample_gust_values_independently_reverified'])
            reader.sample_climk_era5=lambda **kw:{**a,'event_key':'altered'}
            with self.assertRaisesRegex(DamagePreviewError,'differs'):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c,
                    original_netcdf_bytes=b'header',original_sites_json_bytes=b'{}')

    def test_original_source_both_required_and_reader_fail_closed(self):
        a,b,c=fixtures()
        for raw,sites in ((b'netcdf',None),(None,b'{}'),('netcdf',b'{}'),(b'',b'{}')):
            with self.subTest(raw=raw,sites=sites),self.assertRaises(DamagePreviewError):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c,
                    original_netcdf_bytes=raw,original_sites_json_bytes=sites)
        reader=SimpleNamespace(sample_climk_era5=lambda **kw: (_ for _ in ()).throw(ValueError('failed')))
        with patch.dict(sys.modules,{'climk_era5_synthetic_native_sample_v0':reader}):
            with self.assertRaisesRegex(DamagePreviewError,'re-verification failed'):
                preview_conditional_damage(sample=a,synthetic_assets=b,vulnerabilities=c,
                    original_netcdf_bytes=b'not-a-real-netcdf',
                    original_sites_json_bytes=b'{}')

    def test_cli_produces_only_conditional_preview_and_refuses_overwrite(self):
        a,b,c=fixtures()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name,data in [('sample.json',a),('assets.json',b),('vlt.json',c)]:
                (root/name).write_text(json.dumps(data))
            out=root/'result.json'
            script=str(Path(__file__).resolve().parents[1]/'scripts'/'climk_era5_synthetic_damage_preview_v0.py')
            cmd=[sys.executable,script,'--source-sample',str(root/'sample.json'),
                 '--synthetic-assets',str(root/'assets.json'),'--vlt',str(root/'vlt.json'),
                 '--out',str(out)]
            completed=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(completed.returncode,0,completed.stderr)
            self.assertEqual(json.loads(out.read_text()),calculate())
            repeated=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(repeated.returncode,0)
            self.assertEqual(json.loads(out.read_text()),calculate())


if __name__=='__main__':
    unittest.main()
