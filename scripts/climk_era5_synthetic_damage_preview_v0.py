#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pinned CLIMK-ERA5 point gust -> declared *synthetic* conditional damage PREVIEW.

This does NOT authenticate a forwarded point-sampling JSON independently of
its original NetCDF, does NOT sample an annual event process or calculate
insured/reinsured claims, AAL, OEP, AEP, financial prices or a Zurich book.
Never label extreme-top-50 selected windstorms as an annual frequency sample.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import Path

PINNED_ERA5_SHA256 = '92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102'
SAMPLE_SCHEMA = 'oc-climk-era5-synthetic-native-point-sample-v0'
ASSETS_SCHEMA = 'oc-climk-era5-synthetic-asset-roster-v0'
VLT_SCHEMA = 'oc-climk-era5-synthetic-conditional-gust-vlt-v0'
PREVIEW_SCHEMA = 'oc-climk-era5-synthetic-conditional-damage-preview-v0'
MEASURE = 'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT'
SAMPLE_FIELDS = {
    'schema_version','status','peril','source_dataset','source_sha256',
    'source_sha_pinned','event_key','storm_index_zero_based','source_storm_name',
    'event_identity_cross_model_matched',
    'source_storm_date_label','source_storm_date_parsed_as_utc',
    'grid_coordinate_system','spatial_sampling','physical_intensity_measure',
    'physical_intensity_unit','relative_intensity_measure','relative_intensity_unit',
    'site_count','site_samples','site_asset_ownership_admitted',
    'source_event_frequency_inferred','full_grid_republished',
    'damage_or_insured_loss_computed','scientifically_admitted',
}
SITE_FIELDS = {
    'site_id','native_cell_x','native_cell_y','selected_cell_center_lon',
    'selected_cell_center_lat','absolute_max_gust_m_s',
    'relative_max_gust_dimensionless',
}
ASSET_FIELDS = {'asset_id','site_id','taxonomy','replacement_cost_eur'}
MAX_ASSETS = 20_000


class DamagePreviewError(ValueError):
    """The physical-sample, synthetic asset or loss-model contract failed closed."""


def _exact(value, keys, label):
    if type(value) is not dict or set(value) != keys:
        raise DamagePreviewError(f'{label}: exact schema required')
    return value


def _identifier(value, label):
    if (type(value) is not str or not 1 <= len(value) <= 128
            or value != value.strip() or any(ord(x) < 32 or ord(x) == 127 for x in value)):
        raise DamagePreviewError(f'{label}: invalid identifier')
    return value


def _integer(value, label, low, high):
    if type(value) is not int or not low <= value <= high:
        raise DamagePreviewError(f'{label}: invalid bounded integer')
    return value


def _finite(value, label, low, high):
    if type(value) not in (int, float):
        raise DamagePreviewError(f'{label}: invalid numeric type')
    try:
        out = float(value)
    except (ValueError, OverflowError) as exc:
        raise DamagePreviewError(f'{label}: invalid finite number') from exc
    if not math.isfinite(out) or not low <= out <= high:
        raise DamagePreviewError(f'{label}: invalid physical bound')
    return out


def _sha(obj):
    return sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('utf-8')).hexdigest()


def _millimeters_per_second(gust):
    # A pinned rounding rule, never a silent Python binary-float to EUR cast.
    _finite(gust, 'native gust m/s', 0, 200)
    try:
        return int((Decimal(str(gust)) * 1000).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError) as exc:
        raise DamagePreviewError('wind gust cannot be represented in mm/s') from exc


