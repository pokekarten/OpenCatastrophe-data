# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Strict, offline NUTS2 exposure × historical windstorm footprint *join*.

A matched row is NOT a claims estimate, vulnerability calibration, real company
portfolio, or PERILS-equivalent market exposure. No external data are bundled.
Input values/geometry must be separately rights-cleared by a caller.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re

NUTS2 = re.compile(r"^[A-Z]{2}[A-Z0-9]{2}$")
EXPOSURE_FIELDS = {
    'record_id', 'dataset_id', 'as_of_date', 'nuts_version', 'nuts2',
    'peril', 'occupancy', 'sum_insured_eur', 'market_scope',
}
HAZARD_FIELDS = {
    'record_id', 'dataset_id', 'event_id', 'event_date', 'nuts_version',
    'nuts2', 'peril', 'gust_mps', 'aggregation',
}
OCCUPANCIES = {'residential', 'commercial_including_industrial'}


class InputError(ValueError):
    pass


def _date(s: object) -> date:
    if type(s) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        raise InputError('dates must be YYYY-MM-DD')
    try:
        return date.fromisoformat(s)
    except ValueError as exc:
        raise InputError('invalid Gregorian calendar date') from exc


def _text(s: object, key: str) -> str:
    if type(s) is not str or not s.strip():
        raise InputError(f'{key} must be nonempty text')
    return s


def _validate_region(r: dict) -> None:
    if not NUTS2.fullmatch(_text(r['nuts2'], 'nuts2')):
        raise InputError('nuts2 must be a country-prefixed NUTS-2 code')
    if not re.fullmatch(r'\d{4}', _text(r['nuts_version'], 'nuts_version')):
        raise InputError('nuts_version must be explicitly verified as four-digit vintage')


def _number(v: object, field: str) -> float:
    if type(v) not in {int, float} or not math.isfinite(v) or v < 0:
        raise InputError(f'{field} must be a finite nonnegative number')
    return float(v)


def join(payload: dict) -> dict:
    if type(payload) is not dict or set(payload) != {'exposures', 'hazards'}:
        raise InputError('expected only exposures and hazards')
    if type(payload['exposures']) is not list or type(payload['hazards']) is not list:
        raise InputError('exposures and hazards must be arrays')
    exposures = {}
    seen_record_ids = set()
    for e in payload['exposures']:
        if type(e) is not dict or set(e) != EXPOSURE_FIELDS:
            raise InputError('exposure fields do not match v0 contract')
        _validate_region(e)
        record_id = _text(e['record_id'], 'record_id')
        _text(e['dataset_id'], 'dataset_id')
        if record_id in seen_record_ids:
            raise InputError('duplicate exposure record_id')
        seen_record_ids.add(record_id)
        _date(e['as_of_date'])
        if e['peril'] != 'windstorm':
            raise InputError('only explicit windstorm coverage is supported')
        if e['occupancy'] not in OCCUPANCIES:
            raise InputError('unrecognised building occupancy')
        if e['market_scope'] != 'insurance_sample_not_full_market':
            raise InputError('no market inference from sampled exposure')
        _number(e['sum_insured_eur'], 'sum_insured_eur')
        key = (e['nuts_version'], e['nuts2'], e['peril'], e['occupancy'])
        if key in exposures:
            raise InputError('duplicate exposure spatial/peril/occupancy key; no automatic sums')
        exposures[key] = e

    matched = []
    unmatched = []
    event_keys = set()
    used_exposures = set()
    for h in payload['hazards']:
        if type(h) is not dict or set(h) != HAZARD_FIELDS:
            raise InputError('hazard fields do not match v0 contract')
        _validate_region(h)
        _text(h['record_id'], 'record_id')
        _text(h['dataset_id'], 'dataset_id')
        _text(h['event_id'], 'event_id')
        event_date = _date(h['event_date'])
        if h['peril'] != 'extratropical_windstorm':
            raise InputError('only physically defined extratropical-windstorm hazard is supported')
        if h['aggregation'] != 'max_of_footprint_grid_cells':
            raise InputError('hazard must be preaggregated explicitly from one event footprint')
        _number(h['gust_mps'], 'gust_mps')
        event_key = (h['dataset_id'], h['event_id'], h['nuts_version'], h['nuts2'])
        if event_key in event_keys:
            raise InputError('duplicate event-region hazard key')
        event_keys.add(event_key)
        candidates = [
            (k, e) for k, e in exposures.items()
            if k[0] == h['nuts_version'] and k[1] == h['nuts2'] and k[2] == 'windstorm'
        ]
        if not candidates:
            unmatched.append({'hazard_record_id': h['record_id'], 'reason': 'no_exact_nuts2_version_and_region'})
            continue
        for key, e in sorted(candidates):
            if event_date < _date(e['as_of_date']):
                unmatched.append({
                    'hazard_record_id': h['record_id'], 'exposure_record_id': e['record_id'],
                    'reason': 'exposure_snapshot_after_event_temporal_leakage',
                })
                continue
            used_exposures.add(key)
            matched.append({
                'hazard_record_id': h['record_id'], 'exposure_record_id': e['record_id'],
                'event_id': h['event_id'], 'nuts2': h['nuts2'],
                'nuts_version': h['nuts_version'], 'occupancy': e['occupancy'],
                'sum_insured_eur': e['sum_insured_eur'], 'gust_mps': h['gust_mps'],
                'hazard_to_coverage': 'extratropical_windstorm_subset_of_windstorm',
                'output_role': 'regional_exposure_hazard_comparison_only',
            })
    unused = sorted(exposures[k]['record_id'] for k in exposures.keys() - used_exposures)
    matched.sort(key=lambda r: (r['event_id'], r['nuts2'], r['occupancy']))
    unmatched.sort(key=lambda r: (r['hazard_record_id'], r.get('exposure_record_id', '')))
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return {
        'evidence_class': 'JOIN_PROOF_ONLY_NO_LOSS_MODEL',
        'input_sha256': hashlib.sha256(canonical.encode()).hexdigest(),
        'matched': matched, 'unmatched_hazards': unmatched,
        'unused_exposure_ids': unused,
        'real_insurer_allocation_inferred': False,
        'economic_or_insured_losses_calculated': False,
        'full_market_extrapolation_performed': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_json', type=Path, help='Locally prepared, rights-cleared records in v0 JSON contract')
    args = parser.parse_args()
    payload = json.loads(args.input_json.read_text(encoding='utf-8'))
    print(json.dumps(join(payload), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
