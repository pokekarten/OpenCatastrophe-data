#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, metadata-only USGS ComCat product-vintage boundary.

No network calls, source downloads, rights admission, original event bytes,
real-time forecast, insurer loss or production event-store claim.

The product identity (source, type, code, updateTime) follows USGS ComCat.
An updateTime is NOT proof of contemporaneous public availability.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re

_SHA = re.compile(r"^[a-f0-9]{64}$")
_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ALLOWED_TYPES = frozenset({"origin", "shakemap", "losspager", "dyfi"})
_ALLOWED_STATUS = frozenset({"UPDATE", "DELETE"})


class ProductVintageBlocked(ValueError):
    """Invalid or inadequately qualified metadata must not become an as-of fact."""


@dataclass(frozen=True)
class ProductRevision:
    event_id: str
    source: str
    product_type: str
    code: str
    update_time_ms: int
    status: str
    original_product_sha256: str | None = None
    controlled_receipt_id: str | None = None
    first_received_at_utc: str | None = None

    @property
    def product_key(self) -> tuple[str, str, str]:
        return (self.source, self.product_type, self.code)

    @property
    def version_key(self) -> tuple[str, str, str, int]:
        return (*self.product_key, self.update_time_ms)


def _utc(value: str) -> datetime:
    if not isinstance(value, str) or not _ISO_UTC.fullmatch(value):
        raise ProductVintageBlocked("expected strict second-precision UTC time")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProductVintageBlocked("invalid calendar time") from exc


def _epoch_ms(value: int) -> datetime:
    if type(value) is not int or value <= 0:
        raise ProductVintageBlocked("updateTime must be positive integer milliseconds")
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ProductVintageBlocked("updateTime is outside supported range") from exc


def validate_revisions(rows: tuple[ProductRevision, ...], *, event_id: str) -> None:
    """Validate one event, preserving each product's version chain separately."""
    if not isinstance(rows, tuple) or not rows or len(rows) > 1000:
        raise ProductVintageBlocked("expected 1..1000 offline product metadata rows")
    if not isinstance(event_id, str) or not _ID.fullmatch(event_id):
        raise ProductVintageBlocked("unsafe event identity")
    seen = set()
    for row in rows:
        if not isinstance(row, ProductRevision):
            raise ProductVintageBlocked("invalid product revision object")
        if row.event_id != event_id:
            raise ProductVintageBlocked("cross-event product metadata not allowed")
        if not all(isinstance(v, str) and _ID.fullmatch(v) for v in (row.source, row.code)):
            raise ProductVintageBlocked("invalid source or product code")
        if row.product_type not in _ALLOWED_TYPES or row.status not in _ALLOWED_STATUS:
            raise ProductVintageBlocked("unsupported product type or status")
        stamp = _epoch_ms(row.update_time_ms)
        if row.version_key in seen:
            raise ProductVintageBlocked("duplicate source/type/code/updateTime version identity")
        seen.add(row.version_key)
        if row.original_product_sha256 is not None and (
            not isinstance(row.original_product_sha256, str)
            or not _SHA.fullmatch(row.original_product_sha256)
        ):
            raise ProductVintageBlocked("malformed original product SHA-256")
        has_id = row.controlled_receipt_id is not None
        has_time = row.first_received_at_utc is not None
        if has_id != has_time:
            raise ProductVintageBlocked("receipt identity and controlled receive-time must accompany one another")
        if has_id:
            if not isinstance(row.controlled_receipt_id, str) or not _ID.fullmatch(row.controlled_receipt_id):
                raise ProductVintageBlocked("unsafe receipt identity")
            received = _utc(row.first_received_at_utc)
            if received < stamp:
                raise ProductVintageBlocked("controlled receipt predates product updateTime")
        # A source URL, product updateTime or digest alone never implies a contemporaneous receipt.


def product_versions(rows: tuple[ProductRevision, ...], *, event_id: str,
                     product_key: tuple[str, str, str]) -> tuple[ProductRevision, ...]:
    validate_revisions(rows, event_id=event_id)
    if not isinstance(product_key, tuple) or len(product_key) != 3 or not all(
        isinstance(x, str) and x for x in product_key
    ):
        raise ProductVintageBlocked("explicit source/type/code key required")
    selected = tuple(sorted(
        (r for r in rows if r.product_key == product_key),
        key=lambda r: r.update_time_ms,
    ))
    if not selected:
        raise ProductVintageBlocked("no product version for declared key")
    return selected


