#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Live, bounded original-Zenodo CLIMK ERA5 → 24 *fictional* building damage receipt.

No trained vulnerability, annual frequency, gross insured loss, reinsurance,
real Zurich sites or provider data copied into Git. Output is conditional
physical loss for ONE selected historical extreme storm, not CAT AEP/OEP.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

PINNED_SHA256 = '92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102'
SCHEMA = 'oc-climk-era5-24-fictional-buildings-source-damage-receipt-v0'
STORM_INDEX = 0
EXPECTED_TIV_EUR = 240_000_000
# Existing OpenCatastrophe-data CROSS_PERIL_PHYSICAL_EVENT_EVIDENCE_V0.md
# uses these source-tested *synthetic* coordinates; they are not insured sites.
SITES = (
    ('SYNTH_CLIMK_A', 5.958677287830914, 52.41546239242131),
    ('SYNTH_CLIMK_B', 6.02, 52.47),
)


def synthetic_inputs():
    """Two known source-sampled fictional sites, 12 invented EUR10m assets each."""
    sites = {
        'schema_version': 'oc-effis-synthetic-sites-v0',
        'crs': 'OGC:CRS84',
        'synthetic_only': True,
        'sites': [
            {'site_id': sid, 'longitude': lon, 'latitude': lat}
            for sid, lon, lat in SITES
        ],
    }
    assets = {
        'schema_version': 'oc-climk-era5-synthetic-asset-roster-v0',
        'synthetic_only': True, 'currency': 'EUR',
        'insurer_label': 'ZURICH_RESEARCH_PROXY_NOT_REAL_ZURICH',
        'rows': [
            {'asset_id': f'SYNTH_BUILDING_{i:02d}',
             'site_id': SITES[i % len(SITES)][0],
             'taxonomy': 'COM_UNCALIBRATED',
             'replacement_cost_eur': 10_000_000}
            for i in range(24)
        ],
    }
    vlt = {
        'schema_version': 'oc-climk-era5-synthetic-conditional-gust-vlt-v0',
        'physical_intensity_measure': 'MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT',
        'normalized_unit': 'mm/s',
        'model_evidence': 'USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION',
        'curves': [
            {'taxonomy': 'COM_UNCALIBRATED',
             'gust_knots_mm_s': [0, 15000, 25000, 35000, 200000],
             'damage_ratio_bps': [0, 0, 100, 2000, 10000]},
        ],
    }
    sites_raw = json.dumps(sites, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=True, allow_nan=False).encode()
    return sites_raw, assets, vlt


