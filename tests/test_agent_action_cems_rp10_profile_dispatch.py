# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest import mock

from scripts import agent_action_protocol_cems_rp10_profile as protocol
from scripts import prepare_agent_action_result_cems_rp10_profile as prepare
from scripts import validate_agent_action_request_cems_rp10_profile as request_validator
from scripts import validate_agent_action_result_cems_rp10_profile as result_validator

MAIN_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED_AT = "2026-09-06T06:30:00Z"
RETRIEVED_AT = "2026-09-06T06:31:00Z"
FINISHED_AT = "2026-09-06T06:32:00Z"
BYTE_COUNT = 272_286_610
SHA256 = "15f86b86c228a065250b05488548d7386ac8e33cec4cba6da93f712f7500f45b"
DATASET_ID = "ec-jrc.cems.europe-mediterranean-river-flood-hazard-maps.2026"
SOURCE_URL = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/"
    "Europe_RP10_filled_depth.tif"
)


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.CEMS_RP10_PROFILE_ACTION,
        "issue": 802,
        "target_sha": MAIN_SHA,
        "dataset_id": DATASET_ID,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _profile_receipt(**overrides):
    value = {
        "schema_version": "oc-cems-rp10-geotiff-profile-receipt-v1",
        "dataset_id": DATASET_ID,
        "source_issue": 793,
        "profile_issue": 802,
        "release": "3.1.1",
        "filename": "Europe_RP10_filled_depth.tif",
        "requested_url": SOURCE_URL,
        "final_url": SOURCE_URL,
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "image/tiff",
        "content_length_header": BYTE_COUNT,
        "receipt_byte_count": BYTE_COUNT,
        "receipt_sha256": SHA256,
        "geotiff_profile": {
            "schema_version": "oc-cems-rp10-geotiff-profile-v1",
            "dataset_id": DATASET_ID,
            "source_issue": 793,
            "profile_issue": 802,
            "release": "3.1.1",
            "filename": "Europe_RP10_filled_depth.tif",
            "source_url": SOURCE_URL,
            "receipt_byte_count": BYTE_COUNT,
            "receipt_sha256": SHA256,
            "receipt_identity_verified": True,
            "driver": "GTiff",
            "band_count": 1,
            "dtypes": ["float32"],
            "width": 10,
            "height": 20,
            "crs": {
                "string": "EPSG:3035",
                "epsg": 3035,
                "wkt": "PROJCRS[synthetic]",
            },
            "transform_gdal": [0.0, 100.0, 0.0, 0.0, 0.0, -100.0],
            "resolution": [100.0, 100.0],
            "bounds": [0.0, 0.0, 1000.0, 2000.0],
            "nodatavals": [-9999.0],
            "scales": [1.0],
            "offsets": [0.0],
            "descriptions": [None],
            "band_units": [None],
            "band_unit_tags": [{}],
            "unit_metadata_present": False,
            "reader": {
                "name": "rasterio",
                "version": "1.5.1",
                "gdal_version": "3.10.3",
                "proj_version": "9.6.0",
            },
            "raster_values_inspected": False,
            "geotiff_metadata_verified": True,
            "benchmark_use_authorized": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        },
        "external_bytes_persisted": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(overrides)
    return value


def _run(*, comments=None, profile_acquirer=None, request=None):
    validated = request_validator.validate_request(
        request or _request(), expected_issue=802
    )
    kwargs = {
        "repository": REPOSITORY,
        "execution_sha": MAIN_SHA,
        "source_comment_id": 1,
        "run_id": 2,
        "run_attempt": 1,
        "started_at": STARTED_AT,
        "profile_acquirer": profile_acquirer or _profile_receipt,
    }
    with mock.patch.object(prepare._base, "utc_now", return_value=FINISHED_AT):
        return prepare.prepare_completed_result(validated, comments or [], **kwargs)


class CemsRp10ProfileRequestTests(unittest.TestCase):
    def test_profile_action_is_issue_and_execution_sha_bound(self) -> None:
        request = _request()
        self.assertIs(
            request_validator.validate_request(request, expected_issue=802), request
        )
        self.assertIn(request["action"], request_validator.ALLOWED_ACTIONS)
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertIn(request["action"], prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(request), 802)

        for mutation in (
            {"issue": 801},
            {"issue": 802.0},
            {"dataset_id": "other-dataset"},
            {"target_sha": "v3.1.1"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(
                request_validator.RequestError
            ):
                request_validator.validate_request(
                    _request(**mutation), expected_issue=802
                )

        for selector in (
            "url", "filename", "return_period_years", "provider", "reader", "parser"
        ):
            selected = _request()
            selected[selector] = "forbidden"
            with self.subTest(selector=selector), self.assertRaises(
                request_validator.RequestError
            ):
                request_validator.validate_request(selected, expected_issue=802)

        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40), MAIN_SHA, REPOSITORY
            )

    def test_existing_receipt_action_still_delegates(self) -> None:
        legacy = request_validator._legacy
        receipt_request = {
            "schema_version": legacy.SCHEMA_VERSION,
            "action": legacy.CEMS_RP10_RECEIPT_ACTION,
            "issue": legacy.CEMS_RP10_RECEIPT_ISSUE,
            "target_sha": MAIN_SHA,
            "dataset_id": legacy.CEMS_RP10_RECEIPT_DATASET_ID,
            "requester": "pokekarten",
        }
        self.assertIs(
            request_validator.validate_request(
                receipt_request, expected_issue=legacy.CEMS_RP10_RECEIPT_ISSUE
            ),
            receipt_request,
        )


class CemsRp10ProfileResultTests(unittest.TestCase):
    def test_profile_receipt_is_bounded_and_keeps_authority_closed(self) -> None:
        receipt = _profile_receipt()
        self.assertIs(
            result_validator.validate_cems_rp10_profile_receipt(receipt), receipt
        )

        for field in (
            "external_bytes_persisted",
            "benchmark_use_authorized",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field), self.assertRaises(
                result_validator.ResultError
            ):
                result_validator.validate_cems_rp10_profile_receipt(
                    _profile_receipt(**{field: True})
                )

        for mutate in (
            lambda r: r.__setitem__("receipt_sha256", "0" * 64),
            lambda r: r["geotiff_profile"].__setitem__("raster_values_inspected", True),
            lambda r: r["geotiff_profile"].__setitem__("benchmark_use_authorized", True),
            lambda r: r["geotiff_profile"]["band_unit_tags"][0].__setitem__("PAYLOAD", "x"),
        ):
            receipt = _profile_receipt()
            mutate(receipt)
            with self.assertRaises(result_validator.ResultError):
                result_validator.validate_cems_rp10_profile_receipt(receipt)

    def test_success_is_metadata_only_and_revalidates_after_dispatch(self) -> None:
        result = _run()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["phase"], "acquisition_receipt")
        receipt = result["evidence"][prepare.CEMS_RP10_PROFILE_FIELD]
        self.assertEqual(receipt["receipt_sha256"], SHA256)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["geotiff_profile"]["raster_values_inspected"])
        self.assertFalse(receipt["benchmark_use_authorized"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertFalse(receipt["model_use_authorized"])
        self.assertNotIn("payload", result)
        self.assertNotIn("values", result)
        self.assertIs(result_validator.validate_result(result), result)

        drifted = copy.deepcopy(result)
        drifted["execution_sha"] = "0" * 40
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

    def test_complete_ledger_dedup_stops_before_profile_worker(self) -> None:
        first = _run()
        prior = {
            "id": 900,
            "user": {"login": "github-actions[bot]"},
            "body": protocol.canonical_result_comment(first),
        }
        worker = mock.Mock(return_value=_profile_receipt())
        duplicate = _run(comments=[prior], profile_acquirer=worker)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["phase"], "request_validation")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 900)
        worker.assert_not_called()

    def test_worker_failure_is_closed_without_provider_detail(self) -> None:
        def blocked_worker():
            raise RuntimeError("provider secret detail")

        result = _run(profile_acquirer=blocked_worker)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], prepare.ACQUISITION_FAILURE_CLASS)
        self.assertIsNone(result["evidence"][prepare.CEMS_RP10_PROFILE_FIELD])


class CemsRp10ProfileWorkflowTests(unittest.TestCase):
    def test_shared_owner_only_dispatcher_uses_profile_aware_entrypoints(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(
            encoding="utf-8"
        )
        validate_job = text.split("  report-result:", 1)[0]
        self.assertIn(
            "python -m scripts.prepare_agent_action_result_cems_rp10_profile", text
        )
        self.assertIn(
            "python -m scripts.post_agent_action_result_cems_rp10_profile", text
        )
        self.assertIn("requirements-cems-geotiff-profile.txt", validate_job)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", text)
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", validate_job)
        self.assertEqual(text.count("issue_comment:"), 1)


if __name__ == "__main__":
    unittest.main()
