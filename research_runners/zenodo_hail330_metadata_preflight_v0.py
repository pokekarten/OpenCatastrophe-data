# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed, offline original-metadata preflight for Zenodo hail-330 v2.

Only reads a caller-supplied metadata.csv. Never downloads or opens HDF5 files.
A publisher MD5 is an integrity receipt, not an authenticity signature, rights
review, or CAT-model admission.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

PUBLISHER_METADATA_MD5 = "6b6b1d4ec919f56ded7669da3f3b2b82"
MAX_METADATA_BYTES = 16 * 1024
COLUMNS = (
    "file_name", "data_source", "country_iso3alpha", "climate_scenario",
    "res_km", "climada_datatype", "climada_name", "version",
)
COUNTRIES = (
    "ALB", "AUT", "BEL", "BIH", "CHE", "CZE", "DEU", "DNK",
    "ESP", "EST", "FRA", "GBR", "GRC", "HRV", "HUN", "IRL",
    "ITA", "LTU", "LUX", "LVA", "MKD", "MNE", "NLD", "POL",
    "PRT", "SRB", "SVK", "SVN",
)
SCENARIOS = ("REF", "PGW")


class HailMetadataError(ValueError):
    """Original metadata is absent, corrupt, drifted or inconsistent."""


def audit_metadata_bytes(data: bytes, *, require_publisher_md5: bool = True) -> dict[str, object]:
    """Check exact release identity and metadata contracts; no HDF5 content claim."""

    if not data or len(data) > MAX_METADATA_BYTES:
        raise HailMetadataError("empty or oversized metadata.csv")
    md5 = hashlib.md5(data).hexdigest()  # noqa: S324 - original publisher's MD5 receipt
    if require_publisher_md5 and md5 != PUBLISHER_METADATA_MD5:
        raise HailMetadataError("original publisher metadata.csv MD5 mismatch")
    try:
        decoded = data.decode("utf-8-sig")
        stream = io.StringIO(decoded, newline="")
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise HailMetadataError("metadata.csv columns or column order differ from Zenodo v2")
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise HailMetadataError(f"malformed UTF-8 CSV: {exc}") from exc

    expected_pairs = {(country, scenario) for country in COUNTRIES for scenario in SCENARIOS}
    seen: set[tuple[str, str]] = set()
    if len(rows) != len(expected_pairs):
        raise HailMetadataError("metadata.csv must contain exactly 56 country-scenario entries")
    for row in rows:
        if set(row) != set(COLUMNS) or any(value is None for value in row.values()):
            raise HailMetadataError("ragged or malformed CSV row")
        country, scenario = row["country_iso3alpha"], row["climate_scenario"]
        pair = (country, scenario)
        if pair not in expected_pairs or pair in seen:
            raise HailMetadataError("unknown or duplicate country/scenario")
        seen.add(pair)
        expected_filename = f"hail_{country}_{'ref' if scenario == 'REF' else 'PGW'}.h5"
        expected_name = f"hail_{country}_{scenario}"
        if (
            row["file_name"] != expected_filename
            or row["climada_name"] != expected_name
            or row["data_source"] != "model"
            or row["res_km"] != "2.2"
            or row["climada_datatype"] != "hail"
            or row["version"] != "v2"
        ):
            raise HailMetadataError(f"unexpected format/version mapping for {country}/{scenario}")
    if seen != expected_pairs:
        raise HailMetadataError("incomplete country/scenario pairs")
    return {
        "evidence_class": "ZENODO_ORIGINAL_METADATA_ONLY_NO_HDF5_OR_CAT_ADMISSION",
        "doi": "10.5281/zenodo.17860440",
        "version": "v2",
        "metadata_md5": md5,
        "metadata_sha256": hashlib.sha256(data).hexdigest(),
        "publisher_md5_checked": require_publisher_md5,
        "country_count": len(COUNTRIES),
        "scenario_count": len(SCENARIOS),
        "file_count": len(rows),
        "source_hdf5_bytes_checked": False,
        "rights_reviewed": False,
        "scientific_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata_csv", type=Path, help="external original Zenodo v2 metadata.csv")
    args = parser.parse_args(argv)
    try:
        if not args.metadata_csv.is_file() or args.metadata_csv.stat().st_size > MAX_METADATA_BYTES:
            raise HailMetadataError("missing or oversized local original metadata.csv")
        report = audit_metadata_bytes(args.metadata_csv.read_bytes())
    except (OSError, HailMetadataError) as exc:
        print(f"NOT_ADMITTED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
