#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Verify a complete, bounded EQ1 event-loss JSONL handoff offline.

The supplied manifest and source-receipt SHA-256 must both match caller-pinned
values. Self-consistent digests do NOT prove source authenticity; the pinned
identities must originate in a separately trusted channel. Without the
optional complete source receipt, individual losses cannot be reconciled
against the originating OpenQuake output. This tool never admits insurance
or annualized losses and does not import into a model or database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import project_oq313_event_loss_handoff_v0 as producer
from scripts import project_oq313_risk_by_event_receipt as numerical
from scripts import profile_oq313_risk_by_event_receipt as source

_SHA = re.compile(r"^[0-9a-f]{64}$")
_F32 = re.compile(r"^[0-9a-f]{8}$")
_MAX_MANIFEST_BYTES = 32_768
_ROW_FIELDS = frozenset({
    "event_id", "rup_id", "rlz_id", "loss_f32_be_hex", "variance_f32_be_hex",
})
_OUT_FIELDS = frozenset({
    "kind", "byte_count", "sha256", "row_count", "row_id_scope",
    "loss_encoding", "variance_encoding",
})
_SOURCE_FIELDS = frozenset({
    "receipt_schema_version", "receipt_sha256", "receipt_byte_count",
    "source_dataset", "experiment_label", "openquake", "selection",
    "quantity", "insurance_scope",
})
_AUTHORITY_FIELDS = frozenset({
    "origin_authenticated_by_this_projection",
    "original_provider_data_rights_confirmed",
    "event_rates_available", "shaking_footprints_available",
    "insured_loss_calculated", "policy_coverage_applied",
    "financial_terms_applied", "annualization_authorized",
    "oasis_odr_conformant", "nextgen_import_verified",
    "model_input_approved", "public_redistribution_authorized",
})


class EventLossHandoffValidationError(ValueError):
    """A loss-only transport artifact has not passed the consumer boundary."""


def _require_sha(value: object, label: str) -> str:
    if type(value) is not str or _SHA.fullmatch(value) is None:
        raise EventLossHandoffValidationError(f"{label} must be lowercase SHA-256")
    return value


def _require_uint(value: object, max_value: int, label: str) -> None:
    if type(value) is not int or not 0 <= value <= max_value:
        raise EventLossHandoffValidationError(f"{label} is not a bounded unsigned integer")


def _require_float32(value: object, label: str) -> None:
    if type(value) is not str or _F32.fullmatch(value) is None:
        raise EventLossHandoffValidationError(f"{label} is not canonical float32 hex")
    number = struct.unpack("!f", bytes.fromhex(value))[0]
    # NaN or infinite are rejected; the source permits negative zero bits.
    if not (-float("inf") < number < float("inf")) or number < 0:
        raise EventLossHandoffValidationError(f"{label} is not finite non-negative float32")


def _parse_canonical(value: bytes, label: str) -> object:
    try:
        result = json.loads(value.decode("utf-8", errors="strict"))
        canonical = producer._canonical_json(result)
    except (UnicodeDecodeError, ValueError, TypeError, OverflowError) as exc:
        raise EventLossHandoffValidationError(f"{label} is not canonical JSON") from exc
    if canonical != value:
        raise EventLossHandoffValidationError(f"{label} canonical bytes drifted")
    return result


