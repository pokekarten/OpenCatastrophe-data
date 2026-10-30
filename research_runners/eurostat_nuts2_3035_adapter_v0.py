# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, version-pinned Eurostat NUTS2 GeoJSON -> CAT spatial-overlay input.

Use *two independent source files* for the SAME NUTS vintage:
  pub/v2/{vintage}/3035/20M/nutsrg_2.json: exact EPSG:3035 polygons;
  pub/v2/{vintage}/4326/20M/nutsrg_2.json: code coverage reference.

Important: these provider GeoJSON assets omit an explicit CRS attribute in the
projected variant. CRS comes ONLY from a separately verified original source
path and an independently approved SHA256, not from numeric coordinate guesses.
No Git redistribution or insurer portfolio is authorized by this converter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ID = re.compile(r'^[A-Z]{2}[A-Z0-9]{2}$')
COUNTRY = re.compile(r'^[A-Z]{2}$')
SHA = re.compile(r'^[a-f0-9]{64}$')
SUPPORTED = {'2021', '2024'}
BASE = 'https://raw.githubusercontent.com/eurostat/Nuts2json/master/pub/v2'


class AdapterError(ValueError):
    """Source shape, pinned-vintage or geographical coverage fails closed."""


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _parse(blob: bytes, name: str) -> list[dict]:
    try:
        doc = json.loads(blob)
    except (UnicodeError, ValueError) as exc:
        raise AdapterError(f'{name}: invalid JSON') from exc
    if not isinstance(doc, dict) or doc.get('type') != 'FeatureCollection':
        raise AdapterError(f'{name}: expected FeatureCollection')
    if doc.get('crs') is not None:
        raise AdapterError(f'{name}: unexpected CRS metadata for known exact provider format')
    features = doc.get('features')
    if not isinstance(features, list) or not features:
        raise AdapterError(f'{name}: features must be a nonempty list')
    return features


def _feature_codes(features: list[dict], name: str) -> dict[str, dict]:
    output = {}
    for feature in features:
        if not isinstance(feature, dict) or feature.get('type') != 'Feature':
            raise AdapterError(f'{name}: invalid feature')
        properties = feature.get('properties')
        if not isinstance(properties, dict):
            raise AdapterError(f'{name}: invalid properties')
        code = properties.get('id')
        if not isinstance(code, str) or not ID.fullmatch(code):
            raise AdapterError(f'{name}: invalid NUTS2 code')
        if code in output:
            raise AdapterError(f'{name}: duplicate NUTS2 {code}')
        if not isinstance(properties.get('na'), str) or not properties['na'].strip():
            raise AdapterError(f'{name}: missing region name for {code}')
        output[code] = feature
    return output


def _validate_area(geometry: object, code: str) -> float:
    from shapely.geometry import shape
    if not isinstance(geometry, dict) or geometry.get('type') not in ('Polygon', 'MultiPolygon'):
        raise AdapterError(f'{code}: projected region must be Polygon/MultiPolygon')
    try:
        polygon = shape(geometry)
    except (ValueError, TypeError, AttributeError) as exc:
        raise AdapterError(f'{code}: invalid polygon coordinates') from exc
    if polygon.is_empty or not polygon.is_valid or not polygon.area > 0:
        raise AdapterError(f'{code}: polygon invalid or empty; no automatic repair')
    if not all(math.isfinite(v) for v in polygon.bounds):
        raise AdapterError(f'{code}: nonfinite geometry')
    # EPSG:3035 is metre-based. Bounds here are intentionally permissive; they
    # protect only against blatantly unprojected lon/lat coordinates, not CRS fraud.
    if max(abs(v) for v in polygon.bounds) < 1000:
        raise AdapterError(f'{code}: source coordinates look unprojected, not EPSG:3035')
    return polygon.area


