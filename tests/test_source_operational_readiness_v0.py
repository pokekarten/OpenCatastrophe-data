# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for conservative operational source readiness reporting."""

from __future__ import annotations

import unittest

from scripts.build_source_access_inventory import (
    _apply_contracts,
    build_inventory,
    summarize_operational_readiness,
)


BASE = {
    "api_status": "research_required",
    "machine_access_class": "research_required",
    "automation_decision": "document_only",
    "next_action": "Research the interface.",
}


def contract(*, status: str, decision: str = "build_later", access_id: str = "example.access") -> dict:
    return {
        "access_id": access_id,
        "interface_type": "fdsn",
        "status": status,
        "probe_mode": "catalogue_query" if status == "probe_ready" else "none",
        "implementation_decision": decision,
    }


class SourceOperationalReadinessTests(unittest.TestCase):
    def test_no_contract_never_claims_live_data(self) -> None:
        row = _apply_contracts(BASE, [])
        self.assertEqual(row["operational_readiness"], "no_concrete_access_contract")
        self.assertEqual(row["contract_statuses"], [])
        self.assertEqual(row["contract_probe_modes"], [])
        self.assertFalse(row["live_data_availability_proven"])

    def test_probe_ready_is_not_live_data_or_permission_to_run_discovery(self) -> None:
        row = _apply_contracts(BASE, [contract(status="probe_ready")])
        self.assertEqual(row["operational_readiness"], "bounded_probe_defined_not_executed")
        self.assertEqual(row["contract_statuses"], ["probe_ready"])
        self.assertEqual(row["contract_probe_modes"], ["catalogue_query"])
        self.assertEqual(row["automation_decision"], "document_only")
        self.assertFalse(row["live_data_availability_proven"])
        self.assertIn("bounded probe", row["next_action"])

    def test_credentials_and_terms_have_distinct_nonexecuting_next_steps(self) -> None:
        credential = _apply_contracts(BASE, [contract(status="blocked_credentials", decision="document_only")])
        terms = _apply_contracts(BASE, [contract(status="restricted_by_terms", decision="do_not_automate")])
        self.assertEqual(credential["operational_readiness"], "credentials_required")
        self.assertIn("outside Git", credential["next_action"])
        self.assertEqual(terms["operational_readiness"], "restricted_by_terms")
        self.assertEqual(terms["automation_decision"], "do_not_automate")
        self.assertIn("Do not automate", terms["next_action"])

    def test_multiple_contracts_fail_closed_without_order_dependence(self) -> None:
        contracts = [
            contract(status="probe_ready", access_id="first"),
            contract(status="restricted_by_terms", decision="do_not_automate", access_id="second"),
        ]
        for records in (contracts, list(reversed(contracts))):
            row = _apply_contracts(BASE, records, allow_contract_promotion=True)
            self.assertEqual(row["operational_readiness"], "select_exact_interface_before_execution")
            self.assertEqual(row["automation_decision"], "do_not_automate")
            self.assertEqual(row["contract_statuses"], ["probe_ready", "restricted_by_terms"])
            self.assertFalse(row["live_data_availability_proven"])

    def test_summary_counts_every_record_but_does_not_claim_live_availability(self) -> None:
        summary = summarize_operational_readiness({
            "entry_count": 3,
            "landscape_entry_count": 2,
            "manifest_entry_count": 1,
            "access_contract_files": ["access/one.json"],
            "entries": [
                {"operational_readiness": "no_concrete_access_contract"},
                {"operational_readiness": "credentials_required"},
                {"operational_readiness": "bounded_probe_defined_not_executed"},
            ],
        })
        self.assertEqual(sum(summary["operational_readiness_counts"].values()), 3)
        self.assertEqual(summary["reviewed_access_contracts"], 1)
        self.assertFalse(summary["model_input_approval_proven_by_this_report"])

    def test_current_canonical_registry_covers_every_known_source(self) -> None:
        inventory = build_inventory()
        rows = inventory["entries"]
        self.assertEqual(len(rows), inventory["entry_count"])
        self.assertEqual(len(rows), inventory["landscape_entry_count"] + inventory["manifest_entry_count"])
        self.assertTrue(all(type(r["operational_readiness"]) is str for r in rows))
        self.assertTrue(all(r["live_data_availability_proven"] is False for r in rows))
        summary = summarize_operational_readiness(inventory)
        self.assertEqual(sum(summary["operational_readiness_counts"].values()), len(rows))


if __name__ == "__main__":
    unittest.main()
