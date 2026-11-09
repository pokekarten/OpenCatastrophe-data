# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Aggregate-only Marche 2022 observed component-damage frequency by outside flood depth.

This is a SINGLE-EVENT, NONREPRESENTATIVE, selected-and-affected survey preview.
It is not an insured loss curve, insurer claim probability, money/TIV ratio,
OEP/AEP, independent holdout, causal curve or production vulnerability model.

Inputs: caller-owned exact v1.0.1 ZIPs outside Git. The imported original
source audit pins hashes, verifies dictionary units and counts 247 valid hw
observations. This module never writes or outputs IDs/coordinates/raw rows.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

from research_runners.marche_2022_survey_original_preflight_v0 import (
    MAX_TOTAL_UNCOMPRESSED, PREFIX, SourceStructureError,
    _cell_text, _read_original, _shared_strings, _zip_checked,
)
from research_runners.marche_2022_water_surface_elevation_probe_v0 import audit_original

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
Z = 1.96  # descriptive Wilson binomial interval; not corrected for selection/cluster bias
MIN_BIN_N = 10
MIN_POSITIVE = 3
MIN_NEGATIVE = 3
DEPTH_BINS = ("[0,0.5)", "[0.5,1)", "[1,2)", "[2,inf)")
SOURCE = {
    "industrial": {
        "depth_col": "AY", "outcome_col": "BK",
        "outcome_header": "Building structure and plants",
        "outcome_section": "Observed damage",
        "dictionary_aspect": "Observed damage",
        "dictionary_field": "Building structure and plants",
        "expected": {"parents": 133, "depth_present": 126, "outcome_present": 127, "paired": 121},
        "outcome_label": "reported building structure and plants damage",
    },
    "residential": {
        "depth_col": "AG", "outcome_col": "AX",
        "outcome_header": "Damage",
        "outcome_section": "Damage to external coating/plaster",
        "dictionary_aspect": "Damage to external coating/perimeter",
        "dictionary_field": "Damage",
        "expected": {"parents": 123, "depth_present": 121, "outcome_present": 122, "paired": 120},
        "outcome_label": "reported damage to external coating/plaster",
    },
}


def _depth(text: str) -> Decimal | None:
    value = text.strip()
    if not value or value == "-":
        return None
    try:
        num = Decimal(value)
    except InvalidOperation as exc:
        raise SourceStructureError("Unexpected non-numeric outside-depth code") from exc
    if not num.is_finite() or num < 0 or num > 10:
        raise SourceStructureError("Invalid outside-depth value in metres")
    return num


def _binary(text: str, sector: str) -> int | None:
    value = text.strip().lower()
    if value in ("", "-"):
        return None
    allowed = {"0": 0, "1": 1} if sector == "industrial" else {"no": 0, "yes": 1}
    if value not in allowed:
        raise SourceStructureError("Unexpected outcome field coding")
    return allowed[value]


def _bin(depth: Decimal) -> str:
    if depth < Decimal("0.5"):
        return DEPTH_BINS[0]
    if depth < Decimal("1"):
        return DEPTH_BINS[1]
    if depth < Decimal("2"):
        return DEPTH_BINS[2]
    return DEPTH_BINS[3]


def _wilson(pos: int, n: int) -> tuple[float, float]:
    phat = pos / n
    z2 = Z * Z
    center = (phat + z2 / (2 * n)) / (1 + z2 / n)
    half = Z * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return center - half, center + half


def _dictionary_outcome_contract(book: bytes, sector: str) -> None:
    cfg = SOURCE[sector]
    with _zip_checked(book, max_entries=100, max_total=MAX_TOTAL_UNCOMPRESSED) as z:
        try:
            root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
            strings = _shared_strings(z)
        except (ET.ParseError, KeyError) as exc:
            raise SourceStructureError("Original outcome dictionary missing") from exc
    matches = 0
    for row in root.iter(NS + "row"):
        fields: dict[str, str] = {}
        for cell in row.findall(NS + "c"):
            match = re.fullmatch(r"([A-Z]+)(\d+)", cell.get("r", ""))
            if match and match.group(1) in ("B", "C", "D", "E"):
                fields[match.group(1)] = _cell_text(cell, strings).strip()
        if (fields.get("B") == cfg["dictionary_aspect"]
            and fields.get("C") == cfg["dictionary_field"]):
            if fields.get("D") != "boolean" or not all(
                q in fields.get("E", "").lower()
                for q in (("0", "1") if sector == "industrial" else ("yes", "no"))
            ):
                raise SourceStructureError("Publisher outcome coding/dictionary changed")
            matches += 1
    if matches != 1:
        raise SourceStructureError("Publisher outcome identity could not be established")


