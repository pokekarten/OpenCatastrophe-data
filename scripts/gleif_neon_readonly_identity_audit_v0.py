#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline read-only GLEIF / Neon identity reconciliation: never import records.

Source A: an independently verified CAT-only SQLite GLEIF Level-1 pilot.
Source B: an operator-provided *read-only* Neon LEI export with a policy
receipt. Neither a database connection to Neon nor a write API exists here.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.export_cat_source_registry_sqlite import (  # noqa: E402
    CAT_APP_ID, CAT_SCHEMA_VERSION,
)
from scripts.gleif_level1_insurer_identity_pilot import (  # noqa: E402
    PILOT_LEIS, valid_lei,
)

SCHEMA = "oc-gleif-neon-readonly-identity-crosscheck-v0"
SNAPSHOT_SCHEMA = "oc-gleif-neon-readonly-export-v0"
MAX_SNAPSHOT_BYTES = 16384
SHA = re.compile(r"[0-9a-f]{64}\Z")


class IdentityAuditError(ValueError):
    """Read-only database identities or proof of import approval is missing."""


def _need(test: bool, message: str) -> None:
    if not test:
        raise IdentityAuditError(message)


def _unique_pairs(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise IdentityAuditError("duplicate key in read-only Neon export")
        data[key] = value
    return data


def _parse_snapshot(original: bytes) -> dict:
    _need(type(original) is bytes and 0 < len(original) <= MAX_SNAPSHOT_BYTES,
          "bounded read-only Neon source export required")
    try:
        obj = json.loads(original.decode("utf-8-sig"), object_pairs_hook=_unique_pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(
                             IdentityAuditError("non-finite JSON constant")))
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, IdentityAuditError):
            raise
        raise IdentityAuditError("malformed read-only Neon export") from exc
    _need(type(obj) is dict and set(obj) == {"schema_version", "feed", "identifiers"},
          "unexpected snapshot fields; export identifiers, not company personal data")
    _need(obj["schema_version"] == SNAPSHOT_SCHEMA, "unsupported read-only snapshot")
    feed = obj["feed"]
    _need(type(feed) is dict and set(feed) == {
        "feed_id", "rights_status", "automated_import_allowed",
    }, "incomplete Neon GLEIF policy proof")
    _need(feed["feed_id"] == "gleif_global"
          and feed["rights_status"] == "cc0_verified"
          and feed["automated_import_allowed"] is False,
          "no reviewed authorization to enable automated GLEIF imports")
    identifiers = obj["identifiers"]
    _need(type(identifiers) is list and len(identifiers) <= len(PILOT_LEIS),
          "only the six selected pilot legal entities may be compared")
    seen = set()
    for row in identifiers:
        _need(type(row) is dict and set(row) == {
            "identifier_scheme", "identifier_value", "is_verified",
        }, "bad Neon identifier export shape")
        lei = row["identifier_value"]
        _need(row["identifier_scheme"] == "GLEIF_LEI"
              and type(lei) is str and lei in PILOT_LEIS and valid_lei(lei)
              and row["is_verified"] is True,
              "non-GLEIF, unsupported, invalid or unverified LEI")
        _need(lei not in seen, "Neon contains duplicate pilot LEI records")
        seen.add(lei)
    return {"present": sorted(seen), "feed": feed}


def _verify_sqlite(original: Path) -> dict:
    path = Path(original).expanduser()
    _need(not path.is_symlink() and path.is_file(),
          "require existing regular CAT-only SQLite file, never a symlink")
    # URI mode=ro *and* query_only prevent opening a writer even if permissions permit.
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as conn:
            conn.execute("PRAGMA query_only=ON")
            _need(conn.execute("PRAGMA application_id").fetchone()[0] == CAT_APP_ID
                  and conn.execute("PRAGMA user_version").fetchone()[0] == CAT_SCHEMA_VERSION,
                  "source is not the separately identified CAT SQLite database")
            _need(conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' "
                "AND name='cat_gleif_legal_entity'").fetchone()[0] == 1,
                "no verified GLEIF Level-1 pilot in this CAT database")
            rows = conn.execute(
                "SELECT lei,source_sha256,source_license,insured_exposure_status,"
                "underwriting_role FROM cat_gleif_legal_entity ORDER BY lei").fetchall()
    except sqlite3.DatabaseError as exc:
        raise IdentityAuditError("read-only GLEIF identity source unavailable") from exc
    _need(len(rows) == len(PILOT_LEIS), "expected exactly the six original GLEIF pilot LEIs")
    seen = set()
    for lei, source_sha, licence, exposure, underwriting_role in rows:
        _need(type(lei) is str and lei in PILOT_LEIS and valid_lei(lei),
              "wrong pilot LEI in source SQLite")
        _need(lei not in seen, "duplicate GLEIF Level-1 identity")
        _need(type(source_sha) is str and SHA.fullmatch(source_sha) is not None,
              "missing source-original LEI SHA-256")
        _need(licence == "CC0-1.0"
              and exposure == "not_available"
              and underwriting_role == "not_determined_from_lei",
              "source identity is not an underwriting or exposure admission")
        seen.add(lei)
    _need(seen == set(PILOT_LEIS), "incomplete GLEIF seed identity set")
    return {lei: source_sha for lei,source_sha,*_ in rows}


def audit_readonly_neon_dedup(cat_db: Path, neon_export_bytes: bytes) -> dict:
    original = _verify_sqlite(cat_db)
    snapshot = _parse_snapshot(neon_export_bytes)
    existing = set(snapshot["present"])
    missing = sorted(set(original) - existing)
    return {
        "schema_version": SCHEMA,
        "status": "READONLY_IDENTITY_COMPARISON_NO_IMPORT",
        "source_class": "CAT_SQLITE_GLEIF_LEVEL1_ORIGINAL_SHA_BOUND",
        "neon_feed": snapshot["feed"]["feed_id"],
        "neon_export_sha256": hashlib.sha256(neon_export_bytes).hexdigest(),
        "cat_lei_count": len(original),
        "already_verified_lei_count": len(existing),
        "missing_lei_count": len(missing),
        "already_verified_leis": sorted(existing),
        "missing_leis_pending_manual_review": missing,
        "source_sha256_by_lei": dict(sorted(original.items())),
        "crosswalk_key": "GLEIF_LEI_EXACT_ISO_17442_VALUE",
        "automatic_import_allowed": False,
        "neon_updated": False,
        "pokemon_database_accessed": False,
        "new_organizations_created": False,
        "parent_or_treaty_inferred": False,
        "insured_exposure_created": False,
        "model_source_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cat-sqlite", type=Path, required=True)
    parser.add_argument("--neon-readonly-export", type=Path, required=True)
    args = parser.parse_args()
    source = args.neon_readonly_export
    if source.is_symlink() or not source.is_file():
        raise IdentityAuditError("read-only Neon export must be a regular file")
    result = audit_readonly_neon_dedup(args.cat_sqlite, source.read_bytes())
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (IdentityAuditError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(1)
