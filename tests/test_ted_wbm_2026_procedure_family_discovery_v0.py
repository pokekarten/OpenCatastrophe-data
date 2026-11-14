# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline TED exact-procedure family search bounds and no-insurer attribution."""
from __future__ import annotations

import io
import json
import unittest

from research_runners import ted_wbm_2026_procedure_family_discovery_v0 as m

EARLY = "7df98c35-4cae-41ff-8385-141125426a4a"
LATE = "0988b2e4-9489-4b3b-9487-cd3a2a624cf5"
KNOWN = {"competition": EARLY, "award": LATE}


def fixture(procedure=LATE, *, pubs=("668506-2026",), rows=None, total=None):
    if rows is None:
        rows = [{
            "publication-number": pub,
            "procedure-identifier": procedure,
            "buyer-name": {"de": ["WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"]},
            "notice-title": {"de": ["Industrielle Sachversicherung"]},
            "publication-date": "2026-09-29",
        } for pub in pubs]
    if total is None:
        total = len(rows)
    return json.dumps({"totalNoticeCount": total, "notices": rows,
                       "fixture_padding": "bounded offline source shape"},
                      ensure_ascii=False).encode("utf-8")


class Response:
    def __init__(self, raw, *, status=200, url=m.api.ENDPOINT):
        self.raw = io.BytesIO(raw)
        self.url = url
        self.status = status
    def geturl(self):
        return self.url
    def read(self, count):
        return self.raw.read(count)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class WBMProcedureFamilyDiscoveryTests(unittest.TestCase):
    def parse(self, raw, proc=LATE):
        return m.parse(proc, raw, known=KNOWN)

    def test_allowlist_comes_from_saved_official_research_receipt(self):
        self.assertEqual(m.known_procedures(), KNOWN)

    def test_exact_uuid_search_limit_page_and_real_execution(self):
        q = json.loads(m.query_body(LATE, known=KNOWN))
        self.assertEqual(q["query"], "procedure-identifier = " + LATE)
        self.assertEqual(q["limit"], 25)
        self.assertEqual(q["page"], 1)
        self.assertEqual(q["fields"][1], "procedure-identifier")
        self.assertFalse(q["checkQuerySyntax"])
        self.assertFalse(q["onlyLatestVersions"])

    def test_unapproved_uuid_cannot_open_broad_search(self):
        with self.assertRaisesRegex(ValueError, "PROCEDURE_NOT_ALLOWLISTED"):
            m.query_body("1e86a664-ae3c-41eb-8529-0242ac130003", known=KNOWN)

    def test_single_known_award_yields_no_claim_of_prior_notice(self):
        r = self.parse(fixture())
        self.assertEqual(r["matching_index_notice_count"], 1)
        self.assertEqual(r["indexed_notices"][0]["publication_number"], "668506-2026")
        self.assertFalse(r["index_candidates_prove_original_predecessor_link"])
        self.assertFalse(r["real_geolocated_insurer_CAT_exposure_admitted"])

    def test_additional_notice_same_bt04_is_source_candidate_only(self):
        r = self.parse(fixture(pubs=("668506-2026", "123456-2026")))
        self.assertEqual(r["matching_index_notice_count"], 2)
        self.assertIn("123456-2026", [x["publication_number"] for x in r["indexed_notices"]])
        self.assertFalse(r["source_xml_bytes_verified_during_this_index_query"])
        self.assertFalse(r["index_candidates_prove_original_predecessor_link"])

    def test_other_family_sibling_does_not_establish_september_link(self):
        r = self.parse(fixture(EARLY, pubs=("286307-2026",)),
                       proc=EARLY)
        self.assertEqual(r["procedure_uuid_index_query"], EARLY)
        self.assertNotEqual(r["procedure_uuid_index_query"], LATE)

    def test_bad_procedure_in_one_row_cannot_join_to_family(self):
        data = json.loads(fixture())
        data["notices"][0]["procedure-identifier"] = EARLY
        with self.assertRaisesRegex(ValueError, "RESPONSE_PROCEDURE_MISMATCH"):
            self.parse(json.dumps(data).encode("utf-8"))

    def test_duplicate_publication_refused(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PUBLICATION"):
            self.parse(fixture(pubs=("668506-2026","668506-2026")))

    def test_more_than_page_limit_requires_explicit_pagination(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_RESULTS_NOT_EXHAUSTIVE"):
            self.parse(fixture(total=26))

    def test_misreported_total_count_blocks(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_RESULTS_NOT_EXHAUSTIVE"):
            self.parse(fixture(total=2))

    def test_zero_count_is_unknown_not_proof_no_procedure(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_RESULTS_NOT_EXHAUSTIVE"):
            self.parse(fixture(rows=[],total=0))

    def test_missing_procedure_field_rejected(self):
        data = json.loads(fixture())
        data["notices"][0].pop("procedure-identifier")
        with self.assertRaises(ValueError):
            self.parse(json.dumps(data).encode())

    def test_wrong_buyer_refused(self):
        data = json.loads(fixture())
        data["notices"][0]["buyer-name"] = "Unrelated company"
        with self.assertRaisesRegex(ValueError, "OTHER_BUYER"):
            self.parse(json.dumps(data).encode())

    def test_missing_title_not_linked(self):
        data = json.loads(fixture())
        data["notices"][0].pop("notice-title")
        with self.assertRaisesRegex(ValueError, "MISSING_OR_OVERSIZED_TITLE"):
            self.parse(json.dumps(data).encode())

    def test_duplicate_json_keys_refused(self):
        data = fixture()
        data = data.replace(b'"notices":', b'"notices":[],"notices":', 1)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            self.parse(data)

    def test_oversized_json_response_refused(self):
        with self.assertRaisesRegex(ValueError, "RESPONSE_NOT_BOUNDED"):
            m.fetch(LATE, known=KNOWN, opener=lambda req, timeout:
                    Response(b"x"*(m.api.MAX_BYTES + 1)))

    def test_other_host_redirect_refused(self):
        with self.assertRaisesRegex(ValueError, "NONOFFICIAL_RESPONSE_URL"):
            m.fetch(LATE, known=KNOWN, opener=lambda req, timeout:
                    Response(fixture(), url="https://untrusted.example/procedure"))

    def test_http202_refused_as_source_json(self):
        with self.assertRaisesRegex(ValueError, "HTTP_NON200_202"):
            m.fetch(LATE, known=KNOWN, opener=lambda req, timeout:
                    Response(fixture(), status=202))

    def test_valid_exact_official_api_transport(self):
        raw = fixture()
        self.assertEqual(m.fetch(LATE, known=KNOWN, opener=lambda req, timeout:
                                 Response(raw)), raw)

    def test_receipt_cannot_claim_source_xml(self):
        receipt = {
            "schema_version": "WBM_2026_TED_OFFICIAL_SEARCH_BT04_LINEAGE_OBSERVATION_V0",
            "api_payload_is_original_eforms_xml": True,
            "indexed_procedure_ids_identical": False,
            "exact_original_xml_pair_rechecked_this_run": False,
        }
        with self.assertRaisesRegex(ValueError, "SOURCE_RECEIPT_NOT_RESEARCH_ONLY"):
            m.known_procedures(receipt=receipt)

    def test_unnamed_sibling_never_automatically_real_insured_property(self):
        r = self.parse(fixture(pubs=("668506-2026","123456-2026")))
        self.assertFalse(r["current_signed_insurer_cover_or_50_40_10_policy_shares_proved"])
        self.assertFalse(r["real_geolocated_insurer_CAT_exposure_admitted"])
        self.assertFalse(r["raw_original_search_json_committed_or_printed"])


if __name__ == "__main__":
    unittest.main()
