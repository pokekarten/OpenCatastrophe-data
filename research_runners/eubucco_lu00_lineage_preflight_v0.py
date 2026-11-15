#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Local, research-only source-lineage profile of EUBUCCO v0.2 Luxembourg LU00.

No network, database, source-geometry extraction, crosswalk, or model admission.
Requires optional pyarrow; only aggregate counts and original-byte SHA are output.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

MAX_BYTES = 256 * 1024 * 1024
MAX_ROWS = 2_000_000
MAX_ROW_GROUPS = 10_000
EXPECTED_PARTITION = "LU00"
EXPECTED_REGION = "LU000"
EXPECTED_SOURCE_ID = "eubucco.buildings.v0.2"
REQUIRED = frozenset(("id", "region_id", "geometry", "geometry_source"))
OPTIONAL_PROVENANCE = (
    "type_source", "subtype_source", "height_source",
    "floors_source", "construction_year_source",
)
OPTIONAL_ATTRIBUTES = ("type", "subtype", "height", "floors", "construction_year")
AVAILABILITY_CATEGORIES = ("present", "null", "blank", "nonfinite")


class EubuccoPreflightError(ValueError):
    """Unusable, unbounded, noncanonical, or unverified original data."""


def _field_bucket(value: object) -> str:
    if value is None:
        return "missing"
    if not isinstance(value, str):
        raise EubuccoPreflightError("unexpected source-provenance field type")
    if not value.strip() or len(value) > 128:
        return "missing"
    if value == "estimated":
        return "model_estimated"
    if value in ("osm", "msft"):
        return value
    if value.startswith("gov-"):
        return "government_label_unverified"
    return "other_source_label_unverified"


