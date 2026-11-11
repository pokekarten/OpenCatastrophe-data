#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exhaustive, offline source/contract gap register and narrowly reviewed live probes.

All canonical source records are represented. Only eleven fixed source-specific
network programs may run, only after their committed access contracts pass
fail-closed rights/authentication preflight. No dynamic URLs, credentials,
provider response bodies, unapproved bulk downloads, or model admissions.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from scripts.build_source_access_inventory import ROOT, InventoryError, build_inventory, canonical_bytes
from scripts.probe_fixed_public_sources_v0 import PROBES
from scripts.validate_source_access import SourceAccessError, validate_path


class SourceCoverageError(ValueError):
    """A source or executable contract is missing or has drifted."""


FIVE_JSON_PROBES = (
    "emsc.seismicportal.fdsn-event",
    "geoboundaries.gbopen",
    "gfz.geomagnetic-kp",
    "noaa.swpc.real-time-solar-wind",
    "wsv.pegelonline.rest-v2.dresden",
)
EXTRA_PROBE_COMMANDS = {
    "dwd.cdc.extreme-wind.http-file": ("-m", "scripts.probe_dwd_historical_directory_v0"),
    "esa.worldcover.2021.v200": ("-m", "scripts.probe_esa_worldcover_tiff_header_v0", "--live"),
    "globaldamwatch.gdw.v1.0": ("-m", "scripts.probe_globaldamwatch_gdw_v1_metadata_v0", "--live"),
    "noaa.coops.water-levels": ("-m", "scripts.probe_noaa_coops_water_levels_v0", "--live"),
    "storm.ibtracs.present-climate.v4.datacite": ("-m", "research_runners.storm_v4_datacite_probe_v0", "--probe-once"),
    "usgs.3dep.s1m.tnmaccess": ("-m", "scripts.probe_usgs_s1m_florida_tnm_v0", "--live"),
}
APPROVED_PROBE_IDS = tuple(sorted(set(FIVE_JSON_PROBES) | set(EXTRA_PROBE_COMMANDS)))
BLOCKED_CONTRACT_STATUSES = frozenset({
    "blocked_registration", "blocked_credentials", "restricted_by_terms",
    "deprecated", "rejected",
})


def preflight_reviewed_probes() -> None:
    """Require original, exact contracts and reviewed automation rights."""
    if set(PROBES) != set(FIVE_JSON_PROBES) or len(APPROVED_PROBE_IDS) != 11:
        raise SourceCoverageError("frozen public API allowlist drift")
    for access_id in APPROVED_PROBE_IDS:
        path = ROOT / "access" / (access_id + ".json")
        contract = validate_path(path)
        rights = contract["rights_and_policy"]
        auth = contract["authentication"]
        probe = contract["probe_contract"]
        if (contract["access_id"] != access_id
                or contract["status"] != "probe_ready"
                or auth["mode"] != "none"
                or probe["requires_credentials"] is not False
                or rights["commercial_automation_status"] != "allowed"
                or rights["dataset_rights_status"] != "verified"
                or rights["api_terms_status"] not in {"same_as_dataset", "separate_reviewed"}
                or not contract["source_ids"]):
            raise SourceCoverageError("reviewed rights, auth, or source scope changed: " + access_id)


def gap_for_record(entry: dict, allowed_ids: frozenset[str]) -> str:
    """Describe remaining work; never infer live verification from a contract."""
    ids = entry["contract_ids"]
    statuses = set(entry["contract_statuses"])
    if not ids:
        return "missing_exact_access_contract"
    if len(ids) != 1:
        return "select_exact_interface"
    if statuses & BLOCKED_CONTRACT_STATUSES:
        return "blocked_by_reviewed_contract"
    if ids[0] in allowed_ids and statuses == {"probe_ready"}:
        return "fixed_reviewed_probe_configured_not_live_verified"
    if "documented_only" in statuses:
        return "review_terms_and_freeze_bounded_request"
    if "probe_ready" in statuses or "verified_anonymous" in statuses:
        return "implement_reviewed_bounded_probe"
    if "verified_authenticated" in statuses:
        return "authenticated_review_required_no_public_runner"
    return "review_contract_state_before_execution"