def validate_event_loss_handoff(
    jsonl: bytes, manifest_bytes: bytes, *,
    expected_manifest_sha256: str, expected_source_receipt_sha256: str,
    source_receipt: bytes | None = None,
) -> dict[str, Any]:
    """Check exact JSONL and manifest; optionally reconcile full source rows."""
    expected_manifest = _require_sha(expected_manifest_sha256, "manifest SHA")
    expected_source = _require_sha(expected_source_receipt_sha256, "source receipt SHA")
    if type(jsonl) is not bytes or not 0 < len(jsonl) <= producer.MAX_OUTPUT_BYTES:
        raise EventLossHandoffValidationError("JSONL exceeds bounded size or is empty")
    if type(manifest_bytes) is not bytes or not 0 < len(manifest_bytes) <= _MAX_MANIFEST_BYTES:
        raise EventLossHandoffValidationError("manifest exceeds bounded size or is empty")
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_digest != expected_manifest:
        raise EventLossHandoffValidationError("manifest differs from pinned SHA-256")

    manifest = _parse_canonical(manifest_bytes, "manifest")
    if type(manifest) is not dict or set(manifest) != (
        {"schema_version", "source", "output"} | _AUTHORITY_FIELDS
    ):
        raise EventLossHandoffValidationError("manifest has unexpected fields")
    if manifest["schema_version"] != producer.SCHEMA_VERSION:
        raise EventLossHandoffValidationError("handoff schema version drifted")
    for flag in _AUTHORITY_FIELDS:
        if manifest[flag] is not False:
            raise EventLossHandoffValidationError(f"unsupported authority flag {flag}")

    origin = manifest["source"]
    output = manifest["output"]
    if type(origin) is not dict or set(origin) != _SOURCE_FIELDS:
        raise EventLossHandoffValidationError("manifest source fields drifted")
    if type(output) is not dict or set(output) != _OUT_FIELDS:
        raise EventLossHandoffValidationError("manifest output fields drifted")
    if origin["receipt_schema_version"] != numerical.SCHEMA_VERSION:
        raise EventLossHandoffValidationError("source receipt schema drifted")
    if origin["receipt_sha256"] != expected_source:
        raise EventLossHandoffValidationError("source receipt differs from pinned SHA-256")
    if origin["source_dataset"] != numerical.SOURCE_DATASET:
        raise EventLossHandoffValidationError("source dataset drifted")
    if origin["experiment_label"] != numerical.EXPERIMENT_LABEL:
        raise EventLossHandoffValidationError("experiment label drifted")
    if origin["insurance_scope"] != "none":
        raise EventLossHandoffValidationError("insured loss scope is forbidden")
    if origin["openquake"] != {
        "commit_sha": numerical.OPENQUAKE_COMMIT_SHA,
        "version": numerical.OPENQUAKE_VERSION,
    }:
        raise EventLossHandoffValidationError("OpenQuake engine identity drifted")
    if origin["quantity"] != {
        "loss_type": numerical.LOSS_TYPE,
        "minimum_asset_loss_structural": numerical.MINIMUM_ASSET_LOSS_STRUCTURAL,
        "name": numerical.QUANTITY,
        "threshold_predicate": numerical._THRESHOLD_PREDICATE,
        "unit": numerical.UNIT,
    }:
        raise EventLossHandoffValidationError("loss quantity/threshold semantics drifted")
    selection = origin["selection"]
    if type(selection) is not dict or set(selection) != {
        "portfolio_agg_id", "structural_loss_id",
    }:
        raise EventLossHandoffValidationError("source selector drifted")
    _require_uint(selection["portfolio_agg_id"], (1 << 32) - 1, "portfolio_agg_id")
    _require_uint(selection["structural_loss_id"], 255, "structural_loss_id")
    _require_uint(origin["receipt_byte_count"], producer.MAX_INPUT_BYTES, "source byte count")
    if origin["receipt_byte_count"] == 0:
        raise EventLossHandoffValidationError("source byte count is zero")

    if (
        output["kind"] != "selected_ground_up_event_loss_jsonl"
        or output["row_id_scope"] != "source_receipt_sha256_plus_event_id"
        or output["loss_encoding"] != "IEEE754_binary32_big_endian_lowercase_hex"
        or output["variance_encoding"] != "IEEE754_binary32_big_endian_lowercase_hex"
    ):
        raise EventLossHandoffValidationError("loss-only transport semantics drifted")
    _require_uint(output["byte_count"], producer.MAX_OUTPUT_BYTES, "output byte count")
    _require_uint(output["row_count"], producer.MAX_ROWS, "output row count")
    if output["row_count"] == 0 or output["byte_count"] != len(jsonl):
        raise EventLossHandoffValidationError("declared row/byte count does not match")
    if _require_sha(output["sha256"], "output SHA") != hashlib.sha256(jsonl).hexdigest():
        raise EventLossHandoffValidationError("loss JSONL SHA-256 mismatch")

    if not jsonl.endswith(b"\n"):
        raise EventLossHandoffValidationError("JSONL missing canonical final newline")
    lines = jsonl.splitlines(keepends=True)
    if len(lines) != output["row_count"]:
        raise EventLossHandoffValidationError("actual row count differs from manifest")
    previous = -1
    for index, line in enumerate(lines):
        row = _parse_canonical(line, f"row {index}")
        if type(row) is not dict or set(row) != _ROW_FIELDS:
            raise EventLossHandoffValidationError("event row fields drifted")
        _require_uint(row["event_id"], (1 << 32) - 1, "event_id")
        _require_uint(row["rup_id"], (1 << 32) - 1, "rup_id")
        _require_uint(row["rlz_id"], (1 << 16) - 1, "rlz_id")
        if row["event_id"] <= previous:
            raise EventLossHandoffValidationError("event IDs must be strictly ascending")
        previous = row["event_id"]
        _require_float32(row["loss_f32_be_hex"], "loss")
        _require_float32(row["variance_f32_be_hex"], "variance")

    reconciled = False
    if source_receipt is not None:
        try:
            expected_rows, expected_manifest_bytes = producer.project_event_loss_handoff(
                source_receipt, expected_receipt_sha256=expected_source,
            )
        except producer.EventLossHandoffError as exc:
            raise EventLossHandoffValidationError("source receipt cannot be reconciled") from exc
        if expected_rows != jsonl or expected_manifest_bytes != manifest_bytes:
            raise EventLossHandoffValidationError("handoff differs from canonical source projection")
        reconciled = True

    return {
        "transport_validation_passed": True,
        "manifest_sha256": manifest_digest,
        "source_receipt_sha256": expected_source,
        "row_count": len(lines),
        "jsonl_sha256": output["sha256"],
        "canonical_source_rows_reconciled": reconciled,
        "origin_authenticated_by_this_validation": False,
        "original_provider_data_rights_confirmed": False,
        "annualized_loss_established": False,
        "insured_loss_established": False,
        "oasis_odr_conformant": False,
        "nextgen_import_verified": False,
        "model_input_approved": False,
    }


