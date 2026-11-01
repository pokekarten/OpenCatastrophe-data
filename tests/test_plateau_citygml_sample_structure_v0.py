# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests. No downloaded source bytes or personal/insured building data."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from research_runners import plateau_citygml_sample_structure_v0 as inspector
from research_runners.plateau_citygml_sample_structure_v0 import (
    CityGMLPreflightError,
    inspect_gml_bytes,
    main,
)

CORE = "http://www.opengis.net/citygml/2.0"
GML = "http://www.opengis.net/gml"
BLDG = "http://www.opengis.net/citygml/building/2.0"
CRS = "http://www.opengis.net/def/crs/EPSG/0/6697"


def sample_xml(*, buildings: str | None = None, envelope: str | None = None) -> bytes:
    if envelope is None:
        envelope = (
            f'<gml:Envelope srsName="{CRS}" srsDimension="3">'
            '<gml:lowerCorner>35.65 139.65 12.0</gml:lowerCorner>'
            '<gml:upperCorner>35.71 139.77 89.0</gml:upperCorner>'
            '</gml:Envelope>'
        )
    if buildings is None:
        buildings = (
            '<core:cityObjectMember><bldg:Building gml:id="building_synthetic_1">'
            '<bldg:measuredHeight uom="m">18.75</bldg:measuredHeight>'
            '<bldg:lod1Solid><gml:Solid/></bldg:lod1Solid>'
            '</bldg:Building></core:cityObjectMember>'
            '<core:cityObjectMember><bldg:Building gml:id="building_synthetic_2">'
            '<bldg:lod0FootPrint><gml:MultiSurface/></bldg:lod0FootPrint>'
            '</bldg:Building></core:cityObjectMember>'
        )
    return (
        f'<core:CityModel xmlns:core="{CORE}" xmlns:gml="{GML}" xmlns:bldg="{BLDG}">'
        f'<gml:boundedBy>{envelope}</gml:boundedBy>{buildings}</core:CityModel>'
    ).encode("utf-8")


def one_building(inner: str = "", id_value: str = "building_synthetic_1") -> str:
    return (
        f'<core:cityObjectMember><bldg:Building gml:id="{id_value}">'
        f'{inner}</bldg:Building></core:cityObjectMember>'
    )


