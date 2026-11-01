#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Combine existing CAT source-access inventory and manual linkage hypotheses.

This is a deterministic *research queue*, NOT a raw-data importer, an evidence
of successful provider access, a new canonical database or a model-input allowlist.
It leaves original landscape, access contracts and accepted manifests authoritative.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any

if __package__:
    from .build_source_access_inventory import build_inventory
    from .source_landscape_contract import load_landscape_shards
    from .source_linkage_audit_v0 import build_audit
else:
    from build_source_access_inventory import build_inventory
    from source_landscape_contract import load_landscape_shards
    from source_linkage_audit_v0 import build_audit


class CrosswalkError(ValueError):
    """Input registries disagree or research boundaries were violated."""


def build_crosswalk(access_inventory: dict[str, Any], linkage_audit: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if either canonical inventory is missing, stale or ambiguous."""
    if access_inventory.get("entry_count") != len(access_inventory.get("entries", [])):
        raise CrosswalkError("access inventory count mismatch")
    if linkage_audit.get("source_count") != len(linkage_audit.get("source_inventory", [])):
        raise CrosswalkError("linkage audit count mismatch")
    if linkage_audit.get("this_report_is_a_model_input_allowlist") is not False:
        raise CrosswalkError("linkage audit has no non-admission boundary")

    access_candidates: dict[str, dict[str, Any]] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for row in access_inventory["entries"]:
        source_id = row.get("source_id")
        kind = row.get("record_type")
        if not isinstance(source_id, str) or not source_id:
            raise CrosswalkError("invalid source identity")
        if kind == "landscape_candidate":
            dest = access_candidates
        elif kind == "admitted_manifest":
            dest = manifests
        else:
            raise CrosswalkError("unknown source record type")
        if source_id in dest:
            raise CrosswalkError("duplicate identity within one source record type")
        dest[source_id] = row
    if len(access_candidates) != access_inventory.get("landscape_entry_count"):
        raise CrosswalkError("landscape count differs in access inventory")
    if len(manifests) != access_inventory.get("manifest_entry_count"):
        raise CrosswalkError("manifest count differs in access inventory")

    discovery: dict[str, dict[str, Any]] = {}
    for row in linkage_audit["source_inventory"]:
        source_id = row.get("candidate_id")
        if not isinstance(source_id, str) or not source_id or source_id in discovery:
            raise CrosswalkError("missing or duplicated linkage candidate ID")
        if (row.get("admission_status") != "not_admitted"
                or row.get("automated_model_import_allowed_by_this_audit") is not False):
            raise CrosswalkError("source linkage inventory cannot grant model admission")
        discovery[source_id] = row
    if set(discovery) != set(access_candidates):
        missing_in_access = sorted(set(discovery) - set(access_candidates))
        missing_in_linkage = sorted(set(access_candidates) - set(discovery))
        raise CrosswalkError(
            "discovery/access inventories disagree: "
            f"missing_in_access={missing_in_access}; missing_in_linkage={missing_in_linkage}"
        )

    links: dict[str, list[dict[str, Any]]] = defaultdict(list)
    link_ids = set()
    for recipe in linkage_audit.get("linkage_hypotheses", []):
        recipe_id = recipe.get("recipe_id")
        endpoints = recipe.get("source_candidate_ids")
        if (not isinstance(recipe_id, str) or not recipe_id or recipe_id in link_ids
                or not isinstance(endpoints, list) or len(endpoints) < 2
                or any(not isinstance(x, str) for x in endpoints)
                or len(set(endpoints)) != len(endpoints)
                or not set(endpoints).issubset(discovery)):
            raise CrosswalkError("malformed, duplicate or dangling linkage recipe")
        link_ids.add(recipe_id)
        if (recipe.get("validation_only") is not True
                or recipe.get("automatic_source_join_allowed") is not False
                or recipe.get("scientific_independence_proven") is not False
                or recipe.get("model_input_admitted") is not False):
            raise CrosswalkError("linkage recipe crossed the non-admission boundary")
        for endpoint in endpoints:
            links[endpoint].append({
                "recipe_id": recipe_id,
                "relationship": recipe.get("relationship"),
                "other_source_ids": sorted(e for e in endpoints if e != endpoint),
                "required_join_evidence": recipe.get("required_join_evidence"),
                "unverified_prerequisites": recipe.get("unverified_prerequisites"),
                "prohibited_inferences": recipe.get("prohibited_inferences"),
                "automatic_join_allowed": False,
                "scientific_independence_proven": False,
            })
    if len(link_ids) != linkage_audit.get("linkage_recipe_count"):
        raise CrosswalkError("linkage recipe count mismatch")

    # A provider landing page can legitimately describe multiple distinct
    # dataset products. Exact shared page URLs are therefore review candidates
    # only, never proof of duplicate source bytes or authority to conflate IDs.
    page_index: dict[str, list[str]] = defaultdict(list)
    for source_id, source in discovery.items():
        url = source.get("authoritative_url")
        if not isinstance(url, str) or not url.strip():
            raise CrosswalkError("source identity/provenance mismatch across derived registers")
        page_index[url].append(source_id)
    url_groups = [
        {"authoritative_url": url, "candidate_ids": sorted(ids),
         "source_bytes_identical_proven": False,
         "automatic_deduplication_allowed": False}
        for url, ids in sorted(page_index.items()) if len(ids) > 1
    ]
    page_peers = {
        source_id: sorted(x for x in ids if x != source_id)
        for _url, ids in page_index.items() if len(ids) > 1 for source_id in ids
    }

    candidates = []
    for source_id in sorted(discovery):
        source = discovery[source_id]
        access = access_candidates[source_id]
        if access.get("source_registry_path") is None:
            raise CrosswalkError("access source lacks canonical registry path")
        # Both derived views must describe the same *original* source record.
        # Matching an ID alone is insufficient when one view is stale or
        # internally inconsistent: it could silently attach a source's access
        # contract or scientific-link hypotheses to a different provider.
        if (access.get("provider") != source.get("provider")
                or access.get("authoritative_url") != source.get("authoritative_url")
                or Path(access["source_registry_path"]).name != source.get("landscape_shard")):
            raise CrosswalkError("source identity/provenance mismatch across derived registers")
        link_rows = sorted(links[source_id], key=lambda r: r["recipe_id"])
        contracts = access.get("contract_ids")
        if not isinstance(contracts, list) or len(set(contracts)) != len(contracts):
            raise CrosswalkError("ambiguous access-contract identities")
        candidates.append({
            "source_id": source_id,
            "source_record_type": "landscape_candidate",
            "canonical_source_path": access["source_registry_path"],
            "provider": source["provider"],
            "authoritative_url": source["authoritative_url"],
            "spatial_scope": source["spatial_scope"],
            "temporal_scope": source["temporal_scope"],
            "categories": source["categories"],
            "potential_roles": source["potential_roles"],
            "access_contract_ids": sorted(contracts),
            "access_contract_statuses": access.get("contract_statuses", []),
            "operational_readiness": access.get("operational_readiness"),
            "rights_posture": access.get("rights_posture"),
            "license_or_terms_flags": access.get("license_or_terms_flags", []),
            "automation_decision": access.get("automation_decision"),
            "access_next_action": access.get("next_action"),
            "same_authoritative_page_candidate_ids": page_peers.get(source_id, []),
            "same_page_proves_identical_source_bytes": False,
            "candidate_join_hypotheses": link_rows,
            "join_hypothesis_count": len(link_rows),
            "scientific_independence_proven": False,
            "manual_lineage_review_required": bool(link_rows),
            "needs_bounded_technical_access_review": True,
            "no_reviewed_access_contract": not bool(contracts),
            "access_proven_by_this_report": False,
            "source_bytes_verified_by_this_report": False,
            "scientific_join_verified_by_this_report": False,
            "model_input_admitted_by_this_report": False,
        })

    # Manifest records are already in a DIFFERENT trust domain: deliberately
    # do not merge them into a similarly named discovery candidate or imply
    # automatic access from a reviewed manifest.
    manifest_rows = [{
        "dataset_id": source_id,
        "source_record_type": "admitted_manifest",
        "canonical_manifest_path": item.get("source_registry_path"),
        "access_contract_ids": sorted(item.get("contract_ids") or []),
        "operational_readiness": item.get("operational_readiness"),
        "access_next_action": item.get("next_action"),
        "source_bytes_verified_by_this_report": False,
        "scientific_join_verified_by_this_report": False,
        "any_additional_model_authority_granted": False,
    } for source_id, item in sorted(manifests.items())]

    readiness_counts = dict(sorted(Counter(row["operational_readiness"] for row in candidates).items()))
    # Category totals overlap: one uncontracted dataset may serve multiple
    # hazards, geographies or scientific roles. These are research-queue
    # counts, not mutually exclusive dataset counts or coverage statistics.
    missing_contract_category_counts = dict(sorted(Counter(
        category
        for row in candidates if row["no_reviewed_access_contract"]
        for category in set(row["categories"])
    ).items()))
    return {
        "profile": "opencatastrophe-source-access-linkage-research-v0",
        "scope": "Non-admission source discovery plus separately reported existing manifests; no provider retrieval, source-byte validation or executable join",
        "candidate_count": len(candidates),
        "manifest_count": len(manifest_rows),
        "candidate_with_access_contract_count": sum(bool(row["access_contract_ids"]) for row in candidates),
        "candidate_without_access_contract_count": sum(not row["access_contract_ids"] for row in candidates),
        "candidate_with_manual_link_hypothesis_count": sum(bool(row["candidate_join_hypotheses"]) for row in candidates),
        "manual_linkage_recipe_count": len(link_ids),
        "shared_authoritative_page_group_count": len(url_groups),
        "shared_authoritative_page_review_groups": url_groups,
        "candidate_readiness_counts": readiness_counts,
        "missing_contract_candidate_category_counts": missing_contract_category_counts,
        "category_counts_are_not_disjoint": True,
        "candidates": candidates,
        "existing_manifests_separate": manifest_rows,
        "external_provider_data_downloaded": False,
        "permission_for_automated_source_join": False,
        "new_rights_or_admission_granted": False,
        "this_report_is_a_model_input_allowlist": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="Print only aggregate access/linkage coverage.")
    parser.add_argument("--out", type=Path, help="Write derived JSON report at this explicit path.")
    args = parser.parse_args(argv)
    try:
        report = build_crosswalk(build_inventory(), build_audit(load_landscape_shards()))
        if args.summary:
            data = {key: value for key, value in report.items()
                    if key not in ("candidates", "existing_manifests_separate")}
        else:
            data = report
        output = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.out is None:
            print(output, end="")
        else:
            if args.out.is_symlink():
                raise CrosswalkError("refuse symbolic-link report destination")
            args.out.write_text(output, encoding="utf-8")
        return 0
    except (CrosswalkError, ValueError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
