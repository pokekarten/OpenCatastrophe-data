# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original XWS Daria 1990 windstorm source: independent bytes/grid/licence gate.

Only original-public CSV sources from EuropeanWindstorms.org (Met Office,
University of Reading, University of Exeter) are requested. CC BY 4.0.
No fake historical event frequency, no claimed insurer portfolio, wind
vulnerability, native Oasis CAT model or annual EP measure. Does not store
raw original CSVs or map any insurance sites at this source preflight stage.

Source footprint is maximum 3-second wind gust during a 72-hour event window.
XWS ~0.22-degree rotated-pole grid, NOT original C3S 0.25-degree EPSG:4326
and NOT NextGen's invented 0.25-degree pilot grid.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, getcontext
import hashlib
import io
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

getcontext().prec = 40
SOURCE_HOME = "https://www.europeanwindstorms.org/"
ORIGINAL_URLS = {
    "grid": SOURCE_HOME + "database/dataDesc/grid_locations.csv",
    "daria_lower95": SOURCE_HOME + "repository/Daria/Daria_biasL95.csv",
    "daria_mean": SOURCE_HOME + "repository/Daria/Daria_biasMean.csv",
    "daria_upper95": SOURCE_HOME + "repository/Daria/Daria_biasU95.csv",
}
ALLOWED_SOURCE_IDS = tuple(ORIGINAL_URLS)
MAX_SOURCE_BYTES = 24_000_000
MAX_ROWS = 300_000
MIN_ROWS = 1_000
SCHEMA = "XWS_DARIA_1990_ORIGINAL_SOURCE_CSV_LICENSE_GRID_PRECHECK_V0"
ATTRIBUTION = ("(c) Copyright Met Office, University of Reading and "
               "University of Exeter. Licensed under Creative Commons "
               "CC BY 4.0 International.")


class XWSSourceBlocked(ValueError):
    """Unreviewed original source file structure or misleading admission."""


def _decimal(text: str, *, minimum: Decimal, maximum: Decimal) -> Decimal:
    if not isinstance(text, str) or not text or text.strip() != text:
        raise XWSSourceBlocked("source decimal value malformed")
    try:
        result = Decimal(text)
    except InvalidOperation as exc:
        raise XWSSourceBlocked("unparsable source decimal") from exc
    if not result.is_finite() or not minimum <= result <= maximum:
        raise XWSSourceBlocked("original source values not physical or outside bounded domain")
    return result


def _load_rows(blob: bytes) -> list[list[str]]:
    if not isinstance(blob, bytes) or not 100 <= len(blob) <= MAX_SOURCE_BYTES:
        raise XWSSourceBlocked("original provider CSV byte size outside bound")
    try:
        content = blob.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise XWSSourceBlocked("original provider CSV non-UTF8") from exc
    reader = csv.reader(io.StringIO(content, newline=""), strict=True)
    records = []
    for row in reader:
        if not row or any(x != x.strip() for x in row):
            raise XWSSourceBlocked("empty or whitespace-mutated provider record")
        records.append(row)
        if len(records) > MAX_ROWS + 1:
            raise XWSSourceBlocked("source CSV exceeds bounded grid records")
    if not records:
        raise XWSSourceBlocked("original CSV has no content")
    return records


def _grid(blob: bytes) -> dict[int, tuple[Decimal, Decimal]]:
    records = _load_rows(blob)
    if records.pop(0) != ["Grid number", "Longitude", "Latitude"]:
        raise XWSSourceBlocked("official WGS84 grid location CSV header changed")
    if not MIN_ROWS <= len(records) <= MAX_ROWS:
        raise XWSSourceBlocked("original rotated grid expected bounded population")
    grid = {}
    for expected, row in enumerate(records):
        if len(row) != 3 or row[0] != str(expected):
            raise XWSSourceBlocked("grid identifier missing, reordered or duplicated")
        lon = _decimal(row[1], minimum=Decimal(-180), maximum=Decimal(180))
        lat = _decimal(row[2], minimum=Decimal(-90), maximum=Decimal(90))
        grid[expected] = (lon, lat)
    return grid


def _gusts(blob: bytes, count: int) -> list[Decimal]:
    records = _load_rows(blob)
    if len(records) != count:
        raise XWSSourceBlocked("storm footprint does not cover exact original XWS grid")
    result = []
    for expected, row in enumerate(records):
        if len(row) != 2 or row[0] != str(expected):
            raise XWSSourceBlocked("storm grid ID missing, reordered or repeated")
        result.append(_decimal(row[1], minimum=Decimal(0), maximum=Decimal(150)))
    return result


