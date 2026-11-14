# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed offline regression for the exact Spanish MITECO IOL download route."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.structured_public_views import render_structured_markdown
from scripts.validate_source_access import SourceAccessError, validate_contract, validate_path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access/es.miteco.snczi.longitudinal-defence-works.2026.json"
VIEW = CONTRACT.with_suffix(".md")
SOURCE_ID = "es.miteco.snczi.longitudinal-defence-works.2026"


class MitecoIolT0ContractTests(unittest.TestCase):
    def test_official_product_exact_route_and_no_probe(self) -> None:
        record = validate_path(CONTRACT)
        self.assertEqual(record["source_ids"], [SOURCE_ID])
        self.assertEqual(record["interface_type"], "http_file")
        self.assertEqual(record["status"], "documented_only")
        self.assertEqual(record["service_root"], "https://www.mapama.gob.es")
        self.assertEqual(record["request_contract"]["path_templates"], ["/app/descargas/descargafichero.aspx"])
        self.assertIn("f=iol.zip", record["request_contract"]["parameter_rules"])
        self.assertEqual(record["probe_contract"]["mode"], "none")
        self.assertEqual(record["implementation_decision"], "document_only")

    def test_rights_and_science_not_implicitly_admitted(self) -> None:
        record = validate_path(CONTRACT)
        rights = record["rights_and_policy"]
        self.assertEqual(rights["dataset_rights_status"], "not_reviewed")
        self.assertEqual(rights["api_terms_status"], "separate_unreviewed")
        self.assertEqual(rights["commercial_automation_status"], "unknown")
        self.assertEqual(rights["redistribution_status"], "unknown")
        self.assertIn("bank-stabilization", record["response_contract"]["scientific_semantics"])
        self.assertEqual(record["probe_contract"]["expected_evidence"], [])

    def test_reject_premature_live_probe(self) -> None:
        record = copy.deepcopy(validate_path(CONTRACT))
        record["status"] = "probe_ready"
        record["probe_contract"]["mode"] = "metadata_get"
        record["probe_contract"]["operation"] = "download_fixed_iol_zip"
        with self.assertRaises(SourceAccessError):
            validate_contract(record)

    def test_generated_projection_matches_canonical(self) -> None:
        record = validate_path(CONTRACT)
        self.assertEqual(VIEW.read_text(encoding="utf-8"), render_structured_markdown(CONTRACT, record, kind="access"))


if __name__ == "__main__":
    unittest.main()
