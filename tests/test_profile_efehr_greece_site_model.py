# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import profile_efehr_greece_site_model as subject


def _profile(raw: bytes):
    return subject._profile_verified_greece_site_bytes(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


class GreeceSiteContentProfileTests(unittest.TestCase):
    def test_canonical_receipt_identity_is_frozen(self):
        self.assertEqual(subject.SOURCE_ISSUE, 285)
        self.assertEqual(subject.SOURCE_SCIENCE_ISSUE, 284)
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
        self.assertEqual(subject.REPOSITORY_PATH, "Vs30/Site_model_Greece.xml")
        self.assertEqual(subject.RECEIPT_COMMENT_ID, 5_388_640_521)
        self.assertEqual(
            subject.RECEIPT_EXECUTION_SHA,
            "9bf3fee5d80431dfa873ee5ae03e07891e6f154a",
        )
        self.assertEqual(subject.RECEIPT_RETRIEVED_AT, "2026-08-23T21:47:08Z")
        self.assertEqual(subject.EXPECTED_BYTE_COUNT, 235_015)
        self.assertEqual(
            subject.EXPECTED_SHA256,
            "613938c3f9e63fb94490ba4514ef7faf4bf3141b86c33fdd5eb7f21f8c175f85",
        )

    def test_profiles_synthetic_structure_without_returning_values(self):
        raw = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">\n'
            b'  <siteModel>\n'
            b'    <site lon="23.70" lat="38.00" region="0" slope="0.01" geology="A"/>\n'
            b'    <site lon="23.71" lat="38.01" region="1" slope="0.02" geology="B"/>\n'
            b'  </siteModel>\n'
            b'</nrml>\n'
        )
        result = _profile(raw)

        self.assertEqual(result["schema_version"], subject.SCHEMA_VERSION)
        self.assertNotEqual(
            result["schema_version"], subject.SHARED_PROFILE_SCHEMA_VERSION
        )
        self.assertEqual(result["root"]["local_name"], "nrml")
        self.assertEqual(result["element_count"], 4)
        profiles = {
            item["name"]["local_name"]: item
            for item in result["attribute_profiles"]
        }
        self.assertEqual(profiles["region"]["occurrence_count"], 2)
        self.assertEqual(profiles["slope"]["finite_decimal_lexical_count"], 2)
        self.assertEqual(profiles["geology"]["finite_decimal_lexical_count"], 0)
        serialized = repr(result)
        for forbidden in ("23.70", "38.00", "0.01", "geology=\"A\""):
            self.assertNotIn(forbidden, serialized)

    def test_public_exact_wrapper_rejects_synthetic_identity_before_parse(self):
        raw = b"<not-xml"
        with mock.patch.object(
            subject.shared_profile,
            "_decode_literal_xml",
            side_effect=AssertionError("XML interpretation must not run"),
        ):
            with self.assertRaisesRegex(subject.GreeceSiteProfileError, "failed closed"):
                subject.profile_verified_greece_site_model(raw)

    def test_dtd_and_entity_rejection_is_inherited(self):
        for raw in (
            b'<!DOCTYPE x [<!ELEMENT x ANY>]><x/>',
            b'<!DOCTYPE x [<!ENTITY a "b">]><x>&a;</x>',
        ):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(
                    subject.GreeceSiteProfileError, "failed closed"
                ):
                    _profile(raw)

    def test_malformed_xml_rejection_is_inherited(self):
        raw = b"<nrml><siteModel></nrml>"
        with self.assertRaisesRegex(subject.GreeceSiteProfileError, "failed closed"):
            _profile(raw)

    def test_shared_profile_schema_drift_fails_closed(self):
        with mock.patch.object(subject.shared_profile, "SCHEMA_VERSION", "drifted-schema"):
            with self.assertRaisesRegex(
                subject.GreeceSiteProfileError, "shared site-profile schema drifted"
            ):
                _profile(b"<root/>")

    def test_shared_profile_result_shape_drift_fails_closed(self):
        with mock.patch.object(
            subject.shared_profile,
            "profile_verified_xml_bytes",
            return_value={
                "schema_version": subject.SHARED_PROFILE_SCHEMA_VERSION,
                "unexpected": True,
            },
        ):
            with self.assertRaisesRegex(
                subject.GreeceSiteProfileError, "result fields drifted"
            ):
                _profile(b"<root/>")

    def test_authority_ceilings_remain_false(self):
        result = _profile(b'<root><site a="1"/></root>')
        for field in (
            "raw_xml_returned",
            "raw_attribute_values_returned",
            "crs_coordinate_semantics_verified",
            "site_parameter_units_verified",
            "missingness_semantics_verified",
            "gsim_site_parameter_sufficiency_verified",
            "site_adjusted_reference_authorized",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)


if __name__ == "__main__":
    unittest.main()