def validate_original_bundle(blobs: dict[str, bytes]) -> dict:
    """Validate complete original bytes, not snippets or caller-provided hashes."""
    if type(blobs) is not dict or set(blobs) != set(ALLOWED_SOURCE_IDS):
        raise XWSSourceBlocked("required four publisher original CSV families missing")
    grid = _grid(blobs["grid"])
    fields = {name: _gusts(blobs[name], len(grid))
              for name in ("daria_lower95", "daria_mean", "daria_upper95")}
    low = fields["daria_lower95"]
    mean = fields["daria_mean"]
    upper = fields["daria_upper95"]
    if any(not lo <= mid <= hi for lo, mid, hi in zip(low, mean, upper)):
        raise XWSSourceBlocked("original lower/mean/upper uncertainty pointwise order broken")
    # Show numeric ranges without copying source site's per-grid locations.
    summaries = {
        name: {
            "original_grid_points": len(values),
            "wind_gust_mps_min": str(min(values)),
            "wind_gust_mps_mean": str(sum(values) / Decimal(len(values))),
            "wind_gust_mps_max": str(max(values)),
            "points_ge_25_mps": sum(v >= 25 for v in values),
        }
        for name, values in fields.items()
    }
    return {
        "schema": SCHEMA,
        "status": "OFFICIAL_ORIGINAL_XWS_CSV_BYTES_PARSED_NOT_MODEL_ADMITTED",
        "publisher": "Extreme Wind Storms (XWS), Met Office/Reading/Exeter",
        "publisher_original_page": "https://www.europeanwindstorms.org/cgi-bin/storms/storms.cgi?storm1=Daria",
        "original_files": {
            name: {
                "url": ORIGINAL_URLS[name],
                "full_bytes": len(blobs[name]),
                "full_sha256": hashlib.sha256(blobs[name]).hexdigest(),
            }
            for name in ALLOWED_SOURCE_IDS
        },
        "source_grid_original_points": len(grid),
        "source_grid_coordinate_unit": "degrees longitude, latitude",
        "source_grid_rotated_pole_0p22_degree_native": True,
        "source_grid_wgs84_lat_lon_from_original_grid_locations": True,
        "max_gust_measure": "MAXIMUM_3_SECOND_10M_GUST_OVER_72H",
        "wind_gust_unit": "m/s",
        "storm": "Daria / Burns Day storm, January 1990",
        "three_uncertainty_variants": summaries,
        "source_license": "CC-BY-4.0",
        "required_attribution": ATTRIBUTION,
        "original_source_files_not_uploaded_to_repo": True,
        "insurer_site_specific_wind_gust_extracted": False,
        "actual_RV_insured_locations_or_values_observed": False,
        "2022_NRW_HU_physical_coordinates_crosswalk_completed": False,
        "original_XWS_storms_are_complete_unbiased_annual_event_catalogue": False,
        "wind_vulnerability_calibrated_for_German_2022_HU_GFK": False,
        "full_Germany_modelled_GUL_IL_RI_OEP_AEP": False,
        "cross_source_XWS_and_C3S_event_identity_equivalent": False,
    }


def download_official_original(*, opener=urlopen) -> dict[str, bytes]:
    result = {}
    for name in ALLOWED_SOURCE_IDS:
        url = ORIGINAL_URLS[name]
        req = Request(url, headers={
            "User-Agent": "OpenCatastrophe-XWS-original-source-metadata-research/0.1",
            "Accept": "text/csv,text/plain,application/octet-stream",
            "Accept-Encoding": "identity",
        }, method="GET")
        with opener(req, timeout=40) as response:
            if response.status != 200 or response.geturl() != url:
                raise XWSSourceBlocked("original provider HTTP status or final URL drift")
            declared = response.headers.get("Content-Length")
            if declared is not None and (
                not declared.isdecimal() or int(declared) > MAX_SOURCE_BYTES):
                raise XWSSourceBlocked("original CSV claimed Content-Length too large")
            blob = response.read(MAX_SOURCE_BYTES + 1)
        if len(blob) > MAX_SOURCE_BYTES or (declared is not None and len(blob) != int(declared)):
            raise XWSSourceBlocked("original CSV exceeds bounds or was truncated")
        result[name] = blob
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="opt in to FOUR public original CSV GETs; bounded, no raw file output")
    parser.add_argument("--out-receipt", type=Path,
                        help="write JSON metadata receipt, not third-party original CSV")
    args = parser.parse_args()
    if not args.live:
        parser.exit(2, "BLOCKED: explicit --live required for source retrieval\n")
    try:
        receipt = validate_original_bundle(download_official_original())
        payload = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.out_receipt:
            if args.out_receipt.exists() or not args.out_receipt.parent.is_dir():
                raise XWSSourceBlocked("receipt output path exists or parent is missing")
            args.out_receipt.write_text(payload, encoding="utf-8")
        print(payload)
    except (XWSSourceBlocked, OSError, ValueError) as exc:
        parser.exit(2, "XWS_ORIGINAL_SOURCE_BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
