# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
try:
    SPEC = importlib.util.spec_from_file_location(
        "audit_sample_candidates", SCRIPTS / "audit_sample_candidates.py"
    )
    assert SPEC and SPEC.loader
    sample_audit = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = sample_audit
    SPEC.loader.exec_module(sample_audit)
finally:
    sys.path.pop(0)

DWD = ROOT / "manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json"


class SampleCandidateAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dwd = sample_audit.load_manifest(DWD)

    def test_current_registry_is_audited_deterministically(self) -> None:
        first = sample_audit.audit_manifest_directory()
        second = sample_audit.audit_manifest_directory()
        self.assertEqual(first, second)
        expected_ids = sorted(path.stem for path in (ROOT / "manifests").glob("*.json"))
        self.assertEqual([result.dataset_id for result in first], expected_ids)

    def test_current_registry_has_exact_expected_sample_rights_classification(self) -> None:
        results = {
            result.dataset_id: result for result in sample_audit.audit_manifest_directory()
        }
        expected_eligible = {
            "copernicus.c3s.european-windstorm-reanalysis.v1.0",
            "copernicus.cems.gfm.v4.1.1",
            "copernicus.cems.glofas-historical",
            "copernicus.cems.on-demand-mapping",
            "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03",
            "efehr.eshm20",
            "efehr.esrm20.european-exposure-model.v1.0",
            "efehr.esrm20.vulnerability.v1.1",
            "google.open-buildings.v3",
            "microsoft.globalml-building-footprints",
            "storm.ibtracs.present-climate.v4",
            "wsv.pegelonline.elbe-dresden-discharge.2020-2023",
        }
        expected_blocked = {
            "eiopa.catastrophe-data-hub.exposure.2023-12-05",
            "eiopa.catastrophe-data-hub.historical-loss.2023-12-05",
        }
        actual_eligible = {
            dataset_id
            for dataset_id, result in results.items()
            if result.source_rights_eligible
        }
        actual_blocked = set(results) - actual_eligible
        self.assertEqual(actual_eligible, expected_eligible)
        self.assertEqual(actual_blocked, expected_blocked)

        for dataset_id in sorted(expected_eligible):
            with self.subTest(dataset_id=dataset_id):
                result = results[dataset_id]
                self.assertFalse(result.existing_raw_publication_ready)
                self.assertEqual(result.status, "eligible_for_asset_specific_sample_review")

        for dataset_id in sorted(expected_blocked):
            with self.subTest(dataset_id=dataset_id):
                result = results[dataset_id]
                self.assertFalse(result.source_rights_eligible)
                self.assertEqual(result.status, "blocked_by_source_contract")
                self.assertIn("raw_redistribution_not_in_scope", result.source_blockers)

    def test_current_metadata_only_registry_never_reports_existing_raw_publication_ready(self) -> None:
        for result in sample_audit.audit_manifest_directory():
            with self.subTest(dataset_id=result.dataset_id):
                self.assertFalse(result.existing_raw_publication_ready)
                self.assertIsNotNone(result.repository_publication_blocker)

    def test_source_contract_mutations_fail_closed(self) -> None:
        mutations = (
            ("licence", lambda payload: payload["licensing"].__setitem__("status", "unknown"), "licensing_not_verified"),
            ("commercial", lambda payload: payload["licensing"].__setitem__("commercial_use_status", "restricted"), "commercial_use_not_allowed"),
            ("redistribution", lambda payload: payload["redistribution"].__setitem__("status", "restricted"), "redistribution_not_allowed"),
            ("scope", lambda payload: payload["redistribution"].__setitem__("scope", "derived_only"), "raw_redistribution_not_in_scope"),
            ("personal", lambda payload: payload["privacy"].__setitem__("personal_data_status", "unknown"), "personal_data_not_clear"),
            ("confidential", lambda payload: payload["privacy"].__setitem__("confidential_or_proprietary_status", "contains"), "confidentiality_not_clear"),
            ("access", lambda payload: payload.__setitem__("access_class", "restricted"), "source_access_not_publicly_acquirable"),
        )
        for name, mutate, expected_blocker in mutations:
            payload = copy.deepcopy(self.dwd)
            mutate(payload)
            with self.subTest(name=name):
                result = sample_audit.audit_manifest(payload)
                self.assertFalse(result.source_rights_eligible)
                self.assertIn(expected_blocker, result.source_blockers)
                self.assertEqual(result.status, "blocked_by_source_contract")

    def test_source_blocker_dominates_even_if_repository_raw_gate_passes(self) -> None:
        payload = copy.deepcopy(self.dwd)
        payload["access_class"] = "restricted"
        payload["review"]["status"] = "approved_raw"
        payload["raw_artifact"] = {
            "byte_size": 12,
            "sha256": "0" * 64,
            "storage_reference": "external://sample-pilot/restricted/example.bin",
        }
        result = sample_audit.audit_manifest(payload)
        self.assertFalse(result.source_rights_eligible)
        self.assertIn("source_access_not_publicly_acquirable", result.source_blockers)
        self.assertFalse(result.existing_raw_publication_ready)
        self.assertEqual(result.status, "blocked_by_source_contract")
        self.assertEqual(
            result.repository_publication_blocker,
            "restricted source access blocks raw source-byte publication",
        )

    def test_repository_review_and_exact_artifact_identity_remain_separate_gates(self) -> None:
        current = sample_audit.audit_manifest(self.dwd)
        self.assertTrue(current.source_rights_eligible)
        self.assertFalse(current.existing_raw_publication_ready)
        self.assertIn("repository review scope", current.repository_publication_blocker or "")

        reviewed = copy.deepcopy(self.dwd)
        reviewed["review"]["status"] = "approved_raw"
        reviewed_without_artifact = sample_audit.audit_manifest(reviewed)
        self.assertTrue(reviewed_without_artifact.source_rights_eligible)
        self.assertFalse(reviewed_without_artifact.existing_raw_publication_ready)
        self.assertEqual(
            reviewed_without_artifact.repository_publication_blocker,
            "raw publication requires raw_artifact identity",
        )

        reviewed["raw_artifact"] = {
            "byte_size": 12,
            "sha256": "0" * 64,
            "storage_reference": "external://sample-pilot/dwd/example.bin",
        }
        ready = sample_audit.audit_manifest(reviewed)
        self.assertTrue(ready.source_rights_eligible)
        self.assertTrue(ready.existing_raw_publication_ready)
        self.assertEqual(ready.status, "existing_raw_publication_ready")
        self.assertIsNone(ready.repository_publication_blocker)

    def test_cli_json_is_sorted_and_machine_readable(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/audit_sample_candidates.py", "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        ids = [item["dataset_id"] for item in payload]
        self.assertEqual(ids, sorted(ids))
        self.assertTrue(all("status" in item for item in payload))

    def test_cli_fails_closed_for_empty_manifest_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/audit_sample_candidates.py",
                    "--manifest-dir",
                    tmp,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.startswith("BLOCKED:"), result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
