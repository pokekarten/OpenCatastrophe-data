# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline Eurostat Nuts2json *label-point* code-vintage audit, not geometry overlap.

No downloads, external data bytes, property value estimates, boundaries or inferred
historical insurance coverage are included. The user provides source files.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

_CODE = re.compile(r"^[A-Z]{2}[A-Z0-9]{2}$")
_CRS = 'urn:ogc:def:crs:OGC:1.3:CRS84'


class VintageError(ValueError):
    """Invalid vintage input: refuse automatic geographic alignment."""


def _load(blob: bytes) -> tuple[dict, int, str]:
    try:
        data = json.loads(blob)
    except (ValueError, UnicodeError) as exc:
        raise VintageError('invalid JSON') from exc
    if not isinstance(data, dict) or data.get('type') != 'FeatureCollection':
        raise VintageError('expected NUTS2 FeatureCollection')
    if data.get('name') != 'nutspt_2' or data.get('crs') != {
        'type': 'name', 'properties': {'name': _CRS}
    }:
        raise VintageError('expected Eurostat NUTS2 label points in CRS84')
    features = data.get('features')
    if not isinstance(features, list) or not features:
        raise VintageError('empty or invalid features')
    ids: dict[str, tuple[float, float]] = {}
    missing_area = 0
    for feature in features:
        if not isinstance(feature, dict) or feature.get('type') != 'Feature':
            raise VintageError('invalid feature type')
        props = feature.get('properties')
        geom = feature.get('geometry')
        if not isinstance(props, dict) or not isinstance(geom, dict):
            raise VintageError('invalid properties/geometry')
        code = props.get('id')
        if not isinstance(code, str) or not _CODE.fullmatch(code):
            raise VintageError('invalid NUTS2 region code')
        if code in ids:
            raise VintageError('duplicate NUTS2 region code')
        if not isinstance(props.get('na'), str) or not props['na'].strip():
            raise VintageError('missing region label')
        area = props.get('ar')
        if area is None:
            missing_area += 1
        elif type(area) not in (int, float) or not math.isfinite(area) or area < 0:
            raise VintageError('invalid area metadata')
        coordinates = geom.get('coordinates')
        if geom.get('type') != 'Point' or not isinstance(coordinates, list) or len(coordinates) != 2:
            raise VintageError('expected label Point, not boundary polygon')
        lon, lat = coordinates
        if (type(lon) not in (int, float) or type(lat) not in (int, float) or
                not math.isfinite(lon) or not math.isfinite(lat) or
                not -180 <= lon <= 180 or not -90 <= lat <= 90):
            raise VintageError('invalid CRS84 label coordinate')
        ids[code] = (float(lon), float(lat))
    return ids, missing_area, hashlib.sha256(blob).hexdigest()


def audit(baseline: bytes, successor: bytes, baseline_version: str, successor_version: str) -> dict:
    if baseline_version != '2021' or successor_version != '2024':
        raise VintageError('only explicitly sourced NUTS 2021 -> NUTS 2024 is supported')
    a, area_missing_a, sha_a = _load(baseline)
    b, area_missing_b, sha_b = _load(successor)
    sa, sb = set(a), set(b)
    added, removed, common = sorted(sb-sa), sorted(sa-sb), sorted(sa&sb)
    countries = sorted({code[:2] for code in sa|sb})
    return {
        'evidence_class': 'OFFICIAL_REGION_LABEL_CODE_AUDIT_NOT_POLYGON_VALIDATION',
        'baseline_version': baseline_version, 'successor_version': successor_version,
        'baseline_sha256': sha_a, 'successor_sha256': sha_b,
        'baseline_nuts2_count': len(a), 'successor_nuts2_count': len(b),
        'common_code_count': len(common),
        'retired_codes': removed, 'new_codes': added,
        'area_metadata_null_counts': {'2021': area_missing_a, '2024': area_missing_b},
        'country_code_counts': {
            country: {'2021': sum(x.startswith(country) for x in sa),
                      '2024': sum(x.startswith(country) for x in sb)}
            for country in countries
        },
        'label_points_are_not_boundaries': True,
        'unchanged_code_proves_boundary_equivalence': False,
        'real_exposure_or_losses_calculated': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path, help='Raw Eurostat 2021 nutspt_2.json')
    parser.add_argument('successor', type=Path, help='Raw Eurostat 2024 nutspt_2.json')
    parser.add_argument('--expect-baseline-sha256', required=True)
    parser.add_argument('--expect-successor-sha256', required=True)
    args = parser.parse_args()
    actual = audit(args.baseline.read_bytes(), args.successor.read_bytes(), '2021', '2024')
    if (actual['baseline_sha256'] != args.expect_baseline_sha256.lower() or
            actual['successor_sha256'] != args.expect_successor_sha256.lower()):
        raise VintageError('unapproved GeoJSON bytes / checksum mismatch')
    print(json.dumps(actual, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
