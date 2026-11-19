#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read exactly frozen DWD station-00003 metadata TABLE SHAPES, not source rows.

This is an offline original-source structure audit. It uses the existing
SHA-pinned, no-follow metadata evidence gate, records only member/header
identities and row counts, and deliberately grants no geographic or temporal
validity to wind measurements.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from scripts import dwd_metadata_temporal_evidence as evidence

MAX_MEMBER_BYTES = 512_000
MAX_HEADER_BYTES = 4_096
MAX_ROWS = 50_000
HEADER_TOKEN = re.compile(r"[A-Za-z_\u00c0-\u024f][\w .()/:%-]{0,95}\Z")


class MetadataShapeBlocked(ValueError):
    """Source original or metadata schema cannot be safely inventoried."""


def _table_shape(raw: bytes) -> dict:
    if not raw or len(raw) > MAX_MEMBER_BYTES:
        raise MetadataShapeBlocked("metadata source member exceeds bounded byte gate")
    # Record the encoding decision as a best-effort byte decoding hint, never
    # as an assertion of an authoritative original format specification.
    try:
        text = raw.decode("utf-8-sig")
        encoding_hint = "utf-8"
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError as exc:
            raise MetadataShapeBlocked("unsupported metadata member text encoding") from exc
        encoding_hint = "cp1252_heuristic"
    lines = text.splitlines()
    if len(lines) > MAX_ROWS + 1:
        raise MetadataShapeBlocked("metadata original exceeds audited line limit")
    if not lines or len(lines[0].encode("utf-8")) > MAX_HEADER_BYTES:
        raise MetadataShapeBlocked("missing or overlong metadata header")
    first = lines[0]
    delimiters = [separator for separator in (";", "\t") if separator in first]
    result = {
        "member_sha256": hashlib.sha256(raw).hexdigest(),
        "member_bytes": len(raw),
        "encoding_hint": encoding_hint,
        "header_recognized": False,
        "columns": [],
        "delimiter": None,
        "nonempty_data_lines": sum(bool(line.strip()) for line in lines[1:]),
        "same_field_count_on_data_lines": False,
        "temporal_intervals_validated": False,
        "station_coordinates_validated": False,
    }
    if len(delimiters) != 1:
        result["shape_status"] = "blocked_delimiter_not_verified"
        return result
    delimiter = delimiters[0]
    try:
        columns = next(csv.reader([first], delimiter=delimiter, strict=True))
    except csv.Error:
        result["shape_status"] = "blocked_header_parse"
        return result
    cleaned = [token.strip().lstrip("\ufeff") for token in columns]
    if (len(cleaned) < 2 or len(cleaned) > 80
            or len(set(x.casefold() for x in cleaned)) != len(cleaned)
            or any(not HEADER_TOKEN.fullmatch(x) for x in cleaned)):
        result["shape_status"] = "blocked_unrecognized_header"
        return result
    # Only provider COLUMN NAMES (not data rows) are surfaced. Original
    # station coordinates and instrument measurements never leave memory.
    result.update({
        "header_recognized": True,
        "columns": cleaned,
        "delimiter": "semicolon" if delimiter == ";" else "tab",
    })
    for line in lines[1:]:
        if not line.strip():
            continue
        try:
            fields = next(csv.reader([line], delimiter=delimiter, strict=True))
        except csv.Error:
            result["shape_status"] = "blocked_csv_row_shape"
            return result
        if len(fields) != len(cleaned):
            result["shape_status"] = "blocked_csv_row_field_count"
            return result
    result["same_field_count_on_data_lines"] = True
    result["shape_status"] = "syntactically_consistent_unreviewed_columns"
    return result


def profile(path: Path, *, expected_sha256: str = evidence.EXPECTED_METADATA_SHA256) -> dict:
    path = Path(path)
    try:
        verified = evidence._collect(path, expected_sha256, evidence.EXPECTED_STATION_ID)
        # Reopen through the existing no-follow, bounded, regular-file route
        # and compare the original hash before any member data are interpreted.
        original = evidence._read_bounded_regular_snapshot(
            path, verified["metadata_asset"]["byte_size"])
    except (OSError, evidence.TemporalEvidenceError) as exc:
        raise MetadataShapeBlocked("pinned original metadata ZIP evidence gate failed") from exc
    if hashlib.sha256(original).hexdigest() != expected_sha256:
        raise MetadataShapeBlocked("original changed since required evidence snapshot")
    families = {}
    try:
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            for family, members in sorted(verified["required_family_members"].items()):
                items = []
                for member in members:
                    info = archive.getinfo(member["path"])
                    if info.file_size > MAX_MEMBER_BYTES:
                        raise MetadataShapeBlocked("metadata member exceeds strict source size bound")
                    raw = archive.read(info)
                    shape = _table_shape(raw)
                    if shape["member_sha256"] != member["sha256"]:
                        raise MetadataShapeBlocked("metadata family member changed after evidence gate")
                    items.append({
                        "member": member["path"],
                        **shape,
                    })
                families[family] = items
    except (zipfile.BadZipFile, RuntimeError, KeyError) as exc:
        raise MetadataShapeBlocked("provider ZIP member extraction failed") from exc
    members_total = sum(len(members) for members in families.values())
    recognized = sum(x["header_recognized"] for members in families.values() for x in members)
    return {
        "profile": "opencatastrophe-dwd-00003-metadata-original-table-shapes-v0",
        "source_zip_sha256": expected_sha256,
        "station_id": evidence.EXPECTED_STATION_ID,
        "frozen_measurement_sha256": evidence.MEASUREMENT_SHA256,
        "measurement_window": evidence.MEASUREMENT_WINDOW,
        "required_families": families,
        "members_examined": members_total,
        "recognized_delimited_headers": recognized,
        "valid_geography_for_measurement_window": False,
        "valid_instrument_for_measurement_window": False,
        "valid_parameter_for_measurement_window": False,
        "model_input_approved": False,
        "raw_metadata_rows_persisted": False,
        "next_action": "Independently review original DWD column semantics and period endpoints; implement interval join only after authoritative field mapping.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        output = profile(args.source_zip)
    except MetadataShapeBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
