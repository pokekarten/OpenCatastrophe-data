# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline GitHub vs Neon production metadata coverage audit for all three source layers.

No network, database access, SQL, provider files or mutation. Requires an independently
pinned GitHub SHA directory listing (landscape/, access/, manifests/) and a read-only
Neon registry.source_record metadata export. Missing files are a manual review
queue, never a request to automatically import data or upgrade rights.

Example:
  python scripts/audit_cat_source_registry_two_way_v0.py \
    --github-inventory /private/github-three-dir.json \
    --neon-export /private/neon-main-metadata.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from scripts.audit_cat_source_registry_three_way_v0 import (
    _github, _neon, _rows, _sha,
)
from scripts.audit_insurance_landscape_sync_v0 import load as strict_load

REPO = "pokekarten/OpenCatastrophe-data"
MANIFEST = re.compile(r"manifests/([A-Za-z0-9][A-Za-z0-9._-]*)\.json\Z")
STATUSES = frozenset({"approved_metadata_only", "approved_derived"})
KINDS = ("landscape_candidate", "access_contract", "admitted_manifest")


def _github_manifests(rows):
    found = {}
    for row in _rows(rows, "pinned three-directory GitHub inventory"):
        path = row.get("path")
        if not isinstance(path, str) or not path.startswith("manifests/"):
            continue
        if MANIFEST.fullmatch(path) is None:
            raise ValueError(f"noncanonical manifest path: {path}")
        if path in found or row.get("type") != "file" or not _sha(row.get("sha")):
            raise ValueError(f"invalid or repeated GitHub manifest: {path}")
        found[path] = row["sha"]
    if not found:
        raise ValueError("GitHub manifest inventory absent")
    return found


def _neon_manifests(rows):
    found, keys = {}, set()
    for row in _rows(rows, "Neon production metadata export"):
        path = row.get("git_path")
        if row.get("classification") != "admitted_manifest" and (
            not isinstance(path, str) or not path.startswith("manifests/")
        ):
            continue
        match = MANIFEST.fullmatch(path) if isinstance(path, str) else None
        if match is None:
            raise ValueError(f"admitted manifest has noncanonical path: {path}")
        source_id = match.group(1)
        key = "manifest:" + source_id
        if (path in found or key in keys or row.get("classification") != "admitted_manifest"
            or row.get("source_id") != source_id or row.get("source_key") != key
            or row.get("repo") != REPO or not _sha(row.get("git_blob_sha"))
            or row.get("admissible_for_raw") is not False
            or row.get("review_status") not in STATUSES
            or not isinstance(row.get("rights_status"), str)
            or not row["rights_status"]):
            raise ValueError(f"unsafe manifest identity, admission or provenance: {path}")
        found[path] = row
        keys.add(key)
    if not found:
        raise ValueError("Neon admitted manifest records absent")
    return found


def compare(github_inventory, production_export):
    """Generate a deterministic, fail-closed manual reconciliation report."""
    github = _github(github_inventory)
    github.update({path: {"sha": sha, "type": "admitted_manifest"}
                   for path, sha in _github_manifests(github_inventory).items()})
    neon = _neon(production_export, "production")
    neon.update(_neon_manifests(production_export))
    out = {}
    for kind in KINDS:
        gh = {p: o for p, o in github.items() if o["type"] == kind}
        nd = {p: o for p, o in neon.items() if o["classification"] == kind}
        shared = sorted(set(gh) & set(nd))
        out[kind] = {
            "github_files": len(gh),
            "neon_records": len(nd),
            "exact_blob_matches": sum(gh[p]["sha"] == nd[p]["git_blob_sha"] for p in shared),
            "missing_in_neon": [{"git_path": p, "github_blob_sha": gh[p]["sha"]}
                                for p in sorted(set(gh) - set(nd))],
            "blob_drift_requires_review": [{
                "git_path": p, "github_blob_sha": gh[p]["sha"],
                "neon_blob_sha": nd[p]["git_blob_sha"]}
                for p in shared if gh[p]["sha"] != nd[p]["git_blob_sha"]],
            "neon_paths_absent_from_git": sorted(set(nd) - set(gh)),
        }
    review = any((v["missing_in_neon"] or v["blob_drift_requires_review"]
                  or v["neon_paths_absent_from_git"]) for v in out.values())
    return {
        "schema": "cat-source-registry-two-way-v0",
        "classes": out,
        "github_canonical_metadata_files": len(github),
        "neon_canonical_metadata_records": len(neon),
        "review_needed": bool(review),
        "automatic_production_sync_authorized": False,
        "source_data_acquisition_or_model_use_authorized": False,
        "manifest_metadata_admission_is_not_raw_admission": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-inventory", type=Path, required=True)
    parser.add_argument("--neon-export", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = compare(strict_load(args.github_inventory), strict_load(args.neon_export))
    except (ValueError, OSError, UnicodeError, TypeError) as exc:
        print("INVALID_METADATA: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 2 if result["review_needed"] else 0


if __name__ == "__main__":
    sys.exit(main())
