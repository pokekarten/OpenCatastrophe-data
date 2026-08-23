# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Select source-native OQ3.13 portfolio structural rows for the EQ1 receipt."""

from __future__ import annotations

import struct
from collections.abc import Mapping, Sequence
from numbers import Integral
from typing import Any

try:
    from scripts.project_oq313_risk_by_event_receipt import (
        OQ313RiskByEventReceiptError,
        project_oq313_risk_by_event_receipt,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from project_oq313_risk_by_event_receipt import (
        OQ313RiskByEventReceiptError,
        project_oq313_risk_by_event_receipt,
    )

SOURCE_DATASET = "risk_by_event"
EVENTS_DATASET = "events"
LOSS_TYPE = "structural"
_EXPECTED_COLUMNS = ("event_id", "agg_id", "loss_id", "variance", "loss")
_EXPECTED_DTYPES = {
    "event_id": "uint32",
    "agg_id": "uint32",
    "loss_id": "uint8",
    "variance": "float32",
    "loss": "float32",
}
_EXPECTED_EVENT_FIELDS = ("id", "rup_id", "rlz_id")
_EXPECTED_EVENT_DTYPES = {
    "id": "uint32",
    "rup_id": "uint32",
    "rlz_id": "uint16",
}


class OQ313DatastoreSelectionError(ValueError):
    """The completed datastore does not satisfy the fixed EQ1 selection contract."""


def _uint(value: object, *, label: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise OQ313DatastoreSelectionError(f"{label} must be an integer")
    result = int(value)
    if result < 0 or result > maximum:
        raise OQ313DatastoreSelectionError(f"{label} is outside its source dtype")
    return result


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise OQ313DatastoreSelectionError(f"{label} must be a mapping")
    return value


def _resolve_structural_loss_id(oq: object) -> int:
    loss_types = getattr(oq, "loss_types", None)
    if (
        not isinstance(loss_types, Sequence)
        or isinstance(loss_types, (str, bytes, bytearray))
        or not loss_types
    ):
        raise OQ313DatastoreSelectionError("oq.loss_types must be a non-empty sequence")
    normalized = list(loss_types)
    if any(type(loss_type) is not str for loss_type in normalized):
        raise OQ313DatastoreSelectionError("oq.loss_types entries must be strings")
    if len(set(normalized)) != len(normalized):
        raise OQ313DatastoreSelectionError("oq.loss_types must be unique")
    if normalized.count(LOSS_TYPE) != 1:
        raise OQ313DatastoreSelectionError("structural loss type must exist exactly once")

    lti = _mapping(getattr(oq, "lti", None), label="oq.lti")
    if set(lti) != set(normalized):
        raise OQ313DatastoreSelectionError("oq.lti keys must match oq.loss_types")
    for index, loss_type in enumerate(normalized):
        observed = _uint(lti[loss_type], label=f"oq.lti[{loss_type}]", maximum=255)
        if observed != index:
            raise OQ313DatastoreSelectionError("oq.lti disagrees with loss_types order")
    return normalized.index(LOSS_TYPE)


def _assert_no_policy_input(oq: object) -> None:
    inputs = _mapping(getattr(oq, "inputs", None), label="oq.inputs")
    for key, value in inputs.items():
        if type(key) is not str:
            raise OQ313DatastoreSelectionError("oq.inputs keys must be strings")
        lowered = key.casefold()
        if "policy" not in lowered and "insurance" not in lowered:
            continue
        absent = value is None
        if isinstance(value, str):
            absent = value == ""
        elif isinstance(value, (tuple, list)):
            absent = not value
        if not absent:
            raise OQ313DatastoreSelectionError("policy/insurance input is forbidden")


def _f32_hex(value: object, *, label: str) -> str:
    try:
        return struct.pack("!f", value).hex()
    except (OverflowError, struct.error, TypeError, ValueError) as exc:
        raise OQ313DatastoreSelectionError(f"{label} is not binary32-compatible") from exc


def _frame_records(frame: object) -> list[object]:
    columns = getattr(frame, "columns", None)
    if columns is None or tuple(columns) != _EXPECTED_COLUMNS:
        raise OQ313DatastoreSelectionError(
            f"risk_by_event columns must be exactly {_EXPECTED_COLUMNS}"
        )
    for name, expected_dtype in _EXPECTED_DTYPES.items():
        try:
            dtype = str(frame[name].dtype)
        except (KeyError, TypeError, AttributeError) as exc:
            raise OQ313DatastoreSelectionError(
                f"cannot inspect risk_by_event dtype for {name}"
            ) from exc
        if dtype != expected_dtype:
            raise OQ313DatastoreSelectionError(
                f"risk_by_event {name} dtype must be {expected_dtype}"
            )
    try:
        records = list(frame.to_records(index=False))
    except (AttributeError, TypeError, ValueError) as exc:
        raise OQ313DatastoreSelectionError("cannot materialize risk_by_event rows") from exc
    return records


def _assert_events_native_dtype(raw: object) -> None:
    dtype = getattr(raw, "dtype", None)
    names = getattr(dtype, "names", None)
    if names is None or tuple(names) != _EXPECTED_EVENT_FIELDS:
        raise OQ313DatastoreSelectionError(
            f"events fields must be exactly {_EXPECTED_EVENT_FIELDS}"
        )
    fields = getattr(dtype, "fields", None)
    if not isinstance(fields, Mapping):
        raise OQ313DatastoreSelectionError("cannot inspect events structured dtype")
    for name, expected_dtype in _EXPECTED_EVENT_DTYPES.items():
        try:
            field_spec = fields[name]
            field_dtype = field_spec[0]
        except (KeyError, TypeError, IndexError) as exc:
            raise OQ313DatastoreSelectionError(
                f"cannot inspect events dtype for {name}"
            ) from exc
        if str(field_dtype) != expected_dtype:
            raise OQ313DatastoreSelectionError(
                f"events {name} dtype must be {expected_dtype}"
            )


def _event_to_rupture(dstore: object) -> dict[int, tuple[int, int]]:
    try:
        raw = dstore[EVENTS_DATASET][:]
    except (KeyError, TypeError, AttributeError) as exc:
        raise OQ313DatastoreSelectionError("cannot read events dataset") from exc
    _assert_events_native_dtype(raw)
    links: dict[int, tuple[int, int]] = {}
    for index, record in enumerate(raw):
        try:
            event_id = _uint(
                record["id"],
                label=f"events[{index}].id",
                maximum=(1 << 32) - 1,
            )
            rup_id = _uint(
                record["rup_id"],
                label=f"events[{index}].rup_id",
                maximum=(1 << 32) - 1,
            )
            rlz_id = _uint(
                record["rlz_id"],
                label=f"events[{index}].rlz_id",
                maximum=(1 << 16) - 1,
            )
        except (KeyError, TypeError, IndexError) as exc:
            raise OQ313DatastoreSelectionError("events row shape drifted") from exc
        if event_id in links:
            raise OQ313DatastoreSelectionError("events ids must be unique")
        links[event_id] = (rup_id, rlz_id)
    if not links:
        raise OQ313DatastoreSelectionError("events dataset must not be empty")
    return links


def select_oq313_risk_by_event_receipt(
    dstore: object,
    oq: object,
) -> tuple[bytes, dict[str, Any]]:
    """Select exact portfolio structural rows and invoke the reviewed projector."""

    try:
        risk_group = dstore[SOURCE_DATASET]
        attrs = risk_group.attrs
        frame = dstore.read_df(SOURCE_DATASET)
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise OQ313DatastoreSelectionError("cannot read risk_by_event dataset") from exc
    try:
        portfolio_agg_id = _uint(
            attrs["K"],
            label="risk_by_event.attrs[K]",
            maximum=(1 << 32) - 1,
        )
        loss_type_count_raw = attrs["L"]
    except (KeyError, TypeError, AttributeError) as exc:
        raise OQ313DatastoreSelectionError(
            "risk_by_event attrs must contain K and L"
        ) from exc

    structural_loss_id = _resolve_structural_loss_id(oq)
    loss_type_count = _uint(
        loss_type_count_raw,
        label="risk_by_event.attrs[L]",
        maximum=256,
    )
    if loss_type_count != len(oq.loss_types):
        raise OQ313DatastoreSelectionError("risk_by_event L disagrees with oq.loss_types")
    _assert_no_policy_input(oq)

    concurrent_tasks = _uint(
        getattr(oq, "concurrent_tasks", None),
        label="oq.concurrent_tasks",
        maximum=(1 << 31) - 1,
    )
    records = _frame_records(frame)
    event_links = _event_to_rupture(dstore)

    selected: list[dict[str, object]] = []
    seen_events: set[int] = set()
    for index, record in enumerate(records):
        try:
            event_id = _uint(
                record["event_id"],
                label=f"risk_by_event[{index}].event_id",
                maximum=(1 << 32) - 1,
            )
            agg_id = _uint(
                record["agg_id"],
                label=f"risk_by_event[{index}].agg_id",
                maximum=(1 << 32) - 1,
            )
            loss_id = _uint(
                record["loss_id"],
                label=f"risk_by_event[{index}].loss_id",
                maximum=255,
            )
        except (KeyError, TypeError, IndexError) as exc:
            raise OQ313DatastoreSelectionError("risk_by_event row shape drifted") from exc
        if agg_id != portfolio_agg_id or loss_id != structural_loss_id:
            continue
        if event_id in seen_events:
            raise OQ313DatastoreSelectionError("selected event ids must be unique")
        seen_events.add(event_id)
        if event_id not in event_links:
            raise OQ313DatastoreSelectionError("selected event has no events linkage")
        rup_id, rlz_id = event_links[event_id]
        try:
            loss = record["loss"]
            variance = record["variance"]
        except (KeyError, TypeError, IndexError) as exc:
            raise OQ313DatastoreSelectionError("risk_by_event loss fields drifted") from exc
        selected.append(
            {
                "event_id": event_id,
                "rup_id": rup_id,
                "rlz_id": rlz_id,
                "loss_f32_be_hex": _f32_hex(
                    loss,
                    label=f"risk_by_event[{index}].loss",
                ),
                "variance_f32_be_hex": _f32_hex(
                    variance,
                    label=f"risk_by_event[{index}].variance",
                ),
            }
        )
    if not selected:
        raise OQ313DatastoreSelectionError("no portfolio structural rows selected")

    try:
        return project_oq313_risk_by_event_receipt(
            selected,
            portfolio_agg_id=portfolio_agg_id,
            structural_loss_id=structural_loss_id,
            concurrent_tasks=concurrent_tasks,
            policy_present=False,
            insured_loss_present=False,
        )
    except OQ313RiskByEventReceiptError as exc:
        raise OQ313DatastoreSelectionError("selected rows failed receipt projection") from exc