class CityGmlSampleStructureTests(unittest.TestCase):
    def test_valid_synthetic_two_building_sample_flags_not_model_ready(self):
        raw = sample_xml()
        result = inspect_gml_bytes(raw)
        self.assertEqual(result["local_gml_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["local_gml_byte_count"], len(raw))
        self.assertEqual(result["building_element_count"], 2)
        self.assertEqual(result["measured_height_m_count"], 1)
        self.assertEqual(result["measured_height_missing_count"], 1)
        self.assertEqual(result["lod1_property_declared_building_count"], 1)
        self.assertEqual(result["lod0_property_declared_building_count"], 1)
        self.assertEqual(result["root_envelope_crs"], "EPSG:6697")
        self.assertTrue(result["gml_ids_unique_within_sample"])
        for key in (
            "vertical_datum_independently_verified",
            "envelope_geographic_location_verified",
            "original_zip_member_crc_verified",
            "original_provider_bytes_authenticated",
            "municipality_release_identity_verified",
            "geometry_topology_validated",
            "height_measurement_method_verified",
            "full_xml_schema_validated",
            "licence_and_privacy_cleared",
            "model_input_approved",
            "provider_network_access",
        ):
            self.assertFalse(result[key], key)
        serialized = json.dumps(result)
        for secret in ("building_synthetic", "35.65", "139.77", "18.75"):
            self.assertNotIn(secret, serialized)

    def test_declared_lods_do_not_prove_any_geometry(self):
        building = one_building(
            '<bldg:lod2Solid/><bldg:lod3MultiSurface/>'
        )
        result = inspect_gml_bytes(sample_xml(buildings=building))
        self.assertEqual(result["lod2_property_declared_building_count"], 1)
        self.assertEqual(result["lod3_property_declared_building_count"], 1)
        self.assertFalse(result["geometry_topology_validated"])

    def test_building_parts_counted_separately_from_building_heights(self):
        building = one_building(
            '<bldg:consistsOfBuildingPart><bldg:BuildingPart gml:id="part_synthetic">'
            '<bldg:measuredHeight uom="m">12</bldg:measuredHeight>'
            '</bldg:BuildingPart></bldg:consistsOfBuildingPart>'
        )
        result = inspect_gml_bytes(sample_xml(buildings=building))
        self.assertEqual(result["building_part_element_count"], 1)
        self.assertEqual(result["building_element_count"], 1)
        self.assertEqual(result["measured_height_m_count"], 0)

    def test_missing_buildings_fail(self):
        with self.assertRaisesRegex(CityGMLPreflightError, "no directly declared buildings"):
            inspect_gml_bytes(sample_xml(buildings=""))

    def test_wrong_crs_and_2d_crs_blocked(self):
        for crs in (
            "http://www.opengis.net/def/crs/EPSG/0/6668",
            "EPSG:4326", "http://www.opengis.net/def/crs/EPSG/0/6677"
        ):
            with self.subTest(crs=crs):
                xml = sample_xml().replace(CRS.encode(), crs.encode())
                with self.assertRaises(CityGMLPreflightError):
                    inspect_gml_bytes(xml)

    def test_missing_crs_or_dimension_blocked(self):
        for old in (f'srsName="{CRS}"', 'srsDimension="3"'):
            with self.subTest(old=old):
                raw = sample_xml().replace(old.encode(), b"")
                with self.assertRaisesRegex(CityGMLPreflightError, "envelope must explicitly"):
                    inspect_gml_bytes(raw)

    def test_nested_crs_override_or_dimension_conflict_blocked(self):
        for attr in ('srsName="EPSG:4326"', 'srsDimension="2"'):
            raw = sample_xml(buildings=one_building(f'<gml:Polygon {attr}/>'))
            with self.subTest(attr=attr), self.assertRaises(CityGMLPreflightError):
                inspect_gml_bytes(raw)

    def test_inverted_or_zero_extent_envelope_blocked(self):
        for corner in (
            "35.60 139.77 100", "35.65 139.65 12.0"
        ):
            with self.subTest(corner=corner):
                raw = sample_xml().replace(
                    b"<gml:upperCorner>35.71 139.77 89.0</gml:upperCorner>",
                    f"<gml:upperCorner>{corner}</gml:upperCorner>".encode()
                )
                with self.assertRaises(CityGMLPreflightError):
                    inspect_gml_bytes(raw)

    def test_nan_infinite_and_invalid_triples_blocked(self):
        for bad in ("NaN 139.65 10", "36 139 Infinity", "35 139", "35 139 0 1"):
            with self.subTest(bad=bad):
                raw = sample_xml().replace(b"35.65 139.65 12.0", bad.encode())
                with self.assertRaises(CityGMLPreflightError):
                    inspect_gml_bytes(raw)

    def test_duplicate_building_id_blocks(self):
        member = one_building() + one_building()
        with self.assertRaisesRegex(CityGMLPreflightError, "duplicated"):
            inspect_gml_bytes(sample_xml(buildings=member))

    def test_bad_or_missing_gml_id_blocks(self):
        for val in ('', 'a b', '0', 'x' * 200):
            with self.subTest(id=val[:10]):
                with self.assertRaises(CityGMLPreflightError):
                    inspect_gml_bytes(sample_xml(buildings=one_building(id_value=val)))
        no_id = one_building().replace(' gml:id="building_synthetic_1"', "")
        with self.assertRaisesRegex(CityGMLPreflightError, "missing gml:id"):
            inspect_gml_bytes(sample_xml(buildings=no_id))

    def test_invalid_height_unit_and_numeric_values_block(self):
        for text, unit in (("20", "ft"), ("-1", "m"), ("0", "m"), ("NaN", "m"), ("1001", "m")):
            with self.subTest(text=text, unit=unit):
                raw = sample_xml(buildings=one_building(
                    f'<bldg:measuredHeight uom="{unit}">{text}</bldg:measuredHeight>'
                ))
                with self.assertRaises(CityGMLPreflightError):
                    inspect_gml_bytes(raw)

    def test_duplicate_measured_height_blocked(self):
        with self.assertRaisesRegex(CityGMLPreflightError, "duplicate measuredHeight"):
            inspect_gml_bytes(sample_xml(buildings=one_building(
                '<bldg:measuredHeight uom="m">1</bldg:measuredHeight>'
                '<bldg:measuredHeight uom="m">2</bldg:measuredHeight>'
            )))

    def test_dtd_and_entities_rejected_without_resolution(self):
        for insertion in (b'<!DOCTYPE core:CityModel [<!ENTITY x "expanded">]>',
                          b'<!DOCTYPE core:CityModel SYSTEM "file:///etc/passwd">'):
            with self.subTest(insertion=insertion[:20]):
                raw = b'<?xml version="1.0"?>' + insertion + sample_xml()
                with self.assertRaisesRegex(CityGMLPreflightError, "DTD"):
                    inspect_gml_bytes(raw)

    def test_malformed_xml_and_wrong_root_namespace_rejected(self):
        for raw in (b"<bad", b"<CityModel/>", sample_xml().replace(CORE.encode(), b"urn:bad")):
            with self.subTest(raw=raw[:20]):
                with self.assertRaises(CityGMLPreflightError):
                    inspect_gml_bytes(raw)

    def test_finite_element_budget_enforced(self):
        with patch.object(inspector, "MAX_XML_ELEMENTS", 5):
            with self.assertRaisesRegex(CityGMLPreflightError, "element count"):
                inspect_gml_bytes(sample_xml())

    def test_finite_depth_budget_enforced(self):
        nested = "<gml:description>" * 65 + "</gml:description>" * 65
        with self.assertRaisesRegex(CityGMLPreflightError, "depth"):
            inspect_gml_bytes(sample_xml(buildings=one_building(nested)))

    def test_input_size_bound(self):
        for raw in (b"", b"x" * (inspector.MAX_GML_BYTES + 1)):
            with self.assertRaises(CityGMLPreflightError):
                inspect_gml_bytes(raw)

    def test_cli_uses_safe_local_reader_and_never_prints_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic_citygml.gml"
            path.write_bytes(sample_xml())
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(["--input", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(err.getvalue(), "")
            self.assertEqual(json.loads(out.getvalue())["building_element_count"], 2)
            self.assertNotIn(str(path), out.getvalue())

    def test_nonexistent_cli_input_fails_without_path_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sensitive_path_missing.gml"
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(main(["--input", str(path)]), 2)
            self.assertEqual(out.getvalue(), "")
            self.assertIn("BLOCKED:", err.getvalue())
            self.assertNotIn(str(path), err.getvalue())


if __name__ == "__main__":
    unittest.main()
