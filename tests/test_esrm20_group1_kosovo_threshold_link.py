# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only scientific scope tests; no provider bytes in fixtures."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from research_runners import esrm20_group1_kosovo_threshold_link as subject


def _settings(*, minimum="2000", present=True, mode="ebrisk"):
    return {
        "calculation_mode": mode,
        "calculation_mode_present": True,
        "minimum_asset_loss_structural": minimum,
        "minimum_asset_loss_structural_present": present,
        "defaults_inferred": False,
    }


def _source_profile():
    return {
        "schema_version": subject.runtime.SCHEMA_VERSION,
        "project_id": subject.config.PROJECT_ID,
        "project_path": subject.config.PROJECT_PATH,
        "commit_sha": subject.config.COMMIT_SHA,
        "candidate_key": subject.config.GROUP1_KEY,
        "repository_path": subject.config.GROUP1_PATH,
        "byte_count": subject.config.GROUP1_BYTE_COUNT,
        "sha256": subject.config.GROUP1_SHA256,
        "raw_config_returned": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "runtime_scalars": _settings(),
    }


class Group1ThresholdLinkTests(unittest.TestCase):
    def compare(self, *, source=None, derived=None, identical=True):
        return subject.compare_profiles(
            source_profile=_source_profile() if source is None else source,
            derived_runtime=_settings() if derived is None else derived,
            reconstructed_bytes_identical=identical,
        )

    def test_matching_explicit_minimum_loss_is_config_scope_only(self):
        result = self.compare()
        self.assertEqual(result["status"], "GROUP1_SOURCE_TO_RECONSTRUCTED_THRESHOLD_EQUIVALENT")
        self.assertTrue(result["source_config_threshold_match_verified"])
        self.assertEqual(result["source_group1_minimum_asset_loss_structural_eur"], 2000)
        self.assertEqual(result["reconstructed_minimum_asset_loss_structural_eur"], 2000)
        for flag in (
            "historical_group_assignment_verified",
            "published_esrm20_same_group_config_verified",
            "published_esrm20_same_threshold_verified",
            "threshold_compatibility_verified",
            "denominator_semantics_verified",
            "annualization_semantics_verified",
            "reference_loss_agreement_verified",
            "external_bytes_persisted",
            "provider_values_returned",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[flag], False, flag)

    @staticmethod
    def source_membership_ini(*, change_exposure=False, duplicate=False, omit_kosovo=False):
        countries = [f"Country{chr(65 + i)}" for i in range(22)] + ["Kosovo"]
        if omit_kosovo:
            countries[-1] = "CountryZ"
        if duplicate:
            countries[-1] = countries[0]
        exposed = list(countries)
        if change_exposure:
            exposed[-1] = "AnotherCountry"
        sites = "\n".join(
            f"    ../Vs30/Site_model_{name}.xml" for name in countries
        )
        exposures = "\n".join(
            f"    ../Exposure/OQ_Exposure_Input_{name}.xml" for name in exposed
        )
        return (
            "[site_params]\nsite_model_file =\n" + sites + "\n"
            "[exposure]\nexposure_file =\n" + exposures + "\n"
        )

    def test_source_group1_kosovo_site_and_exposure_membership(self):
        result = subject._group1_country_membership(self.source_membership_ini())
        self.assertEqual(result["source_group1_country_count"], 23)
        self.assertTrue(result["source_group1_kosovo_site_model_present"])
        self.assertTrue(result["source_group1_kosovo_exposure_present"])
        self.assertTrue(result["source_group1_site_exposure_lists_identical"])
        self.assertIs(result["published_kosovo_output_group_assignment_verified"], False)

    def test_group1_source_membership_missing_duplicate_and_mismatch_rejected(self):
        for variant in (
            {"change_exposure": True},
            {"duplicate": True},
            {"omit_kosovo": True},
        ):
            with self.subTest(variant=variant):
                with self.assertRaises(subject.SourceThresholdLinkError):
                    subject._group1_country_membership(
                        self.source_membership_ini(**variant)
                    )

    def test_group1_source_membership_wrong_count_or_path_rejected(self):
        original = self.source_membership_ini()
        with self.assertRaises(subject.SourceThresholdLinkError):
            subject._group1_country_membership(
                original.replace("Site_model_CountryA.xml", "Site_model_missing.xml")
            )
        with self.assertRaises(subject.SourceThresholdLinkError):
            subject._group1_country_membership(
                original.replace("    ../Vs30/Site_model_CountryA.xml\n", "")
            )
        with self.assertRaises(subject.SourceThresholdLinkError):
            subject._group1_country_membership(
                original.replace("../Vs30/", "../../Vs30/", 1)
            )

    def test_changed_source_hash_rejected_even_with_same_runtime(self):
        source = _source_profile()
        source["sha256"] = "0" * 64
        with self.assertRaisesRegex(subject.SourceThresholdLinkError, "identity"):
            self.compare(source=source)

    def test_unverified_publisher_or_model_authority_rejected(self):
        source = _source_profile()
        source["historical_group_assignment_verified"] = True
        with self.assertRaisesRegex(subject.SourceThresholdLinkError, "authority"):
            self.compare(source=source)

    def test_derived_config_must_match_exact_transform(self):
        with self.assertRaisesRegex(subject.SourceThresholdLinkError, "deterministic"):
            self.compare(identical=False)

    def test_changed_or_implicit_minimum_loss_rejected(self):
        for variant in (
            _settings(minimum="0"), _settings(minimum="2500"),
            _settings(present=False), _settings(mode="scenario_risk"),
            {**_settings(), "defaults_inferred": True},
        ):
            with self.subTest(variant=variant):
                with self.assertRaises(subject.SourceThresholdLinkError):
                    self.compare(derived=variant)
        source = _source_profile()
        source["runtime_scalars"] = _settings(minimum="0")
        with self.assertRaises(subject.SourceThresholdLinkError):
            self.compare(source=source)

    def test_non_boolean_identical_flag_not_accepted(self):
        with self.assertRaises(subject.SourceThresholdLinkError):
            self.compare(identical=1)

    def test_reuses_existing_source_authorities_before_reporting(self):
        group1 = b"synthetic group1, not source data"
        derived = (
            b"[general]\ncalculation_mode = ebrisk\n"
            b"minimum_asset_loss = {'structural': 2000}\n"
        )
        with tempfile.TemporaryDirectory() as temp:
            source_path = Path(temp) / "group1.ini"
            derived_path = Path(temp) / "reconstructed.ini"
            source_path.write_bytes(group1)
            derived_path.write_bytes(derived)
            with mock.patch.object(
                subject.config, "build_kosovo_residential_ebrisk_config",
                return_value=(derived, {}),
            ) as builder, mock.patch.object(
                subject.runtime, "project_group1_risk_runtime_scalars",
                return_value=_source_profile(),
            ) as projector, mock.patch.object(
                subject, "_group1_country_membership",
                return_value={
                    "source_group1_country_count": 23,
                    "source_group1_kosovo_site_model_present": True,
                    "source_group1_kosovo_exposure_present": True,
                    "source_group1_site_exposure_lists_identical": True,
                    "published_kosovo_output_group_assignment_verified": False,
                },
            ) as country_check:
                result = subject.run(source_path, derived_path)
            country_check.assert_called_once_with(group1.decode("utf-8"))
            builder.assert_called_once_with(group1)
            projector.assert_called_once_with(group1)
        self.assertTrue(result["source_config_threshold_match_verified"])

    def test_edited_reconstruction_fails_before_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "group1"
            dst = Path(temp) / "derived"
            src.write_bytes(b"source")
            dst.write_bytes(b"tampered")
            with mock.patch.object(
                subject.config, "build_kosovo_residential_ebrisk_config",
                return_value=(b"original", {}),
            ), mock.patch.object(
                subject.runtime, "project_group1_risk_runtime_scalars",
            ) as projector:
                with self.assertRaisesRegex(subject.SourceThresholdLinkError, "differs"):
                    subject.run(src, dst)
                projector.assert_not_called()

    def test_oversized_input_is_refused_before_parser(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "oversized"
            path.write_bytes(b"x" * (subject.MAX_SOURCE_BYTES + 1))
            with self.assertRaisesRegex(subject.SourceThresholdLinkError, "bounded"):
                subject._read_bounded_file(path, subject.MAX_SOURCE_BYTES)


if __name__ == "__main__":
    unittest.main()
