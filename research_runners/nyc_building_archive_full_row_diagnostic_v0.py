# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline full-row *diagnostic* for a claimed NYC BUILDING 2024 archive CSV.

Builds on the independently hash-checked local file/header preflight v0.
Streams the complete source without exporting or storing original records,
individual BIN/DOITT IDs, BBLs, coordinates, paths, or insured values.
Passing says ONLY that local file structure and caller-declared counts
agree: it cannot authenticate the City of New York archival release or
its vintage, rights, completeness, geometry, building stock or insurer TIV.
"""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import csv
from datetime import datetime
import hmac
import io
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile, BadZipFile

from research_runners.nyc_building_archive_receipt_v0 import (
    ALIASES,
    ArchiveGateError,
    MAX_CSV_MEMBER_UNCOMPRESSED,
    MAX_HEADER_BYTES,
    REQUIRED,
    SOURCE_ID,
    _csv_header,
    _local_file,
    _zip_header,
    inspect as inspect_receipt,
    sha256_file,
)

MAX_ROWS = 5_000_000
MAX_CSV_FIELD_BYTES = 8 * 1024 * 1024
BIN = re.compile(r"[1-5][0-9]{6}\Z")
BBL = re.compile(r"[1-5][0-9]{9}\Z")
INTEGER = re.compile(r"[0-9]+\Z")
YEAR = re.compile(r"[12][0-9]{3}\Z")


@contextmanager
def _original_csv_stream(path: Path):
    if path.suffix.lower() == ".csv":
        with path.open("rb") as raw:
            yield raw
    elif path.suffix.lower() == ".zip":
        # Verify ZIP again immediately before reading; no extraction ever.
        _zip_header(path)
        try:
            with ZipFile(path) as archive:
                files = [info for info in archive.infolist() if not info.is_dir()]
                if len(files) != 1 or files[0].file_size > MAX_CSV_MEMBER_UNCOMPRESSED:
                    raise ArchiveGateError("unapproved ZIP CSV member count or size")
                with archive.open(files[0], "r") as raw:
                    yield raw
        except (BadZipFile, EOFError, OSError, RuntimeError) as exc:
            raise ArchiveGateError("ZIP CSV read failed") from exc
    else:
        raise ArchiveGateError("only CSV or single-CSV ZIP is supported")


def _post_2024(value: str) -> bool | None:
    """False = dated by 2024; True = later; None = missing/invalid."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.year > 2024


def _scan_rows(stream, expected_rows: int) -> dict[str, int]:
    # _csv_header consumes the first source line with a hard byte budget.
    names = _csv_header(stream)
    if not REQUIRED.issubset(names):
        raise ArchiveGateError("required reviewed NYC OTI schema missing")
    index = {key: i for i, key in enumerate(names)}
    counts = Counter()
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(MAX_CSV_FIELD_BYTES)
        with io.TextIOWrapper(stream, encoding="utf-8", errors="strict", newline="") as decoded:
            reader = csv.reader(decoded, strict=True)
            for cells in reader:
                counts["total_source_csv_rows"] += 1
                if counts["total_source_csv_rows"] > MAX_ROWS:
                    raise ArchiveGateError("source row count exceeded fixed budget")
                if len(cells) != len(names):
                    raise ArchiveGateError("CSV data row has wrong number of columns")
                # These are counts, not a validation of physical property identity.
                bin_value = cells[index["bin"]].strip()
                if not BIN.fullmatch(bin_value):
                    counts["bin_missing_or_invalid"] += 1
                elif bin_value[1:] == "000000":
                    counts["bin_unassigned_million_placeholder"] += 1
                else:
                    counts["bin_well_formed_nonplaceholder"] += 1
                doitt = cells[index["doitt_id"]].strip()
                if len(doitt) > 16 or not INTEGER.fullmatch(doitt):
                    counts["doitt_missing_or_invalid"] += 1
                elif not doitt.strip("0"):
                    counts["doitt_zero_unknown_historic_identity"] += 1
                else:
                    counts["doitt_positive_numeric_unverified_unique"] += 1
                base = cells[index["base_bbl"]].strip()
                mappluto = cells[index["mappluto_bbl"]].strip()
                if not BBL.fullmatch(base):
                    counts["base_bbl_missing_or_invalid"] += 1
                if not BBL.fullmatch(mappluto):
                    counts["mappluto_bbl_missing_or_invalid"] += 1
                if BBL.fullmatch(base) and BBL.fullmatch(mappluto):
                    counts["base_bbl_equal_billing"] += base == mappluto
                    counts["base_bbl_different_billing"] += base != mappluto
                feature = cells[index["feature_code"]].strip()
                if len(feature) > 16 or not INTEGER.fullmatch(feature):
                    counts["feature_code_missing_or_invalid"] += 1
                elif feature == "2100":
                    counts["standard_building_feature_code_2100"] += 1
                elif feature == "1003":
                    counts["placeholder_triangle_code_1003"] += 1
                else:
                    counts["other_non2100_feature"] += 1
                geometry = cells[index["the_geom"]].strip()
                if not geometry:
                    counts["geometry_missing"] += 1
                else:
                    counts["geometry_nonempty_unverified"] += 1
                year = cells[index["construction_year"]].strip()
                if not year or year == "0":
                    counts["construction_year_missing_or_zero"] += 1
                elif not YEAR.fullmatch(year):
                    counts["construction_year_malformed"] += 1
                elif int(year) > 2024:
                    counts["construction_year_after_2024"] += 1
                lastedit = cells[index["last_edited_date"]].strip()
                edit_after = _post_2024(lastedit)
                if edit_after is None:
                    counts["last_edit_missing_or_malformed"] += 1
                elif edit_after:
                    counts["last_edit_after_2024_flagged"] += 1
    except (UnicodeError, csv.Error, OverflowError) as exc:
        raise ArchiveGateError("malformed CSV source text, encoding or field") from exc
    finally:
        csv.field_size_limit(previous_limit)

    if counts["total_source_csv_rows"] != expected_rows:
        raise ArchiveGateError("actual CSV row count differs from operator-declared total")
    if counts["total_source_csv_rows"] < 1:
        raise ArchiveGateError("empty building inventory CSV")
    return {k: int(v) for k, v in sorted(counts.items())}


