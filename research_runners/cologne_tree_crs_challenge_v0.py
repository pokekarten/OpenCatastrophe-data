# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Five-offset original Cologne tree CRS challenge (candidate evidence only).

This research-only canary uses provider-advertised WFS `SORTBY=Baumnummer`
with fixed, bounded `COUNT=1` requests, then challenges an EPSG:25832
hypothesis against the independent Cologne KGG Stadtviertel WGS84 envelope.
No original tree rows, coordinates, identifiers or features are persisted or
printed. Geographic plausibility is NOT proof of positional accuracy, model
admission, complete exposure or permission for insured-location joins.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from cologne_public_wfs_feature_probe_v0 import WfsSampleError, inspect_geojson

# A modest five-point distributed-index sample; not statistically random,
# representative, complete or invariant when the live register changes.
OFFSETS = (0, 750, 2500, 5000, 10000)
BASE = "https://geoportal.stadt-koeln.de/wss/service/baumkataster_extern_wfs/guest"
QUERY_PREFIX = (
    "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
    "&TYPENAMES=ms:baumkataster&COUNT=1&SORTBY=Baumnummer"
)
QUERY_FORMAT = "&OUTPUTFORMAT=application%2Fjson%3B%20subtype%3Dgeojson"
MAX_BYTES = 8192
# Official city KGG Stadtviertel WFS FeatureType WGS84BoundingBox.
# This is only a spatial *envelope*, NOT an independent point-in-city proof.
KGG_BOUNDS = (6.80547870, 50.83135123, 7.16330759, 51.09018683)


class ChallengeError(ValueError):
    """An original sample, source ordering or spatial hypothesis failed."""


class DenyRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sample_url(offset: int) -> str:
    if offset not in OFFSETS:
        raise ChallengeError("unapproved WFS offset")
    return BASE + QUERY_PREFIX + "&STARTINDEX=" + str(offset) + QUERY_FORMAT


def parse_source_sample(raw: bytes) -> dict[str, object]:
    """Parse one real response in memory; return receipt and private point only."""
    try:
        evidence = inspect_geojson(raw, "tree")
        doc = json.loads(raw.decode("utf-8"))
    except (WfsSampleError, UnicodeError, ValueError) as exc:
        raise ChallengeError("original feature failed conservative schema gate") from exc
    feature = doc["features"][0]
    tree_id = feature["properties"]["Baumnummer"]
    district = feature["properties"].get("Stadtteil") or ""
    if not isinstance(district, str) or len(district) > 80:
        raise ChallengeError("invalid source district text")
    x, y = feature["geometry"]["coordinates"][:2]
    # Raw city-district label remains private to the in-memory spatial challenge.
    # It is never included in the public/human-readable receipt.
    return {
        "response_size": evidence["response_size"],
        "response_sha256": evidence["sha256"],
        "tree_id_sha256": hashlib.sha256(tree_id.encode("utf-8")).hexdigest(),
        "coords_internal": (float(x), float(y)),
        "source_stadtteil_internal": district.strip(),
        "source_crs_declaration": evidence["source_crs_declaration"],
    }


def acquire_one(offset: int) -> dict[str, object]:
    """Exactly one fixed-origin, read-only, capped original WFS GET."""
    url = sample_url(offset)
    req = Request(url, headers={
        "Accept": "application/json,application/geo+json",
        "User-Agent": "OpenCatastrophe-data-Cologne-CRS-challenge/1",
    }, method="GET")
    try:
        with build_opener(DenyRedirects).open(req, timeout=20) as response:
            if response.status != 200 or response.geturl() != url:
                raise ChallengeError("unexpected source HTTP status or redirect")
            if response.headers.get_content_type().lower() not in {
                "application/json", "application/geo+json"
            }:
                raise ChallengeError("source did not return GeoJSON media type")
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > MAX_BYTES:
                raise ChallengeError("source declared oversized original bytes")
            raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise ChallengeError("original source request failed bounded network gate") from exc
    if len(raw) > MAX_BYTES:
        raise ChallengeError("source exceeded bounded byte read")
    return parse_source_sample(raw)


