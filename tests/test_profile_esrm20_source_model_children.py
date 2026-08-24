# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from scripts import profile_esrm20_source_model_children as subject

PATH = next(iter(subject.RECEIPTS))
XML = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><sourceModel><pointSource id="p1"/></sourceModel></nrml>'
RECEIPT = (len(XML), hashlib.sha256(XML).hexdigest())


def _receipt(payload: bytes) -> tuple[int, str]:
    return len(payload), hashlib.sha256(payload).hexdigest()


class SourceModelContentProfileTests(unittest.TestCase):
    def test_profiles_only_after_exact_byte_identity(self) -> None:
        with patch.dict(subject.RECEIPTS, {PATH: RECEIPT}, clear=True):
            profile = subject.profile_source_model(PATH, XML)
        self.assertTrue(profile["byte_identity_verified"])
        self.assertTrue(profile["source_model_content_profiled"])
        self.assertEqual(profile["root_element"], "nrml")
        self.assertEqual(profile["element_type_counts"], {"nrml": 1, "pointSource": 1, "sourceModel": 1})
        self.assertFalse(profile["external_reference_scan_performed"])
        self.assertFalse(profile["transitive_dependency_byte_closure_verified"])
        self.assertFalse(profile["runtime_compatibility_verified"])
        self.assertFalse(profile["external_bytes_persisted"])
        self.assertFalse(profile["publication_authorized"])
        self.assertFalse(profile["model_use_authorized"])

    def test_profiles_direct_effective_tectonic_regions_without_source_identity(self) -> None:
        payload = (
            b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><sourceModel>'
            b'<pointSource id="p1" tectonicRegion="Active Shallow Crust"/>'
            b'<areaSource id="a1" tectonicRegion="Active Shallow Crust"/>'
            b'<complexFaultSource id="f1" tectonicRegion="Subduction Interface"/>'
            b'</sourceModel></nrml>'
        )
        with patch.dict(subject.RECEIPTS, {PATH: _receipt(payload)}, clear=True):
            profile = subject.profile_source_model_tectonic_regions(PATH, payload)
        self.assertEqual(profile["source_count"], 3)
        self.assertEqual(
            profile["effective_tectonic_region_counts"],
            {"Active Shallow Crust": 2, "Subduction Interface": 1},
        )
        self.assertEqual(
            profile["tectonic_region_provenance_counts"],
            {"direct": 3, "source_group": 0, "direct_and_source_group": 0},
        )
        self.assertNotIn("p1", str(profile))
        self.assertFalse(profile["runtime_compatibility_verified"])
        self.assertFalse(profile["model_use_authorized"])

    def test_profiles_source_group_inheritance_and_matching_direct_declaration(self) -> None:
        payload = (
            b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><sourceModel>'
            b'<sourceGroup tectonicRegion="Subduction Interface">'
            b'<complexFaultSource id="a"/>'
            b'<complexFaultSource id="b" tectonicRegion="Subduction Interface"/>'
            b'</sourceGroup></sourceModel></nrml>'
        )
        with patch.dict(subject.RECEIPTS, {PATH: _receipt(payload)}, clear=True):
            profile = subject.profile_source_model_tectonic_regions(PATH, payload)
        self.assertEqual(profile["effective_tectonic_region_counts"], {"Subduction Interface": 2})
        self.assertEqual(
            profile["tectonic_region_provenance_counts"],
            {"direct": 0, "source_group": 1, "direct_and_source_group": 1},
        )

    def test_rejects_conflicting_group_and_direct_tectonic_region(self) -> None:
        payload = (
            b'<nrml><sourceModel><sourceGroup tectonicRegion="Active Shallow Crust">'
            b'<areaSource tectonicRegion="Stable Shallow Crust"/>'
            b'</sourceGroup></sourceModel></nrml>'
        )
        with patch.dict(subject.RECEIPTS, {PATH: _receipt(payload)}, clear=True):
            with self.assertRaisesRegex(subject.SourceModelContentProfileError, "conflicts"):
                subject.profile_source_model_tectonic_regions(PATH, payload)

    def test_rejects_missing_or_blank_effective_tectonic_region(self) -> None:
        payloads = (
            b'<nrml><sourceModel><pointSource/></sourceModel></nrml>',
            b'<nrml><sourceModel><pointSource tectonicRegion=" "/></sourceModel></nrml>',
            b'<nrml><sourceModel><sourceGroup><pointSource tectonicRegion="A"/></sourceGroup></sourceModel></nrml>',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                with patch.dict(subject.RECEIPTS, {PATH: _receipt(payload)}, clear=True):
                    with self.assertRaises(subject.SourceModelContentProfileError):
                        subject.profile_source_model_tectonic_regions(PATH, payload)

    def test_rejects_control_bearing_tectonic_region(self) -> None:
        payload = b'<nrml><sourceModel><pointSource tectonicRegion="Active&#10;Crust"/></sourceModel></nrml>'
        with patch.dict(subject.RECEIPTS, {PATH: _receipt(payload)}, clear=True):
            with self.assertRaisesRegex(subject.SourceModelContentProfileError, "control"):
                subject.profile_source_model_tectonic_regions(PATH, payload)

    def test_rejects_unsupported_source_nesting(self) -> None:
        payloads = (
            b'<nrml><sourceModel><wrapper><pointSource tectonicRegion="A"/></wrapper></sourceModel></nrml>',
            b'<nrml><sourceModel><pointSource tectonicRegion="A"><areaSource tectonicRegion="A"/></pointSource></sourceModel></nrml>',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                with patch.dict(subject.RECEIPTS, {PATH: _receipt(payload)}, clear=True):
                    with self.assertRaisesRegex(subject.SourceModelContentProfileError, "nesting"):
                        subject.profile_source_model_tectonic_regions(PATH, payload)

    def test_rejects_path_outside_exact_receipt_set(self) -> None:
        with self.assertRaisesRegex(subject.SourceModelContentProfileError, "outside exact receipt set"):
            subject.profile_source_model("Hazard/source_models/guessed.xml", XML)

    def test_rejects_byte_count_drift_before_parsing(self) -> None:
        with patch.dict(subject.RECEIPTS, {PATH: RECEIPT}, clear=True):
            with self.assertRaisesRegex(subject.SourceModelContentProfileError, "byte count"):
                subject.profile_source_model(PATH, XML + b" ")

    def test_rejects_hash_drift_before_parsing(self) -> None:
        same_length = bytearray(XML)
        same_length[-2] = ord(" ")
        with patch.dict(subject.RECEIPTS, {PATH: RECEIPT}, clear=True):
            with self.assertRaisesRegex(subject.SourceModelContentProfileError, "SHA-256"):
                subject.profile_source_model(PATH, bytes(same_length))

    def test_rejects_dtd_or_entity_declarations(self) -> None:
        payload = b'<!DOCTYPE nrml [<!ENTITY x "y">]><nrml>&x;</nrml>'
        receipt = (len(payload), hashlib.sha256(payload).hexdigest())
        with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
            with self.assertRaisesRegex(subject.SourceModelContentProfileError, "DTD/entity"):
                subject.profile_source_model(PATH, payload)

    def test_rejects_utf16_dtd_before_xml_parser(self) -> None:
        payload = (
            '<?xml version="1.0" encoding="UTF-16"?>'
            '<!DOCTYPE nrml [<!ENTITY x "y">]><nrml>&x;</nrml>'
        ).encode("utf-16")
        receipt = (len(payload), hashlib.sha256(payload).hexdigest())
        with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
            with patch.object(subject.ET, "fromstring", side_effect=AssertionError("parser must not run")) as parser:
                with self.assertRaisesRegex(subject.SourceModelContentProfileError, "must be UTF-8"):
                    subject.profile_source_model(PATH, payload)
        parser.assert_not_called()

    def test_rejects_bomless_utf16_before_xml_parser(self) -> None:
        xml = '<?xml version="1.0"?><!DOCTYPE nrml [<!ENTITY x "y">]><nrml>&x;</nrml>'
        for encoding in ("utf-16-le", "utf-16-be"):
            with self.subTest(encoding=encoding):
                payload = xml.encode(encoding)
                receipt = (len(payload), hashlib.sha256(payload).hexdigest())
                with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
                    with patch.object(
                        subject.ET, "fromstring", side_effect=AssertionError("parser must not run")
                    ) as parser:
                        with self.assertRaisesRegex(subject.SourceModelContentProfileError, "NUL"):
                            subject.profile_source_model(PATH, payload)
                    parser.assert_not_called()

    def test_rejects_long_non_utf8_xml_declaration_before_parser(self) -> None:
        payload = (
            '<?xml version="1.0"' + (" " * 600) + 'encoding="ISO-8859-1"?><nrml/>'
        ).encode("utf-8")
        receipt = (len(payload), hashlib.sha256(payload).hexdigest())
        with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
            with patch.object(subject.ET, "fromstring", side_effect=AssertionError("parser must not run")) as parser:
                with self.assertRaisesRegex(subject.SourceModelContentProfileError, "declares a non-UTF-8"):
                    subject.profile_source_model(PATH, payload)
        parser.assert_not_called()

    def test_rejects_non_utf8_xml_declaration_before_parser(self) -> None:
        payload = b'<?xml version="1.0" encoding="ISO-8859-1"?><nrml/>'
        receipt = (len(payload), hashlib.sha256(payload).hexdigest())
        with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
            with patch.object(subject.ET, "fromstring", side_effect=AssertionError("parser must not run")) as parser:
                with self.assertRaisesRegex(subject.SourceModelContentProfileError, "declares a non-UTF-8"):
                    subject.profile_source_model(PATH, payload)
        parser.assert_not_called()

    def test_rejects_non_bytes(self) -> None:
        with patch.dict(subject.RECEIPTS, {PATH: RECEIPT}, clear=True):
            with self.assertRaisesRegex(subject.SourceModelContentProfileError, "must be bytes"):
                subject.profile_source_model(PATH, XML.decode())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
