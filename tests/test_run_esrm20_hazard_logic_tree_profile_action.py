# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from unittest import mock

from scripts import run_esrm20_hazard_logic_tree_profile_action as subject

EXECUTION_SHA = "1" * 40


def request_body(*, sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True, separators=(",", ":"))


def source_xml() -> str:
    return """<nrml xmlns=\"http://openquake.org/xmlns/nrml/0.5\">
  <logicTree logicTreeID=\"source-lt\">
    <logicTreeBranchSet branchSetID=\"bs1\" uncertaintyType=\"sourceModel\">
      <logicTreeBranch branchID=\"b1\">
        <uncertaintyModel>../Sources/model.xml</uncertaintyModel>
        <uncertaintyWeight>1.0</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>"""


def gsim_xml() -> str:
    return """<nrml xmlns=\"http://openquake.org/xmlns/nrml/0.5\">
  <logicTree logicTreeID=\"gmpe-lt\">
    <logicTreeBranchSet branchSetID=\"g1\" uncertaintyType=\"gmpeModel\" applyToTectonicRegionType=\"Active Shallow Crust\">
      <logicTreeBranch branchID=\"g1b1\">
        <uncertaintyModel>[GMPETable]
gmpe_table = \"table.hdf5\"</uncertaintyModel>
        <uncertaintyWeight>0.5</uncertaintyWeight>
      </logicTreeBranch>
      <logicTreeBranch branchID=\"g1b2\">
        <uncertaintyModel>BooreAtkinson2008</uncertaintyModel>
        <uncertaintyWeight>0.5</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
  </logicTree>
</nrml>"""


class HazardLogicTreeProfileActionTests(unittest.TestCase):
    def test_request_is_exact_main_bound_and_has_no_provider_selector(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=481, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for forbidden in ("path", "url", "project_id", "parser", "inventory"):
            self.assertNotIn(forbidden, parsed)
        with self.assertRaisesRegex(subject.HazardLogicTreeProfileActionError, "target_sha"):
            subject.validate_request(
                request_body(sha="2" * 40), expected_issue=481, execution_sha=EXECUTION_SHA
            )

    def test_pure_profile_derives_source_path_and_gsim_key_names_without_values(self) -> None:
        profile = subject._derive_profile(
            gsim_xml_text=gsim_xml(), source_xml_text=source_xml()
        )
        self.assertEqual(profile["source_tree"]["dependency_count"], 1)
        self.assertEqual(
            profile["source_tree"]["dependencies"][0]["resolved_path"],
            "Sources/model.xml",
        )
        self.assertEqual(
            profile["source_tree"]["dependencies"][0]["origins"],
            [{"uncertainty_type": "sourceModel", "branch_id": "b1"}],
        )
        self.assertEqual(profile["gsim_tree"]["branch_set_count"], 1)
        self.assertEqual(profile["gsim_tree"]["branch_count"], 2)
        self.assertEqual(
            profile["gsim_tree"]["unique_requested_gsim_tokens"],
            ["BooreAtkinson2008", "GMPETable"],
        )
        self.assertEqual(profile["gsim_tree"]["unique_argument_keys"], ["gmpe_table"])
        self.assertEqual(
            profile["gsim_tree"]["external_resource_argument_keys"], ["gmpe_table"]
        )
        self.assertFalse(profile["gsim_tree"]["argument_values_returned"])
        self.assertFalse(profile["raw_xml_returned"])
        rendered = json.dumps(profile, sort_keys=True)
        self.assertNotIn("table.hdf5", rendered)
        subject._validate_profile(profile)

    def test_source_hdf5_companion_cannot_appear_without_explicit_inventory(self) -> None:
        profile = subject._derive_profile(
            gsim_xml_text=gsim_xml(), source_xml_text=source_xml()
        )
        mutated = copy.deepcopy(profile)
        mutated["source_tree"]["dependencies"].append(
            {
                "resolved_path": "Sources/model.hdf5",
                "is_hdf5_companion": True,
                "origins": [{"uncertainty_type": "sourceModel", "branch_id": "b1"}],
            }
        )
        mutated["source_tree"]["dependency_count"] = 2
        with self.assertRaisesRegex(subject.HazardLogicTreeProfileActionError, "HDF5"):
            subject._validate_profile(mutated)

    def test_durable_gsim_profile_rejects_argument_values_and_unknown_keys(self) -> None:
        profile = subject._derive_profile(
            gsim_xml_text=gsim_xml(), source_xml_text=source_xml()
        )
        mutated = copy.deepcopy(profile)
        mutated["gsim_tree"]["argument_values"] = {"gmpe_table": "secret.hdf5"}
        with self.assertRaisesRegex(subject.HazardLogicTreeProfileActionError, "fields drifted"):
            subject._validate_profile(mutated)

        mutated = copy.deepcopy(profile)
        mutated["gsim_tree"]["external_resource_argument_keys"] = ["not_a_resource"]
        with self.assertRaisesRegex(subject.HazardLogicTreeProfileActionError, "durable sets"):
            subject._validate_profile(mutated)

    def test_run_profile_closes_only_byte_and_content_gates(self) -> None:
        profile = subject._derive_profile(
            gsim_xml_text=gsim_xml(), source_xml_text=source_xml()
        )
        with mock.patch.object(subject, "acquire_and_profile", return_value=profile):
            result = subject.run_profile(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["content_profile_verified"])
        self.assertFalse(result["transitive_dependency_byte_closure_verified"])
        self.assertFalse(result["runtime_compatibility_verified"])
        self.assertFalse(result["model_use_authorized"])

    def test_profile_failure_is_atomic(self) -> None:
        with mock.patch.object(
            subject,
            "acquire_and_profile",
            side_effect=subject.HazardLogicTreeProfileActionError("provider detail"),
        ):
            result = subject.run_profile(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profile"])
        self.assertFalse(result["byte_identity_verified"])
        self.assertFalse(result["content_profile_verified"])
        self.assertNotIn("provider detail", json.dumps(result))

    def test_trusted_pass_rejects_authority_widening(self) -> None:
        profile = subject._derive_profile(
            gsim_xml_text=gsim_xml(), source_xml_text=source_xml()
        )
        with mock.patch.object(subject, "acquire_and_profile", return_value=profile):
            result = subject.run_profile(execution_sha=EXECUTION_SHA)
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA))

        mutated = copy.deepcopy(result)
        mutated["runtime_compatibility_verified"] = True
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            mutated, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(subject.HazardLogicTreeProfileActionError, "runtime_compatibility_verified"):
            subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
