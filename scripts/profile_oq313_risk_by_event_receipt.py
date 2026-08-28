# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile a canonical OpenQuake 3.13 risk_by_event receipt offline.

The profiler consumes the full canonical receipt already produced by the reviewed
EQ1 OQ3.13 projection path. It does not run OpenQuake, fetch provider bytes, or
annualize the event losses. Its output is descriptive evidence only: exact source
identity, event/rupture/realization counts, binary32 loss extrema, predeclared
empirical nearest-rank points, and exact binary sums of the stored float32 values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import struct
import sys
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

try:
    from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import run_esrm20_kosovo_residential_ebrisk_openquake313_action as action

SCHEMA_VERSION = "oc-oq313-risk-by-event-profile-v1"
_SOURCE_SCHEMA_VERSION = "oc-oq313-risk-by-event-receipt-v2"
_BUFFER_SIZE = 1024 * 1024
_EMPIRICAL_RANKS = (
    ("p50", 1, 2),
    ("p90", 9, 10),
    ("p95", 19, 20),
    ("p99", 99, 100),
    ("p995", 199, 200),
    ("p999", 999, 1000),
)


class OQ313RiskByEventProfileError(RuntimeError):
    """The full numerical receipt cannot be profiled safely."""


def _stable_stat(path: Path) -> tuple[int, int]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise OQ313RiskByEventProfileError("cannot stat numerical receipt") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise OQ313RiskByEventProfileError(
            "numerical receipt must be one regular non-symlink file"
        )
    if info.st_size <= 0:
        raise OQ313RiskByEventProfileError("numerical receipt must be non-empty")
    return info.st_size, info.st_mtime_ns


