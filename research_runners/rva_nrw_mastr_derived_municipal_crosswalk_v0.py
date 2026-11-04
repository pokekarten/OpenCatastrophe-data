# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only, exact-Git-blob-pinned MaStR-derived PV municipal cohort vs official NRW roof PV.

No insurer sites, installation addresses, individual names or municipality records
are exported; only count/sum diagnostics for the whole state. The MaStR source is
a THIRD-PARTY TRANSFORMATION of official data, not the federal raw export.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from xml.etree import ElementTree as ET

from research_runners import rva_nrw_original_rooftop_pv_xlsx_v0 as nrw
from research_runners import rva_nrw_original_pv_schema_observation_v0 as xlsx_schema
from research_runners import rva_nrw_original_pv_class_aggregates_v0 as xlsx_aggregates

THIRD_PARTY_COMMIT = "4208eeb39ce49eb2d12c60b0d7f3f51a7dacd9ef"
THIRD_PARTY_BLOB_SHA1 = "38d2427b792eb7418e214da18281973bcbe9f897"
THIRD_PARTY_PATH = "data/photovoltaik-gemeinden-deutschland-2026-10-02.csv"
THIRD_PARTY_URL = (
    f"https://raw.githubusercontent.com/mwhitex/solarzahlen-daten/"
    f"{THIRD_PARTY_COMMIT}/{THIRD_PARTY_PATH}"
)
THIRD_PARTY_LICENSE = "Datenlizenz Deutschland - Namensnennung - Version 2.0"
THIRD_PARTY_ATTRIBUTION = (
    "solarzahlen.de. Quelle: Marktstammdatenregister, Bundesnetzagentur "
    "(dl-de/by-2-0), Daten geändert"
)
MASTR_REPORTED_SNAPSHOT = "2026-10-02"
MAX_CSV_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 12000
EXPECTED_GERMANY_MUNICIPALITIES = 10759
EXPECTED_NRW_MUNICIPALITIES = 396
RE_AGS = re.compile(r"^[0-9]{8}$")
RE_NONNEG_INTEGER = re.compile(r"^(0|[1-9][0-9]*)$")
RE_NONNEG_DECIMAL = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")
FIELDS = (
    "ags", "einheiten_in_betrieb", "gebaeudesolaranlagen",
    "balkonkraftwerke", "freiflaeche", "sonstige", "kwp",
)
COUNTS = FIELDS[1:6]


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def fetch_secondary(*, open_url=urllib.request.urlopen) -> bytes:
    req = urllib.request.Request(
        THIRD_PARTY_URL, headers={"User-Agent": "OpenCatastrophe-original-research/1.0"},
    )
    with open_url(req, timeout=35) as response:
        chunks, total = [], 0
        while True:
            block = response.read(128 * 1024)
            if not block:
                break
            total += len(block)
            if total > MAX_CSV_BYTES:
                raise ValueError("SECONDARY_SOURCE_OVERSIZE")
            chunks.append(block)
        return b"".join(chunks)


def parse_count(raw: str) -> int:
    if not isinstance(raw, str) or not RE_NONNEG_INTEGER.fullmatch(raw):
        raise ValueError("MASTR_MUNICIPAL_NONNEG_INTEGER_REQUIRED")
    n = int(raw)
    if n > 100000000:
        raise ValueError("MASTR_MUNICIPAL_INTEGER_EXCESS")
    return n


def parse_power(raw: str) -> Decimal:
    if not isinstance(raw, str) or not RE_NONNEG_DECIMAL.fullmatch(raw):
        raise ValueError("MASTR_MUNICIPAL_KWP_INVALID")
    try:
        n = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError("MASTR_MUNICIPAL_KWP_INVALID") from exc
    if not n.is_finite() or n > Decimal("100000000000"):
        raise ValueError("MASTR_MUNICIPAL_KWP_EXCESS")
    return n