def _sample_sites(sample):
    _exact(sample, SAMPLE_FIELDS, 'CLIMK original point-sample receipt')
    required = {
        'schema_version': SAMPLE_SCHEMA,
        'status': 'SOURCE_VERIFIED_SYNTHETIC_HAZARD_SAMPLE_NOT_LOSS',
        'peril': 'WINDSTORM', 'source_dataset': 'CLIMK-WINDS v2 / ERA5',
        'source_sha256': PINNED_ERA5_SHA256, 'source_sha_pinned': True,
        'event_identity_cross_model_matched': False,
        'source_storm_date_parsed_as_utc': False,
        'grid_coordinate_system': 'source_native_lat_lon_degrees',
        'spatial_sampling': 'nearest_native_grid_center_no_extrapolation',
        'physical_intensity_measure': MEASURE,
        'physical_intensity_unit': 'm s**-1',
        'relative_intensity_measure': 'MAX_GUST_DIVIDED_BY_98TH_PERCENTILE_CLIMATOLOGY',
        'relative_intensity_unit': 'dimensionless',
        'site_asset_ownership_admitted': False,
        'source_event_frequency_inferred': False,
        'full_grid_republished': False,
        'damage_or_insured_loss_computed': False,
        'scientifically_admitted': False,
    }
    for name, expected in required.items():
        if type(sample.get(name)) is not type(expected) or sample[name] != expected:
            raise DamagePreviewError(f'{name}: unexpected scientific identity or admission claim')
    index = _integer(sample['storm_index_zero_based'], 'storm_index_zero_based', 0, 49)
    if sample['event_key'] != f'climk-winds:v2:ERA5:storm-index:{index}':
        raise DamagePreviewError('event identity does not match storm index')
    _identifier(sample['source_storm_name'], 'storm name')
    _identifier(sample['source_storm_date_label'], 'storm date label')
    sites = sample['site_samples']
    if type(sites) is not list or not 1 <= len(sites) <= MAX_ASSETS:
        raise DamagePreviewError('bounded nonempty site-sample list required')
    if sample['site_count'] != len(sites) or type(sample['site_count']) is not int:
        raise DamagePreviewError('site_count does not match supplied gust observations')
    result = {}
    seen_native_cells = {}
    for row in sites:
        _exact(row, SITE_FIELDS, 'source-native sampled site')
        sid = _identifier(row['site_id'], 'site_id')
        if sid in result:
            raise DamagePreviewError('duplicate sampled site')
        x = _integer(row['native_cell_x'], 'native lon index', 0, 268)
        y = _integer(row['native_cell_y'], 'native lat index', 0, 180)
        lon = _finite(row['selected_cell_center_lon'], 'selected native longitude', -180, 180)
        lat = _finite(row['selected_cell_center_lat'], 'selected native latitude', -90, 90)
        ratio = _finite(row['relative_max_gust_dimensionless'], 'native gust ratio', 0, 100)
        gust = _millimeters_per_second(row['absolute_max_gust_m_s'])
        # Repeated marker labels at the very same original grid cell are
        # not independent samples; they must have identical source fields.
        # No spatial diversification or extra hazard observation is inferred.
        cell = (x, y)
        source_values = (lon, lat, ratio, gust)
        if cell in seen_native_cells and seen_native_cells[cell] != source_values:
            raise DamagePreviewError('conflicting native source values for one ERA5 grid cell')
        seen_native_cells[cell] = source_values
        result[sid] = gust
    return result


def _curves(vulnerability):
    _exact(vulnerability, {'schema_version','physical_intensity_measure','normalized_unit',
                           'model_evidence','curves'}, 'explicit synthetic VLT')
    expected = {
        'schema_version': VLT_SCHEMA,
        'physical_intensity_measure': MEASURE,
        'normalized_unit': 'mm/s',
        'model_evidence': 'USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION',
    }
    for name, value in expected.items():
        if vulnerability.get(name) != value or type(vulnerability[name]) is not type(value):
            raise DamagePreviewError(f'{name}: unsupported loss function basis')
    rows = vulnerability['curves']
    if type(rows) is not list or not 1 <= len(rows) <= 50:
        raise DamagePreviewError('one or more explicit, bounded VLT curves required')
    curves = {}
    for row in rows:
        _exact(row, {'taxonomy','gust_knots_mm_s','damage_ratio_bps'}, 'VLT row')
        tax = _identifier(row['taxonomy'], 'taxonomy')
        knots = row['gust_knots_mm_s']
        ratios = row['damage_ratio_bps']
        if (tax in curves or type(knots) is not list or type(ratios) is not list
                or not 2 <= len(knots) == len(ratios) <= 20):
            raise DamagePreviewError('VLT curve length/identity invalid')
        for k, r in zip(knots, ratios):
            _integer(k, 'gust knot', 0, 200_000)
            _integer(r, 'damage ratio bps', 0, 10000)
        if (knots[0] != 0 or ratios[0] != 0 or
                any(x >= y for x, y in zip(knots, knots[1:])) or
                any(x > y for x, y in zip(ratios, ratios[1:]))):
            raise DamagePreviewError('VLT must start at zero and be nondecreasing bounded ratio')
        curves[tax] = tuple(zip(knots, ratios))
    return curves


