# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_efehr_greece_exposure_wrapper as subject


def _profile(raw: bytes):
    return subject._profile_verified_greece_exposure_bytes(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


class GreeceExposureWrapperProfileTests(unittest.TestCase):
    def test_canonical_receipt_identity_is_frozen(self):
        self.assertEqual(subject.SOURCE_ISSUE, 285)
        self.assertEqual(subject.RECEIPT_ISSUE, 285)
        self.assertEqual(subject.DATASET_ID, "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(subject.PROJECT_ID, 269)
        self.assertEqual(subject.PROJECT_PATH, "efehr/esrm20")
        self.assertEqual(subject.RELEASE, "v1.0")
        self.assertEqual(
            subject.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(subject.CONSUMER_EVENT, "Greece_07-9-1999")
        self.assertEqual(
            subject.REPOSITORY_PATH,
            "Exposure/OQ_Exposure_Input_Greece.xml",
        )
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5_388_640_521)
        self.assertEqual(
            subject.RECEIPT_EXECUTION_SHA,
            "9bf3fee5d80431dfa873ee5ae03e07891e6f154a",
        )
        self.assertEqual(subject.RECEIPT_RETRIEVED_AT, "2026-08-23T21:47:08Z")
        self.assertEqual(subject.EXPECTED_BYTE_COUNT, 697)
        self.assertEqual(
            subject.EXPECTED_SHA256,
            "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556",
        )

    def test_profiles_synthetic_structure_without_returning_values(self):
        raw = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">\n'
            b'  <exposureModel id="athens-secret" category="buildings" '
            b'taxonomySource="source-secret">\n'
            b'    <description>provider-secret-description</description>\n'
            b'    <conversions><costTypes>\n'
            b'      <costType name="structural" type="aggregated" unit="EUR"/>\n'
            b'    </costTypes></conversions>\n'
            b'    <tagNames>region occupancy</tagNames>\n'
            b'  </exposureModel>\n'
            b'</nrml>\n'
        )
        result = _profile(raw)

        self.assertEqual(result["schema_version"], subject.SCHEMA_VERSION)
        self.assertNotEqual(
            result["schema_version"], subject.SHARED_PROFILE_SCHEMA_VERSION
        )
        self.assertEqual(result["root"]["local_name"], "nrml")
        self.assertEqual(result["element_count"], 7)
        profiles = {
            item["name"]["local_name"]: item
            for item in result["attribute_profiles"]
        }
        self.assertEqual(profiles["category"]["occurrence_count"], 1)
        self.assertEqual(profiles["unit"]["finite_decimal_lexical_count"], 0)
        self.assertGreater(result["non_whitespace_text_element_count"], 0)

        serialized = repr(result)
        for forbidden in (
            "athens-secret",
            "source-secret",
            "provider-secret-description",
            "structural",
            "aggregated",
            "EUR",
            "region occupancy",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_public_exact_wrapper_rejects_synthetic_identity_before_parse(self):
        with self.assertRaisesRegex(
            subject.GreeceExposureProfileError,
            "failed closed",
        ):
            subject.profile_verified_greece_exposure_wrapper(b"<not-xml")

    def test_dtd_and_entity_rejection_is_inherited(self):
        for raw in (
            b'<!DOCTYPE x [<!ELEMENT x ANY>]><x/>',
            b'<!DOCTYPE x [<!ENTITY a "b">]><x>&a;</x>',
        ):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(
                    subject.GreeceExposureProfileError,
                    "failed closed",
                ):
                    _profile(raw)

    def test_malformed_xml_rejection_is_inherited(self):
        raw = b"<nrml><exposureModel></nrml>"
        with self.assertRaisesRegex(
            subject.GreeceExposureProfileError,
            "failed closed",
        ):
            _profile(raw)

    def test_shared_profile_schema_drift_fails_closed(self):
        original = subject.shared_profile.SCHEMA_VERSION
        subject.shared_profile.SCHEMA_VERSION = "drifted-schema"
        try:
            with self.assertRaisesRegex(
                subject.GreeceExposureProfileError,
                "shared XML-profile schema drifted",
            ):
                _profile(b"<root/>")
        finally:
            subject.shared_profile.SCHEMA_VERSION = original

    def test_shared_authority_widening_fails_closed(self):
        original = subject.shared_profile.profile_verified_xml_bytes

        def widened(*args, **kwargs):
            result = original(*args, **kwargs)
            result["publication_authorized"] = True
            return result

        subject.shared_profile.profile_verified_xml_bytes = widened
        try:
            with self.assertRaisesRegex(
                subject.GreeceExposureProfileError,
                "widened authority",
            ):
                _profile(b"<root/>")
        finally:
            subject.shared_profile.profile_verified_xml_bytes = original

    def test_exposure_authority_ceilings_remain_false_and_site_fields_do_not_leak(self):
        result = _profile(b'<root><asset cost="1"/></root>')
        for field in subject._EXPOSURE_FALSE_FIELDS:
            self.assertIs(result[field], False)
        for field in (
            "site_parameter_units_verified",
            "gsim_site_parameter_sufficiency_verified",
            "site_adjusted_reference_authorized",
        ):
            self.assertNotIn(field, result)


if __name__ == "__main__":
    unittest.main()