def inspect_secondary(original: bytes, *, pin_blob: bool = True) -> dict:
    if not isinstance(original, bytes) or not 100 <= len(original) <= MAX_CSV_BYTES:
        raise ValueError("SECONDARY_SOURCE_BYTES_INVALID")
    actual_blob = git_blob_sha1(original)
    if pin_blob and actual_blob != THIRD_PARTY_BLOB_SHA1:
        raise ValueError("SECONDARY_GIT_BLOB_SHA_MISMATCH")
    try:
        content = original.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("SECONDARY_CSV_UTF8_INVALID") from exc
    reader = csv.DictReader(io.StringIO(content, newline=""), delimiter=",")
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or len(fields) > 70 or not set(FIELDS).issubset(fields):
        raise ValueError("SECONDARY_CSV_SCHEMA_MISMATCH")
    if "export_datum" not in fields:
        raise ValueError("SECONDARY_EXPORT_DATE_FIELD_REQUIRED")
    count, keys = 0, set()
    nrw_keys = set()
    state_totals = Counter()
    state_power = Decimal(0)
    source_dates = set()
    category_difference_count = 0
    for row in reader:
        count += 1
        if count > MAX_RECORDS or None in row or any(v is None for v in row.values()):
            raise ValueError("SECONDARY_CSV_RECORD_STRUCTURE")
        ags = row["ags"]
        if not RE_AGS.fullmatch(ags) or ags in keys:
            raise ValueError("SECONDARY_AGS_DUPLICATE_OR_BAD_FORMAT")
        keys.add(ags)
        source_dates.add(row["export_datum"])
        if ags.startswith("05"):
            nrw_keys.add(ags)
            observed = {k: parse_count(row[k]) for k in COUNTS}
            for k, val in observed.items():
                state_totals[k] += val
            state_power += parse_power(row["kwp"])
            if sum(observed[k] for k in COUNTS if k != "einheiten_in_betrieb") != observed["einheiten_in_betrieb"]:
                category_difference_count += 1
    if pin_blob and count != EXPECTED_GERMANY_MUNICIPALITIES:
        raise ValueError("SECONDARY_EXPECTED_SOURCE_ROW_COUNT_CHANGED")
    if pin_blob and source_dates != {MASTR_REPORTED_SNAPSHOT}:
        raise ValueError("SECONDARY_REPORT_DATE_NOT_PINNED")
    if pin_blob and len(nrw_keys) != EXPECTED_NRW_MUNICIPALITIES:
        raise ValueError("SECONDARY_NRW_REGION_COUNT_MISMATCH")
    return {
        "source_is_federal_original_export": False,
        "secondary_csv_exact_git_blob_sha1": actual_blob,
        "secondary_csv_full_sha256": hashlib.sha256(original).hexdigest(),
        "secondary_original_bytes": len(original),
        "secondary_declared_export_date": MASTR_REPORTED_SNAPSHOT,
        "source_municipality_count": count,
        "source_field_count": len(fields),
        "nrw_key_set_private_only": nrw_keys,
        "nrw_unit_sums": dict(sorted(state_totals.items())),
        "nrw_all_generation_pv_capacity_kwp": str(state_power),
        "nrw_rows_with_category_count_difference": category_difference_count,
        "individual_municipality_measurements_emitted": False,
        "company_RV_insured_addresses_observed": False,
    }


def official_nrw_ags(original: bytes) -> set[str]:
    nrw.parse_original(
        original, expected_sha256=nrw.EXPECTED_SHA256,
        expected_bytes=nrw.EXPECTED_BYTES, expected_structure=nrw.EXPECTED_STRUCTURE,
    )
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        shared = xlsx_schema._shared_strings(archive)
        root = ET.fromstring(archive.read("xl/worksheets/sheet4.xml"))
        rows = root.findall(".//m:sheetData/m:row", nrw.NS)
        decoded = [xlsx_aggregates.parse_row_cells(r, shared) for r in rows[1:]]
        return xlsx_aggregates.check_ags(decoded)


def crosswalk(secondary: dict, official_ags: set[str]) -> dict:
    if len(official_ags) != EXPECTED_NRW_MUNICIPALITIES or any(
        not RE_AGS.fullmatch(key) or not key.startswith("05") for key in official_ags
    ):
        raise ValueError("OFFICIAL_NRW_AGS_BOUNDARY_UNKNOWN")
    from_second = secondary["nrw_key_set_private_only"]
    left, right = official_ags - from_second, from_second - official_ags
    if left or right:
        # Only aggregate missing counts, never municipal identifiers.
        raise ValueError(
            f"NRW_MASTR_CROSSWALK_INCOMPLETE_OFFICIAL_ONLY_{len(left)}_SECONDARY_ONLY_{len(right)}"
        )
    return {
        "schema": "NRW_PUBLIC_MASTR_DERIVED_20261002_VS_NRW_ROOF_POTENTIAL_20260312_AGG_V0",
        "federal_mastr_raw_export_reprocessed_by_this_run": False,
        "secondary_lineage": "mwhitex/solarzahlen-daten pinned GitHub commit; originates MaStR 2026-10-02",
        "secondary_original_git_blob_sha1": secondary["secondary_csv_exact_git_blob_sha1"],
        "secondary_original_sha256": secondary["secondary_csv_full_sha256"],
        "secondary_original_bytes": secondary["secondary_original_bytes"],
        "official_nrw_potential_original_sha256": nrw.EXPECTED_SHA256,
        "official_nrw_municipality_keys": len(official_ags),
        "secondary_nrw_municipality_keys": len(from_second),
        "join_exact_AGS_count": len(official_ags),
        "unmatched_official_count": len(left),
        "unmatched_secondary_count": len(right),
        "secondary_nrw_reported_active_pv_unit_sums_by_type": secondary["nrw_unit_sums"],
        "secondary_nrw_reported_active_all_pv_capacity_kwp": secondary["nrw_all_generation_pv_capacity_kwp"],
        "secondary_nrw_category_nonadditive_municipalities": secondary["nrw_rows_with_category_count_difference"],
        "NRW_potential_capacity_is_not_installed_pv_capacity": True,
        "overall_pv_kWp_includes_nonroof_types": True,
        "installed_units_are_not_distinct_buildings": True,
        "year_2026_is_not_RV_2025_insurer_book": True,
        "real_RV_installed_covered_pv_units_or_sums_observed": False,
        "independent_mastr_primary_xml_verified": False,
        "source_rights_model_admission_complete": False,
        "official_potential_municipality_values_used_for_insurer_weights": False,
        "private_or_municipal_rows_emitted": False,
        "native_cat_or_reinsurance_result_produced": False,
    }


def main() -> int:
    secondary = inspect_secondary(fetch_secondary(), pin_blob=True)
    official = official_nrw_ags(nrw.fetch_official())
    print(json.dumps(crosswalk(secondary, official), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TimeoutError, ET.ParseError) as exc:
        print(f"NRW_MASTR_MUNICIPAL_AGGREGATE_BLOCKED: {type(exc).__name__}: "
              f"{str(exc)[:85]}", file=sys.stderr)
        sys.exit(2)
