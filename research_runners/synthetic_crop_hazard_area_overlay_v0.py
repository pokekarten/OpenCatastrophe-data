#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only crop parcel / hazard area intersection falsifier.

Never uses JRC source rows, insurer locations, TIV, vulnerability, or losses.
The declared EPSG:3035 CRS is a metre-based *fixture coordinate frame*;
synthetic polygons do not represent real German locations. Coverage outside
explicit hazard support is UNKNOWN, not dry. Overlap uses maximum intensity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from shapely import get_num_coordinates
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.errors import GEOSException


class OverlayError(ValueError):
    """Fail closed on geometry, provenance, bounds, or ambiguous support."""


MAX_PARCELS = 32
MAX_ZONES = 32
MAX_COORDINATES = 2000
MAX_JSON_BYTES = 200_000
TOL_M2 = 1e-6


def _geometry(value: object):
    if not isinstance(value, dict) or value.get('type') not in ('Polygon', 'MultiPolygon'):
        raise OverlayError('polygonal GeoJSON required, not points or label coordinates')
    try:
        geom = shape(value)
        if (geom.is_empty or not geom.is_valid or geom.area <= 0 or
                not math.isfinite(geom.area) or get_num_coordinates(geom) > MAX_COORDINATES or
                not all(math.isfinite(v) for v in geom.bounds)):
            raise OverlayError('invalid, empty, oversized or nonfinite polygon')
    except (GEOSException, ValueError, TypeError, IndexError, OverflowError) as exc:
        raise OverlayError('cannot parse a valid bounded polygon') from exc
    return geom


def _source_contract(payload: object, schema: str, collection: str):
    if (not isinstance(payload, dict) or set(payload) !=
            {'schema', 'crs', 'synthetic_only', 'external_source_rows_used', collection} and
            not (collection == 'zones' and isinstance(payload, dict) and set(payload) ==
                 {'schema', 'crs', 'synthetic_only', 'external_source_rows_used',
                  'event_id', 'peril', 'unit', collection})):
        raise OverlayError('unexpected synthetic input schema or metadata')
    if (payload['schema'] != schema or payload['crs'] != 'EPSG:3035' or
            payload['synthetic_only'] is not True or
            type(payload['external_source_rows_used']) is not int or
            payload['external_source_rows_used'] != 0):
        raise OverlayError('only invented local-metre fixture polygons allowed')
    return payload[collection]


def _round_area(number: float) -> float:
    if not math.isfinite(number) or number < -TOL_M2:
        raise OverlayError('nonfinite or negative intersection area')
    return round(max(0.0, number), 6)


