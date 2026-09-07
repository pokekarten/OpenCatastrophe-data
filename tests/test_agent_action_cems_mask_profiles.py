# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import unittest
from unittest import mock

from scripts import acquire_cems_europe_mask_profiles as worker
from scripts import acquire_cems_europe_mask_receipts as mask_receipts
from scripts import agent_action_protocol_cems_mask_profiles as protocol
from scripts import prepare_agent_action_result_cems_mask_profiles as prepare
from scripts import profile_cems_europe_mask_geotiffs as profile_mod
from scripts import profile_cems_europe_rp10_geotiff as rp10_profile_mod
from scripts import validate_agent_action_request_cems_mask_profiles as request_validator
from scripts import validate_agent_action_result_cems_mask_profiles as result_validator
from scripts import validate_agent_action_result_cems_rp10_profile as rp10_result_validator

MAIN_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED_AT = "2026-09-07T18:00:00Z"
RETRIEVED_AT = "2026-09-07T18:01:00Z"
FINISHED_AT = "2026-09-07T18:02:00Z"


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


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.CEMS_MASK_PROFILES_ACTION,
        "issue": 816,
        "target_sha": MAIN_SHA,
        "dataset_id": request_validator.CEMS_MASK_PROFILES_DATASET_ID,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _rp10_geotiff_profile() -> dict:
    return {
        "schema_version": profile_mod.RP10_PROFILE_SCHEMA_VERSION,
        "dataset_id": profile_mod.DATASET_ID,
        "source_issue": rp10_profile_mod.SOURCE_ISSUE,
        "profile_issue": rp10_profile_mod.PROFILE_ISSUE,
        "release": rp10_profile_mod.RELEASE,
        "filename": rp10_profile_mod.FILENAME,
        "source_url": rp10_profile_mod.SOURCE_URL,
        "receipt_byte_count": rp10_profile_mod.ACCEPTED_BYTE_COUNT,
        "receipt_sha256": rp10_profile_mod.ACCEPTED_SHA256,
        "receipt_identity_verified": True,
        "driver": "GTiff",
        "band_count": 1,
        "dtypes": ["float32"],
        "width": 110162,
        "height": 51992,
        "crs": {"string": "EPSG:4326", "epsg": 4326, "wkt": "WGS84"},
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
        "nodatavals": [-9999.0],
        "scales": [1.0],
        "offsets": [0.0],
        "descriptions": [None],
        "band_units": [None],
        "band_unit_tags": [{}],
        "unit_metadata_present": False,
        "reader": {
            "name": "rasterio",
            "version": "test",
            "gdal_version": "test",
            "proj_version": "test",
        },
        "raster_values_inspected": False,
        "geotiff_metadata_verified": True,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _rp10_profile_receipt() -> dict:
    return {
        "schema_version": rp10_result_validator._PROFILE_SCHEMA_VERSION,
        "dataset_id": profile_mod.DATASET_ID,
        "source_issue": rp10_profile_mod.SOURCE_ISSUE,
        "profile_issue": rp10_profile_mod.PROFILE_ISSUE,
        "release": rp10_profile_mod.RELEASE,
        "filename": rp10_profile_mod.FILENAME,
        "requested_url": rp10_profile_mod.SOURCE_URL,
        "final_url": rp10_profile_mod.SOURCE_URL,
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "image/tiff",
        "content_length_header": rp10_profile_mod.ACCEPTED_BYTE_COUNT,
        "receipt_byte_count": rp10_profile_mod.ACCEPTED_BYTE_COUNT,
        "receipt_sha256": rp10_profile_mod.ACCEPTED_SHA256,
        "geotiff_profile": _rp10_geotiff_profile(),
        "external_bytes_persisted": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _mask_geotiff_profile(kind: str) -> dict:
    accepted = profile_mod.MASK_RECEIPTS[kind]
    filename = accepted["filename"]
    profile = _rp10_geotiff_profile()
    profile.update(
        {
            "schema_version": profile_mod.PROFILE_SCHEMA_VERSION,
            "source_issue": 809,
            "profile_issue": 816,
            "filename": filename,
            "source_url": profile_mod.BASE_URL + filename,
            "receipt_byte_count": accepted["byte_count"],
            "receipt_sha256": accepted["sha256"],
            "dtypes": ["uint8"],
            "nodatavals": [255.0],
            "mask_kind": kind,
            "mask_values_inspected": False,
        }
    )
    return profile


def _mask_profile_receipt(kind: str) -> dict:
    accepted = profile_mod.MASK_RECEIPTS[kind]
    filename = accepted["filename"]
    return {
        "schema_version": worker.PROFILE_RECEIPT_SCHEMA_VERSION,
        "dataset_id": profile_mod.DATASET_ID,
        "source_issue": 809,
        "profile_issue": 816,
        "release": profile_mod.RELEASE,
        "mask_kind": kind,
        "filename": filename,
        "requested_url": profile_mod.BASE_URL + filename,
        "final_url": profile_mod.BASE_URL + filename,
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "image/tiff",
        "content_length_header": accepted["byte_count"],
        "receipt_byte_count": accepted["byte_count"],
        "receipt_sha256": accepted["sha256"],
        "geotiff_profile": _mask_geotiff_profile(kind),
        "external_bytes_persisted": False,
        "mask_values_inspected": False,
        "mask_value_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _aggregate() -> dict:
    rp10_receipt = _rp10_profile_receipt()
    mask_profiles = [
        _mask_profile_receipt(kind)
        for kind, _filename in mask_receipts.ASSETS
    ]
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "dataset_id": profile_mod.DATASET_ID,
        "source_issue": 809,
        "profile_issue": 816,
        "release": profile_mod.RELEASE,
        "rp10_profile_receipt": rp10_receipt,
        "mask_profile_receipts": mask_profiles,
        "comparisons": [
            profile_mod.compare_mask_profile_to_rp10(
                item["geotiff_profile"],
                rp10_receipt["geotiff_profile"],
            )
            for item in mask_profiles
        ],
        "external_bytes_persisted": False,
        "mask_values_inspected": False,
        "mask_value_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _run(*, comments=None, profile_acquirer=None):
    validated = request_validator.validate_request(_request(), expected_issue=816)
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
            profile_acquirer=profile_acquirer or _aggregate,
        )


class CemsMaskProfileActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_exact_execution_sha(self) -> None:
        request = _request()
        self.assertIs(
            request_validator.validate_request(request, expected_issue=816),
            request,
        )
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertIn(request["action"], prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(request), 816)
        for selector in ("url", "filename", "mask", "provider", "reader", "parser", "output"):
            selected = _request()
            selected[selector] = "forbidden"
            with self.subTest(selector=selector), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(selected, expected_issue=816)
        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40),
                MAIN_SHA,
                REPOSITORY,
            )

    def test_aggregate_revalidates_profiles_and_recomputed_comparisons(self) -> None:
        aggregate = _aggregate()
        self.assertIs(result_validator.validate_cems_mask_profiles(aggregate), aggregate)
        self.assertEqual(
            [item["mask_kind"] for item in aggregate["mask_profile_receipts"]],
            ["permanent_water", "spurious_depth"],
        )
        self.assertTrue(all(item["grid_metadata_equal"] for item in aggregate["comparisons"]))
        self.assertTrue(all(not item["container_metadata_equal"] for item in aggregate["comparisons"]))
        self.assertFalse(aggregate["mask_values_inspected"])
        self.assertFalse(aggregate["mask_value_semantics_verified"])

        tampered = copy.deepcopy(aggregate)
        tampered["comparisons"][0]["grid_metadata_equal"] = False
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_mask_profiles(tampered)

        tampered = copy.deepcopy(aggregate)
        tampered["rp10_profile_receipt"]["receipt_sha256"] = "0" * 64
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_mask_profiles(tampered)

    def test_success_and_dedup_stop_before_profile_worker(self) -> None:
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
        duplicate = _run(comments=[prior], profile_acquirer=acquirer)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 900)
        acquirer.assert_not_called()

    def test_worker_uses_only_fixed_mask_routes_with_synthetic_bytes(self) -> None:
        payloads = {
            profile_mod.BASE_URL + "Europe_permanent_water_bodies.tif": b"II*\x00permanent-water",
            profile_mod.BASE_URL + "Europe_spurious_depth_areas.tif": b"II*\x00spurious-depth",
        }
        patched_receipts = {
            kind: {
                "filename": filename,
                "byte_count": len(payloads[profile_mod.BASE_URL + filename]),
                "sha256": hashlib.sha256(payloads[profile_mod.BASE_URL + filename]).hexdigest(),
            }
            for kind, filename in mask_receipts.ASSETS
        }
        seen: list[str] = []

        def opener(request, _timeout):
            seen.append(request.full_url)
            return _Response(request.full_url, payloads[request.full_url])

        def profiler(_path, *, mask_kind):
            accepted = profile_mod.MASK_RECEIPTS[mask_kind]
            filename = accepted["filename"]
            profile = _rp10_geotiff_profile()
            profile.update(
                {
                    "schema_version": profile_mod.PROFILE_SCHEMA_VERSION,
                    "source_issue": 809,
                    "profile_issue": 816,
                    "filename": filename,
                    "source_url": profile_mod.BASE_URL + filename,
                    "receipt_byte_count": accepted["byte_count"],
                    "receipt_sha256": accepted["sha256"],
                    "dtypes": ["uint8"],
                    "nodatavals": [255.0],
                    "mask_kind": mask_kind,
                    "mask_values_inspected": False,
                }
            )
            return profile

        with mock.patch.dict(profile_mod.MASK_RECEIPTS, patched_receipts, clear=True):
            result = worker.acquire_and_profile_cems_masks_against_rp10(
                opener=opener,
                clock=lambda: RETRIEVED_AT,
                monotonic=lambda: 1.0,
                profiler=profiler,
                rp10_acquirer=_rp10_profile_receipt,
            )

        self.assertEqual(
            seen,
            [profile_mod.BASE_URL + filename for _kind, filename in mask_receipts.ASSETS],
        )
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["mask_values_inspected"])
        self.assertFalse(result["mask_value_semantics_verified"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_worker_failure_is_closed_without_provider_detail_in_result(self) -> None:
        def fail():
            raise RuntimeError("provider detail must not persist")

        result = _run(profile_acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(
            result["evidence"][prepare.CEMS_MASK_PROFILES_FIELD]
        )
        self.assertIs(result_validator.validate_result(result), result)

    def test_workflow_uses_profile_entrypoints_and_retains_legacy_breadcrumbs(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(encoding="utf-8")
        self.assertIn("python -m scripts.prepare_agent_action_result_cems_mask_profiles", text)
        self.assertIn("python -m scripts.post_agent_action_result_cems_mask_profiles", text)
        for legacy in (
            "prepare_agent_action_result_cems_masks",
            "post_agent_action_result_cems_masks",
            "prepare_agent_action_result_cems_rp10_profile",
            "post_agent_action_result_cems_rp10_profile",
            "prepare_agent_action_result_cems_rp10.py",
            "post_agent_action_result_cems_rp10.py",
            "prepare_agent_action_result_country_risk.py",
            "post_agent_action_result_country_risk.py",
            "repository-owned frozen DWD worker",
            "python scripts/post_agent_action_result.py",
        ):
            self.assertIn(legacy, text)
        self.assertEqual(text.count("issue_comment:"), 1)


if __name__ == "__main__":
    unittest.main()