def run_live(*, original=None, sampler=None, previewer=None):
    """Default is actual source; injected functions only support offline wiring tests.

    Import the exact upstream NetCDF source components unaltered. The new
    adapter rereads the same 6.79MB original byte buffer a SECOND time and
    checks full point-sample equality, not just matching declared hashes.
    """
    # Injection parameters exist solely for an offline wiring negative oracle.
    # On the normal CLI path these call the unchanged upstream code.
    if original is None:
        from scripts.inspect_climk_winds_era5_v0 import fetch_provider_bytes
        original = fetch_provider_bytes
    if sampler is None:
        from scripts.climk_era5_synthetic_native_sample_v0 import sample_climk_era5
        sampler = sample_climk_era5
    if previewer is None:
        from scripts.climk_era5_synthetic_damage_preview_v0 import preview_conditional_damage
        previewer = preview_conditional_damage

    fetch = original
    sample_func = sampler
    preview_func = previewer
    raw = fetch()
    if type(raw) is not bytes or not 1 <= len(raw) <= 7_500_000:
        raise ValueError('original provider source must be bounded bytes')
    sites_raw, assets, vlt = synthetic_inputs()
    sample = sample_func(original=raw, synthetic_sites_json=sites_raw,
                         storm_index=STORM_INDEX)
    damage = preview_func(sample=sample, synthetic_assets=assets,
                          vulnerabilities=vlt, original_netcdf_bytes=raw,
                          original_sites_json_bytes=sites_raw)
    if (type(damage) is not dict or
            damage.get('schema_version') != 'oc-climk-era5-synthetic-conditional-damage-preview-v0' or
            damage.get('source_sample_gust_values_independently_reverified') is not True or
            damage.get('synthetic_asset_count') != 24 or
            damage.get('native_grid_sampled_site_count') != len(SITES) or
            damage.get('annual_AAL') is not None or
            damage.get('annual_AEP') is not None or
            damage.get('annual_OEP') is not None or
            damage.get('scientifically_calibrated') is not False or
            damage.get('promoted_to_financial_loss_model') is not False or
            damage.get('currency') != 'EUR' or
            damage.get('source_storm_key') != f'climk-winds:v2:ERA5:storm-index:{STORM_INDEX}'):
        raise ValueError('live source loss-preview status or scope not satisfied')
    expected = sum(r['replacement_cost_eur'] for r in assets['rows'])
    if expected != EXPECTED_TIV_EUR:
        raise AssertionError('source-authored synthetic total TIV drifted')
    # Two synthetic site labels do not imply two independent physical
    # hazard cells: the actual fixed Kyrill source sites resolve to one cell.
    # Keep this count independent of the invented building/insurance roster.
    cells_by_site = {
        row['site_id']: (row['native_cell_x'], row['native_cell_y'])
        for row in sample['site_samples']
    }
    asset_cells = [cells_by_site[row['site_id']] for row in assets['rows']]
    distinct_cells = set(cells_by_site.values())
    if (len(cells_by_site) != len(SITES) or not distinct_cells or
            len(asset_cells) != 24):
        raise ValueError('synthetic sites/native source-cell crosswalk drift')
    most_assets_in_one_cell = max(asset_cells.count(cell) for cell in distinct_cells)
    raw_sha = sha256(raw).hexdigest()
    if raw_sha != PINNED_SHA256:
        raise ValueError('provider original bytes differ from independently pinned SHA256')
    total = damage.get('total_conditional_ground_up_eur_exact')
    if (type(total) is not dict or set(total) != {'numerator', 'denominator'} or
            type(total['numerator']) is not int or type(total['denominator']) is not int):
        raise ValueError('conditional damage total is not an exact rational EUR')
    amount = Fraction(total['numerator'], total['denominator'])
    if amount < 0 or amount > EXPECTED_TIV_EUR:
        raise ValueError('physical damage exceeds fictional building replacement value')
    # Only the public source digest, source-specific labels, two synthetic
    # gust samples and aggregate physical loss are exported, never the grid.
    return {
        'schema_version': SCHEMA,
        'status': 'ORIGINAL_SOURCE_SHA_VERIFIED_SYNTHETIC_CONDITIONAL_DAMAGE_ONLY',
        'source_origin': 'Zenodo CLIMK-WINDS v2 ERA5 exact original bytes',
        'source_sha256': raw_sha,
        'source_size_bytes': len(raw),
        'selected_storm_index_zero_based': STORM_INDEX,
        'selected_storm_name': sample['source_storm_name'],
        'selected_storm_date_label_not_utc': sample['source_storm_date_label'],
        'source_model_shared_event_identity_verified': False,
        'source_point_samples': [
            {'synthetic_site_id': x['site_id'],
             'native_cell_x': x['native_cell_x'],
             'native_cell_y': x['native_cell_y'],
             'maximum_wind_gust_m_s': x['absolute_max_gust_m_s']}
            for x in sample['site_samples']
        ],
        'point_reextract_exact_original': True,
        'distinct_native_hazard_grid_cells_sampled': len(distinct_cells),
        'source_sites_share_a_native_grid_cell': len(distinct_cells) < len(cells_by_site),
        'max_fictional_assets_sharing_one_native_grid_cell': most_assets_in_one_cell,
        'synthetic_asset_count': 24,
        'synthetic_total_replacement_cost_eur': EXPECTED_TIV_EUR,
        'synthetic_vlt_sha256': damage['uncalibrated_vlt_sha256'],
        'synthetic_asset_roster_sha256': damage['synthetic_asset_roster_sha256'],
        'conditional_physical_ground_up_eur_exact': total,
        'selection_bias': '50 MOST EXTREME HISTORICAL STORMS; NOT AN ANNUAL FREQUENCY LAW',
        'annual_AAL': None, 'annual_AEP': None, 'annual_OEP': None,
        'insurer_original_gross': None, 'insurer_retained_net': None,
        'outside_reinward_gross': None, 'outside_reretained_net': None,
        'model_calibrated': False,
        'not_representative_insurer_exposure': True,
        'raw_provider_grid_republished': False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='Optional output JSON receipt')
    args = parser.parse_args(argv)
    report = run_live()
    serialized = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n'
    if args.out:
        if args.out.exists():
            parser.error('output exists; original run receipt must not be overwritten')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized, encoding='utf-8')
    else:
        print(serialized, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
