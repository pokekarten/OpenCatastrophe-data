# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "profile_esrm20_scenario_v10_greece_rupture.py"
SPEC = importlib.util.spec_from_file_location("greece_rupture_profile", MODULE_PATH)
assert SPEC and SPEC.loader
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)

NS = profile.EXPECTED_NRML_NAMESPACE


def _xml(child: str = "simpleFaultRupture", *, namespace: str = NS) -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<nrml xmlns="{namespace}"><{child}>'
        f'<magnitude>5.9</magnitude><rake>0</rake>'
        f'<hypocenter lon="23.6" lat="38.2" depth="10"/>'
        f'</{child}></nrml>'
    ).encode("utf-8")


class FixedGreeceRuptureProfileTests(unittest.TestCase):
    def _profile_synthetic(self, data: bytes):
        return profile._profile_verified_greece_rupture(
            data,
            expected_byte_count=len(data),
            expected_sha256=hashlib.sha256(data).hexdigest(),
            expected_namespace=NS,
            allowed_rupture_elements=frozenset(
                {
                    "simpleFaultRupture",
                    "complexFaultRupture",
                    "singlePlaneRupture",
                    "multiPlanesRupture",
                    "griddedRupture",
                }
            ),
        )

    def test_production_identity_constants_match_trusted_receipt(self):
        self.assertEqual(profile.EXPECTED_BYTE_COUNT, 666)
        self.assertEqual(
            profile.EXPECTED_SHA256,
            "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b",
        )

    def test_public_entry_rejects_receipt_alias_drift_before_xml(self):
        with mock.patch.object(profile, "EXPECTED_BYTE_COUNT", 667), mock.patch.object(
            profile.ET, "fromstring"
        ) as parser:
            with self.assertRaisesRegex(
                profile.RuptureProfileError, "production_authority_drift:byte_count"
            ):
                profile.profile_fixed_greece_rupture(b"<nrml/>")
        parser.assert_not_called()

    def test_public_entry_rejects_sha_alias_drift_before_xml(self):
        with mock.patch.object(profile, "EXPECTED_SHA256", "0" * 64), mock.patch.object(
            profile.ET, "fromstring"
        ) as parser:
            with self.assertRaisesRegex(
                profile.RuptureProfileError, "production_authority_drift:sha256"
            ):
                profile.profile_fixed_greece_rupture(b"<nrml/>")
        parser.assert_not_called()

    def test_public_entry_rejects_rupture_allowlist_drift_before_xml(self):
        with mock.patch.object(
            profile,
            "OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS",
            frozenset({"notARupture"}),
        ), mock.patch.object(profile.ET, "fromstring") as parser:
            with self.assertRaisesRegex(
                profile.RuptureProfileError, "production_authority_drift:rupture_elements"
            ):
                profile.profile_fixed_greece_rupture(b"<nrml/>")
        parser.assert_not_called()

    def test_rejects_wrong_byte_count_before_xml(self):
        with self.assertRaisesRegex(profile.RuptureProfileError, "byte_count_mismatch"):
            profile.profile_fixed_greece_rupture(b"<nrml/>")

    def test_rejects_same_size_wrong_sha_before_xml(self):
        with self.assertRaisesRegex(profile.RuptureProfileError, "sha256_mismatch"):
            profile.profile_fixed_greece_rupture(b"x" * 666)

    def test_profiles_only_bounded_structure_and_keeps_authority_false(self):
        result = self._profile_synthetic(_xml())
        self.assertEqual(result["rupture_element_local_name"], "simpleFaultRupture")
        self.assertEqual(result["magnitude_element_count"], 1)
        self.assertEqual(result["rake_element_count"], 1)
        self.assertEqual(result["hypocenter_element_count"], 1)
        self.assertTrue(result["provider_file_content_profiled"])
        for key in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[key], False)
        self.assertNotIn("magnitude", result)
        self.assertNotIn("hypocenter", result)
        self.assertNotIn("rake", result)

    def test_does_not_guess_rupture_type_from_path_or_expected_type(self):
        result = self._profile_synthetic(_xml("singlePlaneRupture"))
        self.assertEqual(result["rupture_element_local_name"], "singlePlaneRupture")

    def test_openquake_3_12_1_individual_rupture_allowlist_is_frozen(self):
        self.assertEqual(
            profile.OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
            frozenset(
                {
                    "simpleFaultRupture",
                    "complexFaultRupture",
                    "singlePlaneRupture",
                    "multiPlanesRupture",
                    "griddedRupture",
                }
            ),
        )

    def test_rejects_unknown_same_namespace_rupture_type(self):
        with self.assertRaisesRegex(profile.RuptureProfileError, "unsupported_rupture_element"):
            self._profile_synthetic(_xml("notARupture"))

    def test_rejects_foreign_namespace(self):
        with self.assertRaisesRegex(profile.RuptureProfileError, "unexpected_nrml_root"):
            self._profile_synthetic(_xml(namespace="urn:not-nrml"))

    def test_rejects_multiple_top_level_children(self):
        data = (
            f'<nrml xmlns="{NS}"><simpleFaultRupture/><singlePlaneRupture/></nrml>'
        ).encode()
        with self.assertRaisesRegex(profile.RuptureProfileError, "rupture_top_level_cardinality"):
            self._profile_synthetic(data)

    def test_rejects_dtd_and_internal_entity_before_elementtree(self):
        data = (
            f'<!DOCTYPE nrml [<!ENTITY x "simpleFaultRupture">]>'
            f'<nrml xmlns="{NS}"><&x;/></nrml>'
        ).encode()
        with self.assertRaisesRegex(profile.RuptureProfileError, "dtd_or_entity_forbidden"):
            self._profile_synthetic(data)

    def test_rejects_utf16_before_dtd_or_parser_bypass(self):
        data = (
            f'<?xml version="1.0" encoding="UTF-16"?>'
            f'<!DOCTYPE nrml [<!ENTITY x "value">]><nrml xmlns="{NS}"/>'
        ).encode("utf-16")
        with self.assertRaisesRegex(profile.RuptureProfileError, "non_utf8_xml_encoding"):
            self._profile_synthetic(data)

    def test_rejects_utf8_bytes_with_conflicting_xml_encoding_declaration(self):
        data = (
            f'<?xml version="1.0" encoding="ISO-8859-1"?>'
            f'<nrml xmlns="{NS}"><simpleFaultRupture/></nrml>'
        ).encode("utf-8")
        with self.assertRaisesRegex(profile.RuptureProfileError, "xml_encoding_declaration_mismatch"):
            self._profile_synthetic(data)

    def test_rejects_non_bytes_exactly(self):
        with self.assertRaisesRegex(TypeError, "data must be bytes"):
            profile.profile_fixed_greece_rupture(bytearray(666))


if __name__ == "__main__":
    unittest.main()
