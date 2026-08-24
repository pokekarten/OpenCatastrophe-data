# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from scripts import profile_esrm20_source_model_children as subject

PATH = next(iter(subject.RECEIPTS))
XML = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><sourceModel><pointSource id="p1" tectonicRegion="Shallow Default"/></sourceModel></nrml>'
RECEIPT = (len(XML), hashlib.sha256(XML).hexdigest())


def _profile(payload: bytes) -> dict:
    receipt = (len(payload), hashlib.sha256(payload).hexdigest())
    with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
        return subject.profile_source_model(PATH, payload)


class SourceModelContentProfileTests(unittest.TestCase):
    def test_profiles_only_after_exact_byte_identity(self) -> None:
        with patch.dict(subject.RECEIPTS, {PATH: RECEIPT}, clear=True):
            profile = subject.profile_source_model(PATH, XML)
        self.assertTrue(profile["byte_identity_verified"])
        self.assertTrue(profile["source_model_content_profiled"])
        self.assertEqual(profile["root_element"], "nrml")
        self.assertEqual(
            profile["element_type_counts"],
            {"nrml": 1, "pointSource": 1, "sourceModel": 1},
        )
        self.assertEqual(
            profile["tectonic_region_type_counts"], {"Shallow Default": 1}
        )
        self.assertEqual(profile["trt_provenance_counts"], {"direct_source": 1})
        self.assertFalse(profile["external_reference_scan_performed"])
        self.assertFalse(profile["transitive_dependency_byte_closure_verified"])
        self.assertFalse(profile["runtime_compatibility_verified"])
        self.assertFalse(profile["external_bytes_persisted"])
        self.assertFalse(profile["publication_authorized"])
        self.assertFalse(profile["model_use_authorized"])

    def test_profiles_source_group_inheritance_and_direct_confirmation(self) -> None:
        payload = b'''<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><sourceModel><sourceGroup tectonicRegion="Subduction Interface"><complexFaultSource id="a"/><complexFaultSource id="b" tectonicRegion="Subduction Interface"/></sourceGroup></sourceModel></nrml>'''
        profile = _profile(payload)
        self.assertEqual(
            profile["tectonic_region_type_counts"], {"Subduction Interface": 2}
        )
        self.assertEqual(
            profile["trt_provenance_counts"],
            {"group_effective_direct_confirmed": 1, "group_inherited": 1},
        )

    def test_rejects_missing_direct_trt(self) -> None:
        payload = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><sourceModel><areaSource id="a"/></sourceModel></nrml>'
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError, "tectonicRegion"
        ):
            _profile(payload)

    def test_rejects_blank_or_control_bearing_trt(self) -> None:
        for trt in (" Shallow Default", "Shallow&#10;Default"):
            with self.subTest(trt=trt):
                payload = f'<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><sourceModel><areaSource tectonicRegion="{trt}"/></sourceModel></nrml>'.encode()
                with self.assertRaises(subject.SourceModelContentProfileError):
                    _profile(payload)

    def test_rejects_group_direct_trt_conflict(self) -> None:
        payload = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><sourceModel><sourceGroup tectonicRegion="Craton"><areaSource tectonicRegion="Shallow Default"/></sourceGroup></sourceModel></nrml>'
        with self.assertRaisesRegex(subject.SourceModelContentProfileError, "conflicts"):
            _profile(payload)

    def test_rejects_mixed_group_and_direct_sources(self) -> None:
        payload = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5"><sourceModel><sourceGroup tectonicRegion="Craton"><areaSource/></sourceGroup><areaSource tectonicRegion="Craton"/></sourceModel></nrml>'
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError,
            "NRML 0.5 sourceModel must contain sourceGroup children",
        ):
            _profile(payload)

    def test_rejects_unknown_or_nested_source_structure(self) -> None:
        unknown = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><sourceModel><mysterySource tectonicRegion="Craton"/></sourceModel></nrml>'
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError, "unsupported source-model child"
        ):
            _profile(unknown)
        nested = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><sourceModel><areaSource tectonicRegion="Craton"><pointSource tectonicRegion="Craton"/></areaSource></sourceModel></nrml>'
        with self.assertRaisesRegex(subject.SourceModelContentProfileError, "nested"):
            _profile(nested)

    def test_rejects_unsupported_namespace_or_empty_model(self) -> None:
        unsupported = b'<nrml xmlns="urn:not-openquake"><sourceModel><areaSource tectonicRegion="Craton"/></sourceModel></nrml>'
        with self.assertRaisesRegex(subject.SourceModelContentProfileError, "unsupported"):
            _profile(unsupported)
        empty = b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"><sourceModel/></nrml>'
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError, "contains no sources"
        ):
            _profile(empty)

    def test_source_count_and_unique_trt_bounds_fail_closed(self) -> None:
        with patch.object(subject, "MAX_SOURCES_PER_FILE", 0):
            with self.assertRaisesRegex(
                subject.SourceModelContentProfileError, "source count"
            ):
                _profile(XML)
        with patch.object(subject, "MAX_UNIQUE_TRTS_PER_FILE", 0):
            with self.assertRaisesRegex(
                subject.SourceModelContentProfileError, "tectonic-region"
            ):
                _profile(XML)

    def test_rejects_path_outside_exact_receipt_set(self) -> None:
        with self.assertRaisesRegex(
            subject.SourceModelContentProfileError, "outside exact receipt set"
        ):
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
            with patch.object(
                subject.ET,
                "fromstring",
                side_effect=AssertionError("parser must not run"),
            ) as parser:
                with self.assertRaisesRegex(
                    subject.SourceModelContentProfileError, "must be UTF-8"
                ):
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
                        subject.ET,
                        "fromstring",
                        side_effect=AssertionError("parser must not run"),
                    ) as parser:
                        with self.assertRaisesRegex(
                            subject.SourceModelContentProfileError, "NUL"
                        ):
                            subject.profile_source_model(PATH, payload)
                    parser.assert_not_called()

    def test_rejects_long_non_utf8_xml_declaration_before_parser(self) -> None:
        payload = (
            '<?xml version="1.0"' + (" " * 600) + 'encoding="ISO-8859-1"?><nrml/>'
        ).encode("utf-8")
        receipt = (len(payload), hashlib.sha256(payload).hexdigest())
        with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
            with patch.object(
                subject.ET,
                "fromstring",
                side_effect=AssertionError("parser must not run"),
            ) as parser:
                with self.assertRaisesRegex(
                    subject.SourceModelContentProfileError,
                    "declares a non-UTF-8",
                ):
                    subject.profile_source_model(PATH, payload)
        parser.assert_not_called()

    def test_rejects_non_utf8_xml_declaration_before_parser(self) -> None:
        payload = b'<?xml version="1.0" encoding="ISO-8859-1"?><nrml/>'
        receipt = (len(payload), hashlib.sha256(payload).hexdigest())
        with patch.dict(subject.RECEIPTS, {PATH: receipt}, clear=True):
            with patch.object(
                subject.ET,
                "fromstring",
                side_effect=AssertionError("parser must not run"),
            ) as parser:
                with self.assertRaisesRegex(
                    subject.SourceModelContentProfileError,
                    "declares a non-UTF-8",
                ):
                    subject.profile_source_model(PATH, payload)
        parser.assert_not_called()

    def test_rejects_non_bytes(self) -> None:
        with patch.dict(subject.RECEIPTS, {PATH: RECEIPT}, clear=True):
            with self.assertRaisesRegex(subject.SourceModelContentProfileError, "must be bytes"):
                subject.profile_source_model(PATH, XML.decode())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
