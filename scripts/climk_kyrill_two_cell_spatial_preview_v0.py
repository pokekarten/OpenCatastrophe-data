#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original CLIMK Kyrill wind at TWO native cells, 24 purely imaginary assets.

This is not measured insured loss, a calibrated vulnerability, joint damage
correlation, insurer exposure, an event rate, annual AAL, AEP, or OEP.
Use unchanged original source-specific native sampler and damage preview.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]

PINNED_SHA256 = '92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102'
CONTRACT = 'OC_CLIMK_KYRILL_TWO_DISTINCT_ERA5_CELLS_SYNTHETIC_PREVIEW_V0'
SITES = (('FICTIONAL_BERLIN', 13.4050, 52.5200),
         ('FICTIONAL_MUNICH', 11.5820, 48.1351))
PER_SITE = 12
REPLACEMENT = 10_000_000


class SpatialPreviewError(ValueError):
    pass


def _fraction(value: object, label: str) -> Fraction:
    if (type(value) is not dict or set(value) != {'numerator', 'denominator'} or
            type(value['numerator']) is not int or
            type(value['denominator']) is not int or value['denominator'] <= 0):
        raise SpatialPreviewError(f'{label}: exact rational required')
    return Fraction(value['numerator'], value['denominator'])


def synthetic_inputs() -> tuple[bytes, dict, dict]:
    sites = {'schema_version':'oc-effis-synthetic-sites-v0',
             'crs':'OGC:CRS84', 'synthetic_only':True,
             'sites':[{'site_id':sid,'longitude':lon,'latitude':lat}
                      for sid,lon,lat in SITES]}
    assets = {'schema_version':'oc-climk-era5-synthetic-asset-roster-v0',
              'synthetic_only':True,'currency':'EUR',
              'insurer_label':'IMAGINARY_24_BUILDINGS_NOT_A_REAL_INSURER',
              'rows':[{'asset_id':f'FICTIONAL_{i:02d}',
                       'site_id':SITES[i % len(SITES)][0],
                       'taxonomy':'RESEARCH_UNCALIBRATED',
                       'replacement_cost_eur':REPLACEMENT}
                      for i in range(len(SITES)*PER_SITE)]}
    vlt = {'schema_version':'oc-climk-era5-synthetic-conditional-gust-vlt-v0',
           'physical_intensity_measure':'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT',
           'normalized_unit':'mm/s',
           'model_evidence':'USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION',
           'curves':[{'taxonomy':'RESEARCH_UNCALIBRATED',
                      'gust_knots_mm_s':[0,15000,25000,35000,200000],
                      'damage_ratio_bps':[0,0,100,2000,10000]}]}
    raw = json.dumps(sites,sort_keys=True,separators=(',', ':'),
                     ensure_ascii=True,allow_nan=False).encode()
    return raw,assets,vlt


