# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Validate an exact RELEASED 3DBAG metadata receipt, never pin a live API by guess.

Release v2025.09.03 has its own original metadata.json. A CityJSON 2.0
serialization version in the live individual-building API is NOT proof that
the response is from this data release. An optional STATIC TILE HEADER with
its own 3DBAG release metadata may be compared to the original receipt.

This is metadata-only, offline, read-only, not a CAT source admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE_URL = "https://data.3dbag.nl/v20250903/metadata.json"
EXPECTED_VERSION = "v2025.09.03"
EXPECTED_DATE = "2025-09-03"
EXPECTED_ID = "8ebe360c-88f5-11f0-9f7f-81a0b9c40fe3"
EXPECTED_CRS = "https://www.opengis.net/def/crs/EPSG/0/7415"
EXPECTED_METADATA_URLS = {
    SOURCE_URL,
    "https://data.3dbag.nl/metadata/v20250903/metadata.json",
}
MAX_BYTES = 250_000


class ReleaseProvenanceError(ValueError):
    """Metadata source identity, date, licence, version or format mismatch."""


def _no_duplicate_keys(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ReleaseProvenanceError("duplicate JSON key in release metadata")
        d[k] = v
    return d


def _bad_constant(_value):
    raise ReleaseProvenanceError("nonfinite number in metadata")


def load(path):
    data = Path(path).read_bytes()
    if not 0 < len(data) <= MAX_BYTES:
        raise ReleaseProvenanceError("empty or oversized source metadata")
    doc = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
                     parse_constant=_bad_constant)
    return doc, hashlib.sha256(data).hexdigest()


def _list(obj, key):
    v = obj.get(key)
    if not isinstance(v, list) or not v:
        raise ReleaseProvenanceError("expected nonempty " + key)
    return v


def validate(source, *, static_cityjson_header=None):
    if not isinstance(source, dict):
        raise ReleaseProvenanceError("missing 3DBAG release metadata object")
    ident = source.get("identificationInfo")
    if not isinstance(ident, dict) or not isinstance(ident.get("citation"), dict):
        raise ReleaseProvenanceError("missing official ISO-like citation")
    citation = ident["citation"]
    if (citation.get("title") != "3DBAG"
            or citation.get("edition") != EXPECTED_VERSION
            or citation.get("date") != EXPECTED_DATE
            or citation.get("dateType") != "creation"
            or citation.get("identifier") != EXPECTED_ID):
        raise ReleaseProvenanceError("3DBAG release citation/version drift")
    refs = _list(source, "referenceSystemInfo")
    if not any(isinstance(r, dict)
               and r.get("referenceSystemIdentifier") == EXPECTED_CRS for r in refs):
        raise ReleaseProvenanceError("3DBAG source EPSG:7415 absent")
    constraints = _list(ident, "resourceConstraints")
    licence_evidence = False
    for constraint in constraints:
        if not isinstance(constraint, dict):
            continue
        for other in constraint.get("otherConstraints", []):
            if not isinstance(other, dict):
                continue
            url, label = other.get("href"), other.get("text")
            if (isinstance(url, str)
                    and re.fullmatch(r"https?://creativecommons\.org/licenses/by/4\.0/?.*", url)
                    and isinstance(label, str)
                    and "3DBAG" in label and "TU Delft" in label):
                licence_evidence = True
    if not licence_evidence:
        raise ReleaseProvenanceError("original release attribution/CC BY 4.0 evidence missing")
    dq = source.get("dataQualityInfo")
    if not isinstance(dq, dict) or not isinstance(dq.get("lineage"), dict):
        raise ReleaseProvenanceError("missing release lineage")
    sources = _list(dq["lineage"], "source")
    steps = _list(dq["lineage"], "processStep")

    tile_metadata_matches = False
    if static_cityjson_header is not None:
        if not isinstance(static_cityjson_header, dict):
            raise ReleaseProvenanceError("static tile header must be object")
        h = static_cityjson_header
        meta = h.get("metadata")
        if (h.get("type") != "CityJSON" or h.get("version") != "2.0"
                or not isinstance(meta, dict)
                or meta.get("referenceSystem") != EXPECTED_CRS
                or meta.get("version") != EXPECTED_VERSION
                or meta.get("fullMetadataUrl") not in EXPECTED_METADATA_URLS):
            raise ReleaseProvenanceError("static CityJSON header not pinned to original release")
        tile_metadata_matches = True

    return {
        "schema": "3dbag-static-release-provenance-receipt-v0",
        "release_id": EXPECTED_VERSION,
        "release_date": EXPECTED_DATE,
        "original_release_metadata_url": SOURCE_URL,
        "source_lineage_entry_count": len(sources),
        "processing_steps_in_metadata": len(steps),
        "source_epsg_7415_verified": True,
        "original_cc_by_4_attribution_found": True,
        "static_cityjson_header_exact_release_match": tile_metadata_matches,
        "live_individual_building_api_release_verified": False,
        "actual_building_volume_verified_for_this_release": False,
        "insurance_rebuild_cost_or_tiv_authorised": False,
        "source_admitted": False,
        "model_input_approved": False,
        "research_only": True,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release-metadata", type=Path, required=True,
                   help="Original official release metadata.json acquired separately")
    p.add_argument("--static-cityjson-header", type=Path,
                   help="Optional release-specific CityJSON header, NOT experimental live API")
    args = p.parse_args(argv)
    try:
        source, sha = load(args.release_metadata)
        header = load(args.static_cityjson_header)[0] if args.static_cityjson_header else None
        result = validate(source, static_cityjson_header=header)
        result["release_metadata_sha256"] = sha
    except (ValueError, OSError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