def inspect(path: Path, expected_sha256: str, *, source_id: str = EXPECTED_SOURCE_ID,
            partition_id: str = EXPECTED_PARTITION) -> dict:
    if source_id != EXPECTED_SOURCE_ID or partition_id != EXPECTED_PARTITION:
        raise EubuccoPreflightError("only v0.2 Luxembourg NUTS2 LU00 is supported")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise EubuccoPreflightError("full original source SHA-256 required before reading")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise EubuccoPreflightError("regular local file and <=256 MiB required")
    try:
        original = path.read_bytes()  # Single exact immutable input for digest AND parser.
    except OSError as exc:
        raise EubuccoPreflightError("cannot read local Parquet") from exc
    if len(original) < 12 or len(original) > MAX_BYTES:
        raise EubuccoPreflightError("empty or oversized input")
    actual_hash = hashlib.sha256(original).hexdigest()
    if actual_hash != expected_sha256:
        raise EubuccoPreflightError("original source SHA-256 mismatch")
    if original[:4] != b"PAR1" or original[-4:] != b"PAR1":
        raise EubuccoPreflightError("missing Parquet header/footer")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise EubuccoPreflightError("optional pinned pyarrow runtime not installed") from exc

    try:
        file = pq.ParquetFile(pa.BufferReader(original))
        meta = file.metadata
        if (meta.num_rows < 1 or meta.num_rows > MAX_ROWS
                or meta.num_row_groups < 1 or meta.num_row_groups > MAX_ROW_GROUPS):
            raise EubuccoPreflightError("row/row-group budget exceeded")
        names = set(file.schema_arrow.names)
        if not REQUIRED.issubset(names):
            raise EubuccoPreflightError("missing EUBUCCO identity/geometry/source columns")
        dtype = file.schema_arrow.field("geometry").type
        if not (pa.types.is_binary(dtype) or pa.types.is_large_binary(dtype)):
            raise EubuccoPreflightError("geometry column is not WKB binary")

        selected = ["id", "region_id", "geometry_source"] + [
            name for name in OPTIONAL_PROVENANCE if name in names
        ] + [name for name in OPTIONAL_ATTRIBUTES if name in names]
        geometry_sources = Counter()
        provenance_counts = {name: Counter() for name in OPTIONAL_PROVENANCE if name in names}
        attribute_counts = {name: Counter() for name in OPTIONAL_ATTRIBUTES if name in names}
        seen_ids = set()
        processed = 0
        for batch in file.iter_batches(batch_size=4096, columns=selected):
            entries = batch.to_pylist()
            for entry in entries:
                ident, region = entry["id"], entry["region_id"]
                if (not isinstance(ident, str) or not ident or len(ident) > 256
                        or ident in seen_ids):
                    raise EubuccoPreflightError("missing, invalid or duplicate EUBUCCO building id")
                if region != EXPECTED_REGION:
                    raise EubuccoPreflightError("partition contains non-LU000 NUTS3 region")
                seen_ids.add(ident)
                geometry_sources[_field_bucket(entry["geometry_source"])] += 1
                for name, count in provenance_counts.items():
                    count[_field_bucket(entry[name])] += 1
                for name, count in attribute_counts.items():
                    value = entry[name]
                    if value is None:
                        count["null"] += 1
                    elif isinstance(value, str) and not value.strip():
                        count["blank"] += 1
                    elif isinstance(value, float) and not math.isfinite(value):
                        count["nonfinite"] += 1
                    else:
                        count["present"] += 1
                processed += 1
        if processed != meta.num_rows:
            raise EubuccoPreflightError("Parquet metadata/decoded row count mismatch")
    except EubuccoPreflightError:
        raise
    except Exception as exc:
        raise EubuccoPreflightError("Parquet decode/schema validation failed") from exc

    return {
        "schema_version": "eubucco-lu00-lineage-preflight-v0",
        "source_id": EXPECTED_SOURCE_ID,
        "provider_nuts2_partition": EXPECTED_PARTITION,
        "provider_nuts3_region": EXPECTED_REGION,
        "source_bytes_sha256": actual_hash,
        "source_bytes": len(original),
        "parquet_row_groups": meta.num_row_groups,
        "total_buildings": processed,
        "geometry_source_families": dict(sorted(geometry_sources.items())),
        "attribute_provenance_families": {
            key: dict(sorted(value.items())) for key, value in sorted(provenance_counts.items())
        },
        "missing_attribute_provenance_columns": sorted(
            set(OPTIONAL_PROVENANCE) - set(provenance_counts)
        ),
        "attribute_value_availability": {
            name: {state: counts[state] for state in AVAILABILITY_CATEGORIES}
            for name, counts in sorted(attribute_counts.items())
        },
        "missing_attribute_value_columns": sorted(set(OPTIONAL_ATTRIBUTES) - set(attribute_counts)),
        "crs_according_to_provider_documentation_only": "EPSG:3035",
        "wkb_geometries_scientifically_validated": False,
        "source_vintage_and_original_government_lineage_verified": False,
        "independence_from_luxembourg_act2023_established": False,
        "provider_rights_and_source_specific_licence_approved": False,
        "model_input_admitted": False,
        "provider_bytes_persisted_by_script": False,
        "building_identifiers_or_geometries_exported": False,
        "warning": (
            "Offline LU00 original-byte and provenance-category preflight only. "
            "Caller-declared original SHA-256 does not establish provider authenticity. "
            "Government, OSM and Microsoft lineage may overlap Luxembourg ACT data; "
            "attribute presence is not attribute accuracy or evidence of observed values; "
            "no independent ground truth, original vintage, geometries, property IDs, "            "source licensing, 2D-versus-roof footprint equivalence or CAT exposure established."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-id", default=EXPECTED_SOURCE_ID)
    parser.add_argument("--partition-id", default=EXPECTED_PARTITION)
    parser.add_argument("--out", type=Path, help="Optional aggregate-only JSON output")
    args = parser.parse_args(argv)
    try:
        result = inspect(
            args.original, args.expected_sha256, source_id=args.source_id,
            partition_id=args.partition_id,
        )
        rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.out:
            if args.out.is_symlink() or args.out.exists():
                raise EubuccoPreflightError("refuse overwrite/symlink output")
            with args.out.open("x", encoding="utf-8") as stream:
                stream.write(rendered)
        else:
            sys.stdout.write(rendered)
    except (EubuccoPreflightError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