def validate_spatial_preview(*, sample: dict, damage: dict, assets: dict) -> dict:
    """Pure scientific contract checks; NOT by itself original-byte authentication."""
    if type(sample) is not dict or type(damage) is not dict or type(assets) is not dict:
        raise SpatialPreviewError('expected bounded source-sample, preview and fictional asset objects')
    expected = {'schema_version':'oc-climk-era5-synthetic-native-point-sample-v0',
                'status':'SOURCE_VERIFIED_SYNTHETIC_HAZARD_SAMPLE_NOT_LOSS',
                'source_sha256':PINNED_SHA256,'source_sha_pinned':True,
                'source_storm_name':'KYRILL','source_storm_date_label':'20070118',
                'storm_index_zero_based':0,
                'event_key':'climk-winds:v2:ERA5:storm-index:0',
                'physical_intensity_measure':'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT',
                'physical_intensity_unit':'m s**-1',
                'event_identity_cross_model_matched':False,
                'source_event_frequency_inferred':False,
                'scientifically_admitted':False}
    if any(type(sample.get(k)) is not type(v) or sample.get(k) != v
           for k,v in expected.items()):
        raise SpatialPreviewError('original CLIMK physical event identity/measure invalid')
    original_sites = sample.get('site_samples')
    if (type(original_sites) is not list or sample.get('site_count') != 2 or
            len(original_sites) != 2 or
            {x.get('site_id') for x in original_sites if type(x) is dict} !=
            {site[0] for site in SITES}):
        raise SpatialPreviewError('exactly both independent geographic markers required')
    cells = {}
    gusts = {}
    for site in original_sites:
        ident = site['site_id']; ix=site.get('native_cell_x'); iy=site.get('native_cell_y')
        if type(ix) is not int or type(iy) is not int or not 0<=ix<=268 or not 0<=iy<=180:
            raise SpatialPreviewError('invalid original native ERA5 index')
        cells[ident] = (ix,iy)
        gust=site.get('absolute_max_gust_m_s')
        if type(gust) not in (float,int) or not 0 <= gust <= 200:
            raise SpatialPreviewError('invalid original storm gust')
        try:
            gusts[ident] = int((Decimal(str(gust))*1000).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        except Exception as exc:
            raise SpatialPreviewError('invalid native gust conversion') from exc
    if len(set(cells.values())) != 2:
        raise SpatialPreviewError('SITES SHARE ONE CELL: spatial study not supported')
    fixed={'schema_version':'oc-climk-era5-synthetic-conditional-damage-preview-v0',
           'source_storm_key':sample['event_key'],'currency':'EUR',
           'synthetic_asset_count':24,'native_grid_sampled_site_count':2,
           'source_sample_gust_values_independently_reverified':True,
           'scientifically_calibrated':False,'promoted_to_financial_loss_model':False,
           'annual_AAL':None,'annual_AEP':None,'annual_OEP':None,
           'insured_original_gross':None,'insurer_retained_net':None,
           'external_re_inward_gross':None,'external_re_retained_net':None}
    if any(type(damage.get(k)) is not type(v) or damage.get(k) != v
           for k,v in fixed.items()):
        raise SpatialPreviewError('original conditional-preview status/finite scope invalid')
    roster=assets.get('rows')
    if (type(roster) is not list or len(roster)!=24 or
            assets.get('synthetic_only') is not True or
            assets.get('currency') != 'EUR'):
        raise SpatialPreviewError('exact fictional 24-building EUR inventory required')
    by_site = Counter(r.get('site_id') for r in roster if type(r) is dict)
    if by_site != {sid:PER_SITE for sid,_,_ in SITES}:
        raise SpatialPreviewError('12 synthetic buildings per distinct ERA5 cell required')
    roster_by_asset = {}
    for row in roster:
        ident=row.get('asset_id')
        if (type(ident) is not str or ident in roster_by_asset or
                type(row.get('replacement_cost_eur')) is not int or
                row['replacement_cost_eur'] != REPLACEMENT):
            raise SpatialPreviewError('duplicate or inconsistent synthetic asset/replacement value')
        roster_by_asset[ident]=row
    rows=damage.get('asset_conditional_damage')
    if type(rows) is not list or len(rows)!=24:
        raise SpatialPreviewError('all 24 per-asset conditional losses required')
    site_damage = {sid:Fraction(0) for sid,_,_ in SITES}
    seen=set()
    for row in rows:
        if type(row) is not dict:
            raise SpatialPreviewError('invalid conditional loss row')
        ident=row.get('asset_id')
        if ident not in roster_by_asset or ident in seen:
            raise SpatialPreviewError('missing/duplicate conditional asset')
        seen.add(ident)
        sid=roster_by_asset[ident]['site_id']
        if (row.get('site_id') != sid or row.get('replacement_cost_eur') != REPLACEMENT or
                type(row.get('native_gust_mm_s')) is not int or
                row['native_gust_mm_s'] != gusts[sid]):
            raise SpatialPreviewError('asset site/gust differs from original cell')
        claim=_fraction(row.get('conditional_expected_ground_up_eur_exact'), 'asset conditional EUR')
        if not 0<=claim<=REPLACEMENT:
            raise SpatialPreviewError('unphysical synthetic loss ratio')
        site_damage[sid]+=claim
    total=sum(site_damage.values(),Fraction())
    if total != _fraction(damage.get('total_conditional_ground_up_eur_exact'), 'total conditional EUR'):
        raise SpatialPreviewError('per-site expected physical damage does not conserve')
    if not 0 <= total <= 24 * REPLACEMENT:
        raise SpatialPreviewError('invented physical replacement cost exceeded')
    def rat(v:Fraction)->dict: return {'numerator':v.numerator,'denominator':v.denominator}
    return {
        'contract':CONTRACT,
        'status':'TWO_ORIGINAL_NATIVE_CELLS_SYNTHETIC_DAMAGE_NOT_CALIBRATED',
        'source_sha256':PINNED_SHA256,
        'source_physical_event_key':sample['event_key'],
        'source_storm_name':sample['source_storm_name'],
        'source_storm_date_label_unverified_utc':sample['source_storm_date_label'],
        'number_of_distinct_native_ERA5_cells':2,
        'invented_assets':24,'invented_replacement_eur':24*REPLACEMENT,
        'per_site':[{'site_id':sid,'native_cell_x':cells[sid][0],
                     'native_cell_y':cells[sid][1],
                     'native_gust_mm_s':gusts[sid],
                     'invented_assets':PER_SITE,
                     'conditional_expected_physical_loss_eur_exact':rat(site_damage[sid])}
                    for sid,_,_ in SITES],
        'conditional_expected_physical_loss_total_eur_exact':rat(total),
        'synthetic_roster_sha256':damage.get('synthetic_asset_roster_sha256'),
        'uncalibrated_vlt_sha256':damage.get('uncalibrated_vlt_sha256'),
        'original_source_bytes_verified_in_this_pure_function':False,
        'source_event_frequency_inferred':False,
        'fitted_spatial_damage_dependence':False,
        'annual_AAL':None,'annual_AEP':None,'annual_OEP':None,
        'insurer_original_gross':None,'insurer_retained_net':None,
    }


def run_live() -> dict:
    from scripts.inspect_climk_winds_era5_v0 import fetch_provider_bytes
    from scripts.climk_era5_synthetic_native_sample_v0 import sample_climk_era5
    from scripts.climk_era5_synthetic_damage_preview_v0 import preview_conditional_damage
    source=fetch_provider_bytes()
    if type(source) is not bytes or sha256(source).hexdigest() != PINNED_SHA256:
        raise SpatialPreviewError('authentic provider SHA256 required')
    sites,roster,vulnerability=synthetic_inputs()
    sample=sample_climk_era5(original=source,synthetic_sites_json=sites,storm_index=0)
    damage=preview_conditional_damage(sample=sample,synthetic_assets=roster,
                                      vulnerabilities=vulnerability,
                                      original_netcdf_bytes=source,
                                      original_sites_json_bytes=sites)
    result=validate_spatial_preview(sample=sample,damage=damage,assets=roster)
    result['original_source_bytes_verified_in_this_pure_function']=True
    return result


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    result=run_live()
    data=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n'
    if args.out is None:
        print(data,end='')
    else:
        if args.out.exists():
            ap.error('never overwrite original provider execution research evidence')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('x',encoding='utf-8') as handle:
            handle.write(data)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
