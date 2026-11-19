# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Privacy-safe depth and derived-water-elevation source type audit.

The original Form A `hw` is **water depth outside the building, metres**;
the "Water surface elevation" field is an independently derived height,
not interchangeable with `hw` or indoor peak depth. The publisher
dictionary and original frozen ZIPs are checked explicitly. Return counts,
never survey values, IDs, geocoordinates, attributes or damage amounts.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research_runners.marche_2022_survey_original_preflight_v0 import (
    MAX_TOTAL_UNCOMPRESSED, PREFIX, SourceStructureError, _cell_text,
    _read_original, _shared_strings, _zip_checked, audit_archive,
)

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
TARGET_COLUMN = {"industrial": "AZ", "residential": "AH"}
DEPTH_COLUMN = {"industrial": "AY", "residential": "AG"}
DEPTH_MISSING_IN_DICTIONARY = {"industrial": "7", "residential": "2"}
# Separately observed in the frozen v1.0.1 asset: storage types, not depths.
ORIGINAL_COUNTS = {
    "industrial": {"numeric": 76, "non_numeric": 57, "blank": 0},
    "residential": {"numeric": 102, "non_numeric": 21, "blank": 0},
}
ORIGINAL_OUTSIDE_DEPTH_COUNTS = {
    "industrial": {"numeric": 126, "non_numeric": 7, "blank": 0},
    "residential": {"numeric": 121, "non_numeric": 2, "blank": 0},
}


def classify_storage(value: str) -> str:
    if not value.strip():
        return "blank"
    try:
        number = Decimal(value.strip())
    except InvalidOperation:
        return "non_numeric"
    if not number.is_finite():
        raise SourceStructureError("Nonfinite water-surface candidate")
    return "numeric"


def profile_form_a(workbook: bytes, *, sector: str, expected_parents: int) -> dict:
    if sector not in TARGET_COLUMN:
        raise SourceStructureError("Unknown Marche sector")
    with _zip_checked(workbook, max_entries=100, max_total=MAX_TOTAL_UNCOMPRESSED) as z:
        try:
            root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
            strings = _shared_strings(z)
        except (KeyError, ET.ParseError) as exc:
            raise SourceStructureError("Original workbook unavailable or malformed") from exc
    target = TARGET_COLUMN[sector]
    depth_col = DEPTH_COLUMN[sector]
    counts = {"numeric": 0, "non_numeric": 0, "blank": 0}
    outside_counts = {"numeric": 0, "non_numeric": 0, "blank": 0}
    ids: set[str] = set()
    header_ok = False
    for row in root.iter(NS + "row"):
        try:
            index = int(row.get("r", "0"))
        except ValueError as exc:
            raise SourceStructureError("Bad workbook row index") from exc
        if index < 3:
            continue
        selected: dict[str, str] = {}
        for cell in row.findall(NS + "c"):
            address = cell.get("r", "")
            match = re.fullmatch(r"([A-Z]+)([0-9]+)", address)
            if not match or int(match.group(2)) != index:
                raise SourceStructureError("Bad workbook cell reference")
            col = match.group(1)
            if col in ("A", target, depth_col):
                if col in selected:
                    raise SourceStructureError("Duplicate relevant workbook cell")
                selected[col] = _cell_text(cell, strings)
        if index == 3:
            header_ok = (
                selected.get("A", "").strip() == "ID"
                and selected.get(target, "").strip() == "Water surface elevation"
                and selected.get(depth_col, "").strip() == "hw"
            )
            continue
        identifier = selected.get("A", "").strip()
        if not identifier:
            # Original parent validator separately rejects populated orphan rows.
            continue
        if identifier in ids:
            raise SourceStructureError("Duplicate source Form A parent")
        ids.add(identifier)
        counts[classify_storage(selected.get(target, ""))] += 1
        outside_counts[classify_storage(selected.get(depth_col, ""))] += 1
    if not header_ok or len(ids) != expected_parents:
        raise SourceStructureError("Form A source label or parent population mismatch")
    return {
        "sector": sector,
        "parent_count": len(ids),
        "variable_label": "Water surface elevation",
        "storage_type_counts": counts,
        "outside_water_depth_field": "hw",
        "outside_water_depth_column": depth_col,
        "outside_water_depth_storage_counts": outside_counts,
        "water_depth_above_floor_verified": False,
        "vertical_datum_verified": False,
        "can_fit_depth_damage_function": False,
        "individual_source_values_exported": False,
    }