def assess_crs_hypothesis(
    samples: list[dict[str, object]],
    transform,
) -> dict[str, object]:
    """Validate a candidate ETRS89/UTM32 hypothesis using an injected transform.

    A KGG bounding-box pass is a necessary plausibility condition, never a
    sufficient georeferencing or scientific validation condition.
    """
    if len(samples) != len(OFFSETS):
        raise ChallengeError("all five fixed offsets required")
    tree_ids = [s["tree_id_sha256"] for s in samples]
    if len(set(tree_ids)) != len(OFFSETS):
        raise ChallengeError("duplicate or unstable tree identifiers")
    if not all(s["source_crs_declaration"] == "not_declared" for s in samples):
        raise ChallengeError("source CRS changed; restart versioned review")
    lons, lats = [], []
    for sample in samples:
        x, y = sample["coords_internal"]
        if not (math.isfinite(x) and math.isfinite(y)
                and 250_000 <= x <= 500_000 and 5_550_000 <= y <= 5_750_000):
            raise ChallengeError("source coordinates not compatible with NRW UTM32")
        lon, lat = transform(x, y)
        if not (math.isfinite(lon) and math.isfinite(lat)):
            raise ChallengeError("non-finite transformation")
        west, south, east, north = KGG_BOUNDS
        if not (west <= lon <= east and south <= lat <= north):
            raise ChallengeError("candidate projected point outside official city envelope")
        lons.append(lon)
        lats.append(lat)
    if max(lons) - min(lons) < 0.05 or max(lats) - min(lats) < 0.05:
        raise ChallengeError("source sample insufficiently spatially distributed")
    return {
        "source": "Stadt Koeln Baumkataster public WFS",
        "provider_crs_declared": "not_declared",
        "candidate_source_crs": "EPSG:25832",
        "candidate_target_crs": "EPSG:4326",
        "source_order": "Baumnummer",
        "fixed_offsets": list(OFFSETS),
        "sample_count": len(samples),
        "all_transformed_points_inside_kgg_bbox": True,
        "bbox_is_not_polygon_containment": True,
        "transformed_span_degrees_rounded": {
            "longitude": round(max(lons) - min(lons), 3),
            "latitude": round(max(lats) - min(lats), 3),
        },
        "source_response_sha256": [s["response_sha256"] for s in samples],
        "stable_id_hashes_sha256": hashlib.sha256(
            "".join(tree_ids).encode("ascii")
        ).hexdigest(),
        "source_snapshot_pinned": False,
        "scientific_validation_complete": False,
        "model_admitted": False,
        "external_source_bytes_persisted": False,
    }


def run_live() -> dict[str, object]:
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise ChallengeError(
            "requires reviewed optional pyproj profile: "
            "pip install -r requirements-eu-flood-spatial.txt"
        ) from exc
    samples = [acquire_one(i) for i in OFFSETS]
    # One extra fixed-offset request challenges per-call deterministic ordering.
    replay = acquire_one(OFFSETS[0])
    if (replay["tree_id_sha256"] != samples[0]["tree_id_sha256"]
            or replay["coords_internal"] != samples[0]["coords_internal"]):
        raise ChallengeError("source order/coordinates changed during live challenge")
    transformer = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)
    receipt = assess_crs_hypothesis(samples, transformer.transform)
    receipt["replay_first_identity_and_coordinates_match"] = True
    receipt["observed_utc"] = datetime.now(timezone.utc).isoformat()
    receipt["verified_live"] = True
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="opt in to six bounded public provider requests")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("offline by default; pass --live to run source challenge")
    try:
        print(json.dumps(run_live(), sort_keys=True))
        return 0
    except ChallengeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
