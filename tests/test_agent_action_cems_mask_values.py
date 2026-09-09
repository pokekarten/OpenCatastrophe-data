# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from scripts import acquire_cems_europe_mask_receipts as mask_receipts
from scripts import acquire_cems_europe_mask_value_inventories as worker
from scripts import agent_action_protocol_cems_mask_values as protocol
from scripts import prepare_agent_action_result_cems_mask_values as prepare
from scripts import profile_cems_europe_mask_geotiffs as metadata
from scripts import profile_cems_europe_mask_values as values
from scripts import validate_agent_action_request_cems_mask_values as request_validator
from scripts import validate_agent_action_result_cems_mask_values as result_validator

MAIN_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED_AT = "2026-09-09T18:30:00Z"
RETRIEVED_AT = "2026-09-09T18:31:00Z"
FINISHED_AT = "2026-09-09T18:32:00Z"
TOTAL_CELLS = 110162 * 51992


class _Socket:
    def settimeout(self, _timeout: float) -> None:
        pass


class _Response:
    def __init__(self, url: str, payload: bytes, *, final_url: str | None = None):
        self.status = 200
        self._url = final_url or url
        self._payload = payload
        self._offset = 0
        self._oc_response_socket = _Socket()
        self.headers = {
            "Content-Type": "image/tiff",
            "Content-Length": str(len(payload)),
        }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


def _digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.CEMS_MASK_VALUE_INVENTORIES_ACTION,
        "issue": 823,
        "target_sha": MAIN_SHA,
        "dataset_id": request_validator.CEMS_MASK_VALUE_INVENTORIES_DATASET_ID,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _inventory() -> dict:
    payload = {
        "total_cells": TOTAL_CELLS,
        "block_count": 51992,
        "nodata_value": -9999,
        "nodata_count": TOTAL_CELLS - 3,
        "nan_non_nodata_count": 0,
        "positive_infinity_count": 0,
        "negative_infinity_count": 0,
        "finite_count": 3,
        "zero_count": 0,
        "nonzero_count": 3,
        "finite_min": 1,
        "finite_max": 1,
        "cardinality_cap": 32,
        "cardinality_cap_exceeded": False,
        "finite_unique_value_count": 1,
        "finite_value_counts": [{"value": 1, "count": 3}],
        "encoding_observation": "single_finite_value_candidate_support",
    }
    payload["inventory_sha256"] = _digest(payload)
    return payload


def _value_result(kind: str) -> dict:
    accepted = metadata.MASK_RECEIPTS[kind]
    payload = {
        "schema_version": values.SCHEMA_VERSION,
        "dataset_id": metadata.DATASET_ID,
        "release": metadata.RELEASE,
        "source_issue": 809,
        "profile_issue": 823,
        "mask_kind": kind,
        "filename": accepted["filename"],
        "receipt_byte_count": accepted["byte_count"],
        "receipt_sha256": accepted["sha256"],
        "receipt_identity_verified": True,
        "grid": {
            "width": 110162,
            "height": 51992,
            "crs": "EPSG:4326",
            "transform_gdal": [
                -24.54208333,
                0.0008333333333333334,
                0.0,
                71.13375,
                0.0,
                -0.0008333333333333334,
            ],
            "resolution": [0.0008333333333333334, 0.0008333333333333334],
            "bounds": [
                -24.54208333,
                27.80708333333334,
                67.25958333666668,
                71.13375,
            ],
            "band_count": 1,
            "dtype": "float64",
        },
        "inventory": _inventory(),
        "mask_values_inspected": True,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }
    payload["result_sha256"] = _digest(payload)
    return payload


