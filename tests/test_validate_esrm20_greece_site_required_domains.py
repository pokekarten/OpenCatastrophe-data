# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts import validate_esrm20_greece_site_required_domains as subject


def _xml(site_rows: list[dict[str, str]]) -> bytes:
    sites = []
    for row in site_rows:
        attributes = " ".join(
            f'{name}="{value}"'
            for name, value in {
                "lat": "37.98",
                "lon": "23.72",
                **row,
            }.items()
        )
        sites.append(f"<site {attributes}/>")
    return (
        '<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">'
        "<siteModel>"
        + "".join(sites)
        + "</siteModel></nrml>"
    ).encode("utf-8")


def _profile(raw: bytes, *, expected_site_count: int) -> dict[str, object]:
    return subject.profile_required_site_domains(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_site_count=expected_site_count,
    )


class GreeceSiteRequiredDomainTests(unittest.TestCase):
    def test_classifies_required_consumer_domains_without_uplift(self) -> None:
        raw = _xml(
            [
                {
                    "region": "1",
                    "slope": "0.0001",
                    "geology": "CENOZOIC",
                },
                {
                    "region": "4",
                    "slope": "0.4",
                    "geology": "UNKNOWN",
                },
            ]
        )
        result = _profile(raw, expected_site_count=2)
        domains = result["parameter_domains"]

        self.assertEqual(
            result["required_site_parameter_names"],
            list(subject.REQUIRED_PARAMETERS),
        )
        self.assertEqual(result["required_consumer_domain_reject_total"], 0)
        self.assertEqual(domains["region"]["calibrated_region_count"], 2)
        self.assertEqual(domains["region"]["runtime_default_region_count"], 0)
        self.assertEqual(domains["slope"]["finite_binary64_count"], 2)
        self.assertEqual(domains["slope"]["below_clamp_floor_count"], 1)
        self.assertEqual(domains["slope"]["above_clamp_ceiling_count"], 1)
        self.assertEqual(
            domains["geology"]["recognized_calibrated_label_count"],
            2,
        )

        self.assertFalse(result["required_static_compatibility_complete"])
        self.assertFalse(result["openquake_runtime_value_acceptance_verified"])
        self.assertFalse(result["crs_coordinate_semantics_verified"])
        self.assertFalse(result["missingness_semantics_verified"])
        self.assertFalse(result["gsim_site_parameter_sufficiency_verified"])
        self.assertFalse(result["site_adjusted_reference_authorized"])
        self.assertFalse(result["benchmark_agreement_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_expected_region_and_geology_sets_match_frozen_fingerprints(self) -> None:
        geology = sorted(subject.RECOGNIZED_GEOLOGY_LABELS)
        rows = [
            {
                "region": str(1 + (index % 4)),
                "slope": "0.1",
                "geology": label,
            }
            for index, label in enumerate(geology)
        ]
        result = _profile(_xml(rows), expected_site_count=len(rows))
        domains = result["parameter_domains"]

        self.assertTrue(domains["region"]["matches_expected_exact_value_set"])
        self.assertTrue(domains["geology"]["matches_expected_exact_value_set"])
        self.assertTrue(result["required_static_compatibility_complete"])

    def test_slope_requires_finite_binary64_even_when_decimal_is_finite(self) -> None:
        raw = _xml(
            [
                {
                    "region": "1",
                    "slope": "1e9999",
                    "geology": "CENOZOIC",
                }
            ]
        )
        result = _profile(raw, expected_site_count=1)
        slope = result["parameter_domains"]["slope"]

        self.assertEqual(slope["finite_decimal_count"], 1)
        self.assertEqual(slope["finite_binary64_count"], 0)
        self.assertEqual(slope["consumer_domain_reject_count"], 1)
        self.assertEqual(result["required_consumer_domain_reject_total"], 1)

    def test_region_default_is_distinguished_from_rejection(self) -> None:
        raw = _xml(
            [
                {
                    "region": "0",
                    "slope": "0.1",
                    "geology": "CENOZOIC",
                },
                {
                    "region": "6",
                    "slope": "0.1",
                    "geology": "CENOZOIC",
                },
            ]
        )
        result = _profile(raw, expected_site_count=2)
        region = result["parameter_domains"]["region"]

        self.assertEqual(region["runtime_default_region_count"], 1)
        self.assertEqual(region["calibrated_region_count"], 0)
        self.assertEqual(region["consumer_domain_reject_count"], 1)

    def test_unrecognized_geology_is_visible_as_fixed_effects_fallback(self) -> None:
        raw = _xml(
            [
                {
                    "region": "1",
                    "slope": "0.1",
                    "geology": "NOT-CALIBRATED",
                }
            ]
        )
        result = _profile(raw, expected_site_count=1)
        geology = result["parameter_domains"]["geology"]

        self.assertEqual(geology["recognized_calibrated_label_count"], 0)
        self.assertEqual(geology["fixed_effects_fallback_label_count"], 1)
        self.assertEqual(geology["consumer_domain_reject_count"], 1)

    def test_missing_or_namespaced_required_parameter_fails_closed(self) -> None:
        missing = _xml([{"region": "1", "slope": "0.1"}])
        with self.assertRaisesRegex(subject.GreeceSiteDomainError, "missing required"):
            _profile(missing, expected_site_count=1)

        namespaced = (
            '<nrml xmlns="http://openquake.org/xmlns/nrml/0.5" '
            'xmlns:x="urn:test"><siteModel>'
            '<site lat="37.98" lon="23.72" region="1" slope="0.1" '
            'x:geology="CENOZOIC"/></siteModel></nrml>'
        ).encode("utf-8")
        with self.assertRaisesRegex(
            subject.GreeceSiteDomainError,
            "unexpectedly namespaced",
        ):
            _profile(namespaced, expected_site_count=1)

    def test_wrong_byte_identity_and_site_count_fail_closed(self) -> None:
        raw = _xml(
            [
                {
                    "region": "1",
                    "slope": "0.1",
                    "geology": "CENOZOIC",
                }
            ]
        )
        with self.assertRaisesRegex(subject.GreeceSiteDomainError, "site-profile gate"):
            subject.profile_required_site_domains(
                raw,
                expected_byte_count=len(raw),
                expected_sha256="0" * 64,
                expected_site_count=1,
            )
        with self.assertRaisesRegex(subject.GreeceSiteDomainError, "site count"):
            _profile(raw, expected_site_count=2)

    def test_output_contains_no_synthetic_values_rows_or_coordinates(self) -> None:
        raw = _xml(
            [
                {
                    "region": "3",
                    "slope": "0.0123456789",
                    "geology": "SYNTHETIC-UNRECOGNIZED",
                }
            ]
        )
        result = _profile(raw, expected_site_count=1)
        encoded = json.dumps(result, sort_keys=True)

        self.assertNotIn("0.0123456789", encoded)
        self.assertNotIn("SYNTHETIC-UNRECOGNIZED", encoded)
        self.assertNotIn("37.98", encoded)
        self.assertNotIn("23.72", encoded)
        self.assertFalse(result["raw_xml_returned"])
        self.assertFalse(result["raw_attribute_values_returned"])
        self.assertFalse(result["raw_site_rows_returned"])
        self.assertFalse(result["raw_coordinates_returned"])

    def test_production_constants_bind_exact_public_evidence(self) -> None:
        self.assertEqual(subject.SOURCE_ISSUE, 285)
        self.assertEqual(subject.SITE_STRUCTURE_RESULT_COMMENT_ID, 5389106408)
        self.assertEqual(subject.SEMANTICS_HANDOFF_COMMENT_ID, 5393126444)
        self.assertEqual(subject.OPENQUAKE_VERSION, "3.13.0")
        self.assertEqual(
            subject.OPENQUAKE_COMMIT,
            "16dd69ecea0c6dcaf49c22ca12edc9da3f024889",
        )
        self.assertEqual(
            subject.OPENQUAKE_GSIM,
            "KothaEtAl2020ESHM20SlopeGeology",
        )
        self.assertEqual(subject.EXPECTED_SITE_COUNT, 1491)
        self.assertEqual(
            subject.EXPECTED_REGION_VALUE_SET_SHA256,
            "2100f74540b48d50e35963625f64f84081c74ca7512bc605dc7da10ddc0bffef",
        )
        self.assertEqual(
            subject.EXPECTED_GEOLOGY_VALUE_SET_SHA256,
            "8d9e1a295e459ee88ede1140a5bd01478d3638993cdb79994a2bc2010818c583",
        )


if __name__ == "__main__":
    unittest.main()
