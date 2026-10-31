# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict optional Shapely overlay of NUTS2 polygons and ONE preprocessed wind footprint.

Research-only physical weather summary; no exposure, claims, CAT loss, or calibration.
The caller must locally prepare/pin/licence-clear original source assets and convert
both geometry layers into meter-based EPSG:3035 polygons without using label points.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re


class OverlayError(ValueError):
    pass


def _require_text(x: object, label: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise OverlayError(f'{label} must be nonempty text')
    return x


def _sha(x: object, label: str) -> str:
    value = _require_text(x, label)
    if not re.fullmatch(r'[0-9a-f]{64}', value):
        raise OverlayError(f'{label} must be a lowercase SHA256 digest')
    return value


def _geometry(value: object, kind: str):
    from shapely.geometry import shape
    if not isinstance(value, dict) or value.get('type') not in ('Polygon', 'MultiPolygon'):
        raise OverlayError(f'{kind} requires Polygon or MultiPolygon geometry, never label points')
    try:
        geom = shape(value)
    except (ValueError, TypeError, AttributeError) as e:
        raise OverlayError(f'{kind} cannot be parsed') from e
    if not geom.is_valid or geom.is_empty or geom.area <= 0:
        raise OverlayError(f'{kind} is invalid, empty, or zero area; no automatic repair')
    if not all(math.isfinite(v) for v in geom.bounds):
        raise OverlayError(f'{kind} has nonfinite coordinates')
    return geom


def _date(x: object) -> str:
    s = _require_text(x, 'event_date')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        raise OverlayError('event_date must be ISO YYYY-MM-DD')
    try:
        date.fromisoformat(s)
    except ValueError as e:
        raise OverlayError('invalid event_date') from e
    return s


def overlay(regions: dict, footprint: dict) -> dict:
    """Return region-level weather intersection metrics, never insurance losses.

    Input polygons must already be in EPSG:3035 metres; no silent CRS guessing.
    Footprint cell polygons must not overlap inside a region (double-count risk).
    """
    from shapely.strtree import STRtree
    from shapely.ops import unary_union

    if not isinstance(regions, dict) or set(regions) != {
        'schema_version', 'nuts_version', 'crs', 'features', 'source_sha256'
    } or not isinstance(footprint, dict) or set(footprint) != {
        'schema_version', 'source_id', 'source_sha256', 'crs',
        'event_id', 'event_date', 'peril', 'grid_cells'
    }:
        raise OverlayError('v0 metadata keys mismatch')
    if regions['schema_version'] != 'nuts2-polygons-v0' or footprint['schema_version'] != 'storm-grid-v0':
        raise OverlayError('unsupported input schemas')
    if regions['crs'] != 'EPSG:3035' or footprint['crs'] != 'EPSG:3035':
        raise OverlayError('both layers must explicitly be preprojected to EPSG:3035 metres')
    if regions['nuts_version'] not in ('2021', '2024'):
        raise OverlayError('reviewed NUTS vintage required')
    _sha(regions['source_sha256'], 'regions.source_sha256')
    _sha(footprint['source_sha256'], 'footprint.source_sha256')
    _require_text(footprint['source_id'], 'source_id')
    event_id = _require_text(footprint['event_id'], 'event_id')
    event_date = _date(footprint['event_date'])
    if footprint['peril'] != 'extratropical_windstorm':
        raise OverlayError('only extratropical windstorm footprints supported')
    if not isinstance(regions['features'], list) or not regions['features']:
        raise OverlayError('empty regions')
    if not isinstance(footprint['grid_cells'], list) or not footprint['grid_cells']:
        raise OverlayError('empty footprint cells')
    if len(footprint['grid_cells']) > 1000000:
        raise OverlayError('unbounded footprint cell count')

    region_shapes = []
    region_ids = set()
    for feature in regions['features']:
        if not isinstance(feature, dict) or set(feature) != {'nuts2', 'geometry'}:
            raise OverlayError('region feature keys mismatch')
        code = feature['nuts2']
        if not isinstance(code, str) or not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{2}', code):
            raise OverlayError('invalid NUTS2 ID')
        if code in region_ids:
            raise OverlayError('duplicate NUTS2 ID')
        region_ids.add(code)
        region_shapes.append((code, _geometry(feature['geometry'], 'region')))

    grid_shapes = []
    gusts = []
    cell_ids = set()
    for cell in footprint['grid_cells']:
        if not isinstance(cell, dict) or set(cell) != {'cell_id', 'geometry', 'max_gust_mps'}:
            raise OverlayError('grid cell keys mismatch')
        cell_id = _require_text(cell['cell_id'], 'cell_id')
        if cell_id in cell_ids:
            raise OverlayError('duplicate footprint cell ID')
        cell_ids.add(cell_id)
        gust = cell['max_gust_mps']
        if type(gust) not in (float, int) or gust < 0:
            raise OverlayError('gust must be finite, nonnegative metres per second')
        # math.isfinite(huge_int) can raise OverflowError before this module
        # returns its controlled OverlayError for unrepresentable inputs.
        try:
            numeric_gust = float(gust)
        except (OverflowError, ValueError) as exc:
            raise OverlayError('gust must be finite, nonnegative metres per second') from exc
        if not math.isfinite(numeric_gust):
            raise OverlayError('gust must be finite, nonnegative metres per second')
        grid_shapes.append(_geometry(cell['geometry'], 'grid cell'))
        gusts.append(numeric_gust)

    tree = STRtree(grid_shapes)
    output = []
    for code, region in sorted(region_shapes):
        pieces = []
        weighted = 0.0
        peak = None
        summed_area = 0.0
        for idx in tree.query(region):
            idx = int(idx)
            geom = region.intersection(grid_shapes[idx])
            area = geom.area
            if area <= 0:
                continue
            pieces.append(geom)
            summed_area += area
            weighted += gusts[idx] * area
            peak = gusts[idx] if peak is None else max(peak, gusts[idx])
        if pieces:
            union_area = unary_union(pieces).area
            tol = max(0.01, region.area * 1e-10)
            if summed_area - union_area > tol:
                raise OverlayError(f'overlapping grid cells in {code}; no duplicated area weighting')
            if summed_area > region.area + tol:
                raise OverlayError(f'footprint-covered area exceeds region {code}')
            coverage = min(1.0, summed_area / region.area)
            mean = weighted / summed_area
        else:
            coverage = 0.0
            mean = None
        output.append({
            'nuts2': code, 'nuts_version': regions['nuts_version'],
            'event_id': event_id, 'event_date': event_date,
            'region_area_km2': round(region.area / 1e6, 6),
            'covered_area_km2': round(summed_area / 1e6, 6),
            'covered_area_fraction': round(coverage, 9),
            'max_10m_gust_mps_in_covered_area': peak,
            'area_mean_10m_gust_mps_in_covered_area': None if mean is None else round(mean, 6),
            'uncovered_area_weather_unknown': coverage < 1.0 - 1e-9,
        })
    return {
        'evidence_class': 'PHYSICAL_FOOTPRINT_GEOMETRY_ONLY_NOT_INSURANCE_LOSS',
        'nuts_version': regions['nuts_version'],
        'regions_source_sha256_declared': regions['source_sha256'],
        'footprint_source_sha256_declared': footprint['source_sha256'],
        'event_source_id': footprint['source_id'],
        'event_id': event_id, 'event_date': event_date,
        'region_metrics': output,
        'real_exposure_join_performed': False,
        'insured_losses_calculated': False,
        'vulnerability_model_calibrated': False,
        'economic_losses_calculated': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('regions', type=Path, help='Local rights-cleared EPSG3035 NUTS2 polygon JSON')
    parser.add_argument('footprint', type=Path, help='Local rights-cleared projected storm cell JSON')
    parser.add_argument('--regions-input-sha256', required=True)
    parser.add_argument('--footprint-input-sha256', required=True)
    args = parser.parse_args()
    region_bytes = args.regions.read_bytes()
    footprint_bytes = args.footprint.read_bytes()
    if hashlib.sha256(region_bytes).hexdigest() != _sha(args.regions_input_sha256, 'regions digest'):
        raise OverlayError('regions file bytes do not match approved checksum')
    if hashlib.sha256(footprint_bytes).hexdigest() != _sha(args.footprint_input_sha256, 'footprint digest'):
        raise OverlayError('footprint file bytes do not match approved checksum')
    print(json.dumps(overlay(json.loads(region_bytes), json.loads(footprint_bytes)), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