def _summarize(pairs: list[tuple[Decimal, int]], *, sector: str) -> dict:
    bins: dict[str, Counter[str]] = {name: Counter() for name in DEPTH_BINS}
    for depth, damage in pairs:
        bin_count = bins[_bin(depth)]
        bin_count["n"] += 1
        bin_count["yes"] += damage
    published = []
    for name in DEPTH_BINS:
        n, yes = bins[name]["n"], bins[name]["yes"]
        no = n - yes
        # Suppress small slices AND sparse positive/negative cells. Never emit
        # individual rows or the suppressed positive counts through totals.
        if n < MIN_BIN_N or yes < MIN_POSITIVE or no < MIN_NEGATIVE:
            published.append({"outside_depth_m": name, "suppressed": True})
            continue
        low, high = _wilson(yes, n)
        published.append({
            "outside_depth_m": name, "suppressed": False,
            "surveyed_properties_with_both_values": n,
            "reported_damage_yes": yes,
            "observed_sample_fraction": round(yes / n, 4),
            "descriptive_wilson95_lower": round(low, 4),
            "descriptive_wilson95_upper": round(high, 4),
        })
    return {
        "sector": sector,
        "outcome_label": SOURCE[sector]["outcome_label"],
        "series_label": "within-survey conditional observed component frequency",
        "published_depth_bins": published,
        "suppression_min_bin_n": MIN_BIN_N,
        "suppression_min_each_binary_class": MIN_POSITIVE,
        "wilson95_adjusted_for_survey_selection_or_spatial_clusters": False,
        "single_event_2022_09_15": True,
        "not_insured_loss_probability": True,
        "not_monetary_damage_ratio": True,
        "model_admitted": False,
        "raw_rows_or_coordinates_exported": False,
    }


def audit_sector(data: bytes, sector: str) -> dict:
    if sector not in SOURCE:
        raise SourceStructureError("Unexpected source sector")
    cfg = SOURCE[sector]
    # Fixed original ZIP SHA-256/MD5, form structure, parent counts,
    # actual hw-unit/derived-datum definitions and storage count checks.
    prior = audit_original(data, sector)
    with _zip_checked(data, max_entries=30, max_total=MAX_TOTAL_UNCOMPRESSED) as z:
        f = z.read(PREFIX[sector] + "Form_A.xlsx")
        dic = z.read(PREFIX[sector] + (
            "Data_dictionary.xlsx" if sector == "industrial" else "Data dictionary.xlsx"
        ))
    _dictionary_outcome_contract(dic, sector)
    with _zip_checked(f, max_entries=100, max_total=MAX_TOTAL_UNCOMPRESSED) as w:
        try:
            root = ET.fromstring(w.read("xl/worksheets/sheet1.xml"))
            strings = _shared_strings(w)
        except (ET.ParseError, KeyError) as exc:
            raise SourceStructureError("Original Form A worksheet missing") from exc
    ids: set[str] = set()
    counts: Counter[str] = Counter()
    pairs: list[tuple[Decimal, int]] = []
    for row in root.iter(NS + "row"):
        index = int(row.get("r", "0"))
        if index < 2:
            continue
        columns: dict[str, str] = {}
        for cell in row.findall(NS + "c"):
            match = re.fullmatch(r"([A-Z]+)(\d+)", cell.get("r", ""))
            if not match or int(match.group(2)) != index:
                raise SourceStructureError("Unexpected original workbook coordinate")
            col = match.group(1)
            if col in ("A", cfg["depth_col"], cfg["outcome_col"]):
                if col in columns:
                    raise SourceStructureError("Duplicate Form A relevant cell")
                columns[col] = _cell_text(cell, strings)
        if index == 2:
            if columns.get(cfg["outcome_col"], "").strip() != cfg["outcome_section"]:
                raise SourceStructureError("Expected source outcome section has changed")
        if index == 3:
            if columns.get(cfg["depth_col"], "").strip() != "hw" or \
               columns.get(cfg["outcome_col"], "").strip() != cfg["outcome_header"]:
                raise SourceStructureError("Original outcome/water-depth column labels mismatch")
            continue
        if index < 4 or not columns.get("A", "").strip():
            continue
        key = columns["A"].strip()
        if key in ids:
            raise SourceStructureError("Duplicate Form A parent")
        ids.add(key)
        depth = _depth(columns.get(cfg["depth_col"], ""))
        outcome = _binary(columns.get(cfg["outcome_col"], ""), sector)
        counts["parents"] += 1
        if depth is not None:
            counts["depth_present"] += 1
        if outcome is not None:
            counts["outcome_present"] += 1
        if depth is not None and outcome is not None:
            counts["paired"] += 1
            pairs.append((depth, outcome))
    if {k: counts[k] for k in cfg["expected"]} != cfg["expected"]:
        raise SourceStructureError("Published Form A join coverage has changed")
    if len(ids) != prior["parent_count"]:
        raise SourceStructureError("Parent counts disagree with frozen source audit")
    return _summarize(pairs, sector=sector)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--industrial-zip", required=True, type=Path)
    parser.add_argument("--residential-zip", required=True, type=Path)
    args = parser.parse_args()
    try:
        industrial = audit_sector(_read_original(args.industrial_zip, "industrial"), "industrial")
        residential = audit_sector(_read_original(args.residential_zip, "residential"), "residential")
    except (OSError, ValueError, SourceStructureError, ET.ParseError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "source_release": "10.5281/zenodo.17457884",
        "aggregation_only": True,
        "not_admitted": True,
        "independent_event_holdout": False,
        "selection_bias_adjusted": False,
        "industrial": industrial,
        "residential": residential,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
