# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import profile_esrm20_runtime_exposure_xml as subject

NS05 = subject.NRML_NAMESPACE
NS04 = subject.NRML_NAMESPACE_LEGACY_04


def valid_payload(namespace: str) -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="{namespace}"><exposureModel id="kosovo" category="buildings" taxonomySource="GEM">
<description>Kosovo runtime exposure</description><conversions><costTypes>
<costType name="structural" type="aggregated" unit="EUR"/></costTypes><area type="aggregated" unit="SQM"/></conversions>
<occupancyPeriods>day night</occupancyPeriods><tagNames>occupancy admin</tagNames>
<assets>Exposure_A.csv Exposure_B.csv</assets><exposureFields>
<field oq="taxonomy" input="TAXONOMY"/><field oq="value" type="structural" input="STRUCTURAL"/>
</exposureFields></exposureModel></nrml>'''.encode()


VALID = valid_payload(NS05)


class FakeResponse:
    def __init__(self, payload: bytes, url: str):
        self.payload = payload
        self.offset = 0
        self.url = url
        self.status = 200
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/xml",
            "ETag": '"x"',
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, size=-1):
        if self.offset >= len(self.payload):
            return b""
        end = (
            len(self.payload)
            if size < 0
            else min(len(self.payload), self.offset + size)
        )
        out = self.payload[self.offset : end]
        self.offset = end
        return out


class ProfileTests(unittest.TestCase):
    def test_profile_reports_only_declared_metadata_for_exact_supported_namespaces(self):
        for namespace in (NS04, NS05):
            with self.subTest(namespace=namespace):
                result = subject.profile_xml_bytes(valid_payload(namespace))
                self.assertEqual(result["nrml_namespace"], namespace)
                self.assertEqual(result["exposure_model"]["category"], "buildings")
                self.assertEqual(
                    result["asset_references"], ["Exposure_A.csv", "Exposure_B.csv"]
                )
                self.assertTrue(result["structural_cost_type_declared"])
                self.assertEqual(result["structural_value_inputs"], ["STRUCTURAL"])

    def test_nrml_root_first_divergence_is_bounded_and_ordered(self):
        cases = [
            (
                f'<notnrml xmlns="{NS05}" secret="provider-value"/>'.encode(),
                "runtime exposure NRML root local name drifted",
            ),
            (
                b'<nrml xmlns="urn:provider-secret" secret="provider-value"/>',
                "runtime exposure NRML root namespace is unrecognized",
            ),
            (
                f'<nrml xmlns="{NS04}" secret="provider-value"/>'.encode(),
                "runtime exposure NRML root attributes present",
            ),
            (
                f'<nrml xmlns="{NS05}" secret="provider-value"/>'.encode(),
                "runtime exposure NRML root attributes present",
            ),
        ]
        for payload, expected in cases:
            with (
                self.subTest(expected=expected),
                self.assertRaisesRegex(
                    subject.XmlSemanticProfileError, f"^{expected}$"
                ),
            ):
                subject.profile_xml_bytes(payload)

    def test_supported_root_does_not_allow_foreign_child_namespace(self):
        payload = (
            f'<nrml xmlns="{NS04}" xmlns:x="{NS05}"><x:exposureModel id="x">'
            f'<x:description>x</x:description><x:assets>a.csv</x:assets>'
            f'</x:exposureModel></nrml>'
        ).encode()
        with self.assertRaisesRegex(
            subject.XmlSemanticProfileError, "^expected exactly one exposureModel$"
        ):
            subject.profile_xml_bytes(payload)

    def test_parser_rejects_dtd_foreign_namespace_unknown_children_and_unsafe_assets(
        self,
    ):
        cases = [
            b'<!DOCTYPE x [<!ENTITY x "boom">]><x/>',
            b'<nrml xmlns="urn:wrong"><exposureModel id="x"><description>x</description><assets>a.csv</assets></exposureModel></nrml>',
            f'<nrml xmlns="{NS05}"><exposureModel id="x"><description>x</description><assets>a.csv</assets><mystery/></exposureModel></nrml>'.encode(),
            f'<nrml xmlns="{NS04}"><exposureModel id="x"><description>x</description><assets>../a.csv</assets></exposureModel></nrml>'.encode(),
            f'<nrml xmlns="{NS05}"><exposureModel id="x"><description>x</description><assets>./a.csv</assets></exposureModel></nrml>'.encode(),
            f'<nrml xmlns="{NS04}"><exposureModel id="x"><description>x</description><assets>C:\\a.csv</assets></exposureModel></nrml>'.encode(),
        ]
        for payload in cases:
            with (
                self.subTest(payload=payload),
                self.assertRaises(subject.XmlSemanticProfileError),
            ):
                subject.profile_xml_bytes(payload)

    def test_exact_receipt_identity_is_required_before_interpretation(self):
        target = subject.validate_target(
            source_issue=282,
            dataset_id=subject.DATASET_ID,
            project_id=269,
            commit_sha=subject.COMMIT_SHA,
            repository_path=subject.REPOSITORY_PATH,
        )
        url = subject.raw_file_api_url(target)
        with (
            mock.patch.object(subject, "EXPECTED_BYTE_COUNT", len(VALID)),
            mock.patch.object(
                subject, "EXPECTED_SHA256", hashlib.sha256(VALID).hexdigest()
            ),
        ):
            result = subject._profile_runtime_exposure_xml(
                opener=lambda request, timeout: FakeResponse(VALID, url),
                now=lambda: "2026-08-19T22:00:00Z",
                monotonic=lambda: 0.0,
            )
        self.assertTrue(result["xml_content_interpreted"])
        self.assertFalse(result["exact_kosovo_exposure_selected"])
        self.assertFalse(result["value_structural_wiring_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

        with self.assertRaises(subject.ByteIdentityMismatch):
            subject._profile_runtime_exposure_xml(
                opener=lambda request, timeout: FakeResponse(VALID, url),
                now=lambda: "2026-08-19T22:00:00Z",
                monotonic=lambda: 0.0,
            )

    def test_public_entry_rejects_live_alias_drift_before_provider_access(self):
        with (
            mock.patch.object(subject, "SOURCE_ISSUE", 999),
            mock.patch.object(subject, "_CANONICAL_OPEN_FIXED") as opener,
            self.assertRaisesRegex(
                subject.RuntimeExposureXmlProfileError, "source issue drifted"
            ),
        ):
            subject.profile_runtime_exposure_xml()
            opener.assert_not_called()

    def test_public_target_and_namespace_set_are_frozen(self):
        self.assertEqual(subject.SOURCE_ISSUE, 282)
        self.assertEqual(subject.PROJECT_ID, 269)
        self.assertEqual(
            subject.COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
        )
        self.assertEqual(
            subject.REPOSITORY_PATH, "Exposure/OQ_Exposure_Input_Kosovo.xml"
        )
        self.assertEqual(subject.EXPECTED_BYTE_COUNT, 664)
        self.assertEqual(
            subject.EXPECTED_SHA256,
            "61be4c534e6bdd1577d15dd289b2c604fde41f00f8f636901634daf2f41bcceb",
        )
        self.assertEqual(
            subject.ACCEPTED_NRML_NAMESPACES,
            frozenset(
                {
                    "http://openquake.org/xmlns/nrml/0.4",
                    "http://openquake.org/xmlns/nrml/0.5",
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
