# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only comparison of GitHub access contracts and CAT-only Neon metadata.

No network calls, database credentials, source bytes, SQL writes, or admission.
Inputs are independently exported JSON arrays, pinned to a reviewed Git SHA.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ACCESS_PATH = re.compile(r"access/[A-Za-z0-9][A-Za-z0-9._-]*\.json\Z")
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES = 3_000_000


def _access_path(path):
    return isinstance(path, str) and bool(ACCESS_PATH.fullmatch(path))


def _sha(value):
    return isinstance(value, str) and bool(SHA1.fullmatch(value))


def _records(value, name):
    if not isinstance(value, list):
        raise ValueError(f"{name}: expected a JSON array")
    if not value or len(value) > 1000:
        raise ValueError(f"{name}: empty or oversized inventory")
    if any(not isinstance(x, dict) for x in value):
        raise ValueError(f"{name}: every item must be an object")
    return value


def compare(github_contents, neon_rows):
    """Return bounded metadata drift; never authorize automatic synchronization."""
    github = {}
    for row in _records(github_contents, "github"):
        path = row.get("path")
        if not _access_path(path):
            continue
        if row.get("type") != "file" or not _sha(row.get("sha")):
            raise ValueError(f"github: invalid file or SHA for {path}")
        if path in github:
            raise ValueError(f"github: duplicate path {path}")
        github[path] = row["sha"]
    if not github:
        raise ValueError("github: no access/*.json contracts found")

    neon = {}
    noncanonical = []
    for row in _records(neon_rows, "neon"):
        path = row.get("git_path")
        classification = row.get("classification")
        if classification == "access_contract" and not _access_path(path):
            # Historic research receipts are not canonical access/*.json files.
            if not isinstance(path, str) or not path.strip():
                raise ValueError("neon: contract missing git_path")
            noncanonical.append(path)
            continue
        if not _access_path(path):
            continue
        if not _sha(row.get("git_blob_sha")):
            raise ValueError(f"neon: invalid SHA for {path}")
        if path in neon:
            raise ValueError(f"neon: duplicate path {path}")
        neon[path] = row

    missing = sorted(set(github) - set(neon))
    stale = sorted(set(neon) - set(github))
    drift = sorted(p for p in set(github) & set(neon)
                   if github[p] != neon[p]["git_blob_sha"])
    wrong_type = sorted(p for p in set(github) & set(neon)
                        if neon[p].get("classification") != "access_contract"
                        or neon[p].get("source_key") !=
                        "access:" + p.removeprefix("access/").removesuffix(".json"))
    review_needed = bool(missing or stale or drift or wrong_type)
    return {
        "schema": "insurance-access-sync-v0",
        "github_access_contracts": len(github),
        "neon_canonical_access_contracts": len(neon),
        "exact_blob_matches": sum(github[p] == neon[p]["git_blob_sha"]
                                  for p in set(github) & set(neon)),
        "missing_in_neon": missing,
        "not_on_github": stale,
        "git_blob_drift": drift,
        "wrong_type_or_key": wrong_type,
        "noncanonical_contract_classification": sorted(set(noncanonical)),
        "review_needed": review_needed,
        "automatic_sync_authorized": False,
        "source_rights_or_model_admission_authorized": False,
    }


def _reject_duplicate_object_keys(pairs):
    """Reject ambiguous JSON records instead of silently using last-wins keys."""
    record = {}
    for key, value in pairs:
        if key in record:
            raise ValueError(f"duplicate JSON object key: {key}")
        record[key] = value
    return record


def load(path):
    file = Path(path)
    if file.stat().st_size > MAX_BYTES:
        raise ValueError("JSON inventory exceeds 3 MB")
    return json.loads(
        file.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_object_keys,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-inventory", type=Path, required=True)
    parser.add_argument("--neon-export", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = compare(load(args.github_inventory), load(args.neon_export))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"INVALID_INPUT: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 2 if result["review_needed"] else 0


if __name__ == "__main__":
    sys.exit(main())
