#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Materialize validated, NON-ADMITTED source-discovery metadata into a CAT-only SQLite DB.

No provider data are downloaded or stored. This database is a *derived view* of
landscape/sources*.json, never a source of truth or permission for model use.
A custom SQLite application ID prevents accidental reuse of unrelated stores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

if __package__:
    from .source_landscape_contract import (
        DEFAULT_LANDSCAPE_DIR, LandscapeContractError, load_landscape_shards,
    )
else:
    from source_landscape_contract import (
        DEFAULT_LANDSCAPE_DIR, LandscapeContractError, load_landscape_shards,
    )


CAT_APP_ID = 0x43415431  # ASCII "CAT1"; never use for unrelated databases.
CAT_SCHEMA_VERSION = 1
NON_ADMISSION = "non_admission_discovery_only"


class CATSourceDBError(ValueError):
    """Refuse unsafe or inconsistent database operations."""


def _validated_rows(landscape_dir: Path):
    # The repository's *existing* canonical policy validator owns source safety,
    # duplicate IDs, URL validation, and all fail-closed rights status rules.
    rows = []
    for source_path, shard in load_landscape_shards(landscape_dir):
        file_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
        for entry in shard["entries"]:
            if entry["admission_status"] != "not_admitted":
                raise CATSourceDBError("discovery source cannot be admitted")
            rows.append((entry, source_path.name, file_sha256, shard["review_date"]))
    rows.sort(key=lambda item: item[0]["candidate_id"])
    return rows


def materialize_source_catalog(output: Path, landscape_dir: Path = DEFAULT_LANDSCAPE_DIR) -> dict:
    """Rebuild a projection of the validated catalog; never merge third-party rows."""
    output = Path(output).expanduser().resolve()
    landscape_dir = Path(landscape_dir).expanduser().resolve()
    validated = _validated_rows(landscape_dir)  # Validate *before* opening DB.
    if not validated:
        raise CATSourceDBError("no validated discovery sources")
    if output.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise CATSourceDBError("CAT metadata output must be a SQLite filename")
    if output.is_dir():
        raise CATSourceDBError("database output is a directory")
    if output.is_symlink():
        raise CATSourceDBError("symbolic link output is not permitted")
    output.parent.mkdir(parents=True, exist_ok=True)
    existed = output.exists()
    if existed and not output.is_file():
        raise CATSourceDBError("database output is not a regular file")
    con = sqlite3.connect(output)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        appid = con.execute("PRAGMA application_id").fetchone()[0]
        version = con.execute("PRAGMA user_version").fetchone()[0]
        if existed and (appid != CAT_APP_ID or version != CAT_SCHEMA_VERSION):
            raise CATSourceDBError("refusing to modify an unknown/non-CAT SQLite database")
        if not existed and (appid != 0 or version != 0):
            raise CATSourceDBError("unexpected initial database identity")
        with con:
            if not existed:
                con.execute(f"PRAGMA application_id={CAT_APP_ID}")
                con.execute(f"PRAGMA user_version={CAT_SCHEMA_VERSION}")
            con.executescript("""
CREATE TABLE IF NOT EXISTS cat_source_candidate (
  candidate_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  provider TEXT NOT NULL,
  authoritative_url TEXT NOT NULL,
  spatial_scope TEXT NOT NULL,
  temporal_scope TEXT NOT NULL,
  resolution_or_granularity TEXT NOT NULL,
  access_class_hint TEXT NOT NULL,
  candidate_status TEXT NOT NULL CHECK (candidate_status = 'evidence_checked'),
  rights_review_status TEXT NOT NULL CHECK (rights_review_status = 'not_reviewed'),
  scientific_review_status TEXT NOT NULL CHECK (scientific_review_status = 'not_reviewed'),
  admission_status TEXT NOT NULL CHECK (admission_status = 'not_admitted'),
  discovery_scope TEXT NOT NULL CHECK (discovery_scope = 'non_admission_discovery_only'),
  note TEXT NOT NULL,
  canonical_shard TEXT NOT NULL,
  canonical_sha256 TEXT NOT NULL,
  review_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cat_source_category (
  candidate_id TEXT NOT NULL REFERENCES cat_source_candidate(candidate_id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  PRIMARY KEY (candidate_id, category)
);
CREATE TABLE IF NOT EXISTS cat_source_role (
  candidate_id TEXT NOT NULL REFERENCES cat_source_candidate(candidate_id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  PRIMARY KEY (candidate_id, role)
);
CREATE INDEX IF NOT EXISTS cat_source_provider_index ON cat_source_candidate(provider);
CREATE INDEX IF NOT EXISTS cat_source_category_index ON cat_source_category(category);
CREATE INDEX IF NOT EXISTS cat_source_role_index ON cat_source_role(role);
""")
            con.execute("DELETE FROM cat_source_candidate")
            for entry, filename, digest, reviewed_at in validated:
                con.execute("""INSERT INTO cat_source_candidate VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (entry["candidate_id"], entry["name"], entry["provider"],
                     entry["authoritative_url"], entry["spatial_scope"],
                     entry["temporal_scope"], entry["resolution_or_granularity"],
                     entry["access_class_hint"], entry["candidate_status"],
                     entry["rights_review_status"], entry["scientific_review_status"],
                     entry["admission_status"], NON_ADMISSION, entry["note"],
                     filename, digest, reviewed_at))
                for category in sorted(set(entry["categories"])):
                    con.execute("INSERT INTO cat_source_category VALUES (?,?)",
                                (entry["candidate_id"], category))
                for role in sorted(set(entry["potential_roles"])):
                    con.execute("INSERT INTO cat_source_role VALUES (?,?)",
                                (entry["candidate_id"], role))
        counts = {
            "source_candidates": con.execute("SELECT count(*) FROM cat_source_candidate").fetchone()[0],
            "category_assignments": con.execute("SELECT count(*) FROM cat_source_category").fetchone()[0],
            "role_assignments": con.execute("SELECT count(*) FROM cat_source_role").fetchone()[0],
        }
        if counts["source_candidates"] != len(validated):
            raise CATSourceDBError("database and canonical landscape row counts differ")
        if con.execute("PRAGMA foreign_key_check").fetchall():
            raise CATSourceDBError("foreign-key validation failed")
        if con.execute("SELECT count(*) FROM cat_source_candidate WHERE admission_status != 'not_admitted'").fetchone()[0]:
            raise CATSourceDBError("admission state violation")
        return {
            "profile": "opencatastrophe-cat-source-sqlite-projection-v1",
            "scope": NON_ADMISSION,
            "schema_version": CAT_SCHEMA_VERSION,
            "source_shards": len({r[1] for r in validated}),
            **counts,
            "provider_data_downloaded": False,
            "insured_portfolios_created": False,
            "model_source_admission": False,
        }
    finally:
        con.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True,
                        help="dedicated CAT metadata SQLite database, outside source control")
    parser.add_argument("--landscape", type=Path, default=DEFAULT_LANDSCAPE_DIR,
                        help="canonical landscape shard directory (defaults to this repository)")
    args = parser.parse_args(argv)
    try:
        result = materialize_source_catalog(args.out, args.landscape)
    except (CATSourceDBError, LandscapeContractError, sqlite3.DatabaseError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
