# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, identity-pinned comparison of two public access contract Git blobs.

Never fetch provider bytes, connect to a database, rewrite files, or promote
source rights/model readiness. This is a metadata-only revision-review gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 100_000
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
ACCESS_ID = re.compile(r"[a-z0-9][a-z0-9._-]{2,200}\Z")


class RevisionAuditBlocked(ValueError):
    """A provenance, input integrity, or source identity gate failed."""


def _unique_object_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise RevisionAuditBlocked(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _read_contract(raw: bytes, expected_git_blob_sha: str) -> dict:
    if not isinstance(raw, bytes) or not (0 < len(raw) <= MAX_BYTES):
        raise RevisionAuditBlocked("empty or oversized access metadata file")
    if not isinstance(expected_git_blob_sha, str) or not SHA1.fullmatch(expected_git_blob_sha):
        raise RevisionAuditBlocked("invalid pinned Git blob SHA-1")
    git_object = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    actual_sha = hashlib.sha1(git_object).hexdigest()
    if actual_sha != expected_git_blob_sha:
        raise RevisionAuditBlocked("source Git blob checksum mismatch")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RevisionAuditBlocked("not a valid UTF-8 JSON document") from exc
    if not isinstance(value, dict):
        raise RevisionAuditBlocked("access contract is not a JSON object")
    aid = value.get("access_id")
    if not isinstance(aid, str) or not ACCESS_ID.fullmatch(aid):
        raise RevisionAuditBlocked("access contract ID invalid")
    sources = value.get("source_ids")
    if not isinstance(sources, list) or not sources or any(not isinstance(x, str) or not x for x in sources):
        raise RevisionAuditBlocked("missing source identity list")
    if not isinstance(value.get("provider"), str) or not value["provider"].strip():
        raise RevisionAuditBlocked("missing provider identity")
    if not isinstance(value.get("status"), str) or not value["status"].strip():
        raise RevisionAuditBlocked("missing access status")
    rights = value.get("rights_and_policy")
    if not isinstance(rights, dict) or not isinstance(rights.get("dataset_rights_status"), str):
        raise RevisionAuditBlocked("rights evidence status missing")
    return value


def _changed_paths(a: object, b: object, prefix: str = "") -> list[str]:
    if a == b:
        return []
    if isinstance(a, dict) and isinstance(b, dict):
        changes = []
        for key in sorted(set(a) | set(b)):
            path = prefix + "." + key if prefix else key
            if key not in a or key not in b:
                changes.append(path)
            else:
                changes.extend(_changed_paths(a[key], b[key], path))
        return changes
    # Report list paths as an atomic field, never disclose individual values.
    return [prefix]


def compare(old_raw: bytes, new_raw: bytes, *, old_blob_sha: str, new_blob_sha: str) -> dict:
    old = _read_contract(old_raw, old_blob_sha)
    new = _read_contract(new_raw, new_blob_sha)
    if old["access_id"] != new["access_id"] or old["source_ids"] != new["source_ids"]:
        raise RevisionAuditBlocked("source identity changed: review as a separate source")
    changes = _changed_paths(old, new)
    return {
        "schema": "oc-access-contract-revision-audit-v0",
        "access_id": old["access_id"],
        "old_git_blob_sha": old_blob_sha,
        "new_git_blob_sha": new_blob_sha,
        "old_status": old["status"],
        "new_status": new["status"],
        "old_dataset_rights_status": old["rights_and_policy"]["dataset_rights_status"],
        "new_dataset_rights_status": new["rights_and_policy"]["dataset_rights_status"],
        "changed_field_paths": changes,
        "changed_field_count": len(changes),
        "version_review_required": bool(changes),
        "overwrite_prior_record_authorized": False,
        "automated_provider_access_authorized": False,
        "raw_import_authorized": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--old-blob-sha", required=True)
    parser.add_argument("--new-blob-sha", required=True)
    args = parser.parse_args(argv)
    try:
        old = args.old.read_bytes()
        new = args.new.read_bytes()
        result = compare(old, new, old_blob_sha=args.old_blob_sha, new_blob_sha=args.new_blob_sha)
    except (OSError, RevisionAuditBlocked) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    # Changed contracts require human review; they never auto-authorize a DB update.
    return 2 if result["version_review_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
