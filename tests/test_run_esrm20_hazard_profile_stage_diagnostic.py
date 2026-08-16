# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_hazard_profile_stage_diagnostic as subject

EXECUTION_SHA = "1" * 40


def request_body() -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": EXECUTION_SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True, separators=(",", ":"))


class HazardProfileStageDiagnosticTests(unittest.TestCase):
    def test_request_has_no_provider_or_parser_selector(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=481, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for forbidden in ("path", "url", "project_id", "parser", "xml"):
            self.assertNotIn(forbidden, parsed)

    def test_pure_diagnostic_reports_both_parser_stages_without_content(self) -> None:
        source_xml = """<nrml xmlns=\"http://openquake.org/xmlns/nrml/0.5\"><logicTree logicTreeID=\"s\"><logicTreeBranchSet branchSetID=\"bs\" uncertaintyType=\"sourceModel\"><logicTreeBranch branchID=\"b\"><uncertaintyModel>../Sources/model.xml</uncertaintyModel><uncertaintyWeight>1</uncertaintyWeight></logicTreeBranch></logicTreeBranchSet></logicTree></nrml>"""
        gsim_xml = """<nrml xmlns=\"http://openquake.org/xmlns/nrml/0.5\"><logicTree logicTreeID=\"g\"><logicTreeBranchSet branchSetID=\"gbs\" uncertaintyType=\"gmpeModel\"><logicTreeBranch branchID=\"gb\"><uncertaintyModel>BooreAtkinson2008</uncertaintyModel><uncertaintyWeight>1</uncertaintyWeight></logicTreeBranch></logicTreeBranchSet></logicTree></nrml>"""
        result = subject.diagnose_texts(source_text=source_xml, gsim_text=gsim_xml)
        self.assertTrue(result["source_parser_pass"])
        self.assertTrue(result["gsim_parser_pass"])
        self.assertFalse(result["provider_content_returned"])
        self.assertFalse(result["parser_error_text_returned"])
        self.assertNotIn("model.xml", json.dumps(result))
        self.assertNotIn("BooreAtkinson2008", json.dumps(result))

    def test_source_and_gsim_failures_are_distinguished(self) -> None:
        with mock.patch.object(
            subject,
            "extract_source_model_logic_tree_dependencies",
            side_effect=subject.OpenQuakeLogicTreeError("secret source content"),
        ), mock.patch.object(
            subject.gsim_identity,
            "_profile_xml_text",
            return_value={"unique_requested_gsim_tokens": ["Synthetic"]},
        ):
            result = subject.diagnose_texts(source_text="x", gsim_text="y")
        self.assertFalse(result["source_parser_pass"])
        self.assertTrue(result["gsim_parser_pass"])
        self.assertNotIn("secret", json.dumps(result))

        with mock.patch.object(
            subject,
            "extract_source_model_logic_tree_dependencies",
            return_value=[object()],
        ), mock.patch.object(
            subject.gsim_identity,
            "_profile_xml_text",
            side_effect=subject.gsim_identity.Eshm20GsimIdentityProfileError("secret gsim content"),
        ):
            result = subject.diagnose_texts(source_text="x", gsim_text="y")
        self.assertTrue(result["source_parser_pass"])
        self.assertFalse(result["gsim_parser_pass"])
        self.assertNotIn("secret", json.dumps(result))

    def test_run_diagnostic_publishes_only_stage_status(self) -> None:
        fake_bytes = b"<nrml/>"
        with mock.patch.object(subject.subject, "_acquire_exact_bytes", return_value=fake_bytes), mock.patch.object(
            subject, "diagnose_texts", return_value={
                "source_parser_pass": True,
                "gsim_parser_pass": False,
                "source_parser": "source-parser",
                "gsim_parser": "gsim-parser",
                "provider_content_returned": False,
                "parser_error_text_returned": False,
            }
        ):
            result = subject.run_diagnostic(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["failure_class"], "gsim_parser_failure")
        self.assertFalse(result["diagnostic"]["provider_content_returned"])
        self.assertFalse(result["diagnostic"]["parser_error_text_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])


if __name__ == "__main__":
    unittest.main()
