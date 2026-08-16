# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from scripts import profile_eshm20_source_model_trt as profiler


def nrml(
    body: str,
    *,
    namespace: str = profiler.NRML_04_NAMESPACE,
) -> bytes:
    return (
        f'<nrml xmlns="{namespace}">'
        f"<sourceModel name='synthetic'>{body}</sourceModel>"
        "</nrml>"
    ).encode()


def receipt_for(
    payload: bytes,
    path: str | None = None,
) -> profiler.ExpectedChildReceipt:
    canonical = profiler._canonical_paths()[0] if path is None else path
    return profiler.ExpectedChildReceipt(
        repository_path=canonical,
        byte_count=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
    )


class Eshm20SourceModelTrtProfileTests(unittest.TestCase):
    def test_direct_source_profiles_type_and_trt_without_sensitive_fields(self) -> None:
        payload = nrml(
            "<pointSource id='SECRET-ID' name='SECRET-NAME' "
            "tectonicRegion='Active Shallow Crust'>"
            "<pointGeometry><Point><pos>20.1 42.2</pos></Point></pointGeometry>"
            "<incrementalMFD minMag='4.5'>"
            "<occurRates>SECRET-RATES</occurRates></incrementalMFD>"
            "</pointSource>"
        )
        result = profiler.profile_receipted_source_model(
            payload,
            receipt_for(payload),
        )
        self.assertEqual(result["source_count"], 1)
        self.assertEqual(result["source_type_counts"], {"pointSource": 1})
        self.assertEqual(
            result["tectonic_region_type_counts"],
            {"Active Shallow Crust": 1},
        )
        self.assertEqual(
            result["trt_provenance_counts"],
            {"direct_source": 1},
        )
        rendered = repr(result)
        for forbidden in (
            "SECRET-ID",
            "SECRET-NAME",
            "20.1",
            "42.2",
            "SECRET-RATES",
            "4.5",
        ):
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(result["receipt_payload_identity_verified"])
        self.assertFalse(result["canonical_414_ledger_binding_verified"])
        self.assertFalse(result["source_gsim_trt_compatibility_verified"])

    def test_source_group_inherits_trt_and_matching_direct_value_is_explicit(self) -> None:
        payload = nrml(
            "<sourceGroup tectonicRegion='Subduction Interface'>"
            "<complexFaultSource id='a' name='a'/>"
            "<characteristicFaultSource id='b' name='b' "
            "tectonicRegion='Subduction Interface'/>"
            "</sourceGroup>",
            namespace=profiler.NRML_05_NAMESPACE,
        )
        result = profiler.profile_receipted_source_model(
            payload,
            receipt_for(payload),
        )
        self.assertEqual(result["source_count"], 2)
        self.assertEqual(
            result["source_type_counts"],
            {"characteristicFaultSource": 1, "complexFaultSource": 1},
        )
        self.assertEqual(
            result["tectonic_region_type_counts"],
            {"Subduction Interface": 2},
        )
        self.assertEqual(
            result["trt_provenance_counts"],
            {
                "group_inherited": 1,
                "group_effective_direct_confirmed": 1,
            },
        )

    def test_group_source_trt_conflict_fails_like_openquake_314_semantics(self) -> None:
        payload = nrml(
            "<sourceGroup tectonicRegion='A'>"
            "<pointSource id='x' name='x' tectonicRegion='B'/>"
            "</sourceGroup>",
            namespace=profiler.NRML_05_NAMESPACE,
        )
        with self.assertRaisesRegex(
            profiler.Eshm20SourceModelTrtProfileError,
            "conflicts",
        ):
            profiler.profile_receipted_source_model(
                payload,
                receipt_for(payload),
            )

    def test_missing_or_control_bearing_trt_fails_closed(self) -> None:
        cases = (
            nrml("<pointSource id='x' name='x'/>") ,
            nrml(
                "<sourceGroup tectonicRegion=''>"
                "<pointSource id='x' name='x'/></sourceGroup>",
                namespace=profiler.NRML_05_NAMESPACE,
            ),
            nrml("<pointSource id='x' name='x' tectonicRegion='bad&#1;label'/>") ,
        )
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(
                profiler.Eshm20SourceModelTrtProfileError
            ):
                profiler.profile_receipted_source_model(payload, receipt_for(payload))

    def test_unknown_source_tag_and_nested_group_fail_closed(self) -> None:
        cases = (
            nrml("<mysterySource tectonicRegion='A'/>") ,
            nrml(
                "<sourceGroup tectonicRegion='A'>"
                "<sourceGroup tectonicRegion='A'><pointSource/>"
                "</sourceGroup></sourceGroup>",
                namespace=profiler.NRML_05_NAMESPACE,
            ),
        )
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(
                profiler.Eshm20SourceModelTrtProfileError
            ):
                profiler.profile_receipted_source_model(payload, receipt_for(payload))

    def test_nrml_namespace_and_version_shape_are_bound_fail_closed(self) -> None:
        cases = (
            nrml("<pointSource tectonicRegion='A'/>", namespace="urn:not-nrml"),
            b"<nrml><sourceModel><pointSource tectonicRegion='A'/></sourceModel></nrml>",
            nrml(
                "<pointSource tectonicRegion='A'/>",
                namespace=profiler.NRML_05_NAMESPACE,
            ),
            nrml(
                "<sourceGroup tectonicRegion='A'><pointSource tectonicRegion='A'/></sourceGroup>",
                namespace=profiler.NRML_04_NAMESPACE,
            ),
            nrml(
                "<pointSource xmlns='urn:not-nrml' tectonicRegion='A'/>",
                namespace=profiler.NRML_04_NAMESPACE,
            ),
        )
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(
                profiler.Eshm20SourceModelTrtProfileError
            ):
                profiler.profile_receipted_source_model(payload, receipt_for(payload))

    def test_receipt_identity_is_checked_before_decode_or_xml(self) -> None:
        payload = b"\xff"
        expected = profiler.ExpectedChildReceipt(
            repository_path=profiler._canonical_paths()[0], byte_count=2, sha256="0" * 64
        )
        with self.assertRaisesRegex(profiler.Eshm20SourceModelTrtProfileError, "byte count"):
            profiler.profile_receipted_source_model(payload, expected)
        expected = profiler.ExpectedChildReceipt(
            repository_path=profiler._canonical_paths()[0], byte_count=1, sha256="0" * 64
        )
        with self.assertRaisesRegex(profiler.Eshm20SourceModelTrtProfileError, "SHA-256"):
            profiler.profile_receipted_source_model(payload, expected)

    def test_receipt_authority_drift_and_noncanonical_path_fail_closed(self) -> None:
        payload = nrml("<pointSource tectonicRegion='A'/>")
        bad_path = profiler.ExpectedChildReceipt(
            repository_path="other.xml",
            byte_count=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
        )
        with self.assertRaisesRegex(profiler.Eshm20SourceModelTrtProfileError, "fixed 51"):
            profiler.profile_receipted_source_model(payload, bad_path)
        bad_ledger = profiler.ExpectedChildReceipt(
            repository_path=profiler._canonical_paths()[0],
            byte_count=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            receipt_set_run_id=1,
        )
        with self.assertRaisesRegex(profiler.Eshm20SourceModelTrtProfileError, "receipt-set run"):
            profiler.profile_receipted_source_model(payload, bad_ledger)

    def test_fixed_authority_alias_drift_fails_before_acceptance(self) -> None:
        payload = nrml("<pointSource tectonicRegion='A'/>")
        receipt = receipt_for(payload)
        mutations = {
            "PROJECT_ID": 198,
            "PROJECT_PATH": "efehr/not-eshm20",
            "COMMIT_SHA": "0" * 40,
            "RECEIPT_SET_RESULT_COMMENT_ID": 1,
            "RECEIPT_SET_RUN_ID": 1,
            "RECEIPT_SET_EXECUTION_SHA": "0" * 40,
            "RECEIPT_SET_CHILD_COUNT": 50,
            "RECEIPT_SET_PATHS_SHA256": "0" * 64,
            "CHILD_PARENT_RESULT_COMMENT_ID": 1,
            "OPENQUAKE_COMMIT": "0" * 40,
            "NRML_04_NAMESPACE": "urn:not-nrml",
            "EXPECTED_CHILD_COUNT": 50,
            "EXPECTED_PATHS_SHA256": "0" * 64,
        }
        for name, value in mutations.items():
            with self.subTest(name=name), patch.object(profiler, name, value):
                with self.assertRaisesRegex(
                    profiler.Eshm20SourceModelTrtProfileError, "authority drifted"
                ):
                    profiler.profile_receipted_source_model(payload, receipt)

    def test_imported_authority_primitive_drift_fails_closed(self) -> None:
        payload = nrml("<pointSource tectonicRegion='A'/>")
        receipt = receipt_for(payload)
        with patch.object(profiler, "_require_canonical_child_set", lambda: ()):
            with self.assertRaisesRegex(
                profiler.Eshm20SourceModelTrtProfileError, "authority drifted"
            ):
                profiler.profile_receipted_source_model(payload, receipt)

    def test_xml_security_and_utf8_boundaries_fail_closed(self) -> None:
        samples = (
            b"<!DOCTYPE nrml><nrml/>",
            b"<!ENTITY x 'y'><nrml/>",
            b"<nrml>\x00</nrml>",
            b"<nrml>",
            b"\xff",
        )
        for payload in samples:
            with self.subTest(payload=payload), self.assertRaises(
                profiler.Eshm20SourceModelTrtProfileError
            ):
                profiler.profile_receipted_source_model(payload, receipt_for(payload))

    def test_source_count_bound_fails_closed(self) -> None:
        payload = nrml("<pointSource tectonicRegion='A'/><pointSource tectonicRegion='A'/>")
        with patch.object(profiler, "MAX_SOURCES_PER_FILE", 1):
            with self.assertRaisesRegex(profiler.Eshm20SourceModelTrtProfileError, "source count"):
                profiler.profile_receipted_source_model(payload, receipt_for(payload))

    def test_output_is_deterministic_across_attribute_order(self) -> None:
        first = nrml("<pointSource id='x' name='n' tectonicRegion='A'/>")
        second = nrml("<pointSource tectonicRegion='A' name='n' id='x'/>")
        self.assertEqual(
            profiler._profile_root(profiler._parse_xml(first)),
            profiler._profile_root(profiler._parse_xml(second)),
        )

    def test_aggregate_reprofiles_exact_51_unique_canonical_paths(self) -> None:
        receipted_payloads = []
        serialized_profiles = []
        for path in profiler._canonical_paths():
            payload = nrml("<pointSource tectonicRegion='A'/>")
            receipt = receipt_for(payload, path)
            receipted_payloads.append((payload, receipt))
            serialized_profiles.append(profiler.profile_receipted_source_model(payload, receipt))
        aggregate = profiler.aggregate_source_model_profiles(reversed(receipted_payloads))
        self.assertEqual(aggregate["child_count"], 51)
        self.assertEqual(aggregate["source_count"], 51)
        self.assertEqual(aggregate["source_type_counts"], {"pointSource": 51})
        self.assertEqual(aggregate["tectonic_region_type_counts"], {"A": 51})
        self.assertFalse(aggregate["canonical_414_ledger_binding_verified"])
        self.assertFalse(aggregate["source_gsim_trt_compatibility_verified"])
        with self.assertRaises(profiler.Eshm20SourceModelTrtProfileError):
            profiler.aggregate_source_model_profiles(receipted_payloads[:-1])
        duplicated = receipted_payloads[:-1] + [receipted_payloads[0]]
        with self.assertRaises(profiler.Eshm20SourceModelTrtProfileError):
            profiler.aggregate_source_model_profiles(duplicated)
        with self.assertRaisesRegex(
            profiler.Eshm20SourceModelTrtProfileError, "payload/receipt pair"
        ):
            profiler.aggregate_source_model_profiles(serialized_profiles)


if __name__ == "__main__":
    unittest.main()
