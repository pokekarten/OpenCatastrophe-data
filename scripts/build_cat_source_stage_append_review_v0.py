# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Reproduce an offline, manual-only CAT source-register staging append review.

Inputs are (1) a three-directory, immutable GitHub-commit contents listing,
(2) a separately exported *isolated stage* source_record metadata snapshot,
(3) an independently exported production/main snapshot, and (4) the checked
out canonical public JSON files.

The preview never connects to a database, performs SQL, fetches provider data,
creates an admission, changes rights or authorizes an automatic append. It
checks Git blob identity, strict source contracts, version drift and source
key collisions before producing a *review queue*, not executable SQL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from scripts.audit_cat_source_registry_two_way_v0 import (
    _github, _github_manifests, compare as audit_two_way,
)
from scripts.audit_insurance_landscape_sync_v0 import load as strict_load
from scripts.source_landscape_contract import load_landscape_shard
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
GIT_SHA = re.compile(r"[a-f0-9]{40}\Z")
MAX_CANONICAL_BYTES = 3_000_000
REPO = "pokekarten/OpenCatastrophe-data"


def git_blob_sha(data: bytes) -> str:
    """Git SHA-1 blob identity; independent SHA-256 is recorded separately."""
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _file_receipt(root: Path, path: str, declared_sha: str, kind: str, commit: str) -> dict:
    base = root.resolve()
    file = (base / path).resolve()
    if not file.is_relative_to(base) or not file.is_file():
        raise ValueError(f"invalid or missing local canonical source: {path}")
    if file.stat().st_size > MAX_CANONICAL_BYTES:
        raise ValueError(f"canonical JSON exceeds metadata-only byte ceiling: {path}")
    data = file.read_bytes()
    if git_blob_sha(data) != declared_sha:
        raise ValueError(f"Git blob mismatch / checkout drift: {path}")
    stem = Path(path).stem
    if kind == "landscape_candidate":
        payload = load_landscape_shard(file)
        source_id = stem
        source_key = "landscape_file:" + stem
        status, rights = "non_admission_discovery_only", "not_reviewed"
        name = "OpenCatastrophe source discovery " + stem
        provider, canonical_url = "OpenCatastrophe source discovery", None
    elif kind == "access_contract":
        payload = validate_path(file)
        source_id = payload["access_id"]
        if source_id != stem and not (
            stem.endswith(".documented") and source_id == stem.removesuffix(".documented")
        ):
            raise ValueError(f"access source_id does not match canonical path: {path}")
        source_key = "access:" + source_id
        status = payload["status"]
        rights = payload["rights_and_policy"]["dataset_rights_status"]
        name = provider = payload["provider"]
        canonical_url = payload["documentation_url"]
    else:
        raise ValueError("manifest admissions cannot be appended through this review")
    return {
        "source_key": source_key,
        "source_id": source_id,
        "classification": kind,
        "repo": REPO,
        "git_path": path,
        "git_blob_sha": declared_sha,
        "git_commit_sha": commit,
        "source_name": name,
        "provider": provider,
        "canonical_url": canonical_url,
        "review_status": status,
        "rights_status": rights,
        "admissible_for_raw": False,
        "canonical_json_sha256": hashlib.sha256(data).hexdigest(),
        "manual_review_required": True,
    }


def build_review(github_inventory, stage_export, production_export, root: Path, commit: str) -> dict:
    if not isinstance(commit, str) or GIT_SHA.fullmatch(commit) is None:
        raise ValueError("an immutable 40-character GitHub commit SHA is required")
    stage_result = audit_two_way(github_inventory, stage_export)
    production_result = audit_two_way(github_inventory, production_export)
    gh = _github(github_inventory)
    gh.update({p: {"sha": s, "type": "admitted_manifest"}
               for p, s in _github_manifests(github_inventory).items()})
    stage_paths = {v.get("git_path"): v for v in stage_export}
    prod_paths = {v.get("git_path"): v for v in production_export}
    stage_keys = {v.get("source_key") for v in stage_export}
    prod_keys = {v.get("source_key") for v in production_export}
    candidates, blocked_prod, blocked_manifests = [], [], []
    for path in sorted(gh):
        if path in stage_paths:
            continue
        if path in prod_paths:
            blocked_prod.append(path)
            continue
        kind = gh[path]["type"]
        if kind == "admitted_manifest":
            blocked_manifests.append(path)
            continue
        receipt = _file_receipt(root, path, gh[path]["sha"], kind, commit)
        key = receipt["source_key"]
        if key in stage_keys or key in prod_keys or any(x["source_key"] == key for x in candidates):
            raise ValueError(f"reused source identity in append candidate: {key}")
        candidates.append(receipt)

    def drift(result):
        return [x["git_path"] for kind in result["classes"].values()
                for x in kind["blob_drift_requires_review"]]

    return {
        "schema": "cat-source-register-stage-append-review-v0",
        "github_commit": commit,
        "github_canonical_files": len(gh),
        "isolated_stage_exact_matches": sum(v["exact_blob_matches"] for v in stage_result["classes"].values()),
        "production_exact_matches": sum(v["exact_blob_matches"] for v in production_result["classes"].values()),
        "manual_stage_append_candidates": candidates,
        "stage_lags_production_do_not_append": blocked_prod,
        "missing_manifest_admissions_blocked": blocked_manifests,
        "isolated_stage_version_drift": sorted(drift(stage_result)),
        "production_version_drift": sorted(drift(production_result)),
        "review_required": bool(candidates or blocked_prod or blocked_manifests
                                or stage_result["review_needed"]
                                or production_result["review_needed"]),
        "read_only_no_database_connection": True,
        "sql_or_auto_append_generated": False,
        "production_write_authorized": False,
        "raw_data_or_model_admission_authorized": False,
        "review_boundary": "Source metadata files only. Confirm unchanged original rows, exact local bytes, rights and a separately isolated transaction before any append.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-inventory", type=Path, required=True)
    parser.add_argument("--stage-export", type=Path, required=True)
    parser.add_argument("--production-export", type=Path, required=True)
    parser.add_argument("--github-commit", required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = build_review(
            strict_load(args.github_inventory),
            strict_load(args.stage_export),
            strict_load(args.production_export),
            args.repo_root,
            args.github_commit,
        )
    except (OSError, ValueError, UnicodeError, TypeError) as exc:
        print("INVALID_SOURCE_PROOF: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 2 if result["review_required"] else 0


if __name__ == "__main__":
    sys.exit(main())
