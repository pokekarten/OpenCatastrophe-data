# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire the exact CEMS companion masks ephemerally and inventory all values."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_cems_europe_mask_profiles as _profiles
    from scripts import acquire_cems_europe_mask_receipts as _masks
    from scripts import profile_cems_europe_mask_geotiffs as _metadata
    from scripts import profile_cems_europe_mask_values as _values
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_mask_profiles as _profiles
    import acquire_cems_europe_mask_receipts as _masks
    import profile_cems_europe_mask_geotiffs as _metadata
    import profile_cems_europe_mask_values as _values

SCHEMA_VERSION = "oc-cems-mask-value-inventories-v1"
INVENTORY_RECEIPT_SCHEMA_VERSION = "oc-cems-mask-value-inventory-receipt-v1"
SOURCE_ISSUE = 809
PROFILE_ISSUE = 823


class CemsMaskValueInventoryAcquisitionError(RuntimeError):
    """Raised when trusted acquisition cannot produce exact bounded inventories."""


def _inventory_one(
    kind: str,
    filename: str,
    directory: Path,
    *,
    opener: Callable[[Any, float], Any],
    clock: Callable[[], str],
    monotonic: Callable[[], float],
    profiler: Callable[..., dict[str, Any]],
) -> tuple[dict[str, Any], Path]:
    path = directory / filename
    try:
        with path.open("xb") as sink:
            def tee_opener(request: Any, timeout: float) -> _profiles._TeeResponse:
                return _profiles._TeeResponse(opener(request, timeout), sink)

            receipt = _masks._acquire_one(
                kind,
                filename,
                opener=tee_opener,
                clock=clock,
                monotonic=monotonic,
            )
            sink.flush()

        accepted = _metadata.MASK_RECEIPTS[kind]
        if receipt["byte_count"] != accepted["byte_count"]:
            raise CemsMaskValueInventoryAcquisitionError(
                "CEMS mask value-inventory byte count differs from accepted #809 receipt"
            )
        if receipt["sha256"] != accepted["sha256"]:
            raise CemsMaskValueInventoryAcquisitionError(
                "CEMS mask value-inventory SHA-256 differs from accepted #809 receipt"
            )

        value_inventory = profiler(path, mask_kind=kind)
        if value_inventory.get("external_bytes_persisted") is not False:
            raise CemsMaskValueInventoryAcquisitionError(
                "CEMS mask value profiler reported persisted provider bytes"
            )
        if value_inventory.get("mask_values_inspected") is not True:
            raise CemsMaskValueInventoryAcquisitionError(
                "CEMS mask value profiler did not inspect the complete mask values"
            )
        if value_inventory.get("mask_value_semantics_verified") is not False:
            raise CemsMaskValueInventoryAcquisitionError(
                "CEMS mask value profiler exceeded the Stage B authority ceiling"
            )

        return (
            {
                "schema_version": INVENTORY_RECEIPT_SCHEMA_VERSION,
                "dataset_id": _masks.DATASET_ID,
                "source_issue": SOURCE_ISSUE,
                "profile_issue": PROFILE_ISSUE,
                "release": _masks.RELEASE,
                "mask_kind": kind,
                "filename": filename,
                "requested_url": receipt["requested_url"],
                "final_url": receipt["final_url"],
                "retrieved_at": receipt["retrieved_at"],
                "http_status": receipt["http_status"],
                "media_type": receipt["media_type"],
                "content_length_header": receipt["content_length_header"],
                "receipt_byte_count": receipt["byte_count"],
                "receipt_sha256": receipt["sha256"],
                "value_inventory": value_inventory,
                "external_bytes_persisted": False,
                "mask_values_inspected": True,
                "mask_value_semantics_verified": False,
                "per_cell_scientific_correctness_verified": False,
                "benchmark_use_authorized": False,
                "publication_authorized": False,
                "model_use_authorized": False,
            },
            path,
        )
    except (
        CemsMaskValueInventoryAcquisitionError,
        _masks.CemsMaskReceiptError,
        _values.CemsMaskValueProfileError,
    ):
        raise
    except OSError as exc:
        raise CemsMaskValueInventoryAcquisitionError(
            "CEMS mask value-inventory ephemeral storage failed"
        ) from exc
    except Exception as exc:
        raise CemsMaskValueInventoryAcquisitionError(
            "CEMS mask value-inventory acquisition failed"
        ) from exc


def acquire_cems_mask_value_inventories(
    *,
    opener: Callable[[Any, float], Any] = _masks._open_frozen_source,
    clock: Callable[[], str] = _masks._base.utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    profiler: Callable[..., dict[str, Any]] = _values.profile_cems_mask_value_inventory,
) -> dict[str, Any]:
    """Return bounded full-raster inventories while retaining no provider payload bytes."""
    paths: list[Path] = []
    receipts: list[dict[str, Any]] = []
    try:
        with tempfile.TemporaryDirectory(
            prefix="oc-cems-mask-value-inventories-"
        ) as raw_directory:
            directory = Path(raw_directory)
            for kind, filename in _masks.ASSETS:
                inventory_receipt, path = _inventory_one(
                    kind,
                    filename,
                    directory,
                    opener=opener,
                    clock=clock,
                    monotonic=monotonic,
                    profiler=profiler,
                )
                paths.append(path)
                receipts.append(inventory_receipt)

        if any(path.exists() for path in paths):  # pragma: no cover - defensive postcondition
            raise CemsMaskValueInventoryAcquisitionError(
                "CEMS mask value-inventory provider bytes were not removed"
            )

        return {
            "schema_version": SCHEMA_VERSION,
            "dataset_id": _masks.DATASET_ID,
            "source_issue": SOURCE_ISSUE,
            "profile_issue": PROFILE_ISSUE,
            "release": _masks.RELEASE,
            "mask_value_inventory_receipts": receipts,
            "external_bytes_persisted": False,
            "mask_values_inspected": True,
            "mask_value_semantics_verified": False,
            "per_cell_scientific_correctness_verified": False,
            "benchmark_use_authorized": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }
    except CemsMaskValueInventoryAcquisitionError:
        raise
    except Exception as exc:
        raise CemsMaskValueInventoryAcquisitionError(
            "CEMS mask value-inventory acquisition failed"
        ) from exc
