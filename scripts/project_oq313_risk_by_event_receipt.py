# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Project selected OpenQuake 3.13 event-loss rows into a deterministic receipt."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_VERSION = "oc-oq313-risk-by-event-receipt-v1"
OPENQUAKE_VERSION = "3.13.0"
OPENQUAKE_COMMIT_SHA = "16dd69ecea0c6dcaf49c22ca12edc9da3f024889"
SOURCE_DATASET = "risk_by_event"
EXPERIMENT_LABEL = "reconstructed_experiment"
LOSS_TYPE = "structural"
QUANTITY = "thresholded_ground_up_structural_replacement_cost_loss"
UNIT = "EUR"
MINIMUM_ASSET_LOSS_STRUCTURAL = 2000
_THRESHOLD_PREDICATE = "asset_event_loss > minimum_asset_loss_structural"
_ROW_FIELDS = frozenset({"event_id", "rup_id", "loss_f32_be_hex", "variance_f32_be_hex"})
_F32_HEX = re.compile(r"[0-9a-f]{8}")


class OQ313RiskByEventReceiptError(ValueError):
    """The selected event-loss rows or their declared scope are invalid."""


def _require_uint(value: object, *, label: str, maximum: int) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise OQ313RiskByEventReceiptError(
            f"{label} must be an integer in [0, {maximum}]"
        )
    return value


def _require_positive_int(value: object, *, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise OQ313RiskByEventReceiptError(f"{label} must be a positive integer")
    return value


def _require_f32_hex(value: object, *, label: str) -> str:
    if type(value) is not str or _F32_HEX.fullmatch(value) is None:
        raise OQ313RiskByEventReceiptError(
            f"{label} must be canonical lowercase 8-digit binary32 hex"
        )
    decoded = struct.unpack("!f", bytes.fromhex(value))[0]
    if not math.isfinite(decoded):
        raise OQ313RiskByEventReceiptError(f"{label} must encode a finite binary32")
    if decoded < 0.0:
        raise OQ313RiskByEventReceiptError(f"{label} must not encode a negative value")
    return value


def _require_exact_scope(
    *,
    loss_type: object,
    unit: object,
    minimum_asset_loss_structural: object,
    experiment_label: object,
    policy_present: object,
    insured_loss_present: object,
) -> None:
    if loss_type != LOSS_TYPE:
        raise OQ313RiskByEventReceiptError("loss type must be structural")
    if unit != UNIT:
        raise OQ313RiskByEventReceiptError("unit must be EUR")
    if (
        type(minimum_asset_loss_structural) is not int
        or minimum_asset_loss_structural != MINIMUM_ASSET_LOSS_STRUCTURAL
    ):
        raise OQ313RiskByEventReceiptError(
            "minimum_asset_loss_structural must be exactly 2000"
        )
    if experiment_label != EXPERIMENT_LABEL:
        raise OQ313RiskByEventReceiptError(
            "experiment label must be reconstructed_experiment"
        )
    if type(policy_present) is not bool or type(insured_loss_present) is not bool:
        raise OQ313RiskByEventReceiptError("insurance flags must be booleans")
    if policy_present or insured_loss_present:
        raise OQ313RiskByEventReceiptError(
            "policy/insured-loss surfaces are forbidden in this receipt"
        )


def project_oq313_risk_by_event_receipt(
    rows: Sequence[Mapping[str, object]],
    *,
    portfolio_agg_id: int,
    structural_loss_id: int,
    concurrent_tasks: int,
    loss_type: str = LOSS_TYPE,
    unit: str = UNIT,
    minimum_asset_loss_structural: int = MINIMUM_ASSET_LOSS_STRUCTURAL,
    experiment_label: str = EXPERIMENT_LABEL,
    policy_present: bool = False,
    insured_loss_present: bool = False,
) -> tuple[bytes, dict[str, Any]]:
    """Return canonical JSON bytes and their byte/SHA-256 identity."""

    _require_exact_scope(
        loss_type=loss_type,
        unit=unit,
        minimum_asset_loss_structural=minimum_asset_loss_structural,
        experiment_label=experiment_label,
        policy_present=policy_present,
        insured_loss_present=insured_loss_present,
    )
    agg_id = _require_uint(
        portfolio_agg_id, label="portfolio_agg_id", maximum=(1 << 32) - 1
    )
    loss_id = _require_uint(
        structural_loss_id, label="structural_loss_id", maximum=(1 << 8) - 1
    )
    tasks = _require_positive_int(concurrent_tasks, label="concurrent_tasks")

    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise OQ313RiskByEventReceiptError("rows must be a sequence of mappings")
    if not rows:
        raise OQ313RiskByEventReceiptError("rows must not be empty")

    normalized: list[dict[str, object]] = []
    seen_events: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise OQ313RiskByEventReceiptError(f"row {index} must be a mapping")
        fields = set(row)
        if fields != _ROW_FIELDS:
            raise OQ313RiskByEventReceiptError(
                f"row {index} fields must be exactly {sorted(_ROW_FIELDS)}"
            )
        event_id = _require_uint(
            row["event_id"], label=f"row {index} event_id", maximum=(1 << 32) - 1
        )
        if event_id in seen_events:
            raise OQ313RiskByEventReceiptError("event_id values must be unique")
        seen_events.add(event_id)
        rup_id = _require_uint(
            row["rup_id"], label=f"row {index} rup_id", maximum=(1 << 32) - 1
        )
        loss_hex = _require_f32_hex(
            row["loss_f32_be_hex"], label=f"row {index} loss_f32_be_hex"
        )
        variance_hex = _require_f32_hex(
            row["variance_f32_be_hex"], label=f"row {index} variance_f32_be_hex"
        )
        normalized.append(
            {
                "event_id": event_id,
                "rup_id": rup_id,
                "loss_f32_be_hex": loss_hex,
                "variance_f32_be_hex": variance_hex,
            }
        )

    normalized.sort(key=lambda row: int(row["event_id"]))
    document = {
        "experiment_label": EXPERIMENT_LABEL,
        "insurance_scope": "none",
        "openquake": {
            "commit_sha": OPENQUAKE_COMMIT_SHA,
            "version": OPENQUAKE_VERSION,
        },
        "quantity": {
            "loss_type": LOSS_TYPE,
            "minimum_asset_loss_structural": MINIMUM_ASSET_LOSS_STRUCTURAL,
            "name": QUANTITY,
            "threshold_predicate": _THRESHOLD_PREDICATE,
            "unit": UNIT,
        },
        "rows": normalized,
        "runtime": {"concurrent_tasks": tasks},
        "schema_version": SCHEMA_VERSION,
        "selection": {
            "portfolio_agg_id": agg_id,
            "structural_loss_id": loss_id,
        },
        "source_dataset": SOURCE_DATASET,
    }
    payload = (
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    return payload, {
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
