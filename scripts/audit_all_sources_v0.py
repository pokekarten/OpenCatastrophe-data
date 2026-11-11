#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Audit every registered source offline; never confuse a contract with a live probe.

All rows come from canonical landscape and admitted manifests. Access contracts are
validated by build_inventory(). No network requests, secrets or provider bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from scripts.build_source_access_inventory import (
    InventoryError, build_inventory, canonical_bytes,
)
from scripts.probe_fixed_public_sources_v0 import PROBES


class SourceAuditError(ValueError):
    """The source registry cannot be reported without losing coverage."""


def build_report() -> dict:
    inventory = build_inventory()
    rows = []
    identities = set()
    for entry in inventory["entries"]:
        key = (entry["record_type"], entry["source_id"], entry["source_registry_path"])
        if key in identities:
            raise SourceAuditError("duplicate source record in audit")
        identities.add(key)
        ids = entry["contract_ids"]
        statuses = entry["contract_statuses"]
        if not isinstance(ids, list) or not isinstance(statuses, list):
            raise SourceAuditError("source contract fields are missing")
        rows.append({
            "source_id": entry["source_id"],
            "record_type": entry["record_type"],
            "registry_path": entry["source_registry_path"],
            "access_contract_ids": ids,
            "access_contract_statuses": statuses,
            "readiness": entry["operational_readiness"],
            "rights": entry["rights_posture"],
            "automation_decision": entry["automation_decision"],
            "next_action": entry["next_action"],
            # A repository-only contract inventory cannot prove live reachability.
            "live_probe_verified_this_audit": False,
            "scientific_model_use_approved_this_audit": False,
        })
    if len(rows) != inventory["entry_count"]:
        raise SourceAuditError("audit omitted one or more source records")
    if len(rows) != inventory["landscape_entry_count"] + inventory["manifest_entry_count"]:
        raise SourceAuditError("landscape/manifest coverage mismatch")
    rows.sort(key=lambda r: (r["source_id"], r["record_type"], r["registry_path"]))
    # A frozen probe uses its access_id, which need not equal the source_id.
    # For example PEGELONLINE's Dresden canary is a narrower source contract.
    known_access_ids = {access_id for row in rows for access_id in row["access_contract_ids"]}
    missing_probes = sorted(set(PROBES) - known_access_ids)
    if missing_probes:
        raise SourceAuditError("fixed live probe has no registered access contract: " + ", ".join(missing_probes))
    status_counts = dict(sorted(Counter(row["readiness"] for row in rows).items()))
    if sum(status_counts.values()) != len(rows):
        raise SourceAuditError("readiness tally does not cover every source")
    return {
        "schema_version": "1.0.0",
        "scope": "offline_all_source_registry_and_access_contract_audit",
        "registry_sha256": hashlib.sha256(canonical_bytes(inventory)).hexdigest(),
        "source_review_date_max": inventory["source_review_date_max"],
        "total_source_records": len(rows),
        "landscape_candidates": inventory["landscape_entry_count"],
        "admitted_manifests": inventory["manifest_entry_count"],
        "validated_access_contracts": len(inventory["access_contract_files"]),
        "records_with_exact_contract": sum(bool(row["access_contract_ids"]) for row in rows),
        "readiness_counts": status_counts,
        "fixed_public_live_probe_ids": sorted(PROBES),
        "live_provider_access_verified_by_this_report": False,
        "rights_or_scientific_admission_granted_by_this_report": False,
        "records": rows,
    }


def markdown_summary(report: dict) -> str:
    lines = [
        "# All-source registry audit",
        "",
        "This is an **offline** registry, schema and access-contract audit. "
        "Live connectivity is measured separately in the fixed public-source probe jobs.",
        "",
        f"- Source records checked: **{report['total_source_records']}**",
        f"- Landscape candidates: **{report['landscape_candidates']}**",
        f"- Admitted manifests (pre-existing admission): **{report['admitted_manifests']}**",
        f"- Validated access contracts: **{report['validated_access_contracts']}**",
        f"- Records with a concrete contract: **{report['records_with_exact_contract']}**",
        f"- Fixed public APIs selected for separate live checks: **{len(report['fixed_public_live_probe_ids'])}**",
        "",
        "| Access readiness (not live status) | Records |",
        "| --- | ---: |",
    ]
    for status, count in report["readiness_counts"].items():
        lines.append(f"| {status} | {count} |")
    lines += [
        "",
        "No external provider payloads were downloaded by this audit. "
        "No source rights or model-input status was promoted.",
        "",
        "Use the JSON artifact for **one row per record**, including the actionable next step.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, required=True, help="write per-source JSON receipt")
    parser.add_argument("--markdown", type=Path, required=True, help="write short job summary")
    args = parser.parse_args(argv)
    try:
        report = build_report()
        args.json.write_bytes(canonical_bytes(report))
        args.markdown.write_text(markdown_summary(report), encoding="utf-8")
        print(
            f"PASS: audited {report['total_source_records']} source records; "
            f"{report['validated_access_contracts']} access contracts; "
            f"{report['records_with_exact_contract']} source records linked to contracts"
        )
        return 0
    except (OSError, InventoryError, SourceAuditError) as exc:
        print(f"FAIL: source coverage audit: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