def _inventory_receipt(kind: str) -> dict:
    accepted = metadata.MASK_RECEIPTS[kind]
    filename = accepted["filename"]
    return {
        "schema_version": worker.INVENTORY_RECEIPT_SCHEMA_VERSION,
        "dataset_id": metadata.DATASET_ID,
        "source_issue": 809,
        "profile_issue": 823,
        "release": metadata.RELEASE,
        "mask_kind": kind,
        "filename": filename,
        "requested_url": metadata.BASE_URL + filename,
        "final_url": metadata.BASE_URL + filename,
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "image/tiff",
        "content_length_header": accepted["byte_count"],
        "receipt_byte_count": accepted["byte_count"],
        "receipt_sha256": accepted["sha256"],
        "value_inventory": _value_result(kind),
        "external_bytes_persisted": False,
        "mask_values_inspected": True,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _aggregate() -> dict:
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "dataset_id": metadata.DATASET_ID,
        "source_issue": 809,
        "profile_issue": 823,
        "release": metadata.RELEASE,
        "mask_value_inventory_receipts": [
            _inventory_receipt(kind) for kind, _filename in mask_receipts.ASSETS
        ],
        "external_bytes_persisted": False,
        "mask_values_inspected": True,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _run(*, comments=None, inventory_acquirer=None):
    validated = request_validator.validate_request(_request(), expected_issue=823)
    with mock.patch.object(prepare._base, "utc_now", return_value=FINISHED_AT):
        return prepare.prepare_completed_result(
            validated,
            comments or [],
            repository=REPOSITORY,
            execution_sha=MAIN_SHA,
            source_comment_id=1,
            run_id=2,
            run_attempt=1,
            started_at=STARTED_AT,
            inventory_acquirer=inventory_acquirer or _aggregate,
        )


class CemsMaskValueInventoryActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_exact_execution_sha(self) -> None:
        request = _request()
        self.assertIs(
            request_validator.validate_request(request, expected_issue=823),
            request,
        )
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertIn(request["action"], prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(request), 823)

        for selector in (
            "url",
            "filename",
            "mask",
            "provider",
            "reader",
            "parser",
            "output",
            "cardinality_cap",
            "windows",
        ):
            selected = _request()
            selected[selector] = "forbidden"
            with self.subTest(selector=selector), self.assertRaises(
                request_validator.RequestError
            ):
                request_validator.validate_request(selected, expected_issue=823)

        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40),
                MAIN_SHA,
                REPOSITORY,
            )

    def test_aggregate_revalidates_bounded_inventory_and_authority_ceiling(self) -> None:
        aggregate = _aggregate()
        self.assertIs(
            result_validator.validate_cems_mask_value_inventories(aggregate),
            aggregate,
        )
        self.assertTrue(aggregate["mask_values_inspected"])
        self.assertFalse(aggregate["mask_value_semantics_verified"])
        self.assertFalse(aggregate["benchmark_use_authorized"])
        self.assertFalse(aggregate["model_use_authorized"])

        tampered = copy.deepcopy(aggregate)
        tampered["mask_value_inventory_receipts"][0]["value_inventory"]["inventory"][
            "finite_value_counts"
        ][0]["count"] = 4
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_mask_value_inventories(tampered)

        tampered = copy.deepcopy(aggregate)
        tampered["mask_value_inventory_receipts"][0]["value_inventory"][
            "mask_value_semantics_verified"
        ] = True
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_mask_value_inventories(tampered)

        tampered = copy.deepcopy(aggregate)
        tampered["mask_value_inventory_receipts"][0]["value_inventory"]["grid"][
            "width"
        ] += 1
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_mask_value_inventories(tampered)

    def test_success_and_dedup_stop_before_provider_worker(self) -> None:
        first = _run()
        self.assertEqual(first["status"], "pass")
        self.assertIs(result_validator.validate_result(first), first)
        self.assertFalse(first["external_bytes_persisted"])

        prior = {
            "id": 900,
            "user": {"login": "github-actions[bot]"},
            "body": protocol.canonical_result_comment(first),
        }
        acquirer = mock.Mock(return_value=_aggregate())
        duplicate = _run(comments=[prior], inventory_acquirer=acquirer)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 900)
        acquirer.assert_not_called()

    def test_worker_uses_only_frozen_mask_routes_and_deletes_provider_bytes(self) -> None:
        payloads = {
            metadata.BASE_URL + "Europe_permanent_water_bodies.tif": b"II*\x00water",
            metadata.BASE_URL + "Europe_spurious_depth_areas.tif": b"II*\x00spurious",
        }
        patched_receipts = {
            kind: {
                "filename": filename,
                "byte_count": len(payloads[metadata.BASE_URL + filename]),
                "sha256": hashlib.sha256(
                    payloads[metadata.BASE_URL + filename]
                ).hexdigest(),
            }
            for kind, filename in mask_receipts.ASSETS
        }
        seen: list[str] = []
        seen_paths: list[Path] = []

        def opener(request, _timeout):
            seen.append(request.full_url)
            return _Response(request.full_url, payloads[request.full_url])

        def profiler(path, *, mask_kind):
            seen_paths.append(Path(path))
            accepted = metadata.MASK_RECEIPTS[mask_kind]
            return {
                "receipt_byte_count": accepted["byte_count"],
                "receipt_sha256": accepted["sha256"],
                "external_bytes_persisted": False,
                "mask_values_inspected": True,
                "mask_value_semantics_verified": False,
            }

        with mock.patch.dict(metadata.MASK_RECEIPTS, patched_receipts, clear=True):
            result = worker.acquire_cems_mask_value_inventories(
                opener=opener,
                clock=lambda: RETRIEVED_AT,
                monotonic=lambda: 1.0,
                profiler=profiler,
            )

        self.assertEqual(
            seen,
            [metadata.BASE_URL + filename for _kind, filename in mask_receipts.ASSETS],
        )
        self.assertTrue(all(not path.exists() for path in seen_paths))
        self.assertFalse(result["external_bytes_persisted"])
        self.assertTrue(result["mask_values_inspected"])
        self.assertFalse(result["mask_value_semantics_verified"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_worker_failure_is_closed_without_provider_detail_in_result(self) -> None:
        def fail():
            raise RuntimeError("provider detail must not persist")

        result = _run(inventory_acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(
            result["evidence"][prepare.CEMS_MASK_VALUE_INVENTORIES_FIELD]
        )
        self.assertIs(result_validator.validate_result(result), result)

    def test_workflow_uses_value_entrypoints_and_retains_profile_breadcrumbs(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "python -m scripts.prepare_agent_action_result_cems_mask_values",
            text,
        )
        self.assertIn(
            "python -m scripts.post_agent_action_result_cems_mask_values",
            text,
        )
        for legacy in (
            "prepare_agent_action_result_cems_mask_profiles",
            "post_agent_action_result_cems_mask_profiles",
            "prepare_agent_action_result_cems_masks",
            "post_agent_action_result_cems_masks",
            "prepare_agent_action_result_cems_rp10_profile",
            "post_agent_action_result_cems_rp10_profile",
            "repository-owned frozen DWD worker",
            "python scripts/post_agent_action_result.py",
        ):
            with self.subTest(legacy=legacy):
                self.assertIn(legacy, text)


if __name__ == "__main__":
    unittest.main()
