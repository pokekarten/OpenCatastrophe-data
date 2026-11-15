#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded offline original-byte WFP CHIRPS3-GEFS STAC collection preflight.

Only provider metadata. Never queries items, opens COGs, normalizes rainfall
units, infers historical forecast vintages or admits an insurance model input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

COLLECTION_IDS = {
    "daily": "chirps_daily_forecast",
    "dekad": "chirps_dekad_forecast",
}
HOST_ROOT = "https://api.earthobservation.vam.wfp.org/stac/collections/"
MAX_BYTES = 131072
SHA_RE = re.compile(r"[a-f0-9]{64}\Z")


class Blocked(ValueError):
    """Changed, unproven or oversized official metadata is not admitted."""


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for k, v in pairs:
        if k in out:
            raise Blocked("duplicate metadata JSON key")
        out[k] = v
    return out


def _reject_constant(_: str) -> None:
    raise Blocked("non-finite metadata number")


def inspect(original: bytes, collection: str) -> dict[str, object]:
    if collection not in COLLECTION_IDS:
        raise Blocked("unreviewed WFP collection")
    if type(original) is not bytes or not 0 < len(original) <= MAX_BYTES:
        raise Blocked("empty or oversized provider metadata")
    try:
        record = json.loads(original.decode("utf-8"), object_pairs_hook=_unique,
                            parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Blocked("invalid strict provider JSON") from exc
    if type(record) is not dict or "error" in record or "features" in record:
        raise Blocked("expected one STAC Collection, never features")
    cid = COLLECTION_IDS[collection]
    if record.get("id") != cid or record.get("type") != "Collection":
        raise Blocked("incorrect STAC collection identity")
    if record.get("stac_version") != "1.0.0":
        raise Blocked("unsupported STAC protocol version")
    if record.get("license") != "CC-BY-4.0":
        raise Blocked("unexpected source licence identifier")
    extent = record.get("extent")
    if type(extent) is not dict or type(extent.get("spatial")) is not dict or type(extent.get("temporal")) is not dict:
        raise Blocked("incomplete STAC extent")
    if extent["spatial"].get("bbox") != [[-180, -60, 180, 60]]:
        raise Blocked("changed global 60-degree-latitude bbox")
    interval = extent["temporal"].get("interval")
    if interval != [["2001-01-01T00:00:00Z", None]]:
        raise Blocked("unexpected temporal start or interval")
    providers = record.get("providers")
    if type(providers) is not list or not any(
        type(p) is dict and p.get("name") == "Climate Hazards Center (CHC)"
        and type(p.get("roles")) is list and "producer" in p["roles"]
        for p in providers
    ):
        raise Blocked("original CHC producer lineage not attested")
    links = record.get("links")
    if type(links) is not list or not any(
        type(l) is dict and l.get("rel") == "self"
        and l.get("href") == HOST_ROOT + cid for l in links
    ):
        raise Blocked("exact original STAC collection self link not present")
    assets = record.get("item_assets")
    if type(assets) is not dict or "band" not in assets:
        raise Blocked("no band item-assets metadata")
    band = assets["band"]
    if type(band) is not dict or band.get("type") != "image/tiff; application=geotiff; profile=cloud-optimized":
        raise Blocked("wrong forecast data asset representation")
    rbands = band.get("raster:bands")
    if type(rbands) is not list or len(rbands) != 1 or type(rbands[0]) is not dict:
        raise Blocked("ambiguous or missing raster band metadata")
    spec = rbands[0]
    if spec.get("data_type") != "float32" or spec.get("nodata") != -9999 or type(spec.get("nodata")) not in (int, float):
        raise Blocked("unreviewed raster data type or nodata")
    if spec.get("unit") != "1":
        raise Blocked("reported original unit changed; rerun scientific units review")
    return {
        "profile": "wfp-chirps3-gefs-stac-collection-original-metadata-v0",
        "collection": collection,
        "collection_id": cid,
        "provider_collection_url": HOST_ROOT + cid,
        "stac_version": "1.0.0",
        "bbox": [-180, -60, 180, 60],
        "start_time": "2001-01-01T00:00:00Z",
        "raster_band_unit_as_published": "1",
        "raster_band_nodata": -9999,
        "raster_band_dtype": "float32",
        "precipitation_unit_mm_verified": False,
        "original_issue_time_verified": False,
        "original_cog_bytes_acquired": False,
        "forecast_as_of_validation_allowed": False,
        "insured_loss_model_input_admitted": False,
    }


def verify(path: Path, sha256: str, collection: str) -> dict[str, object]:
    if type(sha256) is not str or not SHA_RE.fullmatch(sha256):
        raise Blocked("original metadata SHA-256 must be 64 lower-case hex characters")
    with path.open("rb") as f:
        raw = f.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        raise Blocked("empty or oversized original metadata")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != sha256:
        raise Blocked("source byte hash mismatch")
    return {
        **inspect(raw, collection),
        "original_metadata_bytes_checked": True,
        "original_metadata_bytes": len(raw),
        "original_metadata_sha256": digest,
        "http_response_provenance_independently_verified": False,
        "provider_bytes_committed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True, choices=sorted(COLLECTION_IDS))
    parser.add_argument("--original-json", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify(args.original_json, args.expected_sha256, args.collection)
    except (Blocked, OSError) as exc:
        print("BLOCKED: " + str(exc))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