def _read_bounded(path: Path, maximum: int, label: str) -> bytes:
    try:
        size, _ = source._stable_stat(path)
        if not 0 < size <= maximum:
            raise EventLossHandoffValidationError(f"{label} exceeds bounded size or is empty")
        payload = source._read_stable_bytes(path)
    except source.OQ313RiskByEventProfileError as exc:
        raise EventLossHandoffValidationError(f"{label} not a stable regular file") from exc
    if len(payload) != size:
        raise EventLossHandoffValidationError(f"{label} changed during read")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-source-receipt-sha256", required=True)
    parser.add_argument("--source-receipt", type=Path, default=None,
                        help="optional full source for independent row-for-row reconciliation")
    args = parser.parse_args(argv)
    try:
        result = validate_event_loss_handoff(
            _read_bounded(args.jsonl, producer.MAX_OUTPUT_BYTES, "JSONL"),
            _read_bounded(args.manifest, _MAX_MANIFEST_BYTES, "manifest"),
            expected_manifest_sha256=args.expected_manifest_sha256,
            expected_source_receipt_sha256=args.expected_source_receipt_sha256,
            source_receipt=(
                _read_bounded(args.source_receipt, producer.MAX_INPUT_BYTES, "source receipt")
                if args.source_receipt is not None else None
            ),
        )
    except EventLossHandoffValidationError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(producer._canonical_json(result).decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
