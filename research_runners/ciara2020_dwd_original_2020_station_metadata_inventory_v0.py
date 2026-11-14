# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inspect ORIGINAL 2020 DWD FX hourly station ZIP geography/device metadata.

This inventories actual publisher-supplied historical metadata before a
scientifically meaningful 2020 DWD FX911 vs ERA5 model-skill comparison.
It prints bounded source-metadata previews, names & SHA256 proofs only.
No timezone, 2020 sensor coordinates, exposure or heights are inferred
from unparsed metadata. No insurer damage functions or model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tomllib
import zipfile

import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd

SCHEMA = "CIARA2020_DWD_ORIGINAL_HISTORICAL_STATION_METADATA_INVENTORY_V0"
REQUIRED_CATEGORIES = ("geographie", "geraete", "parameter")
MAX_ZIP_FILES = 40
MAX_TOTAL_EXPANDED = 25_000_000
MAX_SINGLE_METADATA_BYTES = 250_000
MAX_PREVIEW_LINES = 12
MAX_PREVIEW_LINE_CHARS = 210


class DWDMetadataBlocked(ValueError):
    """Cannot prove exact original 2020 DWD metadata source."""


def inspect_original_metadata_zip(data: bytes, station_id: str) -> dict:
    if not re.fullmatch(r"\d{5}", station_id) or not 40 <= len(data) <= dwd.MAX_ZIP:
        raise DWDMetadataBlocked("invalid bounded original FX source ZIP or station ID")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            info = z.infolist()
            if (not 1 <= len(info) <= MAX_ZIP_FILES
                or sum(x.file_size for x in info) > MAX_TOTAL_EXPANDED
                or any(x.flag_bits & 1 or x.file_size > MAX_TOTAL_EXPANDED
                       or x.filename.startswith(("/", "\\"))
                       or "/" in x.filename or "\\" in x.filename or ".." in x.filename
                       for x in info)):
                raise DWDMetadataBlocked("unsafe or too large original DWD archive structure")
            # DWD source ZIPs may include harmless explanatory .html/.pdf
            # or other metadata files. Only the required three ORIGINAL
            # Metadaten_*.txt payloads are decoded; every other entry is
            # subject to the same path, encryption and bounded size checks.
            found = {}
            names_seen = set()
            for member in info:
                filename = member.filename
                if filename in names_seen:
                    raise DWDMetadataBlocked("duplicate original DWD metadata filename")
                names_seen.add(filename)
                if not filename.lower().startswith("metadaten_"):
                    continue
                if not filename.lower().endswith(".txt"):
                    continue
                for kind in REQUIRED_CATEGORIES:
                    if not filename.lower().startswith("metadaten_" + kind):
                        continue
                    if kind in found:
                        raise DWDMetadataBlocked("ambiguous multiple DWD historical metadata files per type")
                    if member.file_size > MAX_SINGLE_METADATA_BYTES:
                        raise DWDMetadataBlocked("original DWD metadata member oversized")
                    blob = z.read(member)
                    if len(blob) != member.file_size:
                        raise DWDMetadataBlocked("truncated original DWD metadata file")
                    try:
                        text = blob.decode("cp1252")
                    except UnicodeError as exc:
                        raise DWDMetadataBlocked("original DWD publisher metadata undecodable") from exc
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    if len(lines) < 2:
                        raise DWDMetadataBlocked("empty DWD historical source metadata")
                    found[kind] = {
                        "original_member_name": filename,
                        "original_member_sha256": hashlib.sha256(blob).hexdigest(),
                        "original_member_bytes": len(blob),
                        "nonempty_line_count": len(lines),
                        "bounded_publisher_original_first_lines_uninterpreted":
                            [line[:MAX_PREVIEW_LINE_CHARS] for line in lines[:MAX_PREVIEW_LINES]],
                    }
            if set(found) != set(REQUIRED_CATEGORIES):
                raise DWDMetadataBlocked("geography, instrument and parameter DWD original metadata must each exist")
    except (zipfile.BadZipFile, OSError, RuntimeError, UnicodeError) as exc:
        raise DWDMetadataBlocked("DWD original archive invalid or unreadable") from exc
    return {
        "original_archive_sha256": hashlib.sha256(data).hexdigest(),
        "station_id": station_id,
        "original_historical_metadata_types_verified": list(REQUIRED_CATEGORIES),
        "metadata": found,
    }


def inspect_live_original_three_2020_stations() -> dict:
    with dwd.FROZEN_FIRST_REAL_DWD_SOURCE.open("rb") as f:
        accepted = tomllib.load(f)
    if (accepted.get("schema") != dwd.SCHEMA
        or accepted.get("first_original_live_github_run_id") != 43499602678
        or accepted.get("reported_station_count") != 3
        or accepted.get("DWD_reference_timestamps_UTC_harmonization_verified") is not False
        or accepted.get("station_2020_vs_current_geography_instrument_metadata_verified") is not False):
        raise DWDMetadataBlocked("original 2020 DWD source receipt admission mismatch")
    records = accepted["stations"]
    if [x["station_id"] for x in records] != ["02667", "15200", "00603"]:
        raise DWDMetadataBlocked("source-pinned original 3 station identities changed")
    stations = []
    for record in records:
        url = record["original_archive_url"]
        data = dwd._get_publisher_bytes(url, dwd.MAX_ZIP)
        observed = inspect_original_metadata_zip(data, record["station_id"])
        if observed["original_archive_sha256"] != record["original_unmodified_zip_sha256"]:
            raise DWDMetadataBlocked("current actual DWD ZIP changed vs independently SHA-pinned source proof")
        stations.append({
            **observed,
            "DWD_original_archive_url": url,
            "publisher_reported_current_site_position_not_verified_2020": True,
        })
    return {
        "schema": SCHEMA,
        "status": "PUBLISHER_ORIGINAL_2020_DWD_STATION_METADATA_INSPECTED_NOT_YET_HISTORICALLY_INTERPRETED",
        "original_source": dwd.INDEX,
        "original_source_rights": "CC BY 4.0 with Deutscher Wetterdienst attribution",
        "station_count": len(stations),
        "stations": stations,
        "original_2020_geography_valid_from_to_interpreted": False,
        "original_2020_instrument_height_and_type_interpreted": False,
        "original_2020_observation_hour_UTC_semantics_verified": False,
        "station_to_ERA5_matched_hour_bias_or_RMSE_admitted": False,
        "native_GUL_IL_RI_OEP_AEP_insurer_loss_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.add_mutually_exclusive_group(required=True)
    args.add_argument("--dry-run", action="store_true")
    args.add_argument("--live-original-metadata", action="store_true")
    parsed = parser.parse_args()
    try:
        if parsed.dry_run:
            receipt = {
                "schema": SCHEMA,
                "station_ids": ["02667", "15200", "00603"],
                "source_data_licence": "DWD CC BY 4.0, attribution",
                "publisher_original_station_metadata_read": False,
                "2020_site_instrument_or_UTC_validated": False,
                "calibrated_model_or_insured_losses_admitted": False,
            }
        else:
            receipt = inspect_live_original_three_2020_stations()
        print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True))
        return 0
    except (DWDMetadataBlocked, dwd.OriginalDWDRejected, OSError, ValueError) as exc:
        parser.exit(2, "DWD_CIARA2020_ORIGINAL_STATION_METADATA_NO_GO: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