def _ratio(gust_mm_s, points):
    if gust_mm_s > points[-1][0]:
        raise DamagePreviewError('gust above authored VLT range: no extrapolation')
    ix = bisect_right([k for k, _ in points], gust_mm_s)
    if ix >= len(points):
        return Fraction(points[-1][1])
    lo, hi = points[ix-1], points[ix]
    return Fraction(lo[1]) + Fraction(gust_mm_s-lo[0], hi[0]-lo[0]) * (hi[1]-lo[1])


def preview_conditional_damage(*, sample, synthetic_assets, vulnerabilities,
                               original_netcdf_bytes=None, original_sites_json_bytes=None):
    """Source-labeled, secondary-uncertainty-free conditional damage expectation.

    Even with the original publisher SHA, this forwarded JSON can be tampered.
    Hence it is never promoted as an authentic physical-loss source; repeat the
    original sampling against the pinned NetCDF for provider-grounded use.
    """
    site_gusts = _sample_sites(sample)
    if (original_netcdf_bytes is None) != (original_sites_json_bytes is None):
        raise DamagePreviewError('both original NetCDF and original sites JSON required for re-verification')
    reverified = original_netcdf_bytes is not None
    if reverified:
        if (type(original_netcdf_bytes) is not bytes or
                not 1 <= len(original_netcdf_bytes) <= 7_500_000 or
                type(original_sites_json_bytes) is not bytes or
                not 1 <= len(original_sites_json_bytes) <= 5_000_000):
            raise DamagePreviewError('bounded original source bytes required')
        # Import inside this optional real-source path so the 13 offline
        # financial/contract tests do not depend on a NetCDF provider reader.
        try:
            from climk_era5_synthetic_native_sample_v0 import sample_climk_era5
            reproduced = sample_climk_era5(
                original=original_netcdf_bytes,
                synthetic_sites_json=original_sites_json_bytes,
                storm_index=sample['storm_index_zero_based'],
            )
        except Exception as exc:
            raise DamagePreviewError('original NetCDF gust point-sampling re-verification failed') from exc
        if reproduced != sample:
            raise DamagePreviewError('forwarded point sample differs from independently reread source NetCDF')
    _exact(synthetic_assets, {'schema_version','synthetic_only','currency',
                              'insurer_label','rows'}, 'synthetic asset roster')
    if (synthetic_assets['schema_version'] != ASSETS_SCHEMA or
            synthetic_assets['synthetic_only'] is not True or
            synthetic_assets['currency'] != 'EUR'):
        raise DamagePreviewError('synthetic-only EUR roster required')
    _identifier(synthetic_assets['insurer_label'], 'synthetic insurer label')
    curves = _curves(vulnerabilities)
    assets = synthetic_assets['rows']
    if type(assets) is not list or not 1 <= len(assets) <= MAX_ASSETS:
        raise DamagePreviewError('bounded nonempty asset roster required')
    seen_assets, used_sites, total, out = set(), set(), Fraction(0), []
    for row in assets:
        _exact(row, ASSET_FIELDS, 'synthetic asset')
        aid = _identifier(row['asset_id'], 'asset_id')
        sid = _identifier(row['site_id'], 'site_id')
        tax = _identifier(row['taxonomy'], 'taxonomy')
        cost = _integer(row['replacement_cost_eur'], 'asset replacement cost EUR', 1, 10**15)
        if aid in seen_assets or sid not in site_gusts or tax not in curves:
            raise DamagePreviewError('duplicate asset, missing source site or unsupported taxonomy')
        seen_assets.add(aid)
        used_sites.add(sid)
        wind = site_gusts[sid]
        ratio = _ratio(wind, curves[tax])
        claim = ratio * cost / 10000
        total += claim
        out.append({'asset_id':aid,'site_id':sid,'taxonomy':tax,
                    'native_gust_mm_s':wind, 'replacement_cost_eur':cost,
                    'conditional_damage_ratio_bps_exact':{
                        'numerator':ratio.numerator,'denominator':ratio.denominator},
                    'conditional_expected_ground_up_eur_exact':{
                        'numerator':claim.numerator,'denominator':claim.denominator}})
    if used_sites != set(site_gusts):
        raise DamagePreviewError('all supplied source-native site samples must be mapped to synthetic assets')
    return {
        'schema_version':PREVIEW_SCHEMA,
        'status':'HISTORICAL_EXTREME_STORM_CONDITIONAL_SYNTHETIC_DAMAGE_PREVIEW_ONLY',
        'source_era5_sha256_declared':PINNED_ERA5_SHA256,
        'source_sample_json_sha256':_sha(sample),
        'source_sample_gust_values_independently_reverified':reverified,
        'synthetic_asset_roster_sha256':_sha(synthetic_assets),
        'uncalibrated_vlt_sha256':_sha(vulnerabilities),
        'source_storm_key':sample['event_key'],
        'synthetic_insurer_label':synthetic_assets['insurer_label'],
        'currency':'EUR','physical_intensity_measure':MEASURE,
        'native_grid_sampled_site_count':len(site_gusts),
        'synthetic_asset_count':len(out),
        'asset_conditional_damage':sorted(out,key=lambda row:row['asset_id']),
        'total_conditional_ground_up_eur_exact':{
            'numerator':total.numerator,'denominator':total.denominator},
        'model_assumptions':{
            'gust_normalization':'m/s => integer mm/s using decimal ROUND_HALF_UP',
            'damage_law':'piecewise_linear_user_authored_bps_no_extrapolation',
            'damage_uncertainty':'none: conditional expected loss only',
            'storm_sampling':'EXTREME_TOP_50_PER_SOURCE_NOT_AN_ANNUAL_PROBABILITY_LAW'},
        'annual_AAL':None,'annual_AEP':None,'annual_OEP':None,
        'insured_original_gross':None,'insurer_retained_net':None,
        'external_re_inward_gross':None,'external_re_retained_net':None,
        'raw_source_republication':False,
        'scientifically_calibrated':False,
        'promoted_to_financial_loss_model':False,
    }


