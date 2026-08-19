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
