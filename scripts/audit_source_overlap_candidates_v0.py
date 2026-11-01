#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline review of proposed discovery sources against canonical landscape and manifests.

Detect explicit candidate-ID collisions and the same *provider product page*,
not scientific dataset equality. Never fetch providers or upgrade admission.
Only the UI-only query parameter 'tab' and URL fragment are disregarded.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class OverlapAuditError(ValueError):
    pass


def url_identity(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443)):
        raise OverlapAuditError("invalid source HTTPS URL")
    params = [(key, value) for key, value in
              parse_qsl(parsed.query, keep_blank_values=True)
              if key.casefold() != "tab"]
    return urlunsplit(("https", parsed.hostname.casefold(),
                       parsed.path.rstrip("/") or "/",
                       urlencode(sorted(params)), ""))


def _record(item: dict, file: str, kind: str) -> dict:
    if kind == "manifest":
        identity, url = item["dataset_id"], item["canonical_source"]
    else:
        identity, url = item["candidate_id"], item["authoritative_url"]
    if not isinstance(identity, str) or not identity or not isinstance(url, str):
        raise OverlapAuditError("invalid source metadata identity")
    return {"identity": identity, "url": url_identity(url), "file": file, "kind": kind}


def audit(proposed: list[tuple[str, dict]], baseline: list[tuple[str, dict]],
          admitted_manifests: list[tuple[str, dict]]) -> dict:
    """Deterministic, non-admission source page overlap review report."""
    if not proposed:
        raise OverlapAuditError("at least one proposed source shard required")
    entries = [_record(item, file, "proposed") for file, shard in proposed
               for item in shard["entries"]]
    if not entries:
        raise OverlapAuditError("empty proposed source set")
    existing = ([_record(item, file, "discovery") for file, shard in baseline
                 for item in shard["entries"]] +
                [_record(item, file, "manifest") for file, item in admitted_manifests])
    indexed_id, indexed_url = defaultdict(list), defaultdict(list)
    for item in existing + entries:
        indexed_id[item["identity"]].append(item)
        indexed_url[item["url"]].append(item)
    findings = []
    for entry in entries:
        matches: dict[tuple[str, str, str], set[str]] = {}
        for other in indexed_id[entry["identity"]]:
            if other is entry:
                continue
            key = (other["kind"], other["identity"], other["file"])
            matches.setdefault(key, set()).add("same_exact_id")
        for other in indexed_url[entry["url"]]:
            if other is entry:
                continue
            key = (other["kind"], other["identity"], other["file"])
            matches.setdefault(key, set()).add("same_provider_product_page")
        for (kind, identity, file), reasons in sorted(matches.items()):
            findings.append({
                "proposed_id": entry["identity"], "proposed_file": entry["file"],
                "existing_kind": kind, "existing_id": identity,
                "existing_file": file, "reasons": sorted(reasons),
                "automatic_duplicate_decision": False,
            })
    findings.sort(key=lambda item: (item["proposed_id"], item["existing_kind"],
                                   item["existing_id"], item["existing_file"]))
    return {
        "profile": "open-cat-source-overlap-research-v0",
        "proposed_count": len(entries),
        "baseline_discovery_count": sum(len(shard["entries"]) for _, shard in baseline),
        "admitted_manifest_count": len(admitted_manifests),
        "proposal_overlap_findings": len(findings),
        "proposed_candidates_with_findings": len(set(f["proposed_id"] for f in findings)),
        "findings": findings,
        "provider_pages_can_contain_distinct_dataset_products": True,
        "any_source_rights_changed": False,
        "any_source_admitted": False,
        "any_provider_bytes_acquired": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposed", type=Path, action="append", required=True)
    parser.add_argument("--baseline-landscape", type=Path, default=Path("landscape"))
    parser.add_argument("--manifests", type=Path, default=Path("manifests"))
    parser.add_argument("--require-no-overlap", action="store_true")
    args = parser.parse_args(argv)
    try:
        from scripts.source_landscape_contract import load_landscape_shard, load_landscape_shards
        from scripts.validate_manifest import load_manifest
        proposed = [(str(p), load_landscape_shard(p)) for p in args.proposed]
        baseline = [(str(p), shard) for p, shard in
                    load_landscape_shards(args.baseline_landscape)]
        manifests = [(str(p), load_manifest(p)) for p in sorted(args.manifests.glob("*.json"))]
        report = audit(proposed, baseline, manifests)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 2 if args.require_no_overlap and report["proposal_overlap_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
