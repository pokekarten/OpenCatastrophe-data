# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline regression checks for every-source, rights-gated API coverage."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import subprocess
import unittest
from unittest.mock import patch

from scripts import source_api_readiness_v0 as coverage


def entry(*, ids=None, statuses=None):
    return {
        "contract_ids": ids or [],
        "contract_statuses": statuses or [],
    }


class SourceApiReadinessTests(unittest.TestCase):
    def test_every_registered_record_has_a_gap_or_frozen_probe(self):
        report = coverage.build_coverage_report()
        self.assertEqual(report["source_records"], len(report["records"]))
        self.assertEqual(
            report["source_records"],
            report["landscape_candidates"] + report["admitted_manifests"],
        )
        self.assertEqual(
            sum(report["blocker_counts"].values()), report["source_records"]
        )
        self.assertEqual(report["fixed_reviewed_live_probes_configured"], 17)
        self.assertGreater(report["reviewed_access_contracts"], 0)
        self.assertEqual(
            sum(report["contract_status_counts"].values()),
            report["reviewed_access_contracts"],
        )
        self.assertEqual(
            sum(report["contract_automation_rights_counts"].values()),
            report["reviewed_access_contracts"],
        )
        self.assertFalse(report["all_sources_available"])
        self.assertFalse(report["live_provider_requests_made"])
        self.assertFalse(report["new_commercial_rights_approved"])
        self.assertFalse(report["new_model_inputs_admitted"])
        self.assertTrue(
            all(not row["live_probe_verified_by_this_report"]
                and not row["model_input_approved_by_this_report"]
                for row in report["records"])
        )
        self.assertEqual(
            coverage.canonical_bytes(report),
            coverage.canonical_bytes(coverage.build_coverage_report()),
        )
        rendered = coverage.report_markdown(report)
        self.assertIn("Every registered source", rendered)
        self.assertIn(str(report["source_records"]), rendered)

    def test_missing_multiple_blocked_and_reviewed_contracts_are_distinct(self):
        fn = coverage.gap_for_record
        allowed = frozenset({"approved"})
        self.assertEqual(
            fn(entry(), allowed), "missing_exact_access_contract"
        )
        self.assertEqual(
            fn(entry(ids=["approved", "other"], statuses=["probe_ready"]), allowed),
            "select_exact_interface",
        )
        self.assertEqual(
            fn(entry(ids=["approved"], statuses=["blocked_credentials"]), allowed),
            "blocked_by_reviewed_contract",
        )
        self.assertEqual(
            fn(entry(ids=["approved"], statuses=["probe_ready"]), allowed),
            "fixed_reviewed_probe_configured_not_live_verified",
        )
        self.assertEqual(
            fn(entry(ids=["other"], statuses=["probe_ready"]), allowed),
            "implement_reviewed_bounded_probe",
        )
        self.assertEqual(
            fn(entry(ids=["other"], statuses=["documented_only"]), allowed),
            "review_terms_and_freeze_bounded_request",
        )
        self.assertEqual(
            fn(entry(ids=["other"], statuses=["verified_authenticated"]), allowed),
            "authenticated_review_required_no_public_runner",
        )

    def test_live_runner_whitelist_is_exact_and_immutable(self):
        self.assertEqual(set(coverage.FIVE_JSON_PROBES), set(coverage.PROBES))
        self.assertEqual(coverage.command_for("meteoswiss.national-hail-climatology"),
                         ("-m", "scripts.probe_meteoswiss_hail_stac_collection_v0", "--live"))
        self.assertEqual(coverage.command_for("de.berlin.alkis-gebaeude.wfs"),
                         ("-m", "scripts.probe_berlin_alkis_wfs_capabilities_v0", "--live"))
        self.assertEqual(len(coverage.APPROVED_PROBE_IDS), 17)
        self.assertEqual(
            len(coverage.APPROVED_PROBE_IDS),
            len(set(coverage.APPROVED_PROBE_IDS)),
        )
        for access_id in coverage.APPROVED_PROBE_IDS:
            self.assertEqual(coverage.command_for(access_id)[0], "-m")
        with self.assertRaises(KeyError):
            coverage.command_for("arbitrary.user.api")
        coverage.preflight_reviewed_probes()

    def test_revoked_rights_fail_preflight(self):
        real_validate = coverage.validate_path

        def simulate_revocation(path):
            contract = real_validate(path)
            if path.name == "globaldamwatch.gdw.v1.0.json":
                contract["rights_and_policy"]["commercial_automation_status"] = "unknown"
            return contract

        with patch.object(coverage, "validate_path", side_effect=simulate_revocation):
            with self.assertRaisesRegex(coverage.SourceCoverageError, "rights"):
                coverage.preflight_reviewed_probes()

    def test_live_invokes_all_seventeen_exact_runners_without_leaking_stdout(self):
        captured = StringIO()
        with patch.object(coverage, "preflight_reviewed_probes"), patch.object(
            coverage.subprocess, "run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='{"response_sha256":"' + "a" * 64 + '"}'),
        ) as process, redirect_stdout(captured):
            result = coverage.run_reviewed_live_probes()
        self.assertEqual(result, 0)
        self.assertEqual(process.call_count, 17)
        self.assertNotIn("secret-provider-value", captured.getvalue())
        for call, access_id in zip(process.call_args_list, coverage.APPROVED_PROBE_IDS):
            self.assertEqual(
                call.args[0],
                [coverage.sys.executable, *coverage.command_for(access_id)],
            )
            self.assertEqual(call.kwargs["stdout"], subprocess.PIPE)
            self.assertEqual(call.kwargs["stderr"], subprocess.DEVNULL)
            self.assertEqual(call.kwargs["timeout"], 120)
            self.assertFalse(call.kwargs["check"])

    def test_failure_does_not_skip_remaining_reviewed_probes(self):
        calls = 0

        def fail_one(*args, **kwargs):
            nonlocal calls
            calls += 1
            return subprocess.CompletedProcess(
                args=args, returncode=1 if calls == 1 else 0,
                stdout='{"response_sha256":"' + "a" * 64 + '"}',
            )

        with patch.object(coverage, "preflight_reviewed_probes"), patch.object(
            coverage.subprocess, "run", side_effect=fail_one,
        ), redirect_stdout(StringIO()) as output:
            result = coverage.run_reviewed_live_probes()
        self.assertEqual(result, 1)
        self.assertEqual(calls, 17)
        self.assertIn("BLOCKED", output.getvalue())
        self.assertIn("PASS", output.getvalue())

    def test_coverage_mismatch_fails_closed(self):
        fake = {
            "entries": [], "entry_count": 1, "landscape_entry_count": 1,
            "manifest_entry_count": 0,
        }
        with patch.object(coverage, "preflight_reviewed_probes"):
            with self.assertRaisesRegex(coverage.SourceCoverageError, "coverage"):
                coverage.build_coverage_report(fake)

    def test_success_without_provider_digest_is_not_accepted(self):
        with patch.object(coverage, "preflight_reviewed_probes"), patch.object(
            coverage.subprocess, "run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="{}"),
        ), redirect_stdout(StringIO()) as output:
            result = coverage.run_reviewed_live_probes()
        self.assertEqual(result, 1)
        self.assertIn("BLOCKED", output.getvalue())
        self.assertNotIn("PASS |", output.getvalue())

    def test_two_original_nodd_metadata_digests_both_required(self):
        digest_a, digest_b = "a" * 64, "b" * 64
        both = {
            "objects": {
                "version": {"response_sha256": digest_a},
                "countries": {"response_sha256": digest_b},
            },
        }
        import json
        self.assertEqual(
            coverage._receipt_digest(json.dumps(both)),
            "version:" + digest_a + ";countries:" + digest_b,
        )
        del both["objects"]["countries"]
        self.assertIsNone(coverage._receipt_digest(json.dumps(both)))

    def test_full_station_receipt_fields_are_distinct_from_model_admission(self):
        import json
        for label in ("compressed_original_sha256", "original_body_sha256"):
            self.assertEqual(
                coverage._receipt_digest(json.dumps({label: "a" * 64})), "a" * 64,
            )

    def test_no_arbitrary_provider_output_is_included_in_the_summary(self):
        receipt = '{"response_sha256":"' + "a" * 64 + '","provider_secret":"DO_NOT_LOG"}'
        self.assertEqual(coverage._receipt_digest(receipt), "a" * 64)
        self.assertIsNone(coverage._receipt_digest('{"response_sha256":"short"}'))
        with patch.object(coverage, "preflight_reviewed_probes"), patch.object(
            coverage.subprocess, "run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=receipt),
        ), redirect_stdout(StringIO()) as output:
            self.assertEqual(coverage.run_reviewed_live_probes(), 0)
        self.assertNotIn("DO_NOT_LOG", output.getvalue())


if __name__ == "__main__":
    unittest.main()
