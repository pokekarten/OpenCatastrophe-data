# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Local-only geodesic quality screen for bounded Overture Buildings GeoJSONSeq.

Reads a *previously independently lawfully acquired* release-specific sample,
never downloads data, writes to Neon, or promotes source rows into model input.
Only aggregate metrics and local-input digest leave this process; raw feature IDs,
positions, and sources stay in the input file. Input is a research-only preflight.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
from uuid import UUID

from pyproj import Geod
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.ops import orient
from shapely.errors import GEOSException

RELEASE = '2026-10-21.0'
SCHEMA = 'opencatastrophe-overture-building-geojsonseq-geodesic-preflight-v0'
MAX_INPUT_BYTES = 262_144
MAX_FEATURES = 64
MAX_FEATURE_AREA_M2 = 100_000_000
MIN_FEATURE_AREA_M2 = .01
ORIGINAL_KEY = re.compile(
    r'release/2026-10-21\.0/theme=buildings/type=building/'
    r'part-\d{5}-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}-c\d{3}\.zstd\.parquet\Z'
)
GEOD = Geod(ellps='WGS84')


class GeometryQCError(ValueError):
    """Input fails bounded scientific and source identity checks."""


def _object(pairs):
    data = {}
    for name, value in pairs:
        if name in data:
            raise GeometryQCError('duplicate JSON property')
        data[name] = value
    return data


def _nonfinite(value):
    raise GeometryQCError('nonfinite numeric constant')


def _polygon_geometry(value):
    if type(value) is not dict or set(value) != {'type', 'coordinates'}:
        raise GeometryQCError('bad geometry fields')
    kind = value['type']
    if kind not in ('Polygon', 'MultiPolygon'):
        raise GeometryQCError('only polygon footprints are admissible to screening')
    polys = [value['coordinates']] if kind == 'Polygon' else value['coordinates']
    if type(polys) is not list or not polys:
        raise GeometryQCError('no polygons')
    vertices = 0
    for poly in polys:
        if type(poly) is not list or not poly:
            raise GeometryQCError('invalid polygon rings')
        for ring in poly:
            if type(ring) is not list or len(ring) < 4 or ring[0] != ring[-1]:
                raise GeometryQCError('open or short ring')
            for coord in ring:
                if type(coord) is not list or len(coord) != 2:
                    raise GeometryQCError('coordinates must be lon/lat pairs')
                if any(type(x) not in (int, float) or not math.isfinite(x) for x in coord):
                    raise GeometryQCError('invalid lon/lat numeric values')
                if not -180 <= coord[0] <= 180 or not -90 <= coord[1] <= 90:
                    raise GeometryQCError('out of WGS84 lon/lat range')
                vertices += 1
                if vertices > 4096:
                    raise GeometryQCError('excessive polygon vertices')
    geom = shape(value)
    if geom.is_empty or not geom.is_valid or geom.area <= 0:
        raise GeometryQCError('invalid polygon topology')
    xmin, ymin, xmax, ymax = geom.bounds
    if xmax - xmin > 0.2 or ymax - ymin > 0.2:
        raise GeometryQCError('oversized or antimeridian-crossing polygon')
    return geom


def _geodesic_area(geometry):
    polygons = [geometry] if isinstance(geometry, Polygon) else list(geometry.geoms)
    area = sum(abs(GEOD.geometry_area_perimeter(orient(poly, sign=1.0))[0])
               for poly in polygons)
    if not math.isfinite(area) or not MIN_FEATURE_AREA_M2 <= area <= MAX_FEATURE_AREA_M2:
        raise GeometryQCError('implausible geodesic footprint area')
    return area


def _optional_measure(properties, field, lower, upper, *, integer=False):
    value = properties.get(field)
    if value is None:
        return None
    if type(value) not in ((int,) if integer else (int, float)):
        raise GeometryQCError(f'bad {field} type')
    if not math.isfinite(value) or not lower <= value <= upper:
        raise GeometryQCError(f'bad {field} range')
    return value


