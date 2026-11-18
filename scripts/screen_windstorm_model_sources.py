# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exhaustive catalogue-entry screening, NOT scientific admission or live verification."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'hazard_events': {'windstorm', 'wind', 'reanalysis', 'storm_track', 'tracks', 'stochastic_events', 'synthetic_hazard', 'hourly_weather'},
    'wind_observations': {'station_observations', 'in_situ_observations', 'weather_observations', 'hourly_weather', 'climate_observation'},
    'local_wind_modifiers': {'terrain', 'topography', 'elevation', 'land_cover', 'land_use', 'roof_geometry', 'vegetation', 'surface_model', 'wind_exposure'},
    'exposure': {'buildings', 'building_footprints', 'building_attributes', 'building_stock', 'exposure', 'floor_area', 'building_materials', 'roof', 'occupancy', 'building_age', 'building_height'},
    'replacement_values': {'construction_cost', 'replacement_value', 'replacement_value_proxy', 'valuation_proxy', 'valuation_proxies', 'asset_valuation', 'repair_costs'},
    'response': {'vulnerability', 'fragility', 'building_damage', 'damage_observation', 'observed_damage'},
    'loss_validation': {'claims', 'insurance_claims', 'insured_losses', 'economic_losses', 'disaster_loss', 'loss_benchmarks', 'reported_damage', 'historical_losses', 'losses', 'loss'},
    'financial_context': {'insurance_policies', 'reinsurance', 'insured_exposure', 'insurance_market'},
}

def classify(entry):
    categories = set(entry.get('categories', []))
    hits = {role: sorted(categories & terms) for role, terms in RULES.items() if categories & terms}
    return {
        'component_matches': hits,
        'screen_status': 'candidate_requires_geography_semantics_review' if hits else 'no_category_match_not_proven_irrelevant',
        'tropical_cyclone_transfer_review_required': 'tropical_cyclone' in categories,
        'scientifically_admitted_by_screen': False,
        'download_verified_by_screen': False,
    }

def build(root=ROOT):
    records, files = [], []
    for path in sorted((root / 'landscape').glob('*.json')):
        raw = path.read_bytes()
        data = json.loads(raw)
        entries = data.get('entries', []) if isinstance(data, dict) else []
        files.append({'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(raw).hexdigest(), 'entry_count': len(entries)})
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f'Non-object entry in {path}:{index}')
            records.append({
                'catalog': str(path.relative_to(root)), 'entry_index': index,
                'candidate_id': entry.get('candidate_id'), 'name': entry.get('name'),
                'provider_url': entry.get('authoritative_url'),
                'spatial_scope': entry.get('spatial_scope'),
                'catalogue_rights_status': entry.get('rights_review_status', 'unspecified'),
                'catalogue_admission_status': entry.get('admission_status', 'unspecified'),
                **classify(entry),
            })
    return {'schema': 'WINDSTORM_WHOLE_CHAIN_SCREEN_V1',
            'scope': 'All landscape/*.json entries; category-based discovery only; no live endpoint, rights or science approval',
            'rules': {k: sorted(v) for k, v in RULES.items()},
            'files': files, 'record_count': len(records),
            'matched_record_count': sum(bool(r['component_matches']) for r in records),
            'records': records}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + '\n')