def scan(
    path: str,
    expected_sha256: str,
    provider_date: str,
    expected_rows: int,
    source_view: str = SOURCE_ID,
) -> dict:
    """Full local-record audit, never provider vintage/source authentication."""
    if type(expected_rows) is not int or not 1 <= expected_rows <= MAX_ROWS:
        raise ArchiveGateError("positive bounded original row-count receipt required")
    # Existing v0 validates exact source-view ID, caller date, complete
    # container fingerprint, required schema, and ZIP framing up front.
    receipt = inspect_receipt(path, expected_sha256, provider_date, source_view)
    local = _local_file(path)
    with _original_csv_stream(local) as stream:
        counts = _scan_rows(stream, expected_rows)
    # Detect changes while a large file was being parsed. A caller-supplied
    # SHA is still not a provider-signed revision/archival receipt.
    after, size_after = sha256_file(local)
    if not hmac.compare_digest(after, expected_sha256.lower()) or size_after != receipt["size_bytes"]:
        raise ArchiveGateError("source bytes changed during full-row validation")
    return {
        "profile": "nyc_building_2024_archive_full_record_diagnostic_v0",
        "source_view_id": SOURCE_ID,
        "claimed_version_date": provider_date,
        "container_sha256_matches_caller_receipt": True,
        "whole_csv_record_count_verified_against_caller_claim": True,
        "actual_local_csv_records": counts["total_source_csv_rows"],
        "anomaly_and_category_counts": counts,
        "original_source_identifiers_emitted": False,
        "original_source_rows_or_geometry_persisted": False,
        "actual_polygon_geometry_topology_validated": False,
        "global_doitt_id_uniqueness_verified": False,
        "global_bin_uniqueness_verified": False,
        "date_and_expected_row_count_provider_attested": False,
        "official_2024_inventory_release_authenticated": False,
        "source_rights_or_model_admission_approved": False,
        "insured_tiv_or_loss_calculated": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Original local CSV or ZIP; no network downloads")
    parser.add_argument("--expected-sha256", required=True, help="Externally supplied full-file SHA-256")
    parser.add_argument("--provider-version-date", required=True, help="Claimed 2024 YYYY-MM-DD snapshot date")
    parser.add_argument("--expected-rows", required=True, type=int, help="Claimed complete CSV data-row count")
    args = parser.parse_args(argv)
    try:
        result = scan(
            args.archive,
            args.expected_sha256,
            args.provider_version_date,
            args.expected_rows,
        )
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except ArchiveGateError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
