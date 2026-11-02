# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded EMSC one-event read-only connectivity preflight; never an admitted CAT source.

Explicit --probe performs one provider GET, with no redirects, retries, storage of
external data or unbounded query parameters. --fixture works entirely offline.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlencode
from urllib.request import Request, HTTPRedirectHandler, build_opener

HOST = 'https://www.seismicportal.eu'
PATH = '/fdsnws/event/1/query'
PARAMS = (
    ('format', 'json'), ('limit', '1'), ('orderby', 'time'), ('nodata', '204'),
    ('includeallorigins', 'false'), ('includearrivals', 'false'),
)
URL = HOST + PATH + '?' + urlencode(PARAMS)
MAX_BYTES = 1048576
TIMEOUT = 30
_TIMESTAMP = re.compile(r'^\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:\.\d+)?Z$')


class ProbeBlocked(ValueError):
    """Unverified or unsafe sample that must not be promoted."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _unique_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ProbeBlocked('duplicate JSON key')
        result[k] = v
    return result


def _invalid_constant(value):
    raise ProbeBlocked('non-finite JSON constant')


def validate_response(raw: bytes, *, media_type: str, status: int = 200) -> dict:
    if type(status) is not int or status != 200:
        raise ProbeBlocked('non-200 response including no-data is not evidence')
    if media_type.split(';', 1)[0].strip().lower() not in ('application/json', 'application/geo+json'):
        raise ProbeBlocked('unexpected response media type')
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ProbeBlocked('empty or oversized response')
    try:
        payload = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ProbeBlocked('invalid JSON response') from exc
    if not isinstance(payload, dict) or 'error' in payload or payload.get('type') != 'FeatureCollection':
        raise ProbeBlocked('not a valid one-event GeoJSON FeatureCollection')
    features = payload.get('features')
    if not isinstance(features, list) or len(features) != 1:
        raise ProbeBlocked('expected exactly one event')
    event = features[0]
    if not isinstance(event, dict) or event.get('type') != 'Feature':
        raise ProbeBlocked('expected GeoJSON Feature')
    geometry = event.get('geometry')
    properties = event.get('properties')
    if not isinstance(geometry, dict) or geometry.get('type') != 'Point' or not isinstance(properties, dict):
        raise ProbeBlocked('missing Point or event properties')
    coords = geometry.get('coordinates')
    if not isinstance(coords, list) or len(coords) not in (2, 3):
        raise ProbeBlocked('invalid epicentre coordinates')
    for index, coord in enumerate(coords):
        if type(coord) not in (int, float) or not math.isfinite(coord):
            raise ProbeBlocked('non-numeric event coordinate')
        if index == 0 and not -180 <= coord <= 180 or index == 1 and not -90 <= coord <= 90:
            raise ProbeBlocked('out-of-range event coordinate')
    # EMSC emits both GeoJSON coordinates and numeric origin parameters.
    # A disagreement could silently place an earthquake in the wrong region.
    if ('lon' in properties) != ('lat' in properties):
        raise ProbeBlocked('incomplete original longitude/latitude pair')
    if 'lon' in properties:
        for name, position, minimum, maximum in (('lon', 0, -180, 180), ('lat', 1, -90, 90)):
            numeric = properties[name]
            if type(numeric) not in (int, float) or not math.isfinite(numeric) or not minimum <= numeric <= maximum:
                raise ProbeBlocked('invalid original event coordinates')
            if abs(numeric - coords[position]) > 0.000001:
                raise ProbeBlocked('GeoJSON and source event coordinates disagree')
    source_id = properties.get('source_id')
    if not isinstance(source_id, str) or not 1 <= len(source_id) <= 128 or not re.fullmatch(r'[A-Za-z0-9._:-]+', source_id):
        raise ProbeBlocked('missing or unsafe source event identity')
    if 'time' in properties and 'Time' in properties and properties['time'] != properties['Time']:
        raise ProbeBlocked('conflicting event origin time aliases')
    origin_time = properties.get('time', properties.get('Time'))
    if not isinstance(origin_time, str) or not _TIMESTAMP.fullmatch(origin_time):
        raise ProbeBlocked('missing or malformed event UTC time')
    try:
        datetime.fromisoformat(origin_time.replace(' ', 'T').replace('Z', '+00:00'))
    except ValueError as exc:
        raise ProbeBlocked('invalid event calendar time') from exc
    if 'mag' in properties and 'Mag' in properties and properties['mag'] != properties['Mag']:
        raise ProbeBlocked('conflicting event magnitude aliases')
    magnitude = properties.get('mag', properties.get('Mag'))
    if magnitude is not None and (type(magnitude) not in (int, float) or not math.isfinite(magnitude) or not -3 <= magnitude <= 12):
        raise ProbeBlocked('invalid magnitude')
    return {
        'profile': 'emsc-one-event-connectivity-receipt-v0',
        'request_sha256': hashlib.sha256(URL.encode('ascii')).hexdigest(),
        'response_sha256': hashlib.sha256(raw).hexdigest(),
        'response_bytes': len(raw),
        'event_count': 1,
        'epicentre_coordinate_order': 'longitude_latitude_optional_depth',
        'has_declared_magnitude': magnitude is not None,
        'response_schema_verified': True,
        'event_identity_frozen_for_science': False,
        'original_event_completeness_verified': False,
        'raw_data_admitted': False,
        'hazard_model_admitted': False,
        'insurer_exposure_admitted': False,
        'insured_loss_computed': False,
    }


def fetch_one(*, opener=None) -> tuple[bytes, str]:
    """One exact GET. Redirects, compressed bodies and excess bytes are blocked."""
    client = opener or build_opener(NoRedirects())
    req = Request(URL, headers={'Accept': 'application/json', 'Accept-Encoding': 'identity'}, method='GET')
    with client.open(req, timeout=TIMEOUT) as response:
        if response.status != 200 or response.geturl() != URL:
            raise ProbeBlocked('unexpected response status or location')
        if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
            raise ProbeBlocked('compressed response blocked')
        content_length = response.headers.get('Content-Length')
        if content_length is not None and (not content_length.isdigit() or int(content_length) > MAX_BYTES):
            raise ProbeBlocked('oversized Content-Length')
        media_type = response.headers.get('Content-Type', '')
        if media_type.split(';', 1)[0].strip().lower() not in ('application/json', 'application/geo+json'):
            raise ProbeBlocked('unexpected response media type')
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ProbeBlocked('oversized provider body')
        return data, media_type


def read_synthetic_fixture(path: Path) -> bytes:
    """Read a local test fixture from one verified regular-file descriptor.

    Checking the path before opening would allow a symlink replacement race.
    O_NONBLOCK also ensures a FIFO/device cannot hang a validation workflow.
    """
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_NONBLOCK'):
        raise ProbeBlocked('atomic local fixture validation is unsupported')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ProbeBlocked('fixture must be a regular local file')
        if not 0 < info.st_size <= MAX_BYTES:
            raise ProbeBlocked('empty or oversized fixture')
        raw = stream.read(MAX_BYTES + 1)
        if len(raw) != info.st_size:
            raise ProbeBlocked('fixture size changed during read')
        return raw


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--fixture', type=Path, help='local synthetic GeoJSON only (offline)')
    group.add_argument('--probe', action='store_true', help='one exact provider GET, no raw data retained')
    args = parser.parse_args(argv)
    try:
        if args.probe:
            raw, media = fetch_one()
        else:
            raw, media = read_synthetic_fixture(args.fixture), 'application/json'
        receipt = validate_response(raw, media_type=media)
    except (ProbeBlocked, OSError) as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        return 1
    receipt['retrieval_utc'] = datetime.now(timezone.utc).isoformat() if args.probe else None
    receipt['network_provider_get_performed'] = bool(args.probe)
    receipt['external_bytes_persisted'] = False
    print(json.dumps(receipt, sort_keys=True, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