def build_coverage_report(inventory: dict | None = None) -> dict:
    preflight_reviewed_probes()
    inventory = build_inventory() if inventory is None else inventory
    entries = inventory["entries"]
    if (len(entries) != inventory["entry_count"]
            or inventory["landscape_entry_count"] + inventory["manifest_entry_count"] != len(entries)):
        raise SourceCoverageError("source record coverage mismatch")
    available_ids = {access_id for entry in entries for access_id in entry["contract_ids"]}
    if not set(APPROVED_PROBE_IDS).issubset(available_ids):
        raise SourceCoverageError("reviewed live probe lacks a canonical source/contract association")
    seen = set()
    records = []
    allowed = frozenset(APPROVED_PROBE_IDS)
    for entry in entries:
        key = (entry["source_id"], entry["record_type"], entry["source_registry_path"])
        if key in seen:
            raise SourceCoverageError("duplicate source record")
        seen.add(key)
        gap = gap_for_record(entry, allowed)
        records.append({
            "source_id": entry["source_id"],
            "record_type": entry["record_type"],
            "registry_path": entry["source_registry_path"],
            "access_contract_ids": entry["contract_ids"],
            "access_contract_statuses": entry["contract_statuses"],
            "recorded_rights_posture": entry["rights_posture"],
            "operational_readiness": entry["operational_readiness"],
            "blocker_or_next_gate": gap,
            "next_action": entry["next_action"],
            "live_probe_verified_by_this_report": False,
            "model_input_approved_by_this_report": False,
        })
    records.sort(key=lambda r: (r["source_id"], r["record_type"], r["registry_path"]))
    return {
        "schema_version": "1.0.0",
        "scope": "all_registered_sources_offline_contract_gaps_no_provider_requests",
        "source_registry_sha256": __import__("hashlib").sha256(canonical_bytes(inventory)).hexdigest(),
        "source_records": len(records),
        "landscape_candidates": inventory["landscape_entry_count"],
        "admitted_manifests": inventory["manifest_entry_count"],
        "reviewed_access_contracts": len(inventory["access_contract_files"]),
        "fixed_reviewed_live_probes_configured": len(APPROVED_PROBE_IDS),
        "reviewed_live_probe_access_ids": list(APPROVED_PROBE_IDS),
        "blocker_counts": dict(sorted(Counter(r["blocker_or_next_gate"] for r in records).items())),
        "all_sources_available": False,
        "new_commercial_rights_approved": False,
        "live_provider_requests_made": False,
        "new_model_inputs_admitted": False,
        "records": records,
    }


def _cell(value: object) -> str:
    return str(value).replace("|", r"\|").replace("\n", " ").replace("\r", " ")


def report_markdown(report: dict) -> str:
    lines = [
        "# Complete source/API/contract readiness register", "",
        "Offline source coverage only. A configured probe is not a passing live result,",
        "a rights clearance for other products, or CAT model admission.", "",
        f"- Registered records: **{report['source_records']}**",
        f"- Reviewed access contracts: **{report['reviewed_access_contracts']}**",
        f"- Explicitly approved bounded live probe programs: **{report['fixed_reviewed_live_probes_configured']}**",
        "", "| Gate or blocker | Records |", "| --- | ---: |",
    ]
    for name, count in report["blocker_counts"].items():
        lines.append(f"| {_cell(name)} | {count} |")
    lines.extend([
        "", "## Every registered source and its next gate", "",
        "| Source ID | Registry record | Contract IDs | Rights posture | Next gate |",
        "| --- | --- | --- | --- | --- |",
    ])
    for item in report["records"]:
        cells = [
            item["source_id"], item["registry_path"],
            ", ".join(item["access_contract_ids"]) or "none",
            item["recorded_rights_posture"], item["blocker_or_next_gate"],
        ]
        lines.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    lines.extend(["", "Unreviewed endpoints are **not called**. No provider data is saved or admitted.", ""])
    return "\n".join(lines)


def command_for(access_id: str) -> tuple[str, ...]:
    if access_id in FIVE_JSON_PROBES:
        return ("-m", "scripts.probe_fixed_public_sources_v0", "--source", access_id)
    return EXTRA_PROBE_COMMANDS[access_id]


def run_reviewed_live_probes() -> int:
    """One bounded, sequential lane; suppress provider values and secrets in logs."""
    preflight_reviewed_probes()
    outcomes: list[tuple[str, str]] = []
    for access_id in APPROVED_PROBE_IDS:
        try:
            completed = subprocess.run(
                [sys.executable, *command_for(access_id)],
                cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=120, check=False,
            )
            outcome = "PASS" if completed.returncode == 0 else "BLOCKED"
        except (OSError, subprocess.TimeoutExpired):
            outcome = "BLOCKED"
        outcomes.append((access_id, outcome))
    print("## Fixed reviewed live API probes")
    print()
    print("One bounded provider-specific invocation each; output contains no provider response bodies.")
    print("A PASS is only a technical probe receipt, not dataset or model admission.")
    print()
    print("| Reviewed access ID | Result |")
    print("| --- | --- |")
    for access_id, outcome in outcomes:
        print(f"| {access_id} | {outcome} |")
    print()
    return 0 if all(outcome == "PASS" for _, outcome in outcomes) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--run-reviewed-live", action="store_true")
    args = parser.parse_args(argv)
    if args.run_reviewed_live and (args.json or args.markdown):
        parser.error("live mode never writes provider responses or inventory files")
    if not args.run_reviewed_live and (args.json is None or args.markdown is None):
        parser.error("offline mode requires --json and --markdown")
    try:
        if args.run_reviewed_live:
            return run_reviewed_live_probes()
        report = build_coverage_report()
        args.json.write_bytes(canonical_bytes(report))
        args.markdown.write_text(report_markdown(report), encoding="utf-8")
        print(
            f"PASS: {report['source_records']} source records, "
            f"{report['reviewed_access_contracts']} validated contracts, "
            f"{report['fixed_reviewed_live_probes_configured']} reviewed probes configured; "
            "zero provider requests or model admissions"
        )
        return 0
    except (InventoryError, SourceAccessError, SourceCoverageError, OSError) as exc:
        print(f"BLOCKED: source API coverage gate: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
