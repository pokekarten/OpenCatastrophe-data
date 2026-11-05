# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline strict TED Search API BT-04 fields, source classification and refusal."""
from __future__ import annotations

import io
import json
import unittest

from research_runners import ted_wbm_2026_procedure_search_index_v0 as m

PROCEDURE_1 = "1e86a664-ae3c-41eb-8529-0242ac130003"
PROCEDURE_2 = "ad45f0c6-5762-4380-8806-18f2315ef8fa"


def fixture(notice=m.NOTICES[0], *, procedure=PROCEDURE_1, previous=None,
            buyer="WBM Wohnungsbaugesellschaft Berlin-Mitte mbH",
            title="Industrielle Sachversicherung für reine Gewerbeobjekte",
            rows=None):
    if rows is None:
        row = {
            "publication-number": notice,
            "buyer-name": {"de": [buyer]},
            "notice-title": {"de": title},
            "procedure-identifier": [procedure],
        }
        if previous is not None:
            row["previous-notice-id-proc"] = previous
        rows = [row]
    return json.dumps({"totalNoticeCount": len(rows), "notices": rows},
                      ensure_ascii=False).encode("utf-8")


class Response:
    def __init__(self, raw: bytes, *, status=200, url=m.api.ENDPOINT):
        self.payload = io.BytesIO(raw)
        self.status = status
        self.url = url
    def geturl(self):
        return self.url
    def read(self, count):
        return self.payload.read(count)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class TEDWBMProcedureSearchIndexTests(unittest.TestCase):
    def test_competition_query_exact_and_search_executes(self):
        q = json.loads(m.query_body(m.NOTICES[0]))
        self.assertEqual(q["query"], "publication-number = 286307-2026")
        self.assertIn("procedure-identifier", q["fields"])
        self.assertIn("previous-notice-id-proc", q["fields"])
        self.assertEqual(q["limit"], 2)
        self.assertFalse(q["checkQuerySyntax"])

    def test_award_query_not_a_broad_company_search(self):
        q = json.loads(m.query_body(m.NOTICES[1]))
        self.assertEqual(q["query"], "publication-number = 668506-2026")
        self.assertFalse(q["onlyLatestVersions"])

    def test_nonallowlisted_notice_cannot_be_queried(self):
        with self.assertRaisesRegex(ValueError, "NOTICE_NOT_ALLOWLISTED"):
            m.query_body("100-2026")

    def test_indexed_same_bt04_is_not_source_original_proof(self):
        a = m.parse(m.NOTICES[0], fixture(m.NOTICES[0]))
        b = m.parse(m.NOTICES[1], fixture(m.NOTICES[1]))
        result = m.compare(a, b)
        self.assertEqual(result["classification"],
                         "INDEXED_SAME_BT04_REQUIRES_ORIGINAL_REPLAY")
        self.assertTrue(result["search_index_procedure_uuids_identical"])
        self.assertFalse(result["original_eforms_source_uuid_link_confirmed"])
        self.assertFalse(result["actual_insurance_share_or_CAT_model_exposure_admitted"])

    def test_indexed_different_bt04_is_not_silently_overridden(self):
        a = m.parse(m.NOTICES[0], fixture(m.NOTICES[0]))
        b = m.parse(m.NOTICES[1], fixture(m.NOTICES[1], procedure=PROCEDURE_2))
        result = m.compare(a, b)
        self.assertEqual(result["classification"],
                         "INDEXED_DIFFERENT_BT04_REQUIRES_ORIGINAL_REPLAY")
        self.assertFalse(result["search_index_procedure_uuids_identical"])

    def test_explicit_previous_publication_reference_is_a_separate_fact(self):
        a = m.parse(m.NOTICES[0], fixture(m.NOTICES[0]))
        b = m.parse(m.NOTICES[1], fixture(
            m.NOTICES[1], procedure=PROCEDURE_2,
            previous=["286307-2026", "301723-2024"]))
        result = m.compare(a, b)
        self.assertTrue(result["search_index_award_explicitly_references_earlier_publication"])
        self.assertFalse(result["search_index_procedure_uuids_identical"])

    def test_nested_language_maps_do_not_confuse_procedure_fields(self):
        data = json.loads(fixture())
        data["notices"][0]["procedure-identifier"] = {"de": [PROCEDURE_1]}
        row = m.parse(m.NOTICES[0], json.dumps(data).encode())
        self.assertEqual(row["indexed_procedure_uuid_BT04"], PROCEDURE_1)

    def test_missing_procedure_field_is_not_a_match(self):
        data = json.loads(fixture())
        data["notices"][0].pop("procedure-identifier")
        with self.assertRaisesRegex(ValueError, "NOT_ONE_PROCEDURE_UUID"):
            m.parse(m.NOTICES[0], json.dumps(data).encode())

    def test_wrong_second_publication_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "WRONG_PUBLICATION"):
            m.parse(m.NOTICES[1], fixture(m.NOTICES[0]))

    def test_wrong_buyer_blocks(self):
        with self.assertRaisesRegex(ValueError, "WRONG_BUYER"):
            m.parse(m.NOTICES[0], fixture(buyer="Unrelated supplier"))

    def test_wrong_insurance_subject_blocks(self):
        with self.assertRaisesRegex(ValueError, "WRONG_PRODUCT"):
            m.parse(m.NOTICES[0], fixture(title="Vehicles and cars"))

    def test_index_api_duplicate_json_keys_blocked(self):
        raw = fixture()
        raw = raw.replace(b'"notices":', b'"notices":[],"notices":', 1)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            m.parse(m.NOTICES[0], raw)

    def test_invalid_or_non_uuid4_procedure_blocked(self):
        for proc in ("notuuid", "f47ac10b-58cc-11cf-a447-001122334455"):
            with self.subTest(proc=proc), self.assertRaisesRegex(ValueError, "UUID"):
                m.parse(m.NOTICES[0], fixture(procedure=proc))

    def test_search_with_two_results_is_ambiguous_and_blocked(self):
        row = json.loads(fixture())["notices"][0]
        with self.assertRaisesRegex(ValueError, "EXACTLY_ONE_PUBLICATION"):
            m.parse(m.NOTICES[0], fixture(rows=[row, row]))

    def test_bogus_previous_notice_reference_cannot_be_marked_link(self):
        with self.assertRaisesRegex(ValueError, "BAD_PREVIOUS_REFERENCE"):
            m.parse(m.NOTICES[1], fixture(
                m.NOTICES[1], previous=["not-publication"]))

    def test_missing_previous_notice_field_is_unknown_not_link(self):
        early = m.parse(m.NOTICES[0], fixture())
        late = m.parse(m.NOTICES[1], fixture(m.NOTICES[1]))
        self.assertFalse(m.compare(
            early, late)["search_index_award_explicitly_references_earlier_publication"])

    def test_timed_out_and_syntax_only_response_refused(self):
        for obj in (
            {"notices": [], "totalNoticeCount": None},
            {"notices": [], "totalNoticeCount": 0, "timedOut": True},
        ):
            with self.assertRaisesRegex(ValueError, "TIMED_OUT_OR_SYNTAX_ONLY"):
                m.parse(m.NOTICES[0], json.dumps(obj).encode())

    def test_unsupported_nested_response_blocked(self):
        row = json.loads(fixture())["notices"][0]
        value = "x"
        for i in range(7):
            value = {"de": value}
        row["buyer-name"] = value
        with self.assertRaisesRegex(ValueError, "FIELD_TOO_DEEP"):
            m.parse(m.NOTICES[0], json.dumps({
                "notices": [row], "totalNoticeCount": 1}).encode())

    def test_wrong_api_response_host_is_terminal(self):
        with self.assertRaisesRegex(ValueError, "NOT_OFFICIAL_HOST"):
            m.fetch(m.NOTICES[0], opener=lambda req, timeout:
                    Response(fixture(), url="https://mirror.example/v3/notices/search"))

    def test_http_202_not_valid_json_source(self):
        with self.assertRaisesRegex(ValueError, "NON200_RESPONSE"):
            m.fetch(m.NOTICES[0], opener=lambda req, timeout:
                    Response(fixture(), status=202))

    def test_valid_official_api_read_is_bounded(self):
        raw = fixture()
        result = m.fetch(m.NOTICES[0], opener=lambda req, timeout:
                         Response(raw))
        self.assertEqual(result, raw)

    def test_index_evidence_overclaim_is_refused(self):
        a = m.parse(m.NOTICES[0], fixture())
        b = m.parse(m.NOTICES[1], fixture(m.NOTICES[1]))
        b["original_xml_retrieved_and_byte_sha_verified"] = True
        with self.assertRaisesRegex(ValueError, "PROVENANCE_OVERCLAIM"):
            m.compare(a, b)


if __name__ == "__main__":
    unittest.main()
