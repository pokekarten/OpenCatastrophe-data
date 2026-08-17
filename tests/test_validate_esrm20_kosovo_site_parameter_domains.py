# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts import validate_esrm20_kosovo_site_parameter_domains as subject


def _xml(site_rows: list[dict[str, str]]) -> bytes:
    sites = []
    for row in site_rows:
        attributes = " ".join(
            f'{name}="{value}"'
            for name, value in {
                "lat": "42.0",
                "lon": "21.0",
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
    return subject.profile_site_parameter_domains(
        raw,
        expected_byte_count=len(raw),
        expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_site_count=expected_site_count,
    )


class KosovoSiteParameterDomainTests(unittest.TestCase):
    def test_classifies_static_domains_without_promoting_runtime_or_science(self) -> None:
        raw = _xml(
            [
                {
                    "vs30": "500",
                    "xvf": "-12.5",
                    "region": "2",
                    "slope": "0.01",
                    "geology": "CENOZOIC",
                },
                {
                    "vs30": "300",
                    "xvf": "20",
                    "region": "5",
                    "slope": "0.4",
                    "geology": "NOT-CALIBRATED",
                },
            ]
        )
        result = _profile(raw, expected_site_count=2)
        domains = result["parameter_domains"]

        self.assertEqual(result["required_site_parameter_names"], list(subject.REQUIRED_PARAMETERS))
        self.assertEqual(result["site_count"], 2)
        self.assertEqual(result["static_domain_reject_total"], 0)

        self.assertEqual(domains["vs30"]["positive_finite_count"], 2)
        self.assertEqual(domains["xvf"]["static_domain_match_count"], 2)
        self.assertEqual(domains["region"]["integral_numeric_count"], 2)
        self.assertEqual(domains["region"]["static_domain_match_count"], 2)
        self.assertEqual(domains["slope"]["within_clamp_interval_count"], 1)
        self.assertEqual(domains["slope"]["above_clamp_ceiling_count"], 1)
        self.assertEqual(domains["geology"]["recognized_calibrated_label_count"], 1)
        self.assertEqual(domains["geology"]["fixed_effects_fallback_label_count"], 1)

        self.assertTrue(result["static_domain_classification_complete"])
        self.assertFalse(result["openquake_runtime_value_acceptance_verified"])
        self.assertFalse(result["crs_coordinate_semantics_verified"])
        self.assertFalse(result["missingness_semantics_verified"])
        self.assertFalse(result["gsim_site_parameter_sufficiency_verified"])
        self.assertFalse(result["site_adjusted_reference_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_counts_domain_rejections_instead_of_hiding_them(self) -> None:
        raw = _xml(
            [
                {
                    "vs30": "0",
                    "xvf": "NaN",
                    "region": "6.5",
                    "slope": "NaN",
                    "geology": " ",
                }
            ]
        )
        result = _profile(raw, expected_site_count=1)
        domains = result["parameter_domains"]

        self.assertEqual(result["static_domain_reject_total"], 5)
        for name in subject.REQUIRED_PARAMETERS:
            self.assertEqual(domains[name]["static_domain_reject_count"], 1)

    def test_slope_clamping_is_reported_separately_from_rejection(self) -> None:
        raw = _xml(
            [
                {
                    "vs30": "400",
                    "xvf": "0",
                    "region": "0",
                    "slope": "-1",
                    "geology": "UNKNOWN",
                },
                {
                    "vs30": "450",
                    "xvf": "1",
                    "region": "1",
                    "slope": "0.0005",
                    "geology": "HOLOCENE",
                },
                {
                    "vs30": "500",
                    "xvf": "2",
                    "region": "2",
                    "slope": "0.3",
                    "geology": "PLEISTOCENE",
                },
            ]
        )
        result = _profile(raw, expected_site_count=3)
        slope = result["parameter_domains"]["slope"]

        self.assertEqual(slope["below_clamp_floor_count"], 1)
        self.assertEqual(slope["within_clamp_interval_count"], 2)
        self.assertEqual(slope["above_clamp_ceiling_count"], 0)
        self.assertEqual(slope["static_domain_reject_count"], 0)

    def test_missing_required_parameter_fails_closed(self) -> None:
        raw = _xml(
            [
                {
                    "vs30": "400",
                    "xvf": "0",
                    "region": "1",
                    "slope": "0.01",
                }
            ]
        )
        with self.assertRaisesRegex(subject.KosovoSiteDomainError, "missing required"):
            _profile(raw, expected_site_count=1)

    def test_namespaced_required_parameter_fails_closed(self) -> None:
        raw = (
            '<nrml xmlns="http://openquake.org/xmlns/nrml/0.5" xmlns:x="urn:test">'
            '<siteModel><site lat="42" lon="21" x:vs30="400" xvf="0" '
            'region="1" slope="0.01" geology="CENOZOIC"/></siteModel></nrml>'
        ).encode("utf-8")
        with self.assertRaisesRegex(subject.KosovoSiteDomainError, "unexpectedly namespaced"):
            _profile(raw, expected_site_count=1)

    def test_wrong_byte_identity_and_site_count_fail_closed(self) -> None:
        raw = _xml(
            [
                {
                    "vs30": "400",
                    "xvf": "0",
                    "region": "1",
                    "slope": "0.01",
                    "geology": "CENOZOIC",
                }
            ]
        )
        with self.assertRaisesRegex(subject.KosovoSiteDomainError, "site-profile gate"):
            subject.profile_site_parameter_domains(
                raw,
                expected_byte_count=len(raw),
                expected_sha256="0" * 64,
                expected_site_count=1,
            )
        with self.assertRaisesRegex(subject.KosovoSiteDomainError, "site count"):
            _profile(raw, expected_site_count=2)

    def test_output_contains_no_synthetic_provider_values_or_rows(self) -> None:
        raw = _xml(
            [
                {
                    "vs30": "123.456",
                    "xvf": "-7.89",
                    "region": "3",
                    "slope": "0.012345",
                    "geology": "SYNTHETIC-UNRECOGNIZED-LABEL",
                }
            ]
        )
        result = _profile(raw, expected_site_count=1)
        encoded = json.dumps(result, sort_keys=True)

        self.assertNotIn("123.456", encoded)
        self.assertNotIn("-7.89", encoded)
        self.assertNotIn("0.012345", encoded)
        self.assertNotIn("SYNTHETIC-UNRECOGNIZED-LABEL", encoded)
        self.assertFalse(result["raw_xml_returned"])
        self.assertFalse(result["raw_attribute_values_returned"])
        self.assertFalse(result["raw_site_rows_returned"])

    def test_production_wrapper_binds_public_evidence_and_exact_identity(self) -> None:
        self.assertEqual(subject.SITE_STRUCTURE_RESULT_COMMENT_ID, 5310018006)
        self.assertEqual(subject.REQUIRED_PARAMETER_HANDOFF_COMMENT_ID, 5310209812)
        self.assertEqual(subject.XVF_SEMANTICS_COMMENT_ID, 5310202888)
        self.assertEqual(
            subject.OPENQUAKE_COMMIT,
            "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
        )
        self.assertEqual(subject.EXPECTED_SITE_COUNT, 37)


if __name__ == "__main__":
    unittest.main()
