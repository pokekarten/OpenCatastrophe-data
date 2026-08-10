# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.dresden_acquisition_evidence import (
    AcquisitionEvidenceError,
    ExternalArtifactFile,
    acquisition_evidence_sha256,
    canonical_evidence_bytes,
    fingerprint_external_file,
    metadata_resolution_evidence,
    target_acquisition_evidence,
    validate_artifact_descriptor,
    validate_metadata_resolution_evidence,
    validate_target_acquisition_evidence,
)
from scripts.dresden_acquisition_intent import (
    PEGELONLINE_STATION_NUMBER,
    PEGELONLINE_STATION_UUID,
    finalize_acquisition_intent,
)
from scripts.hydrology_grid_matching import DRESDEN_DRAINAGE_AREA_KM2, GlofasGridCell
from scripts.validate_manifest import load_manifest, validate_structure

ROOT = Path(__file__).resolve().parents[1]


def _descriptor(name: str, payload: bytes | None = None) -> dict[str, object]:
    body = payload if payload is not None else f"evidence:{name}".encode("utf-8")
    return {
        "byte_size": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "storage_reference": f"external://dresden-evidence/{name}.json",
    }


def _external_file(
    root: Path,
    name: str,
    *,
    payload: bytes | None = None,
    storage_reference: str | None = None,
) -> ExternalArtifactFile:
    body = payload if payload is not None else f"evidence:{name}".encode("utf-8")
    path = root / f"{name}.bin"
    path.write_bytes(body)
    return ExternalArtifactFile(
        path=path,
        storage_reference=storage_reference or f"external://dresden-evidence/{name}.bin",
    )


