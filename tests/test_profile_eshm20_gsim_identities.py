# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from scripts import profile_eshm20_gsim_identities as profiler


def xml_for(branch_sets: str) -> str:
    return f"<nrml><logicTree>{branch_sets}</logicTree></nrml>"


def branch_set(
    *,
    set_id: str = "bs1",
    branch_id: str = "b1",
    model: str = "ExampleGsim",
    trt: str = "Active Shallow Crust",
    model_attrs: str = "",
    uncertainty_type: str = "gmpeModel",
) -> str:
    return f"""
    <logicTreeBranchSet uncertaintyType="{uncertainty_type}" branchSetID="{set_id}" applyToTectonicRegionType="{trt}">
      <logicTreeBranch branchID="{branch_id}">
        <uncertaintyModel{model_attrs}>{model}</uncertaintyModel>
        <uncertaintyWeight>1.0</uncertaintyWeight>
      </logicTreeBranch>
    </logicTreeBranchSet>
    """


class Eshm20GsimIdentityProfileTests(unittest.TestCase):
    def test_bare_model_token_is_profiled_without_runtime_claim(self) -> None:
        result = profiler._profile_xml_text(xml_for(branch_set()))
        self.assertEqual(result["branch_set_count"], 1)
        self.assertEqual(result["branch_count"], 1)
        self.assertEqual(
            result["unique_requested_gsim_tokens"], ["ExampleGsim"]
        )
        self.assertEqual(result["unique_argument_keys"], [])
        self.assertEqual(
            result["branches"][0]["tectonic_region_type"],
            "Active Shallow Crust",
        )
        self.assertEqual(
            result["branches"][0]["requested_gsim_token"], "ExampleGsim"
        )

    def test_explicit_table_collects_keys_but_never_values(self) -> None:
        model = """[AdjustedGsim]\nfoo = 1.25\nbar = 'secret-value'\n# ignored = 'comment'"""
        result = profiler._profile_xml_text(
            xml_for(branch_set(model=model, model_attrs=' baz="node-attribute-value"'))
        )
        record = result["branches"][0]
        self.assertEqual(record["requested_gsim_token"], "AdjustedGsim")
        self.assertEqual(record["argument_keys"], ["bar", "baz", "foo"])
        rendered = repr(result)
        self.assertNotIn("secret-value", rendered)
        self.assertNotIn("node-attribute-value", rendered)

    def test_output_is_deterministic_across_branch_order(self) -> None:
        first = branch_set(set_id="z", branch_id="z1", model="Zed")
        second = branch_set(set_id="a", branch_id="a1", model="Alpha")
        p1 = profiler._profile_xml_text(xml_for(first + second))
        p2 = profiler._profile_xml_text(xml_for(second + first))
        self.assertEqual(p1, p2)
        self.assertEqual(
            p1["unique_requested_gsim_tokens"], ["Alpha", "Zed"]
        )

    def test_unresolved_token_is_not_serialized_as_verified_gsim_name(self) -> None:
        token = "ExampleAliasToken"
        result = profiler._profile_xml_text(xml_for(branch_set(model=token)))
        self.assertEqual(
            result["branches"][0]["requested_gsim_token"], token
        )
        self.assertEqual(result["unique_requested_gsim_tokens"], [token])
        self.assertNotIn("gsim_name", result["branches"][0])
        self.assertNotIn("unique_gsim_names", result)

    def test_duplicate_ids_non_gmpe_and_ambiguous_models_fail_closed(self) -> None:
        cases = (
            xml_for(branch_set() + branch_set(set_id="bs2", branch_id="b1")),
            xml_for(branch_set(uncertainty_type="sourceModel")),
            xml_for(branch_set(model="[One]\nx = 1\n[Two]\ny = 2")),
            xml_for(branch_set(model="Bare\nx = 1")),
            xml_for(branch_set(model="[[ArrayTable]]\nx = 1")),
            xml_for(branch_set(model="[One]\nx = 1\nx = 2")),
            xml_for(branch_set(model="[One]\nx =")),
        )
        for xml_text in cases:
            with self.subTest(xml=xml_text), self.assertRaises(
                profiler.Eshm20GsimIdentityProfileError
            ):
                profiler._profile_xml_text(xml_text)

    def test_xml_security_boundaries_fail_closed(self) -> None:
        cases = (
            "<!DOCTYPE nrml><nrml />",
            "<!ENTITY x 'y'><nrml />",
            "<nrml>\x00</nrml>",
            "<nrml>",
        )
        for xml_text in cases:
            with self.subTest(xml=xml_text), self.assertRaises(
                profiler.Eshm20GsimIdentityProfileError
            ):
                profiler._profile_xml_text(xml_text)

    def test_payload_identity_is_checked_before_decode_or_xml(self) -> None:
        with self.assertRaisesRegex(
            profiler.Eshm20GsimIdentityProfileError, "byte count"
        ):
            profiler.profile_verified_gsim_identities(b"\xff")

        payload = b"\xff" * profiler.EXPECTED_BYTE_COUNT
        with self.assertRaisesRegex(
            profiler.Eshm20GsimIdentityProfileError, "SHA-256"
        ):
            profiler.profile_verified_gsim_identities(payload)

    def test_verified_profile_has_false_authority_ceilings(self) -> None:
        synthetic = xml_for(branch_set()).encode()
        digest = hashlib.sha256(synthetic).hexdigest()
        with (
            patch.object(profiler, "EXPECTED_BYTE_COUNT", len(synthetic)),
            patch.object(profiler, "EXPECTED_SHA256", digest),
            patch.object(profiler, "EXPECTED_BRANCH_SET_COUNT", 1),
            patch.object(profiler, "EXPECTED_BRANCH_COUNT", 1),
        ):
            result = profiler.profile_verified_gsim_identities(synthetic)

        self.assertFalse(result["alias_resolution_verified"])
        self.assertFalse(result["runtime_compatibility_verified"])
        self.assertFalse(result["gsim_instantiation_verified"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("ExampleGsim", str(result["openquake_reference"]))

    def test_tectonic_region_is_a_bounded_label_not_an_identifier(self) -> None:
        result = profiler._profile_xml_text(
            xml_for(branch_set(trt="Active Shallow Crust"))
        )
        self.assertEqual(
            result["branches"][0]["tectonic_region_type"],
            "Active Shallow Crust",
        )
        with self.assertRaises(profiler.Eshm20GsimIdentityProfileError):
            profiler._profile_xml_text(xml_for(branch_set(trt="bad\x01label")))

    def test_model_and_argument_identifiers_are_bounded(self) -> None:
        for model in ("Bad.Name", "[Bad.Name]", "[Good]\nbad-key = 1"):
            with self.subTest(model=model), self.assertRaises(
                profiler.Eshm20GsimIdentityProfileError
            ):
                profiler._profile_xml_text(xml_for(branch_set(model=model)))


if __name__ == "__main__":
    unittest.main()
