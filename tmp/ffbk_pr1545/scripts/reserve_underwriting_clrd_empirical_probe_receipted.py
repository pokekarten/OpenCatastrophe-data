#!/usr/bin/env python3
"""Source-bound receipt wrapper for the exploratory CLRD UW/reserve probe.

The scientific probe intentionally remains a small standard-library analysis.
This wrapper binds any accepted result to the exact CSV bytes that were
verified before analysis, preventing an arbitrary schema-compatible CSV from
masquerading as the pinned legacy CLRD source.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import tempfile
from pathlib import Path
from typing import Sequence, Tuple

SOURCE_REPOSITORY = "casact/chainladder-python"
SOURCE_COMMIT = "221c4015d7d33c8520f57e3b522970f2e8baffab"
SOURCE_PATH = "chainladder/utils/data/clrd.csv"
SOURCE_GIT_BLOB = "04e54cfa41e7bd879877e5c5aea5e63a6d20d29b"

PILOT_GRCODES = (337, 353, 388, 671, 715, 965, 1066)
DEFAULT_LOB = "wkcomp"
DEFAULT_START_AY = 1988
DEFAULT_END_AY = 1997


def git_blob_sha1_bytes(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode("ascii"))
    h.update(data)
    return h.hexdigest()


def source_identity(data: bytes) -> dict:
    actual_blob = git_blob_sha1_bytes(data)
    return {
        "repository": SOURCE_REPOSITORY,
        "commit": SOURCE_COMMIT,
        "path": SOURCE_PATH,
        "expected_git_blob_sha1": SOURCE_GIT_BLOB,
        "git_blob_sha1": actual_blob,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "matches_pinned_source": actual_blob == SOURCE_GIT_BLOB,
    }


def _load_probe():
    return importlib.import_module("reserve_underwriting_clrd_empirical_probe")


def validate_result(
    result: dict,
    *,
    lob: str,
    grcodes: Sequence[int],
    start_ay: int,
    end_ay: int,
) -> None:
    expected_default = (
        lob == DEFAULT_LOB
        and tuple(grcodes) == PILOT_GRCODES
        and start_ay == DEFAULT_START_AY
        and end_ay == DEFAULT_END_AY
    )
    if expected_default:
        panel = result.get("panel", {})
        if panel.get("n") != 63 or panel.get("companies") != 7 or len(panel.get("years", [])) != 9:
            raise AssertionError(
                f"default pilot is not the expected balanced 7x9 panel: {panel}"
            )

    primary_raw = result.get("primary", {}).get("raw", {})
    for name in ("pearson", "spearman"):
        value = primary_raw.get(name)
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise AssertionError(f"primary {name} correlation is not finite")


def run_bound(
    path: Path,
    *,
    lob: str = DEFAULT_LOB,
    grcodes: Sequence[int] = PILOT_GRCODES,
    start_ay: int = DEFAULT_START_AY,
    end_ay: int = DEFAULT_END_AY,
    require_pinned_source: bool = False,
    validate: bool = False,
) -> dict:
    source_bytes = path.read_bytes()
    identity = source_identity(source_bytes)

    if require_pinned_source and not identity["matches_pinned_source"]:
        raise RuntimeError(
            "FAIL_CLOSED source Git blob mismatch: "
            f"expected {SOURCE_GIT_BLOB}, got {identity['git_blob_sha1']}"
        )

    probe = _load_probe()
    with tempfile.TemporaryDirectory(prefix="ffbk-clrd-bound-") as td:
        bound_path = Path(td) / "clrd.csv"
        bound_path.write_bytes(source_bytes)
        result = probe.run(bound_path, lob, tuple(grcodes), start_ay, end_ay)
        if bound_path.read_bytes() != source_bytes:
            raise RuntimeError("FAIL_CLOSED probe mutated the verified source copy")

    if validate:
        validate_result(
            result,
            lob=lob,
            grcodes=grcodes,
            start_ay=start_ay,
            end_ay=end_ay,
        )

    result = dict(result)
    result["source"] = identity
    result["source_binding"] = {
        "source_read_once_before_analysis": True,
        "analysis_materialized_from_verified_bytes": True,
        "post_analysis_copy_identity_rechecked": True,
        "check_requires_pinned_git_blob": bool(require_pinned_source),
    }
    return result


def parse_grcodes(value: str) -> Tuple[int, ...]:
    try:
        out = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("GRCODE values must be integers") from exc
    if not out:
        raise argparse.ArgumentTypeError("at least one GRCODE is required")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, help="CAS/chainladder legacy CLRD CSV")
    parser.add_argument("--lob", default=DEFAULT_LOB)
    parser.add_argument("--grcodes", type=parse_grcodes, default=PILOT_GRCODES)
    parser.add_argument("--start-ay", type=int, default=DEFAULT_START_AY)
    parser.add_argument("--end-ay", type=int, default=DEFAULT_END_AY)
    parser.add_argument(
        "--check",
        action="store_true",
        help="require the pinned legacy CLRD Git blob and validate the bounded pilot",
    )
    args = parser.parse_args()

    result = run_bound(
        args.csv,
        lob=args.lob,
        grcodes=args.grcodes,
        start_ay=args.start_ay,
        end_ay=args.end_ay,
        require_pinned_source=args.check,
        validate=args.check,
    )
    probe = _load_probe()
    print(
        json.dumps(
            probe.json_safe(result),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
