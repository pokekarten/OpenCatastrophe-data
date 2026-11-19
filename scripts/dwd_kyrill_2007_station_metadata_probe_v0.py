#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded source-byte, raw-schema probe for three ORIGINAL DWD FX_10 metadata ZIPs.

Research provenance only. Report short excerpts of PUBLIC station metadata rows,
not weather observations, not insurers, and not 2007 certified instruments.
An exact historical valid-at-date join follows review of real source layout.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile, BadZipFile

STATIONS = ("00433", "01262", "03379")
BASE = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/extreme_wind/meta_data/"
CONTRACT = "OC_DWD_KYRILL_2007_ORIGINAL_STATION_METADATA_SHAPES_V0"
MAX_ZIP = 30_000
MAX_FILE = 200_000
MAX_TOTAL = 500_000
MAX_MEMBERS = 30
MAX_PREVIEW_LEN = 160
MAX_PREVIEW_LINES = 10

class MetadataProbeBlocked(ValueError):
    """Original metadata structure unsafe or not traceable."""


def classify(name: str) -> str | None:
    low = name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    for fragment, label in (("geographie", "geography"), ("geraete", "instruments"),
                            ("parameter", "parameters"), ("stationsname", "station_names")):
        if fragment in low:
            return label
    return None


def inspect_original_metadata(raw: bytes, *, station: str) -> dict:
    if (type(station) is not str or station not in STATIONS or type(raw) is not bytes
            or not 100 <= len(raw) <= MAX_ZIP or not raw.startswith(b"PK\x03\x04")):
        raise MetadataProbeBlocked("explicit station and bounded original ZIP required")
    out = []
    seen = set()
    count = Counter()
    member_names = []
    try:
        with ZipFile(BytesIO(raw)) as z:
            files = z.infolist()
            if not 1 <= len(files) <= MAX_MEMBERS or sum(i.file_size for i in files) > MAX_TOTAL:
                raise MetadataProbeBlocked("unbounded metadata member count/size")
            for item in files:
                if item.is_dir():
                    continue
                name = item.filename
                if (name in seen or not 0 < len(name) <= 160 or name.startswith("/")
                        or ".." in name.replace("\\", "/").split("/")
                        or item.file_size > MAX_FILE or item.file_size <= 0
                        or (item.external_attr >> 16) & 0o170000 == 0o120000):
                    raise MetadataProbeBlocked("unsafe or duplicate metadata member")
                seen.add(name)
                member_names.append(name)
                payload = z.read(item)  # checks member CRC
                if len(payload) != item.file_size:
                    raise MetadataProbeBlocked("metadata member expanded size differs")
                kind = classify(name)
                if kind is None:
                    continue
                count[kind] += 1
                try:
                    txt = payload.decode("utf-8-sig")
                    encoding = "utf-8-sig"
                except UnicodeDecodeError:
                    try:
                        txt = payload.decode("cp1252")
                        encoding = "cp1252"
                    except UnicodeDecodeError as e:
                        raise MetadataProbeBlocked("unknown metadata encoding") from e
                lines = [line.strip() for line in txt.splitlines() if line.strip()]
                if not lines or len(lines) > 3000:
                    raise MetadataProbeBlocked("empty/oversized metadata rows")
                # A bounded preview includes only STATION METADATA, not weather measurements.
                first = lines[:MAX_PREVIEW_LINES]
                last = lines[-min(3, len(lines)):]
                out.append({
                    "kind": kind, "member": name, "source_member_sha256": sha256(payload).hexdigest(),
                    "member_bytes": len(payload), "line_count": len(lines), "encoding": encoding,
                    "initial_metadata_lines": [s[:MAX_PREVIEW_LEN] for s in first],
                    "final_metadata_lines": [s[:MAX_PREVIEW_LEN] for s in last],
                })
    except (BadZipFile, OSError, RuntimeError, EOFError) as e:
        raise MetadataProbeBlocked("metadata ZIP invalid or CRC failed") from e
    complete = all(count[k] == 1 for k in ("geography", "instruments", "parameters"))
    return {
        "contract": CONTRACT,
        "station_id": station,
        "original_archive_filename": f"Meta_Daten_zehn_min_fx_{station}.zip",
        "original_source_url": BASE + f"Meta_Daten_zehn_min_fx_{station}.zip",
        "original_zip_sha256": sha256(raw).hexdigest(),
        "original_zip_bytes": len(raw),
        "metadata_categories": dict(sorted(count.items())),
        "original_zip_member_names": sorted(member_names),
        "exactly_one_each_required_category_found": complete,
        "original_metadata_schema_unambiguous": complete,
        "metadata_schemas_reproduced": out,
        "source_is_original_DWD_metadata_zip": True,
        "source_2007_instrument_validity_resolved": False,
        "source_2007_station_geography_resolved": False,
        "source_2007_sensor_height_resolved": False,
        "QN1_data_promoted_to_QN3": False,
        "fit_of_any_ERA5_wind_model": False,
        "calibrated_physical_or_insured_damage": False,
        "annual_AAL": None, "annual_AEP": None, "annual_OEP": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for station in STATIONS:
        ap.add_argument(f"--zip-{station}", type=Path, required=True)
    args = ap.parse_args()
    results = []
    for station in STATIONS:
        p = getattr(args, "zip_" + station)
        if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_ZIP:
            ap.error("original metadata ZIP must be a bounded regular file")
        results.append(inspect_original_metadata(p.read_bytes(), station=station))
    print(json.dumps({"contract": CONTRACT, "stations": results}, indent=2,
                     sort_keys=True, ensure_ascii=True, allow_nan=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
