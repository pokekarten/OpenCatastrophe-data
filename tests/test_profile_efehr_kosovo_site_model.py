# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest

from scripts import profile_efehr_kosovo_site_model as subject


def _profile(raw: bytes):
    return subject.profile_verified_xml_bytes(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
    )


class KosovoSiteContentProfileTests(unittest.TestCase):
    def test_profiles_structure_without_returning_provider_values(self):
        raw = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">\n'
            b'  <siteModel>\n'
            b'    <site lon="20.1" lat="42.6" vs30="760" vs30Type="inferred" z1pt0="100" z2pt5="2.5"/>\n'
            b'    <site lon="20.2" lat="42.7" vs30="800" vs30Type="measured" z1pt0="110" z2pt5="2.7"/>\n'
            b'  </siteModel>\n'
            b'</nrml>\n'
        )
        result = _profile(raw)

        self.assertEqual(result["root"]["local_name"], "nrml")
        self.assertEqual(result["element_count"], 4)
        self.assertEqual(result["leaf_element_count"], 2)
        self.assertEqual(result["parser"]["verified_encoding"], "utf-8")
        profiles = {item["name"]["local_name"]: item for item in result["attribute_profiles"]}
        self.assertEqual(profiles["vs30"]["occurrence_count"], 2)
        self.assertEqual(profiles["vs30"]["finite_decimal_lexical_count"], 2)
        self.assertEqual(profiles["vs30Type"]["finite_decimal_lexical_count"], 0)
        self.assertFalse(result["raw_xml_returned"])
        self.assertFalse(result["raw_attribute_values_returned"])
        serialized = repr(result)
        for forbidden in ("20.1", "42.6", "760", "inferred", "2.5"):
            self.assertNotIn(forbidden, serialized)

    def test_byte_identity_precedes_xml_parse(self):
        malformed = b"<not-xml"
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "SHA-256"):
            subject.profile_verified_xml_bytes(
                malformed,
                expected_byte_count=len(malformed),
                expected_sha256="0" * 64,
            )

    def test_rejects_dtd_and_entity_declarations(self):
        for raw in (
            b'<!DOCTYPE x [<!ELEMENT x ANY>]><x/>',
            b'<!DOCTYPE x [<!ENTITY a "b">]><x>&a;</x>',
        ):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(subject.KosovoSiteProfileError, "DTD or entity"):
                    _profile(raw)

    def test_utf16_ordinary_xml_is_rejected_before_parser_semantics(self):
        raw = '<?xml version="1.0" encoding="UTF-16"?><root/>'.encode("utf-16")
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "strict UTF-8"):
            _profile(raw)

    def test_utf16_entity_document_cannot_produce_a_profile(self):
        raw = (
            '<?xml version="1.0" encoding="UTF-16"?>'
            '<!DOCTYPE x [<!ENTITY a "expanded">]><x>&a;</x>'
        ).encode("utf-16")
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "strict UTF-8"):
            _profile(raw)

    def test_utf8_bytes_reject_conflicting_declared_encoding(self):
        for encoding in ("UTF-16", "ISO-8859-1"):
            with self.subTest(encoding=encoding):
                raw = (
                    f'<?xml version="1.0" encoding="{encoding}"?><root/>'.encode("utf-8")
                )
                with self.assertRaisesRegex(
                    subject.KosovoSiteProfileError,
                    "encoding does not match strict UTF-8",
                ):
                    _profile(raw)

    def test_malformed_or_duplicate_xml_declaration_fails_closed(self):
        raw = (
            b'<?xml version="1.0" encoding="UTF-8" encoding="UTF-8"?>'
            b'<root/>'
        )
        with self.assertRaisesRegex(
            subject.KosovoSiteProfileError,
            "XML declaration is malformed or unsupported",
        ):
            _profile(raw)

    def test_utf8_declaration_is_case_insensitive_and_bom_compatible(self):
        raw = (
            b"\xef\xbb\xbf"
            b'<?xml version="1.0" encoding="utf-8" standalone="yes"?>'
            b'<root><site a="1"/></root>'
        )
        result = _profile(raw)
        self.assertTrue(result["parser"]["bom_present"])
        self.assertEqual(result["parser"]["verified_encoding"], "utf-8")
        self.assertEqual(result["root"]["local_name"], "root")

    def test_utf8_bom_is_accepted_but_removed_before_parse(self):
        raw = b"\xef\xbb\xbf<root><site a=\"1\"/></root>"
        result = _profile(raw)
        self.assertTrue(result["parser"]["bom_present"])
        self.assertEqual(result["parser"]["verified_encoding"], "utf-8")
        self.assertEqual(result["root"]["local_name"], "root")

    def test_malformed_xml_fails_closed_after_identity(self):
        raw = b"<nrml><siteModel></nrml>"
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "malformed"):
            _profile(raw)

    def test_names_and_values_are_bounded(self):
        long_name = "x" * (subject.MAX_NAME_UTF8_BYTES + 1)
        raw_name = f"<{long_name}/>".encode("utf-8")
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "name exceeds"):
            _profile(raw_name)

        long_value = "v" * (subject.MAX_ATTRIBUTE_VALUE_UTF8_BYTES + 1)
        raw_value = f'<x a="{long_value}"/>'.encode("utf-8")
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "attribute value exceeds"):
            _profile(raw_value)

    def test_non_whitespace_text_is_counted_not_returned(self):
        raw = b"<root><note>provider-secret-like-text</note><empty>   </empty></root>"
        result = _profile(raw)
        self.assertEqual(result["non_whitespace_text_element_count"], 1)
        self.assertNotIn("provider-secret-like-text", repr(result))

    def test_authority_ceilings_remain_false(self):
        raw = b'<root><site a="1"/></root>'
        result = _profile(raw)
        for field in (
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

    def test_exact_wrapper_rejects_any_synthetic_object(self):
        raw = b"<root/>"
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "byte count"):
            subject.profile_verified_kosovo_site_model(raw)

    def test_oversized_expected_identity_fails_before_xml_work(self):
        raw = b"<root/>"
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "bounded policy"):
            subject.profile_verified_xml_bytes(
                raw,
                expected_byte_count=subject.MAX_XML_BYTES + 1,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_invalid_expected_identity_fails_closed(self):
        raw = b"<root/>"
        with self.assertRaisesRegex(subject.KosovoSiteProfileError, "lowercase hex"):
            subject.profile_verified_xml_bytes(
                raw,
                expected_byte_count=len(raw),
                expected_sha256="G" * 64,
            )


if __name__ == "__main__":
    unittest.main()
