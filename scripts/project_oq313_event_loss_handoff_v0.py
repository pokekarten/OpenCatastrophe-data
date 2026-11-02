#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Project an existing, fully verified OQ3.13 EQ1 receipt to loss-only JSONL.

This is a deterministic, offline transport format for event-level GROUND-UP
structural replacement-cost loss. It is not Oasis ODR, an insured-loss table,
a stochastic event catalogue, an annualization, or an approved model input.
The full numerical receipt must be provided by the caller; the bounded public
commitment alone cannot be converted into 220k individual event-loss records.

Each output row is already checked by the canonical EQ1 receipt validator.
We carry the exact float32 bits, not a decimal re-interpretation or reduction.
An exact SHA-256 expected by the caller protects against changing receipts,
but the caller must independently authenticate the origin and usage rights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_oq313_risk_by_event_receipt as source

SCHEMA_VERSION = "oc-oq313-event-loss-jsonl-handoff-v0"
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_ROWS = 500_000
MAX_OUTPUT_BYTES = 96 * 1024 * 1024
_SHA = re.compile(r"^[0-9a-f]{64}$")


class EventLossHandoffError(ValueError):
    """A receipt, its identity or its local publication boundary is invalid."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii") + b"\n"


def project_event_loss_handoff(
    receipt: bytes, *, expected_receipt_sha256: str,
) -> tuple[bytes, bytes]:
    """Return (exact-row JSONL, bounded manifest), without I/O or admission."""
    if type(receipt) is not bytes or not 0 < len(receipt) <= MAX_INPUT_BYTES:
        raise EventLossHandoffError("receipt must be bounded non-empty bytes")
    if type(expected_receipt_sha256) is not str or not _SHA.fullmatch(expected_receipt_sha256):
        raise EventLossHandoffError("expected SHA-256 must be 64 lowercase hex digits")
    digest = hashlib.sha256(receipt).hexdigest()
    if digest != expected_receipt_sha256:
        raise EventLossHandoffError("supplied receipt differs from expected SHA-256")
    try:
        validated, identity = source._load_validated_receipt(receipt)
    except source.OQ313RiskByEventProfileError as exc:
        raise EventLossHandoffError("receipt did not pass canonical EQ1 validation") from exc

    rows = validated["rows"]
    if not 0 < len(rows) <= MAX_ROWS:
        raise EventLossHandoffError("receipt row count outside bounded research budget")
    lines = []
    total_bytes = 0
    # No event frequency, temporal order, policy, exposure allocation, financial
    # coverage or vulnerability conversion is introduced by this operation.
    for row in rows:
        line = _canonical_json({
            "event_id": row["event_id"],
            "rup_id": row["rup_id"],
            "rlz_id": row["rlz_id"],
            "loss_f32_be_hex": row["loss_f32_be_hex"],
            "variance_f32_be_hex": row["variance_f32_be_hex"],
        })
        total_bytes += len(line)
        if total_bytes > MAX_OUTPUT_BYTES:
            raise EventLossHandoffError("JSONL output exceeds bounded research budget")
        lines.append(line)
    jsonl = b"".join(lines)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "receipt_schema_version": validated["schema_version"],
            "receipt_sha256": identity["sha256"],
            "receipt_byte_count": identity["byte_count"],
            "source_dataset": validated["source_dataset"],
            "experiment_label": validated["experiment_label"],
            "openquake": validated["openquake"],
            "selection": validated["selection"],
            "quantity": validated["quantity"],
            "insurance_scope": validated["insurance_scope"],
        },
        "output": {
            "kind": "selected_ground_up_event_loss_jsonl",
            "byte_count": len(jsonl),
            "sha256": hashlib.sha256(jsonl).hexdigest(),
            "row_count": len(rows),
            "row_id_scope": "source_receipt_sha256_plus_event_id",
            "loss_encoding": "IEEE754_binary32_big_endian_lowercase_hex",
            "variance_encoding": "IEEE754_binary32_big_endian_lowercase_hex",
        },
        "origin_authenticated_by_this_projection": False,
        "original_provider_data_rights_confirmed": False,
        "event_rates_available": False,
        "shaking_footprints_available": False,
        "insured_loss_calculated": False,
        "policy_coverage_applied": False,
        "financial_terms_applied": False,
        "annualization_authorized": False,
        "oasis_odr_conformant": False,
        "nextgen_import_verified": False,
        "model_input_approved": False,
        "public_redistribution_authorized": False,
    }
    return jsonl, _canonical_json(manifest)


def _write_new(path: Path, data: bytes) -> None:
    """Write privately, without symlink following or replacing existing files."""
    if not isinstance(path, Path) or type(data) is not bytes or not data:
        raise EventLossHandoffError("new local output must be non-empty bytes")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as exc:
        raise EventLossHandoffError("cannot create new local output") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        path.unlink(missing_ok=True)
        raise EventLossHandoffError("cannot complete local output") from exc


def write_new_pair(
    jsonl_path: Path, manifest_path: Path, jsonl: bytes, manifest: bytes,
) -> None:
    if type(jsonl_path) is not Path or type(manifest_path) is not Path:
        raise EventLossHandoffError("output paths must be pathlib.Path")
    if jsonl_path.absolute() == manifest_path.absolute():
        raise EventLossHandoffError("JSONL and manifest paths must be distinct")
    if jsonl_path.exists() or jsonl_path.is_symlink() or manifest_path.exists() or manifest_path.is_symlink():
        raise EventLossHandoffError("local output path already exists")
    _write_new(jsonl_path, jsonl)
    try:
        _write_new(manifest_path, manifest)
    except EventLossHandoffError:
        jsonl_path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path, help="full canonical OQ3.13 EQ1 numerical receipt")
    parser.add_argument("--expected-receipt-sha256", required=True)
    parser.add_argument("--jsonl-out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        before = source._stable_stat(args.receipt)
        if before[0] > MAX_INPUT_BYTES:
            raise EventLossHandoffError("input exceeds bounded research budget")
        receipt = source._read_stable_bytes(args.receipt)
        rows, manifest = project_event_loss_handoff(
            receipt, expected_receipt_sha256=args.expected_receipt_sha256,
        )
        write_new_pair(args.jsonl_out, args.manifest_out, rows, manifest)
    except (EventLossHandoffError, source.OQ313RiskByEventProfileError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    # Do not echo model data or provider bytes. Manifest remains on local disk.
    print("PASS: offline loss-only JSONL and provenance manifest created; "
          "no CAT-model or insurance admission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
