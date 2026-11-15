# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline read-only GitHub/Neon landscape-shard registry coverage audit.

This compares *source landscape JSON files*, not unique candidate datasets.
GitHub content metadata and independently exported Neon rows are the only
inputs. No HTTP, database writes, provider data, admission or rights changes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

SHA1 = re.compile(r"[0-9a-f]{40}\Z")
LANDSCAPE_PATH = re.compile(r"landscape/(sources[A-Za-z0-9._-]*)\.json\Z")
MAX_BYTES = 3_000_000
MAX_RECORDS = 500


def _strict_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON object key")
        obj[key] = value
    return obj


def _no_nan(value):
    raise ValueError("nonfinite JSON value is not valid provenance")


def load(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ValueError("inventory exceeds the 3 MB metadata budget")
    return json.loads(p.read_text(encoding="utf-8"),
                      object_pairs_hook=_strict_object, parse_constant=_no_nan)


def _array(value, name):
    if not isinstance(value, list) or not 0 < len(value) <= MAX_RECORDS:
        raise ValueError(f"{name} must be a nonempty bounded array")
    if not all(isinstance(row, dict) for row in value):
        raise ValueError(f"{name} entries must be JSON objects")
    return value


def _sha(value):
    return isinstance(value, str) and bool(SHA1.fullmatch(value))


def _stem(path):
    match = LANDSCAPE_PATH.fullmatch(path) if isinstance(path, str) else None
    return match.group(1) if match else None


def compare(github_contents, neon_rows):
    """Return a review queue; never authorize unattended registration."""
    github = {}
    for row in _array(github_contents, "github directory listing"):
        path = row.get("path")
        stem = _stem(path)
        if stem is None:
            continue
        if row.get("type") != "file" or not _sha(row.get("sha")):
            raise ValueError(f"github file/sha invalid: {path}")
        if path in github:
            raise ValueError(f"github duplicate landscape shard: {path}")
        github[path] = row["sha"]
    if not github:
        raise ValueError("github inventory contains no landscape/sources*.json")

    neon = {}
    for row in _array(neon_rows, "Neon source_record export"):
        path = row.get("git_path")
        if _stem(path) is None:
            continue
        if not _sha(row.get("git_blob_sha")):
            raise ValueError(f"Neon provenance blob SHA malformed: {path}")
        if path in neon:
            raise ValueError(f"Neon duplicate shard path: {path}")
        neon[path] = row
    if not neon:
        raise ValueError("Neon export contains no canonical landscape records")

    shared = sorted(set(github) & set(neon))
    missing = sorted(set(github) - set(neon))
    stale = sorted(set(neon) - set(github))
    drift = sorted(path for path in shared
                   if github[path] != neon[path]["git_blob_sha"])
    wrong = sorted(path for path in shared
                   if neon[path].get("classification") != "landscape_candidate"
                   or neon[path].get("source_id") != _stem(path)
                   or neon[path].get("source_key") != "landscape_file:" + _stem(path))
    unexpected_raw = sorted(path for path in neon
                            if neon[path].get("admissible_for_raw") is not False)
    review = bool(missing or stale or drift or wrong or unexpected_raw)
    return {
        "schema": "insurance-landscape-shard-sync-v0",
        "github_landscape_shards": len(github),
        "neon_landscape_records": len(neon),
        "exact_git_blob_matches": sum(github[path] == neon[path]["git_blob_sha"]
                                      for path in shared),
        "missing_in_neon": [
            {"git_path": path, "git_blob_sha": github[path]}
            for path in missing
        ],
        "neon_paths_not_in_github": stale,
        "shared_paths_with_blob_drift": [
            {"git_path": path, "github_blob_sha": github[path],
             "neon_blob_sha": neon[path]["git_blob_sha"]}
            for path in drift
        ],
        "wrong_classification_or_identity": wrong,
        "unexpected_raw_admission": unexpected_raw,
        "review_needed": review,
        "automatic_sync_authorized": False,
        "source_rights_or_model_admission_authorized": False,
        "repository_shard_is_not_unique_provider_dataset": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-inventory", type=Path, required=True)
    parser.add_argument("--neon-export", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = compare(load(args.github_inventory), load(args.neon_export))
    except (ValueError, OSError, UnicodeError) as exc:
        print("INVALID_INPUT: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 2 if result["review_needed"] else 0


if __name__ == "__main__":
    sys.exit(main())