def replay_product_asof(rows: tuple[ProductRevision, ...], *, event_id: str,
                        product_key: tuple[str, str, str], knowledge_cut_utc: str) -> dict:
    """As-of *metadata gate* using our first controlled receipt, not updateTime.

    The caller's receipt authority and hashes must be checked independently.
    Passing this gate does not admit model use or establish earliest public availability.
    """
    cut = _utc(knowledge_cut_utc)
    versions = product_versions(rows, event_id=event_id, product_key=product_key)
    observed = [r for r in versions
                if r.first_received_at_utc is not None
                and _utc(r.first_received_at_utc) <= cut
                and _epoch_ms(r.update_time_ms) <= cut]
    result = {
        "scope": "OFFLINE_METADATA_GATE_NOT_A_REAL_FORECAST",
        "event_id": event_id,
        "product_key": list(product_key),
        "knowledge_cut_utc": knowledge_cut_utc,
        "model_admitted": False,
        "forecast_skill_proven": False,
    }
    if not observed:
        return {**result, "state": "NO_CONTEMPORANEOUS_CONTROLLED_RECEIPT",
                "product_version": None, "original_sha256": None}
    latest = max(observed, key=lambda r: r.update_time_ms)
    if latest.original_product_sha256 is None:
        return {**result, "state": "ORIGINAL_BYTES_NOT_PINNED",
                "product_version": latest.update_time_ms, "original_sha256": None}
    if latest.status == "DELETE":
        return {**result, "state": "DELETED_AS_OF",
                "product_version": latest.update_time_ms,
                "original_sha256": latest.original_product_sha256}
    return {**result, "state": "CONTROLLED_RECEIPT_METADATA_ELIGIBLE",
            "product_version": latest.update_time_ms,
            "original_sha256": latest.original_product_sha256,
            "controlled_receipt_id": latest.controlled_receipt_id}


def retrospective_update_preview(rows: tuple[ProductRevision, ...], *, event_id: str,
                                 product_key: tuple[str, str, str],
                                 product_update_cut_utc: str) -> dict:
    """Hindcast candidate only: updateTime does NOT establish availability."""
    cut = _utc(product_update_cut_utc)
    versions = product_versions(rows, event_id=event_id, product_key=product_key)
    eligible = [r for r in versions if _epoch_ms(r.update_time_ms) <= cut]
    latest = max(eligible, key=lambda r: r.update_time_ms) if eligible else None
    return {
        "state": "RETROSPECTIVE_PRODUCT_TIME_ONLY_NOT_FORECAST",
        "event_id": event_id,
        "product_key": list(product_key),
        "product_update_cut_utc": product_update_cut_utc,
        "candidate_update_time_ms": latest.update_time_ms if latest else None,
        "status": latest.status if latest else None,
        "model_admitted": False,
        "historical_public_availability_proven": False,
    }


def synthetic_fixture() -> tuple[ProductRevision, ...]:
    # Entirely invented product metadata and hashes, NOT USGS event snapshots.
    def ms(when: str) -> int:
        return int(_utc(when).timestamp() * 1000)
    return (
        ProductRevision("SYNTHETIC-EQ", "synthetic-network", "shakemap", "syn-shake",
                        ms("2023-02-06T01:20:00Z"), "UPDATE",
                        "a" * 64, "LOCAL-R0", "2023-02-06T01:21:00Z"),
        ProductRevision("SYNTHETIC-EQ", "synthetic-network", "shakemap", "syn-shake",
                        ms("2023-02-06T02:00:00Z"), "UPDATE",
                        "b" * 64, "LOCAL-R1", "2023-02-06T02:02:00Z"),
        ProductRevision("SYNTHETIC-EQ", "synthetic-network", "losspager", "syn-pager",
                        ms("2023-02-06T01:23:00Z"), "UPDATE", None, None, None),
    )


def check() -> dict:
    rows = synthetic_fixture()
    key = ("synthetic-network", "shakemap", "syn-shake")
    cuts = ("2023-02-06T01:25:00Z", "2023-02-06T02:01:00Z", "2023-02-06T02:03:00Z")
    records = tuple(replay_product_asof(
        rows, event_id="SYNTHETIC-EQ", product_key=key, knowledge_cut_utc=cut
    ) for cut in cuts)
    assert [x["product_version"] for x in records] == [
        rows[0].update_time_ms, rows[0].update_time_ms, rows[1].update_time_ms]
    assert all(x["model_admitted"] is False for x in records)
    preview = retrospective_update_preview(
        rows, event_id="SYNTHETIC-EQ", product_key=key,
        product_update_cut_utc="2023-02-06T02:01:00Z")
    assert preview["candidate_update_time_ms"] == rows[1].update_time_ms
    assert records[1]["product_version"] != preview["candidate_update_time_ms"]
    return {"classification": "OFFLINE_SYNTHETIC_ONLY", "replays": records,
            "unverified_hindcast_preview": preview,
            "finding": "Provider updateTime alone leaks future-to-observer versions; first controlled receipt gates as-of metadata."}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True))
