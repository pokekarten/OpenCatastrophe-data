#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline exact-source GISCO census-grid identity vs an already verified pixel.

Do not query provider on its own. Accept two small original provider JSON
responses saved temporarily by an authorized process, verify their SHA-256,
and compare GRID_ID/country to the *projected raster cell centre*, not to
a user's home or policyholder. Emit no original provider response body.

The GISCO ID API "year=2021" is an independent *spatial ID* lookup.
It does NOT independently validate the 2026 V3 population count or license
commercial model/underwriting use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE_ID = "eurostat.gisco.census-population-grid.2021"
GISCO_API_GRID_PATH = "/id/censusgrid"
GISCO_API_COUNTRY_PATH = "/id/country"
SAMPLE_PIXEL_ID = 63
SAMPLE_GRID_LOOKUP_ID = 65
GRID_SHA256 = "efbc1beaf69b52af9236bfe961f648accdb765df3558306b364514a4fb63e55a"
COUNTRY_SHA256 = "a5d423959f32c3fbbe09567a54d274724c650a8332070aedeb89114c5f9362bf"
MAX_RESPONSE_BYTES = 2048


class GISCOIdentityError(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GISCOIdentityError("duplicate original provider JSON key")
        result[key] = value
    return result


def _source_attributes(raw: bytes, expected_sha256: str, required_fields: set[str]) -> dict:
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_RESPONSE_BYTES:
        raise GISCOIdentityError("invalid original provider response size")
    if not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise GISCOIdentityError("invalid original response hash")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise GISCOIdentityError("original provider response SHA-256 mismatch")
    try:
        data = json.loads(raw.decode("utf-8"),
                          object_pairs_hook=_unique_object)
    except GISCOIdentityError:
        raise
    except (UnicodeDecodeError, ValueError) as exc:
        raise GISCOIdentityError("invalid original provider JSON") from exc
    if not isinstance(data, list) or len(data) != 1:
        raise GISCOIdentityError("expected exactly one official feature")
    feature = data[0]
    if not isinstance(feature, dict) or set(feature) != {"attributes"}:
        raise GISCOIdentityError("unexpected official feature envelope")
    values = feature["attributes"]
    if not isinstance(values, dict) or set(values) != required_fields:
        raise GISCOIdentityError("unexpected source attributes")
    return values


def verify_original_gisco_cell(
    censusgrid_response: bytes,
    country_response: bytes,
    *,
    raster_x_m: int,
    raster_y_m: int,
    grid_sha256: str,
    country_sha256: str,
) -> dict:
    if (isinstance(raster_x_m, bool) or isinstance(raster_y_m, bool)
            or not isinstance(raster_x_m, int)
            or not isinstance(raster_y_m, int)):
        raise GISCOIdentityError("raster centre must be integral EPSG3035 metres")
    if raster_x_m % 1000 != 500 or raster_y_m % 1000 != 500:
        raise GISCOIdentityError("not a centre of a 1km EPSG3035 cell")

    grid = _source_attributes(
        censusgrid_response, grid_sha256,
        {"grid_id", "uid", "nuts3_id", "OBJECTID"})
    country = _source_attributes(
        country_response, country_sha256,
        {"cntr_id", "OBJECTID"})

    cntr = country["cntr_id"]
    if (not isinstance(cntr, str) or
            not re.fullmatch(r"[A-Z]{2}", cntr) or
            country["OBJECTID"] != cntr):
        raise GISCOIdentityError("original GISCO country lookup drift")
    if (not isinstance(grid["uid"], int) or isinstance(grid["uid"], bool)
            or grid["uid"] <= 0):
        raise GISCOIdentityError("original GISCO cell UID invalid")
    if (not isinstance(grid["nuts3_id"], str) or
            not re.fullmatch(r"[A-Z]{2}[0-9A-Z]{3}", grid["nuts3_id"]) or
            not grid["nuts3_id"].startswith(cntr)):
        raise GISCOIdentityError("country/NUTS3 mismatch")
    expected_id = (
        f"{cntr}_CRS3035RES1000mN{raster_y_m - 500}"
        f"E{raster_x_m - 500}"
    )
    if grid["grid_id"] != expected_id or grid["OBJECTID"] != expected_id:
        raise GISCOIdentityError("original GISCO grid ID differs from TIFF cell")
    return {
        "source_id": SOURCE_ID,
        "profile": "original-gisco-censusgrid-independent-cell-id-v0",
        "grid_id": expected_id,
        "nuts3_id": grid["nuts3_id"],
        "country_id": cntr,
        "raster_x_epsg3035_m": raster_x_m,
        "raster_y_epsg3035_m": raster_y_m,
        "official_grid_api_response_sha256": grid_sha256,
        "official_country_api_response_sha256": country_sha256,
        "original_responses_persisted": False,
        "independent_2021_v3_population_count_verified": False,
        "scientific_model_input_admitted": False,
        "commercial_underwriting_authorized": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--censusgrid-response", type=Path, required=True)
    parser.add_argument("--country-response", type=Path, required=True)
    parser.add_argument("--grid-sha256", default=GRID_SHA256)
    parser.add_argument("--country-sha256", default=COUNTRY_SHA256)
    parser.add_argument("--x", type=int, default=5018500)
    parser.add_argument("--y", type=int, default=5399500)
    args = parser.parse_args(argv)
    try:
        for path in (args.censusgrid_response, args.country_response):
            if path.is_symlink() or not path.is_file():
                raise GISCOIdentityError("original source file unavailable or symlink")
            if not 1 <= path.stat().st_size <= MAX_RESPONSE_BYTES:
                raise GISCOIdentityError("original response outside fixed byte bound")
        receipt = verify_original_gisco_cell(
            args.censusgrid_response.read_bytes(),
            args.country_response.read_bytes(),
            raster_x_m=args.x,
            raster_y_m=args.y,
            grid_sha256=args.grid_sha256,
            country_sha256=args.country_sha256,
        )
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (GISCOIdentityError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "scientific_model_input_admitted": False}),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
