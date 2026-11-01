# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare two independently exported, metadata-only Neon branch manifests.

No database connections, external HTTP, migrations, or automatic merge.
A name, market, or status match is never legal-entity/rights approval.
"""
import argparse
import json
from pathlib import Path

SCHEMA = "OC-NEON-BRANCH-METADATA-V0"
SOURCE_FIELDS = ("git_blob_sha", "review_status", "rights_status", "admissible_for_raw")
CANDIDATE_FIELDS = ("identity_resolution_status", "verified_organization_id")


def load_manifest(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if isinstance(value, dict) and "metadata_manifest" in value:
        value = value["metadata_manifest"]
    if not isinstance(value, dict) or value.get("format") != SCHEMA:
        raise ValueError(f"{path}: invalid manifest format")
    if not isinstance(value.get("sources"), list) or not isinstance(value.get("candidates"), list):
        raise ValueError(f"{path}: sources/candidates must be arrays")
    for collection, key in (("sources", "source_key"), ("candidates", "source_row_key")):
        seen = set()
        for row in value[collection]:
            if not isinstance(row, dict) or not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"{path}: invalid {collection} key")
            if row[key] in seen:
                raise ValueError(f"{path}: duplicate {collection} key {row[key]}")
            seen.add(row[key])
    return value


def compare_collection(main, validation, collection, key, fields, details):
    left = {row[key]: row for row in main[collection]}
    right = {row[key]: row for row in validation[collection]}
    shared = sorted(left.keys() & right.keys())
    main_only = sorted(left.keys() - right.keys())
    validation_only = sorted(right.keys() - left.keys())
    conflicts = []
    for item in shared:
        divergent = [field for field in fields if left[item].get(field) != right[item].get(field)]
        if divergent:
            conflicts.append({"key": item, "fields": divergent})
    result = {
        "main_rows": len(left),
        "validation_rows": len(right),
        "shared_keys": len(shared),
        "main_only": len(main_only),
        "validation_only": len(validation_only),
        "conflicting_shared_keys": len(conflicts),
        "conflict_fields": {f: sum(f in c["fields"] for c in conflicts) for f in fields},
    }
    if details:
        # This shows source identifiers only, never external data or credentials.
        result.update(main_only_keys=main_only, validation_only_keys=validation_only, conflicts=conflicts)
    return result


def compare(main, validation, details=False):
    for value in (main, validation):
        if not isinstance(value, dict) or value.get("format") != SCHEMA:
            raise ValueError("Invalid input format")
    sources = compare_collection(main, validation, "sources", "source_key", SOURCE_FIELDS, details)
    candidates = compare_collection(main, validation, "candidates", "source_row_key", CANDIDATE_FIELDS, details)
    return {
        "format": "OC-NEON-BRANCH-DIFF-V0",
        "sources": sources,
        "organization_candidates": candidates,
        "manual_merge_review_required": bool(
            sources["conflicting_shared_keys"] or candidates["conflicting_shared_keys"]
            or sources["main_only"] or sources["validation_only"]
            or candidates["main_only"] or candidates["validation_only"]
        ),
        "automatic_merge_authorized": False,
        "model_input_approved_by_this_tool": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--details", action="store_true", help="show conflicting metadata keys, never raw bytes")
    args = parser.parse_args()
    result = compare(load_manifest(args.main), load_manifest(args.validation), args.details)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    # Returns 2 when a manual review is needed; never auto-merges even at exit 0.
    return 2 if result["manual_merge_review_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