class DresdenAcquisitionEvidenceTests(unittest.TestCase):
    def _candidate_cells(self) -> list[GlofasGridCell]:
        return [
            GlofasGridCell(51.06, 13.74, DRESDEN_DRAINAGE_AREA_KM2 * 1.01),
            GlofasGridCell(51.10, 13.74, DRESDEN_DRAINAGE_AREA_KM2 * 1.02),
        ]

    def _finalized_intent(
        self,
        candidates: list[GlofasGridCell] | None = None,
    ) -> dict[str, object]:
        return finalize_acquisition_intent(
            pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
            pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
            pegelonline_equidistance_minutes=15,
            station_latitude=51.05,
            station_longitude=13.74,
            glofas_candidate_cells=candidates or self._candidate_cells(),
        )

    def _metadata_evidence(self, finalized: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            return metadata_resolution_evidence(
                finalized_intent=finalized,
                resolved_at="2026-08-10T14:00:00Z",
                glofas_candidate_cells=self._candidate_cells(),
                pegelonline_metadata_request=_external_file(root, "pegel-metadata-request"),
                pegelonline_metadata_response=_external_file(root, "pegel-metadata-response"),
                glofas_upstream_area_request=_external_file(root, "glofas-area-request"),
                glofas_upstream_area_response=_external_file(root, "glofas-area-response"),
            )

    def _target_evidence(
        self,
        finalized: dict[str, object],
        metadata: dict[str, object],
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            return target_acquisition_evidence(
                finalized_intent=finalized,
                metadata_evidence=metadata,
                pegelonline_retrieved_at="2026-08-10T14:10:00Z",
                pegelonline_request_artifact=_external_file(root, "pegel-q-request"),
                pegelonline_data_artifact=_external_file(root, "pegel-q-data"),
                glofas_retrieved_at="2026-08-10T14:20:00Z",
                glofas_request_artifact=_external_file(root, "glofas-dis24-request"),
                glofas_data_artifact=_external_file(root, "glofas-dis24-data"),
            )

    def test_fingerprint_derives_exact_manifest_compatible_identity_from_bytes(self) -> None:
        payload = b"exact external provider bytes\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "artifact.bin"
            path.write_bytes(payload)
            descriptor = fingerprint_external_file(
                path,
                storage_reference="external://dresden-evidence/provider/artifact.bin",
            )
        self.assertEqual(descriptor["byte_size"], len(payload))
        self.assertEqual(descriptor["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertIs(validate_artifact_descriptor(descriptor), descriptor)

    def test_fingerprint_rejects_empty_and_symlink_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            empty = root / "empty.bin"
            empty.write_bytes(b"")
            with self.assertRaisesRegex(AcquisitionEvidenceError, "must not be empty"):
                fingerprint_external_file(empty, storage_reference="external://dresden-evidence/empty.bin")

            target = root / "target.bin"
            target.write_bytes(b"provider bytes")
            link = root / "link.bin"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable in this environment")
            with self.assertRaisesRegex(AcquisitionEvidenceError, "non-symlink"):
                fingerprint_external_file(link, storage_reference="external://dresden-evidence/link.bin")

    def test_fingerprint_binds_open_file_descriptor_to_preopen_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "artifact.bin"
            path.write_bytes(b"stable bytes")
            actual = path.stat()
            replaced = SimpleNamespace(
                st_dev=actual.st_dev,
                st_ino=actual.st_ino + 1,
                st_size=actual.st_size,
                st_mtime_ns=actual.st_mtime_ns,
                st_mode=actual.st_mode,
            )
            with patch("scripts.dresden_acquisition_evidence.os.fstat", return_value=replaced):
                with self.assertRaisesRegex(AcquisitionEvidenceError, "opened safely"):
                    fingerprint_external_file(
                        path,
                        storage_reference="external://dresden-evidence/replaced.bin",
                    )

    def test_artifact_descriptor_is_closed_and_type_strict(self) -> None:
        base = _descriptor("strict")
        for mutation in (
            {**base, "byte_size": True},
            {**base, "byte_size": 0},
            {**base, "sha256": "A" * 64},
            {**base, "storage_reference": "../local.bin"},
            {**base, "unexpected": "field"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(AcquisitionEvidenceError):
                validate_artifact_descriptor(mutation)

    def test_authoritative_builder_rejects_fabricated_descriptor_dicts(self) -> None:
        finalized = self._finalized_intent()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(AcquisitionEvidenceError, "ExternalArtifactFile"):
                metadata_resolution_evidence(
                    finalized_intent=finalized,
                    resolved_at="2026-08-10T14:00:00Z",
                    glofas_candidate_cells=self._candidate_cells(),
                    pegelonline_metadata_request=_descriptor("fabricated"),  # type: ignore[arg-type]
                    pegelonline_metadata_response=_external_file(root, "pegel-metadata-response"),
                    glofas_upstream_area_request=_external_file(root, "glofas-area-request"),
                    glofas_upstream_area_response=_external_file(root, "glofas-area-response"),
                )

    def test_metadata_evidence_binds_full_candidate_set_and_intents(self) -> None:
        finalized = self._finalized_intent()
        evidence = self._metadata_evidence(finalized)
        self.assertEqual(evidence["profile_version"], "2.0.0")
        self.assertEqual(evidence["evidence_type"], "dresden_metadata_resolution")
        self.assertEqual(evidence["resolved_metadata"], finalized["metadata_resolution"])
        self.assertEqual(len(evidence["glofas_candidate_cells"]), 2)
        self.assertEqual(len(evidence["initial_intent_sha256"]), 64)
        self.assertEqual(len(evidence["finalized_intent_sha256"]), 64)
        self.assertIs(
            validate_metadata_resolution_evidence(evidence, finalized_intent=finalized),
            evidence,
        )
        self.assertEqual(
            acquisition_evidence_sha256(evidence),
            hashlib.sha256(canonical_evidence_bytes(evidence)).hexdigest(),
        )

    def test_complete_candidate_set_must_reproduce_selected_winner(self) -> None:
        candidates = self._candidate_cells()
        finalized_from_worse_only = self._finalized_intent([candidates[1]])
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(AcquisitionEvidenceError, "does not reproduce"):
                metadata_resolution_evidence(
                    finalized_intent=finalized_from_worse_only,
                    resolved_at="2026-08-10T14:00:00Z",
                    glofas_candidate_cells=candidates,
                    pegelonline_metadata_request=_external_file(root, "pegel-metadata-request"),
                    pegelonline_metadata_response=_external_file(root, "pegel-metadata-response"),
                    glofas_upstream_area_request=_external_file(root, "glofas-area-request"),
                    glofas_upstream_area_response=_external_file(root, "glofas-area-response"),
                )

    def test_candidate_set_is_canonicalized_and_revalidated_from_serialized_evidence(self) -> None:
        finalized = self._finalized_intent()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence = metadata_resolution_evidence(
                finalized_intent=finalized,
                resolved_at="2026-08-10T14:00:00Z",
                glofas_candidate_cells=list(reversed(self._candidate_cells())),
                pegelonline_metadata_request=_external_file(root, "pegel-metadata-request"),
                pegelonline_metadata_response=_external_file(root, "pegel-metadata-response"),
                glofas_upstream_area_request=_external_file(root, "glofas-area-request"),
                glofas_upstream_area_response=_external_file(root, "glofas-area-response"),
            )
        records = evidence["glofas_candidate_cells"]
        self.assertEqual(
            records,
            sorted(
                records,
                key=lambda item: (item["latitude"], item["longitude"], item["upstream_area_km2"]),
            ),
        )

        tampered = copy.deepcopy(evidence)
        tampered["glofas_candidate_cells"] = [records[1]]
        with self.assertRaisesRegex(AcquisitionEvidenceError, "does not reproduce"):
            validate_metadata_resolution_evidence(tampered, finalized_intent=finalized)

    def test_metadata_artifacts_require_unique_references_and_content_identities(self) -> None:
        finalized = self._finalized_intent()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            duplicate_payload = b"same exact bytes"
            with self.assertRaisesRegex(AcquisitionEvidenceError, "byte-content identities"):
                metadata_resolution_evidence(
                    finalized_intent=finalized,
                    resolved_at="2026-08-10T14:00:00Z",
                    glofas_candidate_cells=self._candidate_cells(),
                    pegelonline_metadata_request=_external_file(
                        root, "request-a", payload=duplicate_payload
                    ),
                    pegelonline_metadata_response=_external_file(
                        root, "response-b", payload=duplicate_payload
                    ),
                    glofas_upstream_area_request=_external_file(root, "glofas-area-request"),
                    glofas_upstream_area_response=_external_file(root, "glofas-area-response"),
                )

    def test_target_evidence_binds_metadata_and_emits_exact_manifest_candidates(self) -> None:
        finalized = self._finalized_intent()
        metadata = self._metadata_evidence(finalized)
        evidence = self._target_evidence(finalized, metadata)
        self.assertEqual(evidence["profile_version"], "2.0.0")
        self.assertEqual(evidence["evidence_type"], "dresden_target_acquisition")
        pegel_data = evidence["retrievals"]["pegelonline_q"]["data_artifact"]
        glofas_data = evidence["retrievals"]["glofas_dis24"]["data_artifact"]
        self.assertEqual(
            evidence["manifest_raw_artifact_candidates"],
            [
                {
                    "manifest": "manifests/wsv.pegelonline.elbe-dresden-discharge.2020-2023.json",
                    "raw_artifact": pegel_data,
                },
                {
                    "manifest": "manifests/copernicus.cems.glofas-historical.json",
                    "raw_artifact": glofas_data,
                },
            ],
        )
        self.assertIs(
            validate_target_acquisition_evidence(
                evidence,
                finalized_intent=finalized,
                metadata_evidence=metadata,
            ),
            evidence,
        )

    def test_target_builder_rejects_fabricated_descriptor_dicts(self) -> None:
        finalized = self._finalized_intent()
        metadata = self._metadata_evidence(finalized)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(AcquisitionEvidenceError, "ExternalArtifactFile"):
                target_acquisition_evidence(
                    finalized_intent=finalized,
                    metadata_evidence=metadata,
                    pegelonline_retrieved_at="2026-08-10T14:10:00Z",
                    pegelonline_request_artifact=_descriptor("fake-request"),  # type: ignore[arg-type]
                    pegelonline_data_artifact=_external_file(root, "pegel-data"),
                    glofas_retrieved_at="2026-08-10T14:20:00Z",
                    glofas_request_artifact=_external_file(root, "glofas-request"),
                    glofas_data_artifact=_external_file(root, "glofas-data"),
                )

    def test_target_retrieval_must_follow_metadata_resolution(self) -> None:
        finalized = self._finalized_intent()
        metadata = self._metadata_evidence(finalized)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(AcquisitionEvidenceError, "predates metadata resolution"):
                target_acquisition_evidence(
                    finalized_intent=finalized,
                    metadata_evidence=metadata,
                    pegelonline_retrieved_at="2026-08-10T13:59:59Z",
                    pegelonline_request_artifact=_external_file(root, "early-pegel-request"),
                    pegelonline_data_artifact=_external_file(root, "early-pegel-data"),
                    glofas_retrieved_at="2026-08-10T14:20:00Z",
                    glofas_request_artifact=_external_file(root, "early-glofas-request"),
                    glofas_data_artifact=_external_file(root, "early-glofas-data"),
                )

    def test_target_artifacts_cannot_reuse_metadata_reference(self) -> None:
        finalized = self._finalized_intent()
        metadata = self._metadata_evidence(finalized)
        metadata_artifact = metadata["artifacts"]["pegelonline_metadata_request"]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reused_reference = _external_file(
                root,
                "target-request",
                storage_reference=metadata_artifact["storage_reference"],
            )
            with self.assertRaisesRegex(AcquisitionEvidenceError, "unique external storage"):
                target_acquisition_evidence(
                    finalized_intent=finalized,
                    metadata_evidence=metadata,
                    pegelonline_retrieved_at="2026-08-10T14:10:00Z",
                    pegelonline_request_artifact=reused_reference,
                    pegelonline_data_artifact=_external_file(root, "unique-pegel-data"),
                    glofas_retrieved_at="2026-08-10T14:20:00Z",
                    glofas_request_artifact=_external_file(root, "unique-glofas-request"),
                    glofas_data_artifact=_external_file(root, "unique-glofas-data"),
                )

    def test_manifest_candidates_are_structurally_compatible_but_do_not_bypass_review(self) -> None:
        finalized = self._finalized_intent()
        metadata = self._metadata_evidence(finalized)
        evidence = self._target_evidence(finalized, metadata)
        candidate = evidence["manifest_raw_artifact_candidates"][0]
        manifest_path = ROOT / candidate["manifest"]
        manifest = load_manifest(manifest_path)
        manifest["raw_artifact"] = candidate["raw_artifact"]
        validate_structure(manifest)
        self.assertEqual(manifest["review"]["status"], "approved_metadata_only")

        with tempfile.TemporaryDirectory() as temp_dir:
            staged = Path(temp_dir) / "candidate.json"
            staged.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_manifest.py"),
                    str(staged),
                    "--public-asset",
                    "raw",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review", (result.stdout + result.stderr).lower())

    def test_canonical_evidence_rejects_non_json_numbers(self) -> None:
        with self.assertRaisesRegex(AcquisitionEvidenceError, "canonical JSON"):
            canonical_evidence_bytes({"bad": float("nan")})


if __name__ == "__main__":
    unittest.main()
