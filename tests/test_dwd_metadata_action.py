# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import stat
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.acquire_dwd_extreme_wind_receipt import AcquisitionError
from scripts.acquire_dwd_metadata_receipt import (
    DATASET_ID,
    EXPECTED_STATION_ID,
    FILENAME,
    REQUIRED_METADATA_FAMILIES,
    SCHEMA_VERSION,
    SOURCE_ISSUE,
    SOURCE_URL,
    _inspection_evidence,
)
from scripts.agent_action_protocol import ProtocolError, canonical_result_comment, semantic_request_id
from scripts.prepare_agent_action_result import build_acquisition_result, prepare_completed_result
from scripts.validate_agent_action_request import (
    ACQUISITION_RECEIPT_ACTION,
    DWD_METADATA_RECEIPT_ACTION,
    DWD_METADATA_RECEIPT_DATASET_ID,
    DWD_METADATA_RECEIPT_ISSUE,
    RequestError,
    validate_request,
)
from scripts.validate_agent_action_result import ResultError, validate_dwd_metadata_receipt

ROOT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = ROOT / "schemas" / "agent-action-request-v1.schema.json"
METADATA_SCHEMA = ROOT / "schemas" / "dwd-metadata-receipt-v1.schema.json"
RESULT_SCHEMA = ROOT / "schemas" / "agent-action-result-v1.schema.json"
REPOSITORY = "pokekarten/OpenCatastrophe-data"
EXECUTION_SHA = "b" * 40
STARTED = "2026-08-12T09:00:00Z"
FINISHED = "2026-08-12T09:00:02Z"

METADATA_REQUEST = {
    "schema_version": "oc-action-request-v1",
    "action": DWD_METADATA_RECEIPT_ACTION,
    "issue": DWD_METADATA_RECEIPT_ISSUE,
    "target_sha": EXECUTION_SHA,
    "dataset_id": DWD_METADATA_RECEIPT_DATASET_ID,
    "requester": "tier2-builder-test",
}
MEASUREMENT_REQUEST = dict(
    METADATA_REQUEST,
    action=ACQUISITION_RECEIPT_ACTION,
    issue=162,
)

METADATA_RECEIPT = {
    "schema_version": SCHEMA_VERSION,
    "dataset_id": DATASET_ID,
    "source_issue": SOURCE_ISSUE,
    "requested_url": SOURCE_URL,
    "final_url": SOURCE_URL,
    "filename": FILENAME,
    "retrieved_at": "2026-08-12T09:00:01Z",
    "byte_count": 8740,
    "sha256": "c" * 64,
    "content_type": "application/zip",
    "last_modified": None,
    "etag": None,
    "archive_member_count": 3,
    "archive_uncompressed_bytes": 30,
    "station_id": EXPECTED_STATION_ID,
    "required_metadata_families": ["equipment", "geography", "parameter"],
    "metadata_members": [
        {"path": "Metadaten_Geraete_00003.txt", "family": "equipment"},
        {"path": "Metadaten_Geographie_00003.txt", "family": "geography"},
        {"path": "Metadaten_Parameter_00003.txt", "family": "parameter"},
    ],
    "temporal_coverage_status": "unverified",
    "external_bytes_persisted": False,
    "publication_authorized": False,
}


def _write_zip(path: Path, names: list[str], *, compression: int = zipfile.ZIP_DEFLATED) -> None:
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        for name in names:
            archive.writestr(name, ("metadata for " + name).encode("utf-8"))


def _inspect(path: Path) -> dict[str, object]:
    return _inspection_evidence(path.as_posix(), deadline=time.monotonic() + 10, monotonic=time.monotonic)


class DwdMetadataActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_no_network_fields(self) -> None:
        self.assertEqual(validate_request(dict(METADATA_REQUEST), expected_issue=211), METADATA_REQUEST)
        for mutation in (
            {"issue": 212},
            {"dataset_id": "other.dataset"},
        ):
            with self.subTest(mutation=mutation), self.assertRaisesRegex(RequestError, "dwd_metadata_receipt is restricted"):
                validate_request(dict(METADATA_REQUEST, **mutation))
        with self.assertRaisesRegex(RequestError, "unexpected=.*url"):
            validate_request(dict(METADATA_REQUEST, url="https://example.invalid/data.zip"))

    def test_request_schema_matches_metadata_action_boundary(self) -> None:
        schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        self.assertIn(DWD_METADATA_RECEIPT_ACTION, schema["properties"]["action"]["enum"])
        rules = schema["allOf"]
        metadata_rules = [
            rule for rule in rules
            if rule.get("if", {}).get("properties", {}).get("action") == {"const": DWD_METADATA_RECEIPT_ACTION}
        ]
        self.assertEqual(len(metadata_rules), 1)
        properties = metadata_rules[0]["then"]["properties"]
        self.assertEqual(properties["issue"], {"const": DWD_METADATA_RECEIPT_ISSUE})
        self.assertEqual(properties["dataset_id"], {"const": DWD_METADATA_RECEIPT_DATASET_ID})

    def test_metadata_and_measurement_semantic_ids_are_distinct_and_target_is_trusted(self) -> None:
        metadata_id = semantic_request_id(METADATA_REQUEST, EXECUTION_SHA, REPOSITORY)
        measurement_id = semantic_request_id(MEASUREMENT_REQUEST, EXECUTION_SHA, REPOSITORY)
        self.assertNotEqual(metadata_id, measurement_id)
        with self.assertRaisesRegex(ProtocolError, "target_sha"):
            semantic_request_id(dict(METADATA_REQUEST, target_sha="a" * 40), EXECUTION_SHA, REPOSITORY)

    def test_valid_provider_native_archive_proves_required_families_but_not_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / FILENAME
            _write_zip(
                path,
                [
                    "Metadaten_Geographie_00003.txt",
                    "Metadaten_Geraete_00003.txt",
                    "Metadaten_Parameter_00003.txt",
                ],
            )
            evidence = _inspect(path)
        self.assertEqual(evidence["station_id"], "00003")
        self.assertEqual(evidence["required_metadata_families"], sorted(REQUIRED_METADATA_FAMILIES))
        self.assertEqual(evidence["temporal_coverage_status"], "unverified")
        self.assertEqual(
            {item["family"] for item in evidence["metadata_members"]},
            REQUIRED_METADATA_FAMILIES,
        )

    def test_missing_generic_or_contradictory_station_families_fail_closed(self) -> None:
        cases = (
            [
                "Metadaten_Geographie_00003.txt",
                "Metadaten_Sonstiges_00003.txt",
                "Metadaten_Parameter_00003.txt",
            ],
            [
                "Metadaten_Geographie_00003.txt",
                "Metadaten_Geraete_99999.txt",
                "Metadaten_Parameter_00003.txt",
            ],
            [
                "prefix_Metadaten_Geographie_00003.txt",
                "Metadaten_Geraete_00003.txt",
                "Metadaten_Parameter_00003.txt",
            ],
        )
        for names in cases:
            with self.subTest(names=names), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / FILENAME
                _write_zip(path, names)
                with self.assertRaises(AcquisitionError):
                    _inspect(path)

    def test_unsupported_compression_special_file_and_encryption_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / FILENAME
            _write_zip(
                path,
                [
                    "Metadaten_Geographie_00003.txt",
                    "Metadaten_Geraete_00003.txt",
                    "Metadaten_Parameter_00003.txt",
                ],
                compression=zipfile.ZIP_BZIP2,
            )
            with self.assertRaisesRegex(AcquisitionError, "unsupported compression"):
                _inspect(path)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / FILENAME
            with zipfile.ZipFile(path, "w") as archive:
                link = zipfile.ZipInfo("Metadaten_Geographie_00003.txt")
                link.create_system = 3
                link.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(link, b"target")
                archive.writestr("Metadaten_Geraete_00003.txt", b"device")
                archive.writestr("Metadaten_Parameter_00003.txt", b"parameter")
            with self.assertRaisesRegex(AcquisitionError, "special-file"):
                _inspect(path)

        class FakeEncryptedArchive:
            def __init__(self, member: zipfile.ZipInfo) -> None:
                self.member = member

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

            def infolist(self) -> list[zipfile.ZipInfo]:
                return [self.member]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / FILENAME
            path.write_bytes(b"x")
            encrypted = zipfile.ZipInfo("Metadaten_Geographie_00003.txt")
            encrypted.flag_bits = 0x1
            encrypted.compress_type = zipfile.ZIP_STORED
            encrypted.compress_size = 1
            encrypted.file_size = 1
            encrypted.external_attr = (stat.S_IFREG | 0o644) << 16
            with patch(
                "scripts.acquire_dwd_metadata_receipt.zipfile.ZipFile",
                return_value=FakeEncryptedArchive(encrypted),
            ), self.assertRaisesRegex(AcquisitionError, "encrypted"):
                _inspect(path)

    def test_metadata_receipt_is_closed_and_temporal_coverage_cannot_be_promoted(self) -> None:
        self.assertEqual(validate_dwd_metadata_receipt(dict(METADATA_RECEIPT)), METADATA_RECEIPT)
        for field, value in (
            ("temporal_coverage_status", "verified"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
            ("station_id", "99999"),
        ):
            with self.subTest(field=field), self.assertRaises(ResultError):
                validate_dwd_metadata_receipt(dict(METADATA_RECEIPT, **{field: value}))

        forged_family = dict(METADATA_RECEIPT)
        forged_family["metadata_members"] = [dict(item) for item in METADATA_RECEIPT["metadata_members"]]
        forged_family["metadata_members"][0]["path"] = "Metadaten_Parameter_00003.txt"
        with self.assertRaisesRegex(ResultError, "provider-native family"):
            validate_dwd_metadata_receipt(forged_family)

        forged_station = dict(METADATA_RECEIPT)
        forged_station["metadata_members"] = [dict(item) for item in METADATA_RECEIPT["metadata_members"]]
        forged_station["metadata_members"][0]["path"] = "Metadaten_Geraete_99999.txt"
        with self.assertRaisesRegex(ResultError, "station 00003"):
            validate_dwd_metadata_receipt(forged_station)

        schema = json.loads(METADATA_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["temporal_coverage_status"], {"const": "unverified"})

    def test_result_schema_and_builder_use_distinct_metadata_receipt_key(self) -> None:
        result = build_acquisition_result(
            METADATA_REQUEST,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
            started_at=STARTED,
            finished_at=FINISHED,
            receipt=dict(METADATA_RECEIPT),
        )
        self.assertEqual(result["action"], DWD_METADATA_RECEIPT_ACTION)
        self.assertEqual(result["phase"], "acquisition_receipt")
        self.assertEqual(result["evidence"]["dwd_metadata_receipt"], METADATA_RECEIPT)
        self.assertNotIn("acquisition_receipt", result["evidence"])

        schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        self.assertIn(DWD_METADATA_RECEIPT_ACTION, schema["properties"]["action"]["enum"])
        self.assertIn("dwdMetadataReceipt", schema["$defs"])

    def test_dispatcher_runs_metadata_only_after_dedup_and_reuses_blocked_attempt(self) -> None:
        calls: list[str] = []

        def metadata_acquirer() -> dict[str, object]:
            calls.append("metadata")
            return dict(METADATA_RECEIPT)

        def measurement_acquirer() -> dict[str, object]:
            raise AssertionError("measurement worker must not be called for metadata action")

        result = prepare_completed_result(
            METADATA_REQUEST,
            [],
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=100,
            run_id=200,
            run_attempt=1,
            started_at=STARTED,
            acquirer=measurement_acquirer,
            metadata_acquirer=metadata_acquirer,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(calls, ["metadata"])

        comments = [{"id": 999, "body": canonical_result_comment(result), "user": {"login": "github-actions[bot]"}}]
        duplicate = prepare_completed_result(
            METADATA_REQUEST,
            comments,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=101,
            run_id=201,
            run_attempt=1,
            started_at=STARTED,
            acquirer=measurement_acquirer,
            metadata_acquirer=metadata_acquirer,
        )
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(calls, ["metadata"])

        blocked = build_acquisition_result(
            METADATA_REQUEST,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=102,
            run_id=202,
            run_attempt=1,
            started_at=STARTED,
            finished_at=FINISHED,
            receipt=None,
        )
        blocked_comments = [{"id": 1000, "body": canonical_result_comment(blocked), "user": {"login": "github-actions[bot]"}}]
        duplicate_after_block = prepare_completed_result(
            METADATA_REQUEST,
            blocked_comments,
            repository=REPOSITORY,
            execution_sha=EXECUTION_SHA,
            source_comment_id=103,
            run_id=203,
            run_attempt=1,
            started_at=STARTED,
            metadata_acquirer=metadata_acquirer,
        )
        self.assertEqual(duplicate_after_block["status"], "duplicate")
        self.assertEqual(calls, ["metadata"])


if __name__ == "__main__":
    unittest.main()
