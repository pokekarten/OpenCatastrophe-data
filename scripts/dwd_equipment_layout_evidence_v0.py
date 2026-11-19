#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""DWD station-00003 original equipment/parameter member *layout evidence*.

Read the independently SHA-pinned original DWD metadata ZIP; inspect the four
equipment TXT/HTML pairs and the parameter TXT/HTML pair. Output bounded
structural fingerprints, not actual rows, instrument values, dates or names.

No inference of instrument transitions or temporal validity. The purpose is to
specify a future, provider-documented historical instrument join without
guessing fixed-width or table-column meaning.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from scripts import dwd_metadata_temporal_evidence as evidence

PAIRS = (
    "Metadaten_Geraete_Windgeschw_Max_Mittelwert_00003",
    "Metadaten_Geraete_Windgeschwindigkeit_Maxwind_00003",
    "Metadaten_Geraete_Windgeschwindigkeit_Min_00003",
    "Metadaten_Geraete_Windrichtung_Maxwind_00003",
    "Metadaten_Parameter_00003",
)
MAX_MEMBER_BYTES = 512_000
MAX_LINES = 512
MAX_LINE_BYTES = 8192
MAX_PARSED_HTML_NODES = 20_000
DATE_TOKEN = re.compile(r"(?<![0-9])(?:18|19|20)[0-9]{6}(?![0-9])")


class EquipmentBlocked(ValueError):
    """Fail closed on original-source identity or bounded-format violations."""