def _json_unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise DamagePreviewError('duplicate JSON field')
        out[k] = v
    return out


def _json_constant(constant):
    raise DamagePreviewError('nonfinite JSON numeric constant is forbidden')


def _load_json(path):
    blob = Path(path).read_bytes()
    if not 1 <= len(blob) <= 5_000_000:
        raise DamagePreviewError('bounded JSON artifact required')
    try:
        return json.loads(blob,object_pairs_hook=_json_unique,parse_constant=_json_constant)
    except DamagePreviewError:
        raise
    except (UnicodeDecodeError, ValueError) as exc:
        raise DamagePreviewError('invalid source JSON') from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-sample',type=Path,required=True)
    parser.add_argument('--synthetic-assets',type=Path,required=True)
    parser.add_argument('--vlt',type=Path,required=True)
    parser.add_argument('--original-netcdf',type=Path,help='optional exact original pinned NetCDF source')
    parser.add_argument('--original-sites',type=Path,help='optional original synthetic-site JSON used by sampler')
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args(argv)
    if (args.original_netcdf is None) != (args.original_sites is None):
        parser.error('both --original-netcdf and --original-sites must be supplied together')
    inputs = [args.source_sample,args.synthetic_assets,args.vlt]
    if args.original_netcdf is not None:
        inputs.extend((args.original_netcdf,args.original_sites))
    if (args.out.is_symlink() or args.out.resolve() in {p.resolve() for p in inputs} or
            args.out.exists()):
        parser.error('output exists or aliases an input; source overwrite forbidden')
    result = preview_conditional_damage(sample=_load_json(args.source_sample),
         synthetic_assets=_load_json(args.synthetic_assets),
         vulnerabilities=_load_json(args.vlt),
         original_netcdf_bytes=(args.original_netcdf.read_bytes() if args.original_netcdf else None),
         original_sites_json_bytes=(args.original_sites.read_bytes() if args.original_sites else None))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
