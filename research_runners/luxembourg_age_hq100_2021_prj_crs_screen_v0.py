# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Parse source-declared HQ100 PRJ WKT only; do not read hazard coordinates.

Publisher SHA1 / SHA256 / all ZIP CRCs and structure are checked first by
the independently tested exact-source AGE HQ100 original preflight.
CRS.to_epsg is a library hypothesis, not surveyed axis/epoch proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    inspect, HQ100OriginalError, _safe_member, MAX_PRJ_BYTES,
)


class HQ100CRSError(ValueError):
    pass


def parse_wkt(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_PRJ_BYTES:
        raise HQ100CRSError("Invalid PRJ source size")
    try:
        from pyproj import CRS, __version__ as pyproj_version
        crs = CRS.from_wkt(raw.decode("utf-8-sig"))
    except (ImportError, UnicodeError, ValueError) as exc:
        raise HQ100CRSError("Cannot identify original PRJ WKT using pinned pyproj") from exc
    epsg = crs.to_epsg(min_confidence=90)
    authority = crs.to_authority(min_confidence=90)
    axis_units = sorted({str(a.unit_name) for a in crs.axis_info
                         if a.unit_name})
    return {
        "original_prj_parsed_as_crs": True,
        "pyproj_version": pyproj_version,
        "crs_epsg_match_at_min90_confidence": epsg,
        "crs_authority_match_at_min90_confidence": (
            [authority[0], authority[1]] if authority else None),
        "original_crs_is_projected": bool(crs.is_projected),
        "original_crs_is_geographic": bool(crs.is_geographic),
        "original_crs_axis_unit_names": axis_units,
        "source_hazard_polygon_axis_and_epoch_field_verified": False,
        "source_hazard_geometry_coordinates_read": False,
        "source_hazard_depth_values_read": False,
        "spatial_join_with_geobase_authorized": False,
        "model_input_admitted": False,
    }


def audit(source_zip: Path) -> dict:
    source = Path(source_zip)
    receipt = inspect(source)
    if not receipt["shp_records_match_dbf_records"]:
        raise HQ100CRSError("Original SHP and DBF record population mismatch")
    try:
        with zipfile.ZipFile(source) as z:
            prs = [x for x in z.infolist() if x.filename.lower().endswith(".prj")]
            if len(prs) != 1:
                raise HQ100CRSError("Source archive must contain exactly one PRJ")
            _safe_member(prs[0])
            with z.open(prs[0]) as f:
                raw = f.read(MAX_PRJ_BYTES + 1)
    except (OSError, zipfile.BadZipFile) as exc:
        raise HQ100CRSError("Failed to read original PRJ from verified source") from exc
    return {
        "profile": "lu-age-hq100-2021-original-prj-crs-screen-v0",
        "original_zip_sha256": receipt["original_zip_sha256_observed"],
        "publisher_sha1_checked": True,
        **parse_wkt(raw),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.source_zip), indent=2, sort_keys=True,
                         allow_nan=False))
    except (OSError, HQ100CRSError, HQ100OriginalError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
