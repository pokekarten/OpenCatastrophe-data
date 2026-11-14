# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare two SHA-pinned, strictly non-admitted landscape source revisions.

This is a read-only/offline *scientific metadata* review gate. It does not
download provider bytes, access Neon, create migrations, authorize publication
or infer that a candidate has become model-ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from scripts.source_landscape_contract import (
    LandscapeContractError, validate_landscape_shard,
)

GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES = 3_000_000
FROZEN_IDENTITY_FIELDS = ("candidate_id", "provider", "authoritative_url")
STATE_FIELDS = ("candidate_status", "rights_review_status",
                "scientific_review_status", "admission_status")


class LandscapeRevisionBlocked(ValueError):
    """The original source identity, non-admission or input proof is invalid."""


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LandscapeRevisionBlocked("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise LandscapeRevisionBlocked("nonfinite numeric JSON is invalid")


def _read(raw: bytes, expected_sha: str) -> dict:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise LandscapeRevisionBlocked("empty/oversized source-shard metadata")
    if type(expected_sha) is not str or GIT_SHA.fullmatch(expected_sha) is None:
        raise LandscapeRevisionBlocked("invalid pinned Git blob SHA")
    got = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if got != expected_sha:
        raise LandscapeRevisionBlocked("Git blob SHA mismatch")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object,
                           parse_constant=_reject_constant)
        if type(value) is not dict:
            raise LandscapeRevisionBlocked("shard metadata is not an object")
        validate_landscape_shard(Path("source-revision.json"), value)
    except (UnicodeError, json.JSONDecodeError, LandscapeContractError) as exc:
        raise LandscapeRevisionBlocked("invalid non-admission source contract") from exc
    seen = set()
    for item in value["entries"]:
        if item["candidate_id"] in seen:
            raise LandscapeRevisionBlocked("repeated candidate_id in one source shard")
        seen.add(item["candidate_id"])
    return value


def compare(old_raw: bytes, new_raw: bytes, *, old_blob_sha: str,
            new_blob_sha: str) -> dict:
    old, new = _read(old_raw, old_blob_sha), _read(new_raw, new_blob_sha)
    original = {r["candidate_id"]: r for r in old["entries"]}
    revised = {r["candidate_id"]: r for r in new["entries"]}
    removed = sorted(set(original) - set(revised))
    if removed:
        raise LandscapeRevisionBlocked(
            "candidate IDs removed or renamed; independent source review required"
        )
    changed = {}
    for cid in sorted(original.keys() & revised.keys()):
        a, b = original[cid], revised[cid]
        if any(a[k] != b[k] for k in FROZEN_IDENTITY_FIELDS):
            raise LandscapeRevisionBlocked(
                "provider/URL identity changed; treat as new source or explicit review"
            )
        if any(a[k] != b[k] for k in STATE_FIELDS):
            raise LandscapeRevisionBlocked("review/admission status changed")
        fields = sorted(k for k in a if a[k] != b[k])
        if fields:
            changed[cid] = fields
    added = sorted(set(revised) - set(original))
    headers = sorted(k for k in ("purpose", "review_date", "schema_version")
                     if old[k] != new[k])
    # Fresh entries are validated by the same strict fail-closed landscape
    # contract and cannot be treated as reviewed rights or admitted models.
    return {
        "schema": "cat-landscape-source-revision-proof-v0",
        "old_git_blob_sha": old_blob_sha,
        "new_git_blob_sha": new_blob_sha,
        "old_candidate_count": len(original),
        "new_candidate_count": len(revised),
        "added_nonadmitted_candidate_ids": added,
        "modified_existing_candidate_fields": changed,
        "changed_shard_header_fields": headers,
        "manual_semantic_review_required": bool(added or changed or headers),
        "rights_approval_authorized": False,
        "source_or_model_admission_authorized": False,
        "source_bytes_downloaded": False,
        "neon_production_mutation_authorized": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old", type=Path, required=True)
    p.add_argument("--new", type=Path, required=True)
    p.add_argument("--old-blob-sha", required=True)
    p.add_argument("--new-blob-sha", required=True)
    args = p.parse_args(argv)
    try:
        result = compare(
            args.old.read_bytes(), args.new.read_bytes(),
            old_blob_sha=args.old_blob_sha, new_blob_sha=args.new_blob_sha,
        )
    except (OSError, LandscapeRevisionBlocked) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 2 if result["manual_semantic_review_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
