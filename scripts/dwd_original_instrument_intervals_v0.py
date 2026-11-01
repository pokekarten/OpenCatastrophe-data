#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Provisional original DWD station-00003 instrument/parameter interval audit.

Original metadata ZIP/source headers verified in #960/#974, wind observations
in #956. This script counts candidate interval overlaps/gaps for 2010-01-01 to
2011-03-31 using explicit, *provisional* inclusive-endpoint interpretation.

No original instrument names, positions, source date rows or sensor heights are
emitted. No guess that an equipment family applies to measured FX_10, and no
CAT scientific admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from scripts import dwd_metadata_temporal_evidence as evidence
from scripts.dwd_equipment_layout_evidence_v0 import (
    PAIRS, _txt_layout, EquipmentBlocked,
)

START = date(2010, 1, 1)
END = date(2011, 3, 31)
EQ_HEADERS = (
    "Stations_ID", "Stationsname", "Geo. Laenge [Grad]", "Geo. Breite [Grad]",
    "Stationshoehe [m]", "Geberhoehe ueber Grund [m]",
    "Von_Datum", "Bis_Datum", "Geraetetyp Name", "Messverfahren",
    "eor", "unnamed_field_11",
)
PAR_HEADERS = (
    "Stations_ID", "Von_Datum", "Bis_Datum", "Stationsname", "Parameter",
    "Parameterbeschreibung", "Einheit", "Datenquelle (Strukturversion_SV)",
    "Zusatz-Info", "Besonderheiten", "Literaturhinweis",
    "eor", "unnamed_field_12",
)
KNOWN_MEASURED_CODES = frozenset(("FX_10", "FNX_10", "FMX_10", "DX_10"))
# Exactly frozen source structural counts proved independently by #974:
# 2 valid calendar tokens per native source record, no silent extra records.
ORIGINAL_ROWS = {
    PAIRS[0]: 1,
    PAIRS[1]: 2,
    PAIRS[2]: 1,
    PAIRS[3]: 2,
    PAIRS[4]: 8,
}
MAX_RECORDS_PER_TABLE = 64
MAX_FOOTER_LINES = 6


class InstrumentAuditBlocked(ValueError):
    """Original member, date, schema or station violates strict gate."""


def _date(value: str) -> date:
    value = value.strip()
    if len(value) != 8 or not value.isascii() or not value.isdigit():
        raise InstrumentAuditBlocked("unsupported original interval date encoding")
    try:
        return date.fromisoformat(value[:4] + "-" + value[4:6] + "-" + value[6:])
    except ValueError as exc:
        raise InstrumentAuditBlocked("invalid original interval date") from exc


def _rows(raw: bytes, expected_headers: tuple[str, ...], family: str = "unknown",
          expected_source_records: int | None = None,
          station_id: str = "00003") -> tuple[list[dict], int]:
    try:
        layout = _txt_layout(raw)
    except EquipmentBlocked as exc:
        raise InstrumentAuditBlocked("original TXT layout evidence blocked") from exc
    if (not layout["header_candidate_recognized"]
            or tuple(layout["source_column_names"]) != expected_headers
            or layout["encoding_hint"] != "utf-8"):
        raise InstrumentAuditBlocked("actual source headers differ from observed original")
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    table_rows = []
    footer_lines = 0
    footer_started = False
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        if line.count(";") <= 1:
            # The actual original *parameter* TXT has a provider attribution
            # footer with one semicolon on original line 10. The observed
            # instrument TXT footers have no semicolons. Require all frozen
            # source rows before accepting a footer, and never skip candidate
            # date-bearing or station-bearing malformed data records.
            if not table_rows or (expected_source_records is not None
                    and len(table_rows) != expected_source_records):
                raise InstrumentAuditBlocked("non-tabular footer before full original source table")
            if (any(char.isdigit() for char in line[:8])
                    or station_id in line or len(line.encode("utf-8")) > 512):
                raise InstrumentAuditBlocked("ambiguous date/station-bearing original footer")
            footer_started = True
            footer_lines += 1
            if footer_lines > MAX_FOOTER_LINES:
                raise InstrumentAuditBlocked("unsupported number of DWD footer lines")
            continue
        if footer_started:
            raise InstrumentAuditBlocked("DWD data rows appear after non-tabular footer")
        # DWD's original metadata TXT is a provider-specific semicolon
        # POSITIONAL format, not safely equivalent to generic CSV quoting.
        # Count exact delimiters and preserve every original column, including
        # its intentionally blank final field; never collapse quoted segments.
        if line.count(";") != len(expected_headers) - 1:
            raise InstrumentAuditBlocked(
                f"source semicolon field-count drift family={family} "
                f"line={line_number} observed={line.count(';')} "
                f"expected={len(expected_headers) - 1}"
            )
        fields = line.split(";")
        if len(fields) != len(expected_headers):
            raise InstrumentAuditBlocked("source positional field-count drift")
        row = dict(zip(expected_headers, (x.strip() for x in fields)))
        if row["Stations_ID"].zfill(5) != station_id:
            raise InstrumentAuditBlocked("DWD source row station identity differs")
        first = _date(row["Von_Datum"])
        last = _date(row["Bis_Datum"])
        if first > last:
            raise InstrumentAuditBlocked("original date interval is inverted")
        row["__begin"] = first
        row["__end"] = last
        table_rows.append(row)
        if len(table_rows) > MAX_RECORDS_PER_TABLE:
            raise InstrumentAuditBlocked("too many original table data rows")
    if not table_rows:
        raise InstrumentAuditBlocked("no original equipment/parameter data records")
    if expected_source_records is not None and len(table_rows) != expected_source_records:
        raise InstrumentAuditBlocked("frozen original data-record count differs from #974")
    return table_rows, footer_lines