def quality_check(payload: bytes, *, release: str, original_s3_key: str):
    if release != RELEASE or not ORIGINAL_KEY.fullmatch(original_s3_key):
        raise GeometryQCError('source release / object identity is not pinned')
    if len(payload) > MAX_INPUT_BYTES or not payload:
        raise GeometryQCError('empty or oversized local sample')
    if b'\x00' in payload:
        raise GeometryQCError('binary input prohibited')
    try:
        text = payload.decode('utf-8', errors='strict')
    except UnicodeDecodeError as exc:
        raise GeometryQCError('non-UTF8 sample') from exc
    # str.splitlines treats RFC 8142 ASCII record separator (\x1e) as a break.
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    if not 1 <= len(lines) <= MAX_FEATURES:
        raise GeometryQCError('batch must contain one to 64 bounded features')
    seen_ids, seen_shapes = set(), set()
    areas, height_count, floors_count, sources_count = [], 0, 0, 0
    prohibited = {'insured_value', 'insurer_account', 'policyholder',
                  'client_id', 'policy_id', 'tiv', 'insurance_contract'}
    exact_geometry_duplicates = 0
    for raw in lines:
        raw = raw.lstrip('\x1e')
        if not raw.strip():
            raise GeometryQCError('empty input record')
        try:
            record = json.loads(raw, object_pairs_hook=_object, parse_constant=_nonfinite)
        except (ValueError, TypeError) as exc:
            raise GeometryQCError('invalid GeoJSONSeq row') from exc
        if type(record) is not dict or record.get('type') != 'Feature':
            raise GeometryQCError('not a GeoJSON feature')
        if set(record) not in ({'type', 'geometry', 'properties'},
                               {'type', 'id', 'geometry', 'properties'}):
            raise GeometryQCError('unexpected GeoJSON record fields')
        props = record['properties']
        if type(props) is not dict:
            raise GeometryQCError('missing Feature properties')
        if any(k.lower() in prohibited for k in props):
            raise GeometryQCError('private or insurer fields are prohibited')
        identity = props.get('id', record.get('id'))
        if type(identity) is not str:
            raise GeometryQCError('missing canonical Overture id')
        try:
            if str(UUID(identity)) != identity:
                raise ValueError('noncanonical uuid')
        except ValueError as exc:
            raise GeometryQCError('bad Overture UUID syntax') from exc
        if 'id' in record and 'id' in props and record['id'] != props['id']:
            raise GeometryQCError('conflicting Overture feature IDs')
        if identity in seen_ids:
            raise GeometryQCError('duplicate identity in source sample')
        seen_ids.add(identity)
        try:
            geom = _polygon_geometry(record['geometry'])
        except (GeometryQCError, GEOSException, TypeError, ValueError, AttributeError, IndexError) as exc:
            raise GeometryQCError('invalid or implausible original polygon') from exc
        boundary = props.get('bbox')
        if boundary is not None:
            if type(boundary) is not dict or set(boundary) != {'xmin', 'ymin', 'xmax', 'ymax'}:
                raise GeometryQCError('bad original bbox fields')
            expected = (boundary['xmin'], boundary['ymin'], boundary['xmax'], boundary['ymax'])
            if any(type(x) not in (float, int) or not math.isfinite(x) for x in expected):
                raise GeometryQCError('non-numeric provider bbox')
            if any(abs(x - y) > 1e-5 for x, y in zip(geom.bounds, expected)):
                raise GeometryQCError('provider bounding box and polygon disagree')
        areas.append(_geodesic_area(geom))
        height_count += _optional_measure(props, 'height', 0.01, 1200) is not None
        floors_count += _optional_measure(props, 'num_floors', 1, 250, integer=True) is not None
        datasets = props.get('sources')
        if datasets is not None:
            if type(datasets) is not list or not 1 <= len(datasets) <= 64:
                raise GeometryQCError('invalid source lineage list')
            for entry in datasets:
                if type(entry) is not dict or type(entry.get('dataset')) is not str or not entry['dataset'].strip():
                    raise GeometryQCError('original source entry lacks dataset')
            sources_count += 1
        fingerprint = hashlib.sha256(geom.normalize().wkb).digest()
        if fingerprint in seen_shapes:
            exact_geometry_duplicates += 1
        seen_shapes.add(fingerprint)
    return {
        'schema': SCHEMA,
        'source_release': release,
        'source_object_key': original_s3_key,
        'sample_sha256': hashlib.sha256(payload).hexdigest(),
        'sampled_features': len(areas),
        'geodesic_area_m2_min': round(min(areas), 2),
        'geodesic_area_m2_median': round(statistics.median(areas), 2),
        'geodesic_area_m2_max': round(max(areas), 2),
        'height_field_present': height_count,
        'floors_field_present': floors_count,
        'source_lineage_array_present': sources_count,
        'identical_shape_with_different_id_candidates': exact_geometry_duplicates,
        'input_original_source_bytes_verified': False,
        'original_file_sha256_verified': False,
        'gers_registry_identity_approved': False,
        'independent_source_rights_approved': False,
        'admitted_model_input': False,
        'insured_value_inferred': False,
        'neon_written': False,
        'note': ('Local input is a bounded, unverified derivative of claimed original source. '
                 'Area is WGS84 geodesic footprint, not gross floor area or insured replacement value.')
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--release', required=True)
    parser.add_argument('--source-object-key', required=True)
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise GeometryQCError('input must be a regular non-symlink file')
        if args.input.stat().st_size > MAX_INPUT_BYTES:
            raise GeometryQCError('oversized file')
        result = quality_check(args.input.read_bytes(), release=args.release,
                               original_s3_key=args.source_object_key)
    except (OSError, GeometryQCError, ValueError) as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
