# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import profile_efehr_greece_exposure_xml as subject


NS = "http://openquake.org/xmlns/nrml/0.5"


def valid_payload(asset: str = "Exposure_Model_Greece.csv") -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="{NS}"><exposureModel id="greece" category="buildings" taxonomySource="GEM">
<description>Greece scenario exposure</description><conversions><costTypes>
<costType name="structural" type="aggregated" unit="EUR"/></costTypes><area type="aggregated" unit="SQM"/></conversions>
<occupancyPeriods>day night</occupancyPeriods><tagNames>occupancy admin</tagNames>
<assets>{asset}</assets><exposureFields>
<field oq="taxonomy" input="TAXONOMY"/><field oq="value" type="structural" input="STRUCTURAL"/>
</exposureFields></exposureModel></nrml>'''.encode()


def profile(raw: bytes):
    return subject._profile_verified_greece_exposure_bytes(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


class GreeceExposureContentProfileTests(unittest.TestCase):
    def test_canonical_receipt_identity_is_frozen(self):
        self.assertEqual(subject.SOURCE_ISSUE, 285)
        self.assertEqual(subject.RECEIPT_ISSUE, 285)
        self.assertEqual(subject.DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(subject.PROJECT_ID, 269)
        self.assertEqual(subject.PROJECT_PATH, "efehr/esrm20")
        self.assertEqual(subject.RELEASE, "v1.0")
        self.assertEqual(subject.COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783")
        self.assertEqual(subject.CONSUMER_EVENT, "Greece_07-9-1999")
        self.assertEqual(subject.REPOSITORY_PATH, "Exposure/OQ_Exposure_Input_Greece.xml")
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5_388_640_521)
        self.assertEqual(subject.RECEIPT_EXECUTION_SHA, "9bf3fee5d80431dfa873ee5ae03e07891e6f154a")
        self.assertEqual(subject.RECEIPT_RETRIEVED_AT, "2026-08-23T21:47:08Z")
        self.assertEqual(subject.EXPECTED_BYTE_COUNT, 697)
        self.assertEqual(subject.EXPECTED_SHA256, "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556")

    def test_profiles_bounded_source_declarations(self):
        raw = valid_payload()
        result = profile(raw)
        self.assertEqual(result["schema_version"], subject.SCHEMA_VERSION)
        self.assertEqual(result["parser"], "profile_esrm20_runtime_exposure_xml.profile_xml_bytes")
        self.assertTrue(result["source_declarations_profiled"])
        declared = result["profile"]
        self.assertEqual(declared["nrml_namespace"], NS)
        self.assertEqual(declared["exposure_model"]["category"], "buildings")
        self.assertEqual(declared["asset_references"], ["Exposure_Model_Greece.csv"])
        self.assertTrue(declared["structural_cost_type_declared"])
        self.assertEqual(declared["structural_value_inputs"], ["STRUCTURAL"])
        self.assertNotIn("<?xml", repr(result))

    def test_byte_identity_mismatch_precedes_xml_parser(self):
        raw = b"<not-xml"
        with (
            mock.patch.object(subject.shared_profile, "profile_xml_bytes") as parser,
            self.assertRaisesRegex(subject.GreeceExposureProfileError, "exact Greece exposure wrapper byte identity mismatch"),
        ):
            subject._profile_verified_greece_exposure_bytes(
                raw,
                expected_byte_count=len(raw) + 1,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )
        parser.assert_not_called()

    def test_public_exact_wrapper_rejects_synthetic_identity_before_parse(self):
        with (
            mock.patch.object(subject.shared_profile, "profile_xml_bytes") as parser,
            self.assertRaisesRegex(subject.GreeceExposureProfileError, "exact Greece exposure wrapper byte identity mismatch"),
        ):
            subject.profile_verified_greece_exposure_xml(valid_payload())
        parser.assert_not_called()

    def test_shared_parser_negative_cases_remain_fail_closed(self):
        cases = (
            b'<!DOCTYPE x [<!ENTITY x "boom">]><x/>',
            b'<nrml xmlns="urn:wrong"><exposureModel id="x"><description>x</description><assets>a.csv</assets></exposureModel></nrml>',
            b'<nrml><exposureModel></nrml>',
            valid_payload("../Exposure_Model_Greece.csv"),
            valid_payload("./Exposure_Model_Greece.csv"),
            valid_payload("C:\\Exposure_Model_Greece.csv"),
        )
        for raw in cases:
            with (
                self.subTest(raw=raw),
                self.assertRaisesRegex(subject.GreeceExposureProfileError, "verified Greece exposure wrapper profile failed closed"),
            ):
                profile(raw)

    def test_shared_parser_contract_drift_fails_closed(self):
        original = subject.shared_profile.MAX_PROFILE_BYTES
        subject.shared_profile.MAX_PROFILE_BYTES = original + 1
        try:
            with self.assertRaisesRegex(subject.GreeceExposureProfileError, "shared exposure profile byte bound drifted"):
                profile(valid_payload())
        finally:
            subject.shared_profile.MAX_PROFILE_BYTES = original

    def test_shared_result_shape_drift_fails_closed(self):
        raw = valid_payload()
        with (
            mock.patch.object(subject.shared_profile, "profile_xml_bytes", return_value={}),
            self.assertRaisesRegex(subject.GreeceExposureProfileError, "shared exposure profile result fields drifted"),
        ):
            profile(raw)

    def test_authority_ceilings_remain_false(self):
        result = profile(valid_payload())
        for field in (
            "raw_xml_returned",
            "referenced_dependency_bytes_receipted",
            "referenced_dependency_content_profiled",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)


if __name__ == "__main__":
    unittest.main()
