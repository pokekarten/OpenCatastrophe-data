# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from scripts import build_esrm20_kosovo_residential_exposure_wrapper as subject


def synthetic_source(*, assets: tuple[str, ...] = subject.SOURCE_ASSETS) -> bytes:
    asset_text = " ".join(assets)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4">
  <exposureModel id="exposure" category="buildings" taxonomySource="GEM taxonomy">
    <description>exposure model</description>
    <conversions><costTypes><costType name="structural" type="aggregated" unit="EUR"/></costTypes></conversions>
    <occupancyPeriods>day night transit</occupancyPeriods>
    <tagNames>occupancy name_2 id_2 id_1 name_1</tagNames>
    <assets>{asset_text}</assets>
  </exposureModel>
</nrml>'''.encode()


class KosovoResidentialWrapperTests(unittest.TestCase):
    def test_exact_identity_is_rejected_before_xml_interpretation(self) -> None:
        with mock.patch.object(
            subject.exposure_profile, "profile_xml_bytes"
        ) as profile:
            with (
                mock.patch.object(subject, "_CANONICAL_PROFILE_XML_BYTES", profile),
                self.assertRaisesRegex(
                    subject.KosovoResidentialWrapperError,
                    "^source wrapper byte identity mismatch$",
                ),
            ):
                subject.build_kosovo_residential_exposure_wrapper(b"not the source")
        profile.assert_not_called()

    def test_non_bytes_are_rejected_before_xml_interpretation(self) -> None:
        with (
            mock.patch.object(subject.exposure_profile, "profile_xml_bytes") as profile,
            self.assertRaisesRegex(
                subject.KosovoResidentialWrapperError,
                "^source wrapper must be bytes$",
            ),
        ):
            subject._verify_source_identity(bytearray(b"x"))  # type: ignore[arg-type]
        profile.assert_not_called()

    def test_verified_synthetic_source_derives_only_residential_deterministically(
        self,
    ) -> None:
        source = synthetic_source()
        first, evidence = subject._derive_from_verified_source(source)
        second, repeated_evidence = subject._derive_from_verified_source(source)

        self.assertEqual(first, second)
        self.assertEqual(evidence, repeated_evidence)
        profile = subject.exposure_profile.profile_xml_bytes(first)
        self.assertEqual(profile["asset_references"], [subject.SELECTED_ASSET])
        self.assertNotIn(b"_Com.csv", first)
        self.assertNotIn(b"_Ind.csv", first)
        self.assertEqual(evidence["experiment_label"], "reconstructed_experiment")
        self.assertEqual(evidence["scope"], "kosovo_residential_only")
        self.assertEqual(
            evidence["selected_asset"],
            {
                "repository_path": "Exposure/OQ_Exposure_Input_Kosovo_Res.csv",
                "byte_count": 160627,
                "sha256": "12a20d393c8d677d304263aed96eb05f81098104fd7e3fb0d119aafc336aa00f",
            },
        )
        self.assertEqual(evidence["output"]["byte_count"], len(first))
        self.assertEqual(
            evidence["output"]["sha256"], hashlib.sha256(first).hexdigest()
        )
        for boundary in (
            "source_wrapper_bytes_returned",
            "selected_asset_bytes_read",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
            "historical_reproduction",
            "value_structural_wiring_verified",
            "horizontal_component_conversion_applied",
        ):
            self.assertIs(evidence[boundary], False)
        self.assertIs(evidence["derived_wrapper_bytes_returned"], True)

    def test_unexpected_source_asset_set_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            subject.KosovoResidentialWrapperError,
            "^source wrapper semantic profile drifted$",
        ):
            subject._derive_from_verified_source(
                synthetic_source(assets=(subject.SELECTED_ASSET,))
            )

    def test_malformed_or_dtd_source_error_is_sanitized(self) -> None:
        for payload in (b"<broken", b'<!DOCTYPE x [<!ENTITY x "boom">]><x/>'):
            with (
                self.subTest(payload=payload),
                self.assertRaisesRegex(
                    subject.KosovoResidentialWrapperError,
                    "^source wrapper profile is invalid$",
                ),
            ):
                subject._derive_from_verified_source(payload)

    def test_live_authority_drift_fails_before_identity_or_profile(self) -> None:
        with (
            mock.patch.object(subject, "CONTROL_ISSUE", 999),
            mock.patch.object(subject, "_verify_source_identity") as verify,
            self.assertRaisesRegex(
                subject.KosovoResidentialWrapperError,
                "^control issue authority drifted$",
            ),
        ):
            subject.build_kosovo_residential_exposure_wrapper(b"x")
        verify.assert_not_called()

    def test_profiler_authority_drift_fails_before_identity(self) -> None:
        with (
            mock.patch.object(subject.exposure_profile, "EXPECTED_BYTE_COUNT", 999),
            mock.patch.object(subject, "_verify_source_identity") as verify,
            self.assertRaisesRegex(
                subject.KosovoResidentialWrapperError,
                "^profiler source byte count authority drifted$",
            ),
        ):
            subject.build_kosovo_residential_exposure_wrapper(b"x")
        verify.assert_not_called()

    def test_public_entry_runs_identity_before_semantic_profile(self) -> None:
        source = synthetic_source()
        with (
            mock.patch.object(subject, "_verify_source_identity", return_value="x") as verify,
            mock.patch.object(
                subject, "_derive_from_verified_source", return_value=(b"derived", {})
            ) as derive,
        ):
            self.assertEqual(
                subject.build_kosovo_residential_exposure_wrapper(source),
                (b"derived", {}),
            )
        verify.assert_called_once_with(source)
        derive.assert_called_once_with(source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