def _coverage(intervals: list[tuple[date, date]]) -> dict:
    counts = Counter()
    d = START
    while d <= END:
        n = sum(start <= d <= end for start, end in intervals)
        counts["one" if n == 1 else "missing" if n == 0 else "overlap"] += 1
        d += timedelta(days=1)
    return {
        "unique_candidate_days": counts["one"],
        "no_candidate_days": counts["missing"],
        "multiple_candidate_days": counts["overlap"],
    }


def _height_status(value: str) -> str:
    try:
        n = Decimal(value.strip().replace(",", "."))
    except InvalidOperation:
        return "unparsed"
    if not n.is_finite() or n < 0 or n > 300:
        return "unparsed"
    return "finite_candidate_only"


def _summary(eq_rows: list[dict], footers: int) -> dict:
    intervals = [(row["__begin"], row["__end"]) for row in eq_rows]
    intersecting = [row for row in eq_rows if
                    row["__begin"] <= END and row["__end"] >= START]
    distinct_devices = {
        (row["Geraetetyp Name"], row["Messverfahren"],
         row["Geberhoehe ueber Grund [m]"])
        for row in intersecting
    }
    heights = Counter(_height_status(row["Geberhoehe ueber Grund [m]"])
                      for row in eq_rows)
    return {
        "original_data_records": len(eq_rows),
        "non_tabular_footer_lines": footers,
        "candidate_history_records_intersecting_measurement_window": len(intersecting),
        "distinct_candidate_device_method_height_combinations_in_window": len(distinct_devices),
        "finite_candidate_sensor_height_records": heights["finite_candidate_only"],
        "unparsed_or_out_of_range_height_records": heights["unparsed"],
        **_coverage(intervals),
        "device_replacement_proven": False,
        "height_measurement_verified": False,
    }


def _parameter_summary(rows: list[dict], footers: int) -> dict:
    grouped = {name: [] for name in sorted(KNOWN_MEASURED_CODES)}
    unknown = 0
    for row in rows:
        key = row["Parameter"].strip().upper()
        if key in grouped:
            grouped[key].append((row["__begin"], row["__end"]))
        else:
            unknown += 1
    # Metadata may contain other wind codes, but those cannot be fabricated as
    # guaranteed observation-column matches. Do NOT merge their intervals.
    supported = {key: {
        "original_candidate_rows": len(groups),
        **_coverage(groups),
    } for key, groups in grouped.items()}
    return {
        "original_data_records": len(rows),
        "non_tabular_footer_lines": footers,
        "rows_with_unmapped_parameter_codes": unknown,
        "pinned_observation_parameter_candidates": supported,
        "parameter_source_units_interpreted": False,
        "measured_fx_10_equipment_family_verified": False,
    }


def analyze(path: Path, *, expected_sha256: str = evidence.EXPECTED_METADATA_SHA256) -> dict:
    try:
        receipt = evidence._collect(Path(path), expected_sha256,
                                    evidence.EXPECTED_STATION_ID)
        snapshot = evidence._read_bounded_regular_snapshot(
            Path(path), receipt["metadata_asset"]["byte_size"])
    except (OSError, evidence.TemporalEvidenceError) as exc:
        raise InstrumentAuditBlocked("pinned DWD metadata original failed evidence gate") from exc
    if hashlib.sha256(snapshot).hexdigest() != expected_sha256:
        raise InstrumentAuditBlocked("DWD original changed after prior source inspection")
    sha_by_path = {m["path"]: m["sha256"]
                   for family in receipt["required_family_members"].values()
                   for m in family}
    expected_pairs = {stem + extension for stem in PAIRS
                      for extension in (".txt", ".html")}
    observed_pairs = {name for name in sha_by_path
                      if name.startswith(("Metadaten_Geraete_", "Metadaten_Parameter_"))}
    if observed_pairs != expected_pairs:
        raise InstrumentAuditBlocked("original device/parameter file set diverged from #974")
    summary = {}
    parameter_result = None
    try:
        with zipfile.ZipFile(io.BytesIO(snapshot), "r") as archive:
            for stem in PAIRS:
                member = stem + ".txt"
                raw = archive.read(member)
                if hashlib.sha256(raw).hexdigest() != sha_by_path[member]:
                    raise InstrumentAuditBlocked("TXT member SHA diverged from exact-source snapshot")
                if stem.startswith("Metadaten_Geraete"):
                    rows, footer_count = _rows(raw, EQ_HEADERS, stem, ORIGINAL_ROWS[stem])
                    summary[stem] = _summary(rows, footer_count)
                else:
                    rows, footer_count = _rows(raw, PAR_HEADERS, stem, ORIGINAL_ROWS[stem])
                    parameter_result = _parameter_summary(rows, footer_count)
    except (KeyError, OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise InstrumentAuditBlocked("source member inspection failed") from exc

    return {
        "profile": "opencatastrophe-dwd-00003-provisional-instrument-interval-audit-v0",
        "source_metadata_sha256": expected_sha256,
        "linked_gust_source_sha256": evidence.MEASUREMENT_SHA256,
        "measurement_window": {"start": START.isoformat(), "end": END.isoformat()},
        "equipment_families": summary,
        "parameter_family": parameter_result,
        "interval_endpoint_assumption": "PROVISIONAL_BOTH_DATES_INCLUSIVE",
        "original_instrument_values_emitted": False,
        "original_station_coordinates_emitted": False,
        "device_provenance_fully_validated": False,
        "model_input_approved": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(analyze(args.source_zip), sort_keys=True, allow_nan=False))
    except InstrumentAuditBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
