# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only roof-form codebook and CityJSON ambiguity regression tests."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from scripts.nrw_lod2_roof_code_gate_v0 import (
    AMBIGUOUS_ROOF_CODES, MAX_CODELIST_BYTES, ROOF_CODES, ROOF_CODELIST_URL,
    RoofCodeError, audit_cityjson_roof_codes, classify, fetch_official_xml,
    main, verify_original_ad_v_xml,
)


def synthetic_codebook() -> bytes:
    namespace = "{http://www.opengis.net/gml}"
    dictionary = ElementTree.Element(namespace + "Dictionary")
    for code, label in ROOF_CODES.items():
        node = ElementTree.SubElement(dictionary, namespace + "dictionaryEntry")
        definition = ElementTree.SubElement(node, namespace + "Definition")
        indexed = ElementTree.SubElement(
            definition, namespace + "name",
            {"codeSpace": "http://www.adv-online.de/codespaces"},
        )
        indexed.text = code
        plain = ElementTree.SubElement(definition, namespace + "name")
        plain.text = label
    return ElementTree.tostring(dictionary, encoding="utf-8", xml_declaration=True)


def sample(root_roof="5000", part_codes=("1000", "3100")) -> bytes:
    root_attributes = {} if root_roof is None else {"roofType": root_roof}
    objs = {"fictional-root": {"type": "Building", "attributes": root_attributes}}
    for idx, code in enumerate(part_codes):
        objs[f"fictional-part-{idx}"] = {
            "type": "BuildingPart",
            "parents": ["fictional-root"],
            "attributes": {"roofType": code},
        }
    return json.dumps({"type": "CityJSON", "CityObjects": objs}, separators=(",", ":")).encode()


class AdVRoofCodeContractTests(unittest.TestCase):
    def test_exact_fifteen_functional_ad_v_codes(self):
        self.assertEqual(len(ROOF_CODES), 15)
        self.assertEqual(classify("1000"), "1000")
        self.assertEqual(classify("3100"), "3100")
        self.assertEqual(classify("5000"), "5000")
        self.assertEqual(classify("9999"), "9999")
        self.assertEqual(AMBIGUOUS_ROOF_CODES, {"5000", "9999"})

    def test_unknown_int_bool_whitespace_or_unreviewed_code_blocked(self):
        for invalid in (1000, True, None, " 1000 ", "1010", "9998", "synthetic-roof", ""):
            with self.subTest(invalid=invalid), self.assertRaises(RoofCodeError):
                classify(invalid)

    def test_official_gml_dictionary_synthetic_shape_accepted(self):
        evidence = verify_original_ad_v_xml(synthetic_codebook())
        self.assertEqual(evidence["reviewed_code_count"], 15)
        self.assertTrue(evidence["codebook_exact_match"])
        self.assertFalse(evidence["raw_xml_embedded"])
        self.assertFalse(evidence["vulnerability_mapping_approved"])
        self.assertEqual(evidence["original_xml_bytes"], len(synthetic_codebook()))

    def test_gml_label_drift_and_invalid_original_xml_blocked(self):
        good = synthetic_codebook()
        for content in (
            good.replace(b"Flachdach", b"Flachdech"),
            good.replace(b"1000", b"1001"),
            good.replace(b"gml", b"foo"),
            b'<!DOCTYPE evil [ <!ENTITY x "invented"> ]>' + good,
            b"not xml",
            b" " * (MAX_CODELIST_BYTES + 1),
        ):
            with self.subTest(size=len(content)), self.assertRaises(RoofCodeError):
                verify_original_ad_v_xml(content)
        with self.assertRaises(RoofCodeError):
            verify_original_ad_v_xml(good, media_type="text/html")

    def test_roof_mixed_root_and_two_distinct_part_roofs_are_not_conflated(self):
        receipt = audit_cityjson_roof_codes(sample())
        self.assertEqual(receipt["root_roof_code_counts"], {"5000": 1})
        self.assertEqual(receipt["part_roof_code_counts"], {"1000": 1, "3100": 1})
        self.assertEqual(receipt["root_mixed_or_other_roof_form"], 1)
        self.assertEqual(receipt["root_specific_roof_form"], 0)
        self.assertEqual(receipt["roots_with_multiple_part_roof_codes"], 1)
        self.assertFalse(receipt["roof_covering_material_inferred"])
        self.assertFalse(receipt["single_building_roof_imputed_from_parts"])
        self.assertFalse(receipt["vulnerability_class_assigned"])
        self.assertNotIn("fictional-root", json.dumps(receipt))

    def test_root_without_code_preserves_child_only_ambiguity(self):
        receipt = audit_cityjson_roof_codes(sample(root_roof=None))
        self.assertEqual(receipt["root_missing_roof_form"], 1)
        self.assertEqual(receipt["root_missing_with_part_roof"], 1)
        self.assertEqual(receipt["root_specific_roof_form"], 0)
        self.assertEqual(receipt["roots_with_multiple_part_roof_codes"], 1)

    def test_unreviewed_codes_or_multiple_parents_rejected(self):
        for invalid in (1010, "1010", 1000, "synthetic-roof", True):
            with self.subTest(code=invalid), self.assertRaises(RoofCodeError):
                audit_cityjson_roof_codes(sample(root_roof=invalid))
        document = json.loads(sample())
        document["CityObjects"]["fictional-part-0"]["parents"] = ["fictional-root", "other"]
        with self.assertRaises(RoofCodeError):
            audit_cityjson_roof_codes(json.dumps(document).encode())

    def test_xml_command_offline_never_calls_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invented.xml"
            path.write_bytes(synthetic_codebook())
            stdout = io.StringIO()
            with patch("scripts.nrw_lod2_roof_code_gate_v0.fetch_official_xml", side_effect=AssertionError("network")):
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(main(["--offline-xml", str(path)]), 0)
            evidence = json.loads(stdout.getvalue())
            self.assertFalse(evidence["live_http_verified"])
            self.assertEqual(evidence["source"], ROOF_CODELIST_URL)

    def test_bounded_live_official_get_mocked(self):
        payload = synthetic_codebook()
        self_test = self

        class Response:
            status = 200
            headers = {"Content-Type": "text/xml; charset=UTF-8", "Content-Length": str(len(payload))}
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def geturl(self): return ROOF_CODELIST_URL
            def read(self, size):
                self_test.assertEqual(size, MAX_CODELIST_BYTES + 1)
                return payload

        class Opener:
            def open(self, request, timeout):
                self_test.assertEqual(request.full_url, ROOF_CODELIST_URL)
                self_test.assertEqual(request.get_method(), "GET")
                self_test.assertEqual(timeout, 12)
                return Response()

        with patch("scripts.nrw_lod2_roof_code_gate_v0.build_opener", return_value=Opener()):
            raw, media = fetch_official_xml()
        self.assertEqual(raw, payload)
        self.assertTrue(media.startswith("text/xml"))


if __name__ == "__main__":
    unittest.main()