def _read_stable_bytes(path: Path) -> bytes:
    if not isinstance(path, Path):
        raise OQ313RiskByEventProfileError("numerical receipt path must be a Path")
    before = _stable_stat(path)
    digest = hashlib.sha256()
    payload = bytearray()
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(_BUFFER_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
                payload.extend(chunk)
    except OSError as exc:
        raise OQ313RiskByEventProfileError("cannot read numerical receipt") from exc
    after = _stable_stat(path)
    if before != after or len(payload) != before[0]:
        raise OQ313RiskByEventProfileError(
            "numerical receipt changed while it was being read"
        )
    # Hash while reading to force the entire file through the stable-read path.
    # The public identity is recomputed again from immutable bytes below.
    digest.hexdigest()
    return bytes(payload)


def _receipt_identity(payload: bytes) -> dict[str, Any]:
    return {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _load_validated_receipt(payload: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(payload) is not bytes or not payload:
        raise OQ313RiskByEventProfileError(
            "numerical receipt must be non-empty bytes"
        )
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise OQ313RiskByEventProfileError(
            "numerical receipt is not strict UTF-8"
        ) from exc
    try:
        document = action._load_json_text(text, label="numerical receipt")
    except action.KosovoResidentialOQ313ActionError as exc:
        raise OQ313RiskByEventProfileError("numerical receipt JSON is invalid") from exc
    if type(document) is not dict:
        raise OQ313RiskByEventProfileError("numerical receipt must be an object")
    if document.get("schema_version") != _SOURCE_SCHEMA_VERSION:
        raise OQ313RiskByEventProfileError(
            "numerical receipt schema is not the canonical v2 receipt"
        )
    runtime = document.get("runtime")
    if type(runtime) is not dict:
        raise OQ313RiskByEventProfileError("numerical receipt runtime is missing")
    concurrent_tasks = runtime.get("concurrent_tasks")
    if type(concurrent_tasks) is not int or concurrent_tasks < 0:
        raise OQ313RiskByEventProfileError(
            "numerical receipt concurrent_tasks is invalid"
        )
    identity = _receipt_identity(payload)
    try:
        return action._validate_numerical_receipt(
            payload,
            identity,
            expected_concurrent_tasks=concurrent_tasks,
        )
    except action.KosovoResidentialOQ313ActionError as exc:
        raise OQ313RiskByEventProfileError(
            "numerical receipt failed current EQ1 validation"
        ) from exc


def _f32_bits(value: str) -> int:
    if type(value) is not str or len(value) != 8:
        raise OQ313RiskByEventProfileError("binary32 value is not canonical hex")
    try:
        bits = int(value, 16)
    except ValueError as exc:
        raise OQ313RiskByEventProfileError("binary32 value is not canonical hex") from exc
    if value != f"{bits:08x}":
        raise OQ313RiskByEventProfileError("binary32 value is not canonical lowercase hex")
    exponent = (bits >> 23) & 0xFF
    if bits >> 31 or exponent == 0xFF:
        raise OQ313RiskByEventProfileError(
            "profile requires finite non-negative binary32 values"
        )
    return bits


def _f32_units_2_neg_149(value: str) -> int:
    bits = _f32_bits(value)
    exponent = (bits >> 23) & 0xFF
    fraction = bits & 0x7FFFFF
    if exponent == 0:
        return fraction
    significand = (1 << 23) | fraction
    return significand << (exponent - 1)


def _normalized_exact_binary(units: int) -> dict[str, Any]:
    if type(units) is not int or units < 0:
        raise OQ313RiskByEventProfileError("exact binary sum units are invalid")
    if units == 0:
        return {
            "coefficient": "0",
            "binary_exponent": 0,
            "approx_decimal": "0",
        }
    coefficient = units
    exponent = -149
    trailing = (coefficient & -coefficient).bit_length() - 1
    coefficient >>= trailing
    exponent += trailing
    with localcontext() as context:
        context.prec = 18
        approximate = Decimal(coefficient) * (Decimal(2) ** exponent)
    return {
        "coefficient": str(coefficient),
        "binary_exponent": exponent,
        "approx_decimal": format(approximate, ".17g"),
    }


def _f32_decimal(value: str) -> str:
    bits = _f32_bits(value)
    decoded = struct.unpack("!f", bits.to_bytes(4, "big"))[0]
    return format(decoded, ".9g")


def _row_view(row: dict[str, Any]) -> dict[str, Any]:
    loss_hex = row["loss_f32_be_hex"]
    variance_hex = row["variance_f32_be_hex"]
    return {
        "event_id": row["event_id"],
        "rup_id": row["rup_id"],
        "rlz_id": row["rlz_id"],
        "loss_f32_be_hex": loss_hex,
        "loss_approx_eur": _f32_decimal(loss_hex),
        "variance_f32_be_hex": variance_hex,
    }


def _nearest_rank(row_count: int, numerator: int, denominator: int) -> int:
    return (numerator * row_count + denominator - 1) // denominator


def profile_receipt(payload: bytes) -> dict[str, Any]:
    """Return a deterministic descriptive profile of one full canonical receipt."""

    document, identity = _load_validated_receipt(payload)
    rows_object = document.get("rows")
    if type(rows_object) is not list or not rows_object:
        raise OQ313RiskByEventProfileError("validated numerical receipt has no rows")
    rows: list[dict[str, Any]] = []
    for row in rows_object:
        if type(row) is not dict:
            raise OQ313RiskByEventProfileError("validated row is not an object")
        rows.append(row)

    ranked = sorted(
        rows,
        key=lambda row: (_f32_bits(row["loss_f32_be_hex"]), row["event_id"]),
    )
    top = sorted(
        rows,
        key=lambda row: (-_f32_bits(row["loss_f32_be_hex"]), row["event_id"]),
    )[:10]

    loss_units = 0
    variance_units = 0
    zero_loss_count = 0
    zero_variance_count = 0
    rupture_ids: set[int] = set()
    realization_counts: Counter[int] = Counter()
    for row in rows:
        loss_bits = _f32_bits(row["loss_f32_be_hex"])
        variance_bits = _f32_bits(row["variance_f32_be_hex"])
        loss_units += _f32_units_2_neg_149(row["loss_f32_be_hex"])
        variance_units += _f32_units_2_neg_149(row["variance_f32_be_hex"])
        zero_loss_count += int(loss_bits == 0)
        zero_variance_count += int(variance_bits == 0)
        rupture_ids.add(row["rup_id"])
        realization_counts[row["rlz_id"]] += 1

    empirical_ranks = []
    for label, numerator, denominator in _EMPIRICAL_RANKS:
        rank = _nearest_rank(len(ranked), numerator, denominator)
        empirical_ranks.append(
            {
                "label": label,
                "probability_fraction": f"{numerator}/{denominator}",
                "rank_1_based": rank,
                "row": _row_view(ranked[rank - 1]),
            }
        )

    event_ids = [row["event_id"] for row in rows]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_receipt": {
            "schema_version": document["schema_version"],
            "identity": identity,
            "openquake": document["openquake"],
            "quantity": document["quantity"],
            "selection": document["selection"],
            "runtime": document["runtime"],
            "experiment_label": document["experiment_label"],
            "insurance_scope": document["insurance_scope"],
            "source_dataset": document["source_dataset"],
        },
        "profile_basis": "empirical_selected_event_rows_without_occurrence_weights",
        "row_count": len(rows),
        "event_id_range": {"minimum": min(event_ids), "maximum": max(event_ids)},
        "distinct_rup_id_count": len(rupture_ids),
        "distinct_rlz_id_count": len(realization_counts),
        "rows_by_rlz_id": [
            {"rlz_id": rlz_id, "row_count": realization_counts[rlz_id]}
            for rlz_id in sorted(realization_counts)
        ],
        "loss": {
            "zero_row_count": zero_loss_count,
            "exact_sum_binary": _normalized_exact_binary(loss_units),
            "minimum_row": _row_view(ranked[0]),
            "maximum_row": _row_view(top[0]),
            "empirical_nearest_ranks": empirical_ranks,
            "top_loss_rows": [_row_view(row) for row in top],
        },
        "variance": {
            "zero_row_count": zero_variance_count,
            "exact_sum_binary": _normalized_exact_binary(variance_units),
        },
        "annualized_metrics_authorized": False,
        "aal_authorized": False,
        "oep_authorized": False,
        "aep_authorized": False,
        "historical_reproduction_verified": False,
        "numerical_reference_loss_verified": False,
        "scientific_validity_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_receipt_file(path: Path) -> dict[str, Any]:
    return profile_receipt(_read_stable_bytes(path))


def _canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Profile a full canonical EQ1 OpenQuake 3.13 risk_by_event receipt "
            "offline without rerunning or annualizing the model."
        )
    )
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        result = profile_receipt_file(args.receipt)
    except OQ313RiskByEventProfileError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(_canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