class MarkupCounts(HTMLParser):
    """Count HTML table structure without collecting provider row text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.table_count = 0
        self.tr_count = 0
        self.th_count = 0
        self.td_count = 0
        self.node_count = 0

    def handle_starttag(self, tag, attrs):
        self.node_count += 1
        if self.node_count > MAX_PARSED_HTML_NODES:
            raise EquipmentBlocked("HTML has too many markup nodes")
        tag = tag.lower()
        if tag == "table":
            self.table_count += 1
        elif tag == "tr":
            self.tr_count += 1
        elif tag == "th":
            self.th_count += 1
        elif tag == "td":
            self.td_count += 1


def _decode_text(raw: bytes) -> tuple[str, str]:
    try:
        return raw.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        # The original DWD HTML examples can contain legacy Western encoding;
        # this is a *hint*, not a scientific or provider-certified encoding.
        return raw.decode("cp1252"), "cp1252_heuristic"


def _valid_calendar_candidates(line: str) -> tuple[int, int, list[int]]:
    tokens = list(DATE_TOKEN.finditer(line))
    valid = 0
    offsets = []
    for candidate in tokens:
        text = candidate.group()
        try:
            date.fromisoformat(text[:4] + "-" + text[4:6] + "-" + text[6:])
        except ValueError:
            continue
        valid += 1
        offsets.append(candidate.start())
    return len(tokens), valid, offsets[:12]


def _txt_layout(raw: bytes) -> dict:
    if not 0 < len(raw) <= MAX_MEMBER_BYTES:
        raise EquipmentBlocked("TXT metadata member out of reviewed byte bound")
    text, encoding = _decode_text(raw)
    lines = text.splitlines()
    if not 0 < len(lines) <= MAX_LINES:
        raise EquipmentBlocked("TXT metadata line count outside reviewed bound")
    if any(len(line.encode("utf-8")) > MAX_LINE_BYTES for line in lines):
        raise EquipmentBlocked("TXT metadata line exceeds reviewed line-size bound")
    nonblank = [line for line in lines if line.strip()]
    if not nonblank:
        raise EquipmentBlocked("TXT metadata member is empty")
    # The actual DWD native TXT headers have 11/12 semicolons. Output ONLY the
    # very first line's structural column titles (never any source row).
    # Strict token safeguards prevent a novel/data-like first line from being
    # exported as a supposed original provider header.
    raw_titles = [field.strip().strip('"') for field in nonblank[0].split(";")]
    # An original DWD provider header can contain unnamed delimiter cells.
    # Never transform a real observation or station value row into a header:
    # first line has ZERO valid date tokens; a same-width second line has at
    # least two real calendar dates. This is a format hypothesis, not meaning.
    header_dates = _valid_calendar_candidates(nonblank[0])[1]
    second_dates = (_valid_calendar_candidates(nonblank[1])[1]
                    if len(nonblank) > 1 else 0)
    same_delimiters = (
        len(nonblank) > 1
        and nonblank[0].count(";") == nonblank[1].count(";")
    )
    populated = [label for label in raw_titles if label]
    blanks = len(raw_titles) - len(populated)
    safe_titles = (
        8 <= len(raw_titles) <= 20
        and len(nonblank[0].encode("utf-8")) <= 512
        and same_delimiters and header_dates == 0 and second_dates >= 2
        and blanks <= 2
        and all(len(label) <= 90 and any(ch.isalpha() for ch in label)
                and not any(ord(ch) < 32 for ch in label)
                for label in populated)
        and len({label.casefold() for label in populated}) == len(populated)
        and any("datum" in label.casefold() or "station" in label.casefold()
                for label in populated)
    )
    # Only emitted when strong provider-header shape evidence holds; unknown
    # punctuation is replaced, blanks explicitly numbered, and no TXT rows
    # are returned. Original header labels are discovery, NOT approved fields.
    source_labels = [
        ("".join(ch if (ch.isalnum() or ch in " _-.(),:/%+[]")
                 else "_" for ch in label) if label else f"unnamed_field_{i}")
        for i, label in enumerate(raw_titles)
    ]
    # Never output original line contents. Character offsets refer only to date
    # CANDIDATES, not approved 'from'/'to' fields.
    signatures = []
    totals = Counter()
    for line in nonblank:
        tokens, valid, offsets = _valid_calendar_candidates(line)
        totals["date_tokens"] += tokens
        totals["valid_calendar_tokens"] += valid
        signatures.append({
            "line_bytes": len(line.encode("utf-8")),
            "whitespace_tokens": len(line.split()),
            "semicolons": line.count(";"),
            "tabs": line.count("\t"),
            "pipes": line.count("|"),
            "date_like_tokens": tokens,
            "valid_calendar_tokens": valid,
            "candidate_date_offsets": offsets,
        })
    return {
        "text_member_bytes": len(raw),
        "text_sha256": hashlib.sha256(raw).hexdigest(),
        "encoding_hint": encoding,
        "total_lines": len(lines),
        "nonempty_lines": len(nonblank),
        "candidate_date_tokens": totals["date_tokens"],
        "valid_calendar_tokens": totals["valid_calendar_tokens"],
        "first_three_line_signatures": signatures[:3],
        "source_column_names": source_labels if safe_titles else [],
        "header_candidate_recognized": bool(safe_titles),
        "source_header_diagnostics_only": {
            "header_empty_field_count": blanks,
            "two_line_delimiter_width_consistent": bool(same_delimiters),
            "first_line_valid_calendar_tokens": header_dates,
            "second_line_valid_calendar_tokens": second_dates,
            "field_count": len(raw_titles),
            "all_nonblank_and_bounded": all(1 <= len(name) <= 90 for name in raw_titles),
            "all_within_restricted_character_set": all(
                bool(re.fullmatch(r"[\w .(),:/%+\-]+", name, re.UNICODE))
                for name in raw_titles),
            "unique_casefolded": len({name.casefold() for name in raw_titles}) == len(raw_titles),
            "station_or_datum_marker_found": any(
                "datum" in name.casefold() or "station" in name.casefold()
                for name in raw_titles),
        },
        "authoritative_column_mapping_proven": False,
        "instrument_change_proven": False,
    }


def _html_layout(raw: bytes) -> dict:
    if not 0 < len(raw) <= MAX_MEMBER_BYTES:
        raise EquipmentBlocked("HTML metadata member out of reviewed byte bound")
    text, encoding = _decode_text(raw)
    parser = MarkupCounts()
    parser.feed(text)
    parser.close()
    return {
        "html_member_bytes": len(raw),
        "html_sha256": hashlib.sha256(raw).hexdigest(),
        "encoding_hint": encoding,
        "tables": parser.table_count,
        "table_rows": parser.tr_count,
        "header_cells": parser.th_count,
        "value_cells": parser.td_count,
        "provider_html_semantics_interpreted": False,
    }


def analyze(path: Path, *, expected_sha256: str = evidence.EXPECTED_METADATA_SHA256) -> dict:
    try:
        receipt = evidence._collect(Path(path), expected_sha256,
                                    evidence.EXPECTED_STATION_ID)
        raw_zip = evidence._read_bounded_regular_snapshot(
            Path(path), receipt["metadata_asset"]["byte_size"])
    except (OSError, evidence.TemporalEvidenceError) as exc:
        raise EquipmentBlocked("frozen DWD metadata ZIP evidence gate failed") from exc
    if hashlib.sha256(raw_zip).hexdigest() != expected_sha256:
        raise EquipmentBlocked("original DWD metadata bytes changed after inspection")

    originals = {
        m["path"]: m["sha256"]
        for members in receipt["required_family_members"].values()
        for m in members
    }
    actual = {name for name in originals if name.startswith(
        ("Metadaten_Geraete_", "Metadaten_Parameter_"))}
    expected = {stem + ext for stem in PAIRS for ext in (".txt", ".html")}
    if actual != expected:
        raise EquipmentBlocked("original source equipment/parameter member set drifted")
    shapes = {}
    try:
        with zipfile.ZipFile(io.BytesIO(raw_zip), "r") as archive:
            for stem in PAIRS:
                txt_name, html_name = stem + ".txt", stem + ".html"
                txt, page = archive.read(txt_name), archive.read(html_name)
                if (hashlib.sha256(txt).hexdigest() != originals[txt_name]
                        or hashlib.sha256(page).hexdigest() != originals[html_name]):
                    raise EquipmentBlocked("original DWD equipment/parameter member SHA changed")
                shapes[stem] = {"txt": _txt_layout(txt), "html": _html_layout(page)}
    except (KeyError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise EquipmentBlocked("original metadata member read failed") from exc
    return {
        "profile": "opencatastrophe-dwd-00003-equipment-layout-receipt-v0",
        "station_id": evidence.EXPECTED_STATION_ID,
        "source_metadata_zip_sha256": expected_sha256,
        "linked_wind_measurement_sha256": evidence.MEASUREMENT_SHA256,
        "member_pairs_verified": len(shapes),
        "pair_layouts": shapes,
        "coordinate_values_emitted": False,
        "instrument_values_emitted": False,
        "original_member_rows_emitted": False,
        "date_field_meanings_verified": False,
        "instrument_timeline_verified": False,
        "measurement_homogeneity_verified": False,
        "model_input_approved": False,
        "next_gate": "Obtain official interpretation of observed TXT columns/HTML and historical sensor validity; never infer them from date-like tokens.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = analyze(args.source_zip)
    except EquipmentBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
