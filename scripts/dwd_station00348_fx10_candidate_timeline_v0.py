#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original station-00348 FX_10 / Maxwind device candidate *daily* overlap.

Station-00348's independent original ZIP SHA, real member headers, and native
date fields have been verified by separate receipts. This code matches only
candidate history intervals against the full actual measurement calendar,
with the inclusive endpoint assumption explicitly UNVERIFIED. No instrument
foreign key, sensor height value, weather correlation or CAT admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
import zipfile

from scripts.dwd_original_instrument_intervals_v0 import (
    EQ_HEADERS, PAR_HEADERS, InstrumentAuditBlocked, _rows,
)
from scripts.probe_dwd_station00348_original_v0 import (
    METADATA_FILE, PINNED_METADATA_SHA256, STATION, MAX_METADATA_ZIP,
    MAX_METADATA_EXPANDED, _snapshot, _zip_open,
)

DEVICE_FILE = "Metadaten_Geraete_Windgeschwindigkeit_Maxwind_00348.txt"
PARAMETER_FILE = "Metadaten_Parameter_00348.txt"
SOURCE_FX_CODE = "FX_10"
KNOWN_CODES = frozenset(("FX_10", "FNX_10", "FMX_10", "DX_10"))
WINDOW_START = date(2010, 1, 1)
WINDOW_END = date(2011, 9, 1)
FROZEN_DEVICE_RECORDS = 1
FROZEN_PARAMETER_RECORDS = 8


class Station00348JoinBlocked(ValueError):
    """The frozen original source cannot support the candidate join contract."""


def _sensor_height_candidate(value: str) -> bool:
    try:
        x = Decimal(value.strip().replace(",", "."))
    except InvalidOperation:
        return False
    return x.is_finite() and Decimal("0") < x <= Decimal("300")


def _unit_class(value: str) -> str:
    label = value.strip().strip('"').strip().casefold().replace(" ", "")
    if label in ("m/s", "m/sec"):
        return "source_meters_per_second_candidate"
    return "unrecognized_unit_sha256_" + hashlib.sha256(
        value.encode("utf-8")).hexdigest()[:12]


def _joint_history(device: list[dict], fx10: list[dict]) -> dict:
    labels = Counter()
    unit_categories = Counter()
    sensor_height_days = 0
    configurations = set()
    day = WINDOW_START
    by_month = {}
    while day <= WINDOW_END:
        equipment = [r for r in device if r["__begin"] <= day <= r["__end"]]
        parameters = [r for r in fx10 if r["__begin"] <= day <= r["__end"]]
        k = ("missing" if not equipment or not parameters
             else "unique" if len(equipment) == 1 and len(parameters) == 1
             else "ambiguous")
        labels[k] += 1
        month = day.strftime("%Y-%m")
        by_month.setdefault(month, {"unique": 0, "missing": 0, "ambiguous": 0})[k] += 1
        if k == "unique":
            eq, par = equipment[0], parameters[0]
            unit_categories[_unit_class(par["Einheit"])] += 1
            if _sensor_height_candidate(eq["Geberhoehe ueber Grund [m]"]):
                sensor_height_days += 1
            configurations.add((eq["Geraetetyp Name"], eq["Messverfahren"],
                                eq["Geberhoehe ueber Grund [m]"]))
        day += timedelta(days=1)
    total = (WINDOW_END - WINDOW_START).days + 1
    if sum(labels.values()) != total:
        raise Station00348JoinBlocked("daily interval conservation failed")
    return {
        "observed_measurement_calendar_days": total,
        "unique_fx10_maxwind_candidate_days": labels["unique"],
        "missing_candidate_days": labels["missing"],
        "multiply_assigned_candidate_days": labels["ambiguous"],
        "plausible_unverified_sensor_height_days": sensor_height_days,
        "distinct_device_method_height_candidate_tuples": len(configurations),
        "source_unit_candidate_days": dict(sorted(unit_categories.items())),
        "monthly_candidate_days": dict(sorted(by_month.items())),
    }


def inspect(path: Path, *, expected_sha256: str = PINNED_METADATA_SHA256) -> dict:
    try:
        source = _snapshot(Path(path), METADATA_FILE, MAX_METADATA_ZIP)
    except (OSError, ValueError) as exc:
        raise Station00348JoinBlocked("original station00348 metadata snapshot blocked") from exc
    digest = hashlib.sha256(source).hexdigest()
    if digest != expected_sha256:
        raise Station00348JoinBlocked("station00348 expected source SHA mismatched")
    raw_tables = {}
    fingerprints = {}
    try:
        with _zip_open(source, max_expanded=MAX_METADATA_EXPANDED) as archive:
            members = set(archive.namelist())
            if DEVICE_FILE not in members or PARAMETER_FILE not in members:
                raise Station00348JoinBlocked("frozen Maxwind/parameter original members missing")
            for filename, columns, count in (
                (DEVICE_FILE, EQ_HEADERS, FROZEN_DEVICE_RECORDS),
                (PARAMETER_FILE, PAR_HEADERS, FROZEN_PARAMETER_RECORDS),
            ):
                original = archive.read(filename)
                fingerprints[filename] = hashlib.sha256(original).hexdigest()
                rows, _footers = _rows(
                    original, columns, filename, count, station_id=STATION,
                )
                raw_tables[filename] = rows
            for filename in members - {DEVICE_FILE, PARAMETER_FILE}:
                with archive.open(filename, "r") as member:
                    while member.read(65_536):
                        pass
    except (InstrumentAuditBlocked, OSError, RuntimeError, zipfile.BadZipFile,
            ValueError) as exc:
        raise Station00348JoinBlocked("source native table or ZIP evidence gate blocked") from exc
    parameter_rows = raw_tables[PARAMETER_FILE]
    codes = {r["Parameter"].strip().upper() for r in parameter_rows}
    if codes != KNOWN_CODES:
        raise Station00348JoinBlocked("original parameter-code vocabulary diverged")
    fx10 = [r for r in parameter_rows if r["Parameter"].strip().upper() == SOURCE_FX_CODE]
    if not fx10:
        raise Station00348JoinBlocked("no original FX_10 parameter history")
    joint = _joint_history(raw_tables[DEVICE_FILE], fx10)
    return {
        "profile": "opencatastrophe-dwd00348-fx10-maxwind-candidate-timeline-v0",
        "station_id": STATION,
        "original_metadata_sha256": digest,
        "original_metadata_matches_live_frozen_sha": digest == PINNED_METADATA_SHA256,
        "instrument_member_sha256": fingerprints[DEVICE_FILE],
        "parameter_member_sha256": fingerprints[PARAMETER_FILE],
        "original_maxwind_instrument_records": FROZEN_DEVICE_RECORDS,
        "original_parameter_records": len(parameter_rows),
        "original_fx10_parameter_records": len(fx10),
        "inclusive_date_endpoints": "PROVISIONAL_RESEARCH_ONLY",
        "device_fx10_foreign_key_verified": False,
        "original_sensor_values_or_coordinates_emitted": False,
        "model_input_approved": False,
        **joint,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(args.metadata_zip), sort_keys=True,
                         ensure_ascii=False, allow_nan=False))
    except Station00348JoinBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