def check_dictionary_for_depth(dictionary: bytes, sector: str) -> bool:
    """Verify source metadata only: raw \`hw\` in metres, derived elevation.

    The original dictionary has row labels in column C, dtype in D, units and
    provenance in E and missing-count G. This function reads no survey rows.
    """
    with _zip_checked(dictionary, max_entries=100, max_total=MAX_TOTAL_UNCOMPRESSED) as z:
        try:
            root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
            strings = _shared_strings(z)
        except (KeyError, ET.ParseError) as exc:
            raise SourceStructureError("Publisher dictionary cannot be read") from exc
    found_hw = False
    found_derived = False
    for row in root.iter(NS + "row"):
        cells: dict[str, str] = {}
        for cell in row.findall(NS + "c"):
            address = cell.get("r", "")
            match = re.fullmatch(r"([A-Z]+)([0-9]+)", address)
            if not match:
                raise SourceStructureError("Malformed dictionary cell")
            col = match.group(1)
            if col in ("C", "D", "E", "G"):
                cells[col] = _cell_text(cell, strings).strip()
        if cells.get("C") == "hw":
            found_hw = (
                cells.get("D") == "float"
                and "Measurement in meters" in cells.get("E", "")
                and cells.get("G") == DEPTH_MISSING_IN_DICTIONARY[sector]
            )
        if cells.get("C") == "Water surface elevation":
            text = cells.get("E", "").lower()
            found_derived = (
                cells.get("D") == "float"
                and "sum of terrain elevation" in text
                and "hw" in text
                and "∆q" in text
            )
    if not (found_hw and found_derived):
        raise SourceStructureError("Original data dictionary rejects hazard field identity")
    return True


def audit_original(data: bytes, sector: str) -> dict:
    parent = audit_archive(data, sector)  # exact Zenodo MD5 + SHA256; source structure
    with _zip_checked(data, max_entries=30, max_total=MAX_TOTAL_UNCOMPRESSED) as z:
        workbook = z.read(PREFIX[sector] + "Form_A.xlsx")
        dictionary = z.read(PREFIX[sector] + ("Data_dictionary.xlsx" if sector == "industrial"
                                               else "Data dictionary.xlsx"))
    result = profile_form_a(
        workbook, sector=sector,
        expected_parents=parent["form_a_unique_parent_survey_count"],
    )
    if result["storage_type_counts"] != ORIGINAL_COUNTS[sector]:
        raise SourceStructureError("Unexpected derived-elevation type counts")
    if result["outside_water_depth_storage_counts"] != ORIGINAL_OUTSIDE_DEPTH_COUNTS[sector]:
        raise SourceStructureError("Unexpected outside-water-depth type counts")
    result["outside_water_depth_meters_dictionary_verified"] = check_dictionary_for_depth(dictionary, sector)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--industrial-zip", required=True, type=Path)
    parser.add_argument("--residential-zip", required=True, type=Path)
    args = parser.parse_args()
    try:
        industrial = audit_original(_read_original(args.industrial_zip, "industrial"), "industrial")
        residential = audit_original(_read_original(args.residential_zip, "residential"), "residential")
        if industrial["parent_count"] + residential["parent_count"] != 256:
            raise SourceStructureError("Original source parent count differs")
    except (OSError, SourceStructureError, ET.ParseError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "frozen_release": "10.5281/zenodo.17457884",
        "source_is_observed_single_event_survey": True,
        "scientifically_admitted": False,
        "privacy_safe_aggregate_only": True,
        "outside_water_depth_numeric_observation_count": (
            industrial["outside_water_depth_storage_counts"]["numeric"]
            + residential["outside_water_depth_storage_counts"]["numeric"]
        ),
        "industrial": industrial, "residential": residential,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
