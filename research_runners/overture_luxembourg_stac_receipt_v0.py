# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only Overture STAC/S3 Luxembourg-city source file 00226 receipt.

Reads up to 16 KiB of provider STAC JSON, four initial plus eight final
Parquet bytes, and 8192 original footer metadata bytes. Does not read source
building rows/coordinates, persist provider files, approve model inputs or SQL.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys

from research_runners.overture_building_original_metadata_probe_v0 import (
    _default_fetch, _metadata_header, _request, ProbeError,
)

STAC_URL = "https://stac.overturemaps.org/2026-10-21.0/buildings/building/00226/00226.json"
S3_OBJECT_KEY = (
    "release/2026-10-21.0/theme=buildings/type=building/"
    "part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet"
)
S3_URL = "https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com/" + S3_OBJECT_KEY
EXPECTED_BYTES = 609459333
EXPECTED_ROWS = 5054907
EXPECTED_ROW_GROUPS_STAC = 256
MAX_STAC_BYTES = 16384
METADATA_PREFIX_BYTES = 8192
SCREEN = (6.129, 49.609, 6.131, 49.611)
SCHEMA = "opencatastrophe-overture-lu-stac-original-file-receipt-v0"


def _no_dups(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ProbeError("duplicate STAC JSON field")
        out[k] = v
    return out


def _nonfinite(x):
    raise ProbeError("nonfinite STAC JSON number")


def _source_range(fetch, start, end, etag=None):
    if (start < 0 or end < start or end >= EXPECTED_BYTES
            or end - start + 1 > METADATA_PREFIX_BYTES):
        raise ProbeError("invalid original byte range")
    limit = end - start + 1
    req = _request(S3_URL, range_header=f"bytes={start}-{end}")
    status, hdr, data = fetch(req, limit)
    if status != 206 or len(data) != limit:
        raise ProbeError("missing exact HTTP 206 byte range")
    if hdr.get("content-range") != f"bytes {start}-{end}/{EXPECTED_BYTES}":
        raise ProbeError("wrong S3 Content-Range")
    if hdr.get("content-length") != str(limit):
        raise ProbeError("wrong S3 Content-Length")
    source_etag = hdr.get("etag", "")
    if not re.fullmatch(r'"[0-9a-f]{32}(?:-\d+)?"', source_etag):
        raise ProbeError("invalid source ETag header")
    if etag and source_etag != etag:
        raise ProbeError("S3 object changed between original byte ranges")
    return data, source_etag


def probe(*, fetch=_default_fetch):
    status, _, raw = fetch(_request(STAC_URL), MAX_STAC_BYTES)
    if status != 200 or len(raw) > MAX_STAC_BYTES:
        raise ProbeError("missing/oversized original STAC item")
    try:
        item = json.loads(raw.decode("utf-8", errors="strict"),
                          object_pairs_hook=_no_dups, parse_constant=_nonfinite)
    except (ValueError, UnicodeError, TypeError) as exc:
        raise ProbeError("invalid original STAC item JSON") from exc
    if (type(item) is not dict or item.get("type") != "Feature"
            or item.get("id") != "00226" or item.get("stac_version") != "1.1.0"):
        raise ProbeError("unexpected Overture STAC identity")
    p = item.get("properties")
    if (type(p) is not dict or p.get("datetime") != "2026-10-21T00:00:00Z"
            or type(p.get("num_rows")) is not int or p["num_rows"] != EXPECTED_ROWS
            or type(p.get("num_row_groups")) is not int
            or p["num_row_groups"] != EXPECTED_ROW_GROUPS_STAC):
        raise ProbeError("STAC source release, rows or row groups changed")
    assets = item.get("assets", {})
    aws = assets.get("aws", {}) if type(assets) is dict else {}
    if (type(aws) is not dict or aws.get("href") != S3_URL
            or type(aws.get("file:size")) is not int
            or aws["file:size"] != EXPECTED_BYTES):
        raise ProbeError("STAC exact AWS asset URI/size changed")
    bbox = item.get("bbox")
    if (type(bbox) is not list or len(bbox) != 4
            or any(type(x) not in (int, float) for x in bbox)
            or not (bbox[0] < SCREEN[2] and bbox[2] > SCREEN[0]
                    and bbox[1] < SCREEN[3] and bbox[3] > SCREEN[1])):
        raise ProbeError("STAC source file does not overlap Luxembourg city bbox")
    head, etag = _source_range(fetch, 0, 3)
    tail, _ = _source_range(fetch, EXPECTED_BYTES - 8, EXPECTED_BYTES - 1, etag)
    if head != b"PAR1" or tail[4:] != b"PAR1":
        raise ProbeError("original parquet magic mismatch")
    footer = struct.unpack("<I", tail[:4])[0]
    if not 1 <= footer <= 2_000_000 or footer >= EXPECTED_BYTES - 12:
        raise ProbeError("implausible original footer size")
    offset = EXPECTED_BYTES - footer - 8
    prefix, _ = _source_range(fetch, offset, offset + METADATA_PREFIX_BYTES - 1, etag)
    parsed = _metadata_header(prefix)
    if parsed["rows_reported"] != EXPECTED_ROWS or parsed["schema_field_count"] != 63:
        raise ProbeError("original parquet header differs from STAC")
    return {
        "schema": SCHEMA, "stac_item": STAC_URL,
        "source_object": S3_OBJECT_KEY,
        "source_object_file_bytes": EXPECTED_BYTES,
        "source_object_reported_rows_not_luxembourg_rows": EXPECTED_ROWS,
        "source_stac_reported_row_groups_not_parsed": EXPECTED_ROW_GROUPS_STAC,
        "parquet_footer_length_bytes": footer,
        "source_parquet_schema_elements": parsed["schema_field_count"],
        "stac_file_bbox_intersects_luxembourg_city": True,
        "original_parquet_metadata_prefix_read_bytes": METADATA_PREFIX_BYTES,
        "original_feature_data_read": False,
        "file_sha256_verified": False, "gers_identity_verified": False,
        "source_rights_approved": False,
        "national_building_count_measured": False,
        "insurer_exposure_approved": False,
        "cat_model_input_approved": False,
        "note": "Source file extent and original Parquet metadata only, not source rows or a national building count."
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Explicit public STAC/S3 read-only probe")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: public source access requires --live", file=sys.stderr)
        return 2
    try:
        out = probe()
    except (ProbeError, OSError, ValueError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
