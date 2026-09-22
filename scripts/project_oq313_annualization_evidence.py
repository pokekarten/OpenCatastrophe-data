# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Project bounded OQ3.13 annualization evidence from one completed datastore.

This module is offline-only. It reads the already completed OpenQuake datastore
and emits the minimum evidence needed to interpret native annualized portfolio
loss output without exporting the datastore, event rows, realization-weight
vectors, or asset-level losses.

The projector does not perform a reference comparison and does not authorize
publication or model use.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import Counter
from numbers import Integral, Real
from typing import Any, Mapping, Sequence

try:
    from scripts import select_oq313_risk_by_event_rows as selector
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import select_oq313_risk_by_event_rows as selector


SCHEMA_VERSION = "oc-oq313-annualization-evidence-v1"
LOSS_TYPE = "structural"
AVG_LOSSES_DATASET = "avg_losses-rlzs/structural"
WEIGHTS_DATASET = "weights"
EVENTS_DATASET = "events"
MAX_REALIZATIONS = 100_000
MAX_ASSETS = 10_000_000


class OQ313AnnualizationEvidenceError(ValueError):
    """The completed datastore does not satisfy the bounded evidence contract."""


def _canonical_payload(document: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
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


def _strict_bool(value: object, *, label: str) -> bool:
    if type(value) is not bool:
        raise OQ313AnnualizationEvidenceError(f"{label} must be bool")
    return value


def _nonnegative_int(value: object, *, label: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise OQ313AnnualizationEvidenceError(f"{label} must be integer")
    result = int(value)
    if result < 0 or result > maximum:
        raise OQ313AnnualizationEvidenceError(f"{label} is outside bounded policy")
    return result


def _positive_real(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise OQ313AnnualizationEvidenceError(f"{label} must be real")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise OQ313AnnualizationEvidenceError(f"{label} must be finite and positive")
    return result


def _optional_nonnegative_real(value: object, *, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise OQ313AnnualizationEvidenceError(f"{label} must be real or null")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise OQ313AnnualizationEvidenceError(
            f"{label} must be finite and non-negative"
        )
    return result


def _f64_hex(value: float, *, label: str) -> str:
    if not math.isfinite(value):
        raise OQ313AnnualizationEvidenceError(f"{label} must be finite")
    return struct.pack("!d", value).hex()


class _NeumaierSum:
    """Deterministic constant-memory compensated binary64 summation."""

    def __init__(self) -> None:
        self.total = 0.0
        self.correction = 0.0

    def add(self, value: float) -> None:
        tentative = self.total + value
        if abs(self.total) >= abs(value):
            self.correction += (self.total - tentative) + value
        else:
            self.correction += (value - tentative) + self.total
        self.total = tentative

    def result(self) -> float:
        value = self.total + self.correction
        if not math.isfinite(value):
            raise OQ313AnnualizationEvidenceError(
                "compensated sum produced non-finite value"
            )
        return value


def _runtime_evidence(oq: object) -> dict[str, Any]:
    investigation_time = _positive_real(
        getattr(oq, "investigation_time", None),
        label="oq.investigation_time",
    )
    risk_investigation_time = _optional_nonnegative_real(
        getattr(oq, "risk_investigation_time", None),
        label="oq.risk_investigation_time",
    )
    ses_per_logic_tree_path = _nonnegative_int(
        getattr(oq, "ses_per_logic_tree_path", None),
        label="oq.ses_per_logic_tree_path",
        maximum=(1 << 31) - 1,
    )
    if ses_per_logic_tree_path == 0:
        raise OQ313AnnualizationEvidenceError(
            "oq.ses_per_logic_tree_path must be positive"
        )
    collect_rlzs = _strict_bool(
        getattr(oq, "collect_rlzs", None),
        label="oq.collect_rlzs",
    )
    number_of_logic_tree_samples = _nonnegative_int(
        getattr(oq, "number_of_logic_tree_samples", None),
        label="oq.number_of_logic_tree_samples",
        maximum=(1 << 31) - 1,
    )

    # Mirror the frozen OQ3.13 event-based annualization definition exactly:
    # (risk_investigation_time or investigation_time) /
    # (investigation_time * ses_per_logic_tree_path).
    numerator = risk_investigation_time or investigation_time
    time_ratio = numerator / (
        investigation_time * float(ses_per_logic_tree_path)
    )
    if not math.isfinite(time_ratio) or time_ratio <= 0.0:
        raise OQ313AnnualizationEvidenceError("derived time_ratio is invalid")

    return {
        "investigation_time_f64_be_hex": _f64_hex(
            investigation_time,
            label="investigation_time",
        ),
        "risk_investigation_time_present": risk_investigation_time is not None,
        "risk_investigation_time_f64_be_hex": (
            None
            if risk_investigation_time is None
            else _f64_hex(
                risk_investigation_time,
                label="risk_investigation_time",
            )
        ),
        "ses_per_logic_tree_path": ses_per_logic_tree_path,
        "collect_rlzs": collect_rlzs,
        "number_of_logic_tree_samples": number_of_logic_tree_samples,
        "sampling_mode": (
            "sampled" if number_of_logic_tree_samples > 0 else "enumerated"
        ),
        "time_ratio_f64_be_hex": _f64_hex(time_ratio, label="time_ratio"),
    }


def _events_evidence(dstore: object) -> tuple[dict[str, Any], int]:
    try:
        raw = dstore[EVENTS_DATASET][:]
    except (KeyError, TypeError, AttributeError) as exc:
        raise OQ313AnnualizationEvidenceError("cannot read events dataset") from exc

    try:
        selector._assert_events_native_dtype(raw)
    except selector.OQ313DatastoreSelectionError as exc:
        raise OQ313AnnualizationEvidenceError("events dtype contract drifted") from exc

    counts: Counter[int] = Counter()
    event_count = 0
    for index, record in enumerate(raw):
        try:
            rlz_id = selector._uint(
                record["rlz_id"],
                label=f"events[{index}].rlz_id",
                maximum=(1 << 16) - 1,
            )
        except (KeyError, TypeError, IndexError, selector.OQ313DatastoreSelectionError) as exc:
            raise OQ313AnnualizationEvidenceError("events row contract drifted") from exc
        counts[rlz_id] += 1
        event_count += 1

    if event_count == 0:
        raise OQ313AnnualizationEvidenceError("events dataset must not be empty")
    if len(counts) > MAX_REALIZATIONS:
        raise OQ313AnnualizationEvidenceError("event realization count exceeds bound")
    ids = sorted(counts)
    if ids != list(range(len(ids))):
        raise OQ313AnnualizationEvidenceError(
            "event realization ids must be dense from zero"
        )

    return {
        "event_count": event_count,
        "realization_count": len(ids),
        "event_count_by_realization": [
            {"rlz_id": rlz_id, "event_count": counts[rlz_id]}
            for rlz_id in ids
        ],
    }, len(ids)


def _read_numeric_array(dstore: object, path: str) -> object:
    try:
        return dstore[path][:]
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise OQ313AnnualizationEvidenceError(
            f"cannot read datastore dataset {path}"
        ) from exc


def _weights_evidence(
    dstore: object,
    *,
    event_realization_count: int,
) -> tuple[dict[str, Any], list[float]]:
    raw = _read_numeric_array(dstore, WEIGHTS_DATASET)
    shape = getattr(raw, "shape", None)
    dtype = str(getattr(raw, "dtype", ""))
    if (
        not isinstance(shape, Sequence)
        or isinstance(shape, (str, bytes, bytearray))
        or len(shape) != 1
    ):
        raise OQ313AnnualizationEvidenceError("weights must be one-dimensional")
    count = _nonnegative_int(
        shape[0],
        label="weights shape",
        maximum=MAX_REALIZATIONS,
    )
    if count == 0:
        raise OQ313AnnualizationEvidenceError("weights must not be empty")
    if dtype not in {"float32", "float64"}:
        raise OQ313AnnualizationEvidenceError(
            "weights dtype must be float32 or float64"
        )

    values: list[float] = []
    digest = hashlib.sha256()
    for index, value in enumerate(raw):
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise OQ313AnnualizationEvidenceError(
                f"weights[{index}] is not numeric"
            ) from exc
        if not math.isfinite(number) or number < 0.0:
            raise OQ313AnnualizationEvidenceError(
                f"weights[{index}] must be finite and non-negative"
            )
        values.append(number)
        digest.update(struct.pack("!d", number))

    if len(values) != count:
        raise OQ313AnnualizationEvidenceError("weights length drifted")
    weight_sum = math.fsum(values)
    if not math.isclose(weight_sum, 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise OQ313AnnualizationEvidenceError("realization weights do not sum to one")
    if event_realization_count > count:
        raise OQ313AnnualizationEvidenceError(
            "events reference more realizations than the weights dataset"
        )

    return {
        "dtype": dtype,
        "count": count,
        "sum_f64_be_hex": _f64_hex(weight_sum, label="weight sum"),
        "values_f64_sha256": digest.hexdigest(),
        "values_returned": False,
    }, values


def _avg_losses_evidence(
    dstore: object,
    *,
    collect_rlzs: bool,
    weights: list[float],
) -> dict[str, Any]:
    raw = _read_numeric_array(dstore, AVG_LOSSES_DATASET)
    shape = getattr(raw, "shape", None)
    dtype = str(getattr(raw, "dtype", ""))
    if (
        not isinstance(shape, Sequence)
        or isinstance(shape, (str, bytes, bytearray))
        or len(shape) != 2
    ):
        raise OQ313AnnualizationEvidenceError(
            "avg_losses-rlzs structural dataset must be two-dimensional"
        )
    asset_count = _nonnegative_int(
        shape[0],
        label="avg_losses asset count",
        maximum=MAX_ASSETS,
    )
    output_realization_count = _nonnegative_int(
        shape[1],
        label="avg_losses realization count",
        maximum=MAX_REALIZATIONS,
    )
    if asset_count == 0 or output_realization_count == 0:
        raise OQ313AnnualizationEvidenceError(
            "avg_losses-rlzs structural dataset must be non-empty"
        )
    if dtype != "float32":
        raise OQ313AnnualizationEvidenceError(
            "avg_losses-rlzs structural dtype must be float32"
        )

    expected_outputs = 1 if collect_rlzs else len(weights)
    if output_realization_count != expected_outputs:
        raise OQ313AnnualizationEvidenceError(
            "avg_losses output realization count disagrees with runtime mode"
        )

    accumulators = [_NeumaierSum() for _ in range(output_realization_count)]
    row_count = 0
    try:
        for row in raw:
            if len(row) != output_realization_count:
                raise OQ313AnnualizationEvidenceError(
                    "avg_losses row width drifted"
                )
            for index, value in enumerate(row):
                number = float(value)
                if not math.isfinite(number) or number < 0.0:
                    raise OQ313AnnualizationEvidenceError(
                        "avg_losses values must be finite and non-negative"
                    )
                accumulators[index].add(number)
            row_count += 1
    except OQ313AnnualizationEvidenceError:
        raise
    except (TypeError, ValueError, OverflowError) as exc:
        raise OQ313AnnualizationEvidenceError(
            "cannot iterate avg_losses-rlzs structural dataset"
        ) from exc

    if row_count != asset_count:
        raise OQ313AnnualizationEvidenceError("avg_losses asset count drifted")
    totals = [accumulator.result() for accumulator in accumulators]

    totals_digest = hashlib.sha256()
    for index, total in enumerate(totals):
        if not math.isfinite(total) or total < 0.0:
            raise OQ313AnnualizationEvidenceError(
                f"portfolio avg loss total {index} is invalid"
            )
        totals_digest.update(struct.pack("!d", total))

    if collect_rlzs:
        engine_mean = totals[0]
        mean_method = "collected_realization_native_portfolio_total"
    else:
        if len(totals) != len(weights):
            raise OQ313AnnualizationEvidenceError(
                "avg loss totals and weights cardinality disagree"
            )
        engine_mean = math.fsum(
            total * weight for total, weight in zip(totals, weights)
        )
        mean_method = "weighted_native_portfolio_totals"

    return {
        "dataset": AVG_LOSSES_DATASET,
        "dtype": dtype,
        "shape": [asset_count, output_realization_count],
        "portfolio_total_by_output_realization_f64_sha256": (
            totals_digest.hexdigest()
        ),
        "portfolio_totals_returned": False,
        "engine_mean_method": mean_method,
        "engine_mean_f64_be_hex": _f64_hex(engine_mean, label="engine mean"),
    }


def project_oq313_annualization_evidence(
    dstore: object,
    oq: object,
) -> tuple[bytes, dict[str, Any]]:
    """Return canonical bounded annualization evidence and its byte identity."""

    try:
        structural_loss_id = selector._resolve_structural_loss_id(oq)
        selector._assert_no_policy_input(oq)
    except selector.OQ313DatastoreSelectionError as exc:
        raise OQ313AnnualizationEvidenceError(
            "loss-type or insurance-scope contract drifted"
        ) from exc

    runtime = _runtime_evidence(oq)
    events, event_realization_count = _events_evidence(dstore)
    weights, weight_values = _weights_evidence(
        dstore,
        event_realization_count=event_realization_count,
    )
    avg_losses = _avg_losses_evidence(
        dstore,
        collect_rlzs=runtime["collect_rlzs"],
        weights=weight_values,
    )

    document = {
        "schema_version": SCHEMA_VERSION,
        "source_datasets": {
            "events": EVENTS_DATASET,
            "weights": WEIGHTS_DATASET,
            "avg_losses": AVG_LOSSES_DATASET,
        },
        "loss_type": LOSS_TYPE,
        "structural_loss_id": structural_loss_id,
        "runtime": runtime,
        "events": events,
        "weights": weights,
        "avg_losses": avg_losses,
        "policy_present": False,
        "insured_loss_present": False,
        "datastore_rows_returned": False,
        "external_provider_bytes_persisted": False,
        "annualization_evidence_projected": True,
        "reference_loss_comparison_performed": False,
        "reference_loss_agreement_verified": False,
        "scientific_validity_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    return _canonical_payload(document)
