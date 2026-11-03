# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, read-only *three-way* CAT source-register reconciliation.

Compares current GitHub JSON-shard listing vs independent Neon production and
isolated-stage metadata exports. No network, SQL, source downloads, writes,
model admissions or unattended branch promotion. A candidate is a *file*, not
an independent dataset/provider or legal right to import its bytes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from scripts.audit_insurance_landscape_sync_v0 import load as strict_load

GIT_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
LANDSCAPE = re.compile(r"landscape/sources[A-Za-z0-9._-]*\.json\Z")
ACCESS = re.compile(r"access/[A-Za-z0-9][A-Za-z0-9._-]*\.json\Z")
MAX_ENTRIES = 500
REPO = "pokekarten/OpenCatastrophe-data"
ACCESS_STATUSES = frozenset({
    "documented_only", "probe_ready", "verified_anonymous",
    "restricted_by_terms", "blocked_credentials",
})
ACCESS_RIGHTS = frozenset({
    "verified", "not_reviewed", "unknown", "conflicting", "restricted",
})


def _kind(path):
    if not isinstance(path, str):
        return None
    if LANDSCAPE.fullmatch(path):
        return "landscape_candidate"
    if ACCESS.fullmatch(path) and path != "access/source-access-inventory.json":
        return "access_contract"
    return None


def _rows(value, label):
    if type(value) is not list or not 1 <= len(value) <= MAX_ENTRIES:
        raise ValueError(f"{label}: nonempty bounded JSON array required")
    if not all(type(r) is dict for r in value):
        raise ValueError(f"{label}: metadata objects required")
    return value


def _sha(value):
    return type(value) is str and GIT_SHA1.fullmatch(value) is not None


def _expected_identity(path, kind):
    stem = path.rsplit("/", 1)[1][:-5]
    return (("landscape_file:" if kind == "landscape_candidate" else "access:")
            + stem, stem)


def _github(listings):
    result = {}
    for row in _rows(listings, "GitHub pinned two-directory inventory"):
        path = row.get("path")
        kind = _kind(path)
        if kind is None:
            continue
        if path in result or row.get("type") != "file" or not _sha(row.get("sha")):
            raise ValueError(f"GitHub duplicated or invalid source identity: {path}")
        result[path] = {"sha": row["sha"], "type": kind}
    if not any(v["type"] == "landscape_candidate" for v in result.values()):
        raise ValueError("GitHub landscape inventory absent")
    if not any(v["type"] == "access_contract" for v in result.values()):
        raise ValueError("GitHub access inventory absent")
    return result


def _neon(rows, label):
    result, keys = {}, set()
    for row in _rows(rows, label):
        path = row.get("git_path")
        kind = _kind(path)
        if kind is None:
            continue
        key, source_id = _expected_identity(path, kind)
        if (path in result or row.get("classification") != kind
            or row.get("source_key") != key or row.get("source_id") != source_id
            or not _sha(row.get("git_blob_sha"))
            or row.get("admissible_for_raw") is not False
            or row.get("repo") != REPO):
            raise ValueError(f"{label}: unsafe classification, provenance or identity: {path}")
        if row["source_key"] in keys:
            raise ValueError(f"{label}: reused source key")
        keys.add(row["source_key"])
        if kind == "landscape_candidate":
            if (row.get("review_status") != "non_admission_discovery_only"
                or row.get("rights_status") != "not_reviewed"):
                raise ValueError(f"{label}: landscape rights/status promoted: {path}")
        elif (row.get("review_status") not in ACCESS_STATUSES
              or row.get("rights_status") not in ACCESS_RIGHTS):
            raise ValueError(f"{label}: access status is not a reviewed metadata label: {path}")
        result[path] = row
    return result


def compare(github_inventory, stage_export, production_export):
    github = _github(github_inventory)
    stage = _neon(stage_export, "stage")
    production = _neon(production_export, "production")
    candidate, unchanged, stage_missing, stage_drift = [], [], [], []
    production_drift, stage_extra, prod_extra = [], [], []
    for path in sorted(github):
        gh = github[path]["sha"]
        staged = stage.get(path)
        live = production.get(path)
        if staged is None:
            stage_missing.append(path)
        elif staged["git_blob_sha"] != gh:
            stage_drift.append(path)
        if live is None:
            if staged is not None and staged["git_blob_sha"] == gh:
                candidate.append({
                    "git_path": path,
                    "git_blob_sha": gh,
                    "classification": github[path]["type"],
                    "source_key": staged["source_key"],
                    "review_status": staged["review_status"],
                    "rights_status": staged["rights_status"],
                })
        elif live["git_blob_sha"] != gh:
            production_drift.append(path)
        else:
            unchanged.append(path)
    stage_extra = sorted(set(stage) - set(github))
    prod_extra = sorted(set(production) - set(github))
    version_conflicts = sorted(
        path for path in set(stage) & set(production)
        if stage[path]["git_blob_sha"] != production[path]["git_blob_sha"]
    )
    review = bool(candidate or stage_missing or stage_drift or production_drift
                  or stage_extra or prod_extra or version_conflicts)
    return {
        "schema": "cat-source-registry-3way-snapshot-v0",
        "github_canonical_files": len(github),
        "github_landscape_shards": sum(x["type"] == "landscape_candidate"
                                       for x in github.values()),
        "github_access_contracts": sum(x["type"] == "access_contract"
                                       for x in github.values()),
        "stage_canonical_records": len(stage),
        "production_canonical_records": len(production),
        "production_current_blob_matches": len(unchanged),
        "manual_append_review_candidates": candidate,
        "stage_missing_paths": stage_missing,
        "stage_blob_drift": stage_drift,
        "production_blob_drift": production_drift,
        "historical_version_conflicts": version_conflicts,
        "stale_stage_paths": stage_extra,
        "stale_production_paths": prod_extra,
        "review_needed": review,
        "automatic_production_sync_authorized": False,
        "source_or_scientific_admission_authorized": False,
        "insurer_data_or_provider_bytes_present": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--github-inventory", type=Path, required=True)
    p.add_argument("--stage-export", type=Path, required=True)
    p.add_argument("--production-export", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        report = compare(strict_load(a.github_inventory),
                         strict_load(a.stage_export),
                         strict_load(a.production_export))
    except (ValueError, OSError, UnicodeError) as exc:
        print("INVALID_METADATA: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 2 if report["review_needed"] else 0


if __name__ == "__main__":
    sys.exit(main())