def convert(projected_geojson: bytes, geographic_reference_geojson: bytes,
            vintage: str, countries: tuple[str, ...]) -> tuple[dict, dict]:
    """Produce exactly the input schema accepted by regional_wind overlay v0."""
    if vintage not in SUPPORTED:
        raise AdapterError('only NUTS vintages 2021 and 2024 are explicitly supported')
    if (not countries or any(not isinstance(c, str) or not COUNTRY.fullmatch(c) for c in countries)
            or len(countries) != len(set(countries))):
        raise AdapterError('countries must be explicit unique upper-case ISO2 codes')
    projected = _feature_codes(_parse(projected_geojson, 'EPSG3035'), 'EPSG3035')
    geographic = _feature_codes(_parse(geographic_reference_geojson, 'EPSG4326'), 'EPSG4326')
    projection_codes = {k for k in projected if k[:2] in countries}
    reference_codes = {k for k in geographic if k[:2] in countries}
    missing_in_projected = sorted(reference_codes - projection_codes)
    unexpected_in_projected = sorted(projection_codes - reference_codes)
    if missing_in_projected or unexpected_in_projected:
        raise AdapterError('cross-projection NUTS2 coverage mismatch: '
                           f'missing={missing_in_projected}, unexpected={unexpected_in_projected}')
    if not projection_codes:
        raise AdapterError('no regions for the requested countries')
    result = []
    summed_area = 0.0
    for code in sorted(projection_codes):
        geometry = projected[code].get('geometry')
        area = _validate_area(geometry, code)
        summed_area += area
        result.append({'nuts2': code, 'geometry': geometry})
    region_input = {
        'schema_version': 'nuts2-polygons-v0',
        'nuts_version': vintage,
        'crs': 'EPSG:3035',
        'features': result,
        'source_sha256': _sha(projected_geojson),
    }
    receipt = {
        'evidence_class': 'GEO_SOURCE_CROSS_PROJECTION_COVERAGE_CHECK_NOT_INSURED_VALUE',
        'vintage': vintage,
        'countries': sorted(countries),
        'projected_source_url': f'{BASE}/{vintage}/3035/20M/nutsrg_2.json',
        'geographic_reference_url': f'{BASE}/{vintage}/4326/20M/nutsrg_2.json',
        'projected_sha256': _sha(projected_geojson),
        'reference_sha256': _sha(geographic_reference_geojson),
        'projected_all_codes_count': len(projected),
        'reference_all_codes_count': len(geographic),
        'selected_regions_count': len(result),
        'selected_source_area_km2': round(summed_area / 1e6, 6),
        'cross_projection_missing_or_extra_codes': [],
        'selected_region_codes': sorted(projection_codes),
        'geometry_is_simplified_20M': True,
        'other_countries_not_audited': True,
        'input_files_sha256_pinned_by_caller': True,
        'real_insurer_exposure_inferred': False,
        'real_storm_cells_ingested': False,
        'losses_calculated': False,
    }
    return region_input, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('epsg3035_source', type=Path)
    parser.add_argument('epsg4326_reference', type=Path)
    parser.add_argument('--vintage', choices=['2021', '2024'], required=True)
    parser.add_argument('--country', action='append', required=True)
    parser.add_argument('--expected-3035-sha256', required=True)
    parser.add_argument('--expected-4326-sha256', required=True)
    parser.add_argument('--out', type=Path, required=True,
                        help='Local-only machine input for regional wind footprint overlay')
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    p_bytes, g_bytes = args.epsg3035_source.read_bytes(), args.epsg4326_reference.read_bytes()
    for actual, expected, label in (
        (_sha(p_bytes), args.expected_3035_sha256, 'projected'),
        (_sha(g_bytes), args.expected_4326_sha256, 'geographic reference'),
    ):
        if not SHA.fullmatch(expected) or actual != expected:
            raise AdapterError(f'{label}: SHA256 does not match independently approved source bytes')
    output, receipt = convert(p_bytes, g_bytes, args.vintage, tuple(args.country))
    if args.out.resolve() == args.receipt.resolve():
        raise AdapterError('output and receipt must be separate files')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    # No data bytes or inferred release right are committed by this tool.
    args.out.write_text(json.dumps(output, sort_keys=True, separators=(',', ':')), encoding='utf-8')
    args.receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