def overlay(parcels: dict, hazard: dict) -> dict:
    """Resolve per-synthetic-field coverage and max-intensity bands in m²."""
    source = _source_contract(parcels, 'synthetic-crop-parcels-v0', 'parcels')
    zones = _source_contract(hazard, 'synthetic-crop-hazard-v0', 'zones')
    if (not isinstance(source, list) or not 1 <= len(source) <= MAX_PARCELS or
            not isinstance(zones, list) or not 1 <= len(zones) <= MAX_ZONES):
        raise OverlayError('bounded nonempty parcel and zone lists required')
    if (not isinstance(hazard['event_id'], str) or
            not re.fullmatch(r'SYNTH-EVENT-[0-9]{3}', hazard['event_id']) or
            hazard['peril'] not in ('flood', 'hail') or
            hazard['unit'] != {'flood': 'm', 'hail': 'mm'}[hazard['peril']]):
        raise OverlayError('event and hazard unit must be explicitly synthetic and peril-specific')

    fields = []
    seen_ids = set()
    for row in source:
        if not isinstance(row, dict) or set(row) != {'parcel_id', 'crop_class', 'geometry'}:
            raise OverlayError('unexpected field attributes')
        pid, crop = row['parcel_id'], row['crop_class']
        if (not isinstance(pid, str) or not re.fullmatch(r'SYNTH-CROP-[0-9]{3}', pid) or
                pid in seen_ids or crop not in ('SYNTH-WHEAT', 'SYNTH-BARLEY', 'SYNTH-MAIZE')):
            raise OverlayError('duplicated or non-synthetic crop identity')
        seen_ids.add(pid)
        geom = _geometry(row['geometry'])
        for _, _, other in fields:
            if geom.intersection(other).area > max(TOL_M2, 1e-10 * min(geom.area, other.area)):
                raise OverlayError('positive-area overlapping fields would double-count crop exposure')
        fields.append((pid, crop, geom))

    prepared = []
    seen_zones = set()
    for zone in zones:
        if not isinstance(zone, dict) or set(zone) != {'zone_id', 'geometry', 'intensity', 'nodata'}:
            raise OverlayError('unexpected hazard support attributes')
        zid = zone['zone_id']
        if (not isinstance(zid, str) or not re.fullmatch(r'SYNTH-ZONE-[0-9]{3}', zid)
                or zid in seen_zones or type(zone['nodata']) is not bool):
            raise OverlayError('duplicate, invalid or non-synthetic hazard zone')
        seen_zones.add(zid)
        raw = zone['intensity']
        if zone['nodata'] is True:
            if raw is not None:
                raise OverlayError('nodata support cannot have a numeric intensity')
            intensity = None
        else:
            if type(raw) not in (int, float) or not math.isfinite(float(raw)):
                raise OverlayError('hazard intensity must be a finite numeric physical unit')
            intensity = float(raw)
            if not 0 <= intensity <= {'flood': 100.0, 'hail': 300.0}[hazard['peril']]:
                raise OverlayError('hazard intensity outside bounded physical range')
        prepared.append((intensity, _geometry(zone['geometry'])))

    valid = [(intensity, geom) for intensity, geom in prepared if intensity is not None]
    unknown = [geom for intensity, geom in prepared if intensity is None]
    valid_union = unary_union([geom for _, geom in valid]) if valid else None
    unknown_union = unary_union(unknown) if unknown else None
    if (valid_union is not None and unknown_union is not None and
            valid_union.intersection(unknown_union).area > TOL_M2):
        raise OverlayError('nodata overlaps valid hazard: do not silently assign either class')

    result = []
    for pid, crop, field in sorted(fields):
        claimed = None
        bands = []
        for intensity in sorted(set(intensity for intensity, _ in valid), reverse=True):
            band_union = unary_union([geom for val, geom in valid if val == intensity])
            clipped = field.intersection(band_union)
            if claimed is not None:
                clipped = clipped.difference(claimed)
            area = _round_area(clipped.area)
            if area > 0:
                bands.append({'intensity': intensity, 'area_m2': area})
            claimed = clipped if claimed is None else claimed.union(clipped)
        covered = _round_area(claimed.area) if claimed is not None else 0.0
        nodata = _round_area(field.intersection(unknown_union).area) if unknown_union is not None else 0.0
        total = _round_area(field.area)
        outside = _round_area(total - covered - nodata)
        if abs(total - (covered + nodata + outside)) > max(1e-5, total * 1e-9):
            raise OverlayError('parcel support areas not conserved')
        if abs(covered - sum(b['area_m2'] for b in bands)) > max(1e-5, total * 1e-9):
            raise OverlayError('max-intensity bands did not conserve covered area')
        result.append({
            'parcel_id': pid, 'crop_class': crop, 'total_area_m2': total,
            'observed_synthetic_support_area_m2': covered,
            'explicit_nodata_area_m2': nodata, 'outside_support_unknown_area_m2': outside,
            'intensity_bands': bands,
        })
    totals = {key: _round_area(sum(item[key] for item in result)) for key in (
        'total_area_m2', 'observed_synthetic_support_area_m2',
        'explicit_nodata_area_m2', 'outside_support_unknown_area_m2')}
    return {
        'profile': 'synthetic-crop-hazard-max-intensity-area-v0',
        'event_id': hazard['event_id'], 'peril': hazard['peril'],
        'intensity_unit': hazard['unit'], 'crs': 'EPSG:3035',
        'synthetic_fixture_coordinates_not_real_locations': True,
        'maximum_intensity_wins_when_hazard_zones_overlap': True,
        'uncovered_area_is_unknown_not_zero_hazard': True,
        'parcel_count': len(result), 'zone_count': len(prepared),
        'totals': totals, 'synthetic_parcels': result,
        'original_source_rows_used': 0, 'insurer_tiv_used': False,
        'vulnerability_applied': False, 'insured_losses_calculated': False,
        'cat_model_ready': False,
    }


def _read_json(path: Path, expected_sha: str) -> dict:
    if not isinstance(expected_sha, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_sha):
        raise OverlayError('caller-pinned lowercase input SHA256 required')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
        raise OverlayError('input must be a small regular local synthetic JSON file')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise OverlayError('synthetic input SHA256 mismatch')
    try:
        return json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise OverlayError('invalid synthetic JSON') from exc


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('synthetic_parcels_json', type=Path)
    p.add_argument('synthetic_hazard_json', type=Path)
    p.add_argument('--parcels-sha256', required=True)
    p.add_argument('--hazard-sha256', required=True)
    args = p.parse_args()
    try:
        result = overlay(
            _read_json(args.synthetic_parcels_json, args.parcels_sha256),
            _read_json(args.synthetic_hazard_json, args.hazard_sha256),
        )
    except (OverlayError, GEOSException, OSError, OverflowError) as exc:
        p.exit(2, 'BLOCKED: ' + str(exc) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
