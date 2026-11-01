#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-original DWD station 00348 device and parameter *layout* receipt.

This checks the separately SHA-pinned real original station-00348 metadata ZIP.
It reports provider-native TXT column names (only if strongly recognizable),
family inventories, date *token* counts and member hashes. No device identities,
original date values, coordinates, sensor heights or rows are emitted. It does
NOT establish a model-ready FX_10 instrument or a historical validity join.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

from scripts.dwd_equipment_layout_evidence_v0 import (
    EquipmentBlocked, _txt_layout, _html_layout,
)
from scripts.probe_dwd_station00348_original_v0 import (
    METADATA_FILE, PINNED_METADATA_SHA256, MAX_METADATA_ZIP,
    MAX_METADATA_EXPANDED, STATION, _snapshot, _zip_open,
    SecondStationBlocked,
)

DEVICE_RE = re.compile(
    r"Metadaten_Geraete_[A-Za-z0-9_]+_" + STATION + r"\.txt\Z"
)
PARAM_RE = re.compile(r"Metadaten_Parameter_" + STATION + r"\.txt\Z")
MAX_DEVICE_FAMILIES = 8


class SecondStationLayoutBlocked(ValueError):
    """Station-specific original metadata failed an exact-source format gate."""


def inspect(path: Path, *, expected_sha256: str = PINNED_METADATA_SHA256) -> dict:
    try:
        snapshot = _snapshot(Path(path), METADATA_FILE, MAX_METADATA_ZIP)
    except (OSError, ValueError) as exc:
        raise SecondStationLayoutBlocked("second station original ZIP snapshot blocked") from exc
    original_sha = hashlib.sha256(snapshot).hexdigest()
    if not isinstance(expected_sha256, str) or original_sha != expected_sha256:
        raise SecondStationLayoutBlocked("second station original metadata SHA-256 mismatch")
    instruments = {}
    parameter = None
    unrecognized_txt = 0
    try:
        with _zip_open(snapshot, max_expanded=MAX_METADATA_EXPANDED) as archive:
            members = {i.filename: i for i in archive.infolist() if not i.is_dir()}
            device_names = sorted(name for name in members if DEVICE_RE.fullmatch(name))
            parameter_names = [name for name in members if PARAM_RE.fullmatch(name)]
            if not (1 <= len(device_names) <= MAX_DEVICE_FAMILIES
                    and len(parameter_names) == 1):
                raise SecondStationLayoutBlocked("device/parameter family original member set unsupported")
            for name in device_names + parameter_names:
                original = archive.read(name)
                layout = _txt_layout(original)
                if not layout["header_candidate_recognized"]:
                    unrecognized_txt += 1
                partner = name[:-4] + ".html"
                html = _html_layout(archive.read(partner)) if partner in members else None
                summary = {
                    "original_txt_member": name,
                    "original_txt_sha256": hashlib.sha256(original).hexdigest(),
                    "original_txt_bytes": len(original),
                    "nonempty_txt_lines": layout["nonempty_lines"],
                    "date_candidate_tokens": layout["valid_calendar_tokens"],
                    "native_header_candidate_recognized": layout["header_candidate_recognized"],
                    "native_source_header_only": layout["source_column_names"],
                    "provider_html_companion_present": bool(html),
                    "provider_html_sha256": html["html_sha256"] if html else None,
                    "provider_html_tables": html["tables"] if html else None,
                    "temporal_meaning_verified": False,
                }
                if name in device_names:
                    instruments[name] = summary
                else:
                    parameter = summary
            # Full CRC/decompression of other original members without
            # printing their data or permitting unreviewed ZIP paths.
            for name in sorted(members):
                if name in device_names + parameter_names:
                    continue
                with archive.open(name) as fh:
                    while fh.read(65_536):
                        pass
    except (EquipmentBlocked, SecondStationBlocked, OSError,
            RuntimeError, zipfile.BadZipFile) as exc:
        raise SecondStationLayoutBlocked("original DWD member not safely readable") from exc
    if parameter is None:
        raise SecondStationLayoutBlocked("original DWD parameter table missing")
    return {
        "profile": "opencatastrophe-dwd-station00348-instrument-layout-v0",
        "station": STATION,
        "metadata_zip_sha256": original_sha,
        "independent_original_source_pinned": original_sha == PINNED_METADATA_SHA256,
        "equipment_txt_family_count": len(instruments),
        "equipment_txt": instruments,
        "parameter_txt": parameter,
        "txt_families_with_unrecognized_headers": unrecognized_txt,
        "sensor_history_temporal_join_verified": False,
        "fx10_to_maxwind_foreign_key_proven": False,
        "original_source_rows_or_coordinates_persisted": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-zip", required=True, type=Path)
    opts = parser.parse_args(argv)
    try:
        result = inspect(opts.metadata_zip)
    except SecondStationLayoutBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
