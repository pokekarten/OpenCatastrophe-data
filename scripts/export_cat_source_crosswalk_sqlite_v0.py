#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Materialize the derived CAT source access/linkage research report in isolated SQLite.

NOT a source of truth, NOT original provider data, NOT a model-input allowlist.
Existing landscape, access and manifest JSON and the linkage audit stay canonical.
This deliberately uses CAT4, distinct from CAT1 geographic, CAT2 spatial
crosswalk and separately merged CAT3 provisional DEU NUTS2021 SQLite files. It never overwrites an existing database.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

if __package__:
    from .build_cat_source_crosswalk_v0 import build_crosswalk, CrosswalkError
    from .build_source_access_inventory import build_inventory
    from .source_landscape_contract import load_landscape_shards
    from .source_linkage_audit_v0 import build_audit
else:
    from build_cat_source_crosswalk_v0 import build_crosswalk, CrosswalkError
    from build_source_access_inventory import build_inventory
    from source_landscape_contract import load_landscape_shards
    from source_linkage_audit_v0 import build_audit


CAT4_APP_ID = 0x43415434
CAT4_VERSION = 1
PROFILE = "opencatastrophe-cat4-derived-source-research-v0"


class CAT4Error(ValueError):
    """Unsafe destination or inconsistent source/access/linkage research state."""


def _validate_report(report: dict) -> None:
    if report.get("profile") != "opencatastrophe-source-access-linkage-research-v0":
        raise CAT4Error("unexpected source research report profile")
    for flag in ("external_provider_data_downloaded", "permission_for_automated_source_join",
                 "new_rights_or_admission_granted", "this_report_is_a_model_input_allowlist"):
        if report.get(flag) is not False:
            raise CAT4Error("research authority boundary violated")
    candidates = report.get("candidates")
    manifests = report.get("existing_manifests_separate")
    if not isinstance(candidates, list) or not isinstance(manifests, list):
        raise CAT4Error("missing research rows")
    if len(candidates) != report.get("candidate_count") or len(manifests) != report.get("manifest_count"):
        raise CAT4Error("source counts do not match rows")
    seen, recipes = set(), {}
    recipe_members: dict[str, set[str]] = defaultdict(set)
    expected_recipe_members: dict[str, set[str]] = {}
    for row in candidates:
        ident = row.get("source_id")
        if not isinstance(ident, str) or not ident or ident in seen:
            raise CAT4Error("invalid or duplicate candidate identity")
        seen.add(ident)
        for flag in ("access_proven_by_this_report", "source_bytes_verified_by_this_report",
                     "scientific_join_verified_by_this_report", "model_input_admitted_by_this_report",
                     "scientific_independence_proven", "same_page_proves_identical_source_bytes"):
            if row.get(flag) is not False:
                raise CAT4Error("candidate research authority boundary violated")
        if row.get("no_reviewed_access_contract") is not (not bool(row.get("access_contract_ids"))):
            raise CAT4Error("candidate reviewed-contract count inconsistent")
        # These fields must come from the reviewed source-access inventory;
        # missing or malformed metadata must not silently erase licence flags.
        for field in ("categories", "potential_roles", "access_contract_ids",
                      "access_contract_statuses", "license_or_terms_flags"):
            values = row.get(field)
            if (type(values) is not list
                    or any(type(value) is not str or not value.strip() for value in values)
                    or len(values) != len(set(values))):
                raise CAT4Error(f"missing or invalid CAT4 reviewed field: {field}")
        if not row["access_contract_ids"] and row["access_contract_statuses"]:
            raise CAT4Error("orphan access-contract status with no contract")
        for field in ("operational_readiness", "rights_posture", "automation_decision",
                      "access_next_action"):
            value = row.get(field)
            if value is not None and (type(value) is not str or not value.strip()):
                raise CAT4Error(f"invalid CAT4 source evidence: {field}")
        for link in row.get("candidate_join_hypotheses", []):
            rid = link.get("recipe_id")
            if not isinstance(rid, str) or not rid:
                raise CAT4Error("missing linkage recipe ID")
            if link.get("automatic_join_allowed") is not False or link.get("scientific_independence_proven") is not False:
                raise CAT4Error("unreviewed scientific linkage promoted")
            fingerprint = (
                link.get("relationship"), link.get("required_join_evidence"),
                link.get("unverified_prerequisites"), link.get("prohibited_inferences"),
            )
            if rid in recipes and recipes[rid] != fingerprint:
                raise CAT4Error("conflicting same-ID linkage recipe")
            if ident in recipe_members[rid]:
                raise CAT4Error("duplicate source/linkage recipe edge")
            recipe_members[rid].add(ident)
            endpoints = link.get("other_source_ids")
            if not isinstance(endpoints, list) or not endpoints:
                raise CAT4Error("linkage recipe has no other endpoints")
            endpoint_set = {ident, *endpoints}
            if rid in expected_recipe_members and expected_recipe_members[rid] != endpoint_set:
                raise CAT4Error("linkage recipe has inconsistent endpoint identities")
            expected_recipe_members[rid] = endpoint_set
            recipes[rid] = fingerprint
    for row in candidates:
        ident = row["source_id"]
        for link in row.get("candidate_join_hypotheses", []):
            other = link.get("other_source_ids")
            if (not isinstance(other, list) or not other
                    or any(not isinstance(x, str) or x not in seen or x == ident for x in other)
                    or len(other) != len(set(other))):
                raise CAT4Error("dangling or self-joined linkage endpoint")
    if len(recipes) != report.get("manual_linkage_recipe_count"):
        raise CAT4Error("linkage recipe count differs from source report")
    for rid, expected in expected_recipe_members.items():
        if recipe_members[rid] != expected:
            raise CAT4Error("linkage recipe missing reciprocal source endpoint")
    if len({r.get("dataset_id") for r in manifests}) != len(manifests):
        raise CAT4Error("duplicate manifest identity")
    for row in manifests:
        if (row.get("source_bytes_verified_by_this_report") is not False
                or row.get("scientific_join_verified_by_this_report") is not False
                or row.get("any_additional_model_authority_granted") is not False):
            raise CAT4Error("manifest trust boundary violated")


def _destination(output: Path) -> Path:
    output = Path(output).expanduser()
    if not output.is_absolute() or not str(output).endswith(".cat.sqlite"):
        raise CAT4Error("explicit absolute new .cat.sqlite output is required")
    root = Path(__file__).resolve().parents[1]
    parent = output.parent.resolve(strict=True)
    if parent == root or root in parent.parents:
        raise CAT4Error("do not write generated data inside Git checkout")
    if output.exists() or output.is_symlink():
        raise CAT4Error("refusing to overwrite an existing file or symlink")
    return parent / output.name


def export_crosswalk_sqlite(output: Path, report: dict) -> dict:
    """Write an exclusive, isolated derived research DB; never persist provider bytes."""
    _validate_report(report)
    target = _destination(output)
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with closing(sqlite3.connect(target)) as con, con:
            con.execute("PRAGMA foreign_keys=ON")
            con.execute(f"PRAGMA application_id={CAT4_APP_ID}")
            con.execute(f"PRAGMA user_version={CAT4_VERSION}")
            con.executescript("""
CREATE TABLE candidate (
  candidate_id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  authoritative_url TEXT NOT NULL,
  canonical_shard TEXT NOT NULL,
  spatial_scope TEXT NOT NULL,
  temporal_scope TEXT NOT NULL,
  readiness TEXT,
  rights_posture TEXT,
  automation_decision TEXT,
  access_next_action TEXT,
  has_concrete_access_contract INTEGER NOT NULL CHECK(has_concrete_access_contract IN(0,1)),
  join_proven INTEGER NOT NULL DEFAULT 0 CHECK(join_proven=0),
  model_admitted INTEGER NOT NULL DEFAULT 0 CHECK(model_admitted=0)
);
CREATE TABLE candidate_category (
  candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
  category TEXT NOT NULL,
  PRIMARY KEY(candidate_id,category)
);
CREATE TABLE source_access_assignment (
  candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
  access_id TEXT NOT NULL,
  PRIMARY KEY(candidate_id,access_id)
);
CREATE TABLE candidate_access_status (
  candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
  contract_status TEXT NOT NULL,
  PRIMARY KEY(candidate_id,contract_status)
);
CREATE TABLE candidate_rights_flag (
  candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
  terms_flag TEXT NOT NULL,
  PRIMARY KEY(candidate_id,terms_flag)
);
CREATE TABLE candidate_role (
  candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
  potential_role TEXT NOT NULL,
  PRIMARY KEY(candidate_id,potential_role)
);
CREATE TABLE source_link_recipe (
  recipe_id TEXT PRIMARY KEY,
  relationship TEXT NOT NULL,
  required_join_evidence TEXT NOT NULL,
  unverified_prerequisites TEXT NOT NULL,
  prohibited_inferences TEXT NOT NULL,
  auto_join_allowed INTEGER NOT NULL DEFAULT 0 CHECK(auto_join_allowed=0)
);
CREATE TABLE recipe_endpoint (
  recipe_id TEXT NOT NULL REFERENCES source_link_recipe(recipe_id),
  candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
  PRIMARY KEY(recipe_id,candidate_id)
);
CREATE TABLE shared_provider_page (
  authoritative_url TEXT NOT NULL,
  candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
  identical_bytes_proven INTEGER NOT NULL DEFAULT 0 CHECK(identical_bytes_proven=0),
  PRIMARY KEY(authoritative_url,candidate_id)
);
CREATE TABLE existing_manifest_separate (
  dataset_id TEXT PRIMARY KEY,
  canonical_manifest_path TEXT NOT NULL,
  readiness TEXT,
  new_authority_granted INTEGER NOT NULL DEFAULT 0 CHECK(new_authority_granted=0)
);
CREATE VIEW uncontracted_candidates AS
  SELECT candidate_id, provider, canonical_shard, readiness, rights_posture
    FROM candidate WHERE has_concrete_access_contract=0;
-- Category totals are NOT disjoint: one candidate can occupy multiple layers.
CREATE VIEW uncontracted_by_category AS
  SELECT cc.category, count(*) AS uncontracted_candidates
    FROM candidate_category cc JOIN candidate c USING(candidate_id)
    WHERE c.has_concrete_access_contract=0
    GROUP BY cc.category;
-- Explicitly review every source with any recorded rights concern. This
-- does not infer permission if the source is not listed here.
CREATE VIEW candidate_rights_review_queue AS
  SELECT DISTINCT c.candidate_id, c.provider, c.rights_posture, c.automation_decision
    FROM candidate c LEFT JOIN candidate_rights_flag f USING(candidate_id)
    WHERE c.rights_posture IS NULL
       OR c.rights_posture <> 'source_rights_verified'
       OR f.terms_flag IS NOT NULL;
CREATE INDEX idx_candidate_readiness ON candidate(readiness);
CREATE INDEX idx_category ON candidate_category(category);
CREATE INDEX idx_endpoint_candidate ON recipe_endpoint(candidate_id);
""")
            with con:
                by_id = {r["source_id"]: r for r in report["candidates"]}
                all_recipes = {}
                for ident, r in sorted(by_id.items()):
                    con.execute("INSERT INTO candidate VALUES (?,?,?,?,?,?,?,?,?,?,?,0,0)", (
                        ident, r["provider"], r["authoritative_url"], r["canonical_source_path"],
                        r["spatial_scope"], r["temporal_scope"], r["operational_readiness"],
                        r["rights_posture"], r["automation_decision"], r["access_next_action"],
                        int(bool(r["access_contract_ids"])),
                    ))
                    for category in sorted(set(r["categories"])):
                        con.execute("INSERT INTO candidate_category VALUES (?,?)", (ident, category))
                    for access in sorted(r["access_contract_ids"]):
                        con.execute("INSERT INTO source_access_assignment VALUES (?,?)", (ident, access))
                    # Contract statuses are source-level aggregates, not a
                    # fabricated one-to-one mapping to specific interface IDs.
                    for status in sorted(r["access_contract_statuses"]):
                        con.execute("INSERT INTO candidate_access_status VALUES (?,?)", (ident, status))
                    for flag in sorted(r["license_or_terms_flags"]):
                        con.execute("INSERT INTO candidate_rights_flag VALUES (?,?)", (ident, flag))
                    for role in sorted(r["potential_roles"]):
                        con.execute("INSERT INTO candidate_role VALUES (?,?)", (ident, role))
                    for link in r["candidate_join_hypotheses"]:
                        rid = link["recipe_id"]
                        all_recipes[rid] = (
                            rid, link["relationship"], link["required_join_evidence"],
                            link["unverified_prerequisites"], link["prohibited_inferences"],
                        )
                for row in sorted(report["existing_manifests_separate"], key=lambda r: r["dataset_id"]):
                    con.execute("INSERT INTO existing_manifest_separate VALUES (?,?,?,0)", (
                        row["dataset_id"], row["canonical_manifest_path"], row["operational_readiness"],
                    ))
                for recipe in sorted(all_recipes.values()):
                    if any(not isinstance(v, str) or not v for v in recipe):
                        raise CAT4Error("missing scientific recipe proof fields")
                    con.execute("INSERT INTO source_link_recipe VALUES (?,?,?,?,?,0)", recipe)
                for ident, r in sorted(by_id.items()):
                    for link in r["candidate_join_hypotheses"]:
                        con.execute("INSERT OR IGNORE INTO recipe_endpoint VALUES (?,?)",
                                    (link["recipe_id"], ident))
                    for peer in r["same_authoritative_page_candidate_ids"]:
                        if peer not in by_id or by_id[peer]["authoritative_url"] != r["authoritative_url"]:
                            raise CAT4Error("invalid shared provider page peer")
                        con.execute("INSERT INTO shared_provider_page VALUES (?,?,0)",
                                    (r["authoritative_url"], ident))
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise CAT4Error("invalid crosswalk foreign keys")
            counts = {
                "candidates": con.execute("SELECT count(*) FROM candidate").fetchone()[0],
                "manifests": con.execute("SELECT count(*) FROM existing_manifest_separate").fetchone()[0],
                "recipes": con.execute("SELECT count(*) FROM source_link_recipe").fetchone()[0],
                "uncontracted": con.execute("SELECT count(*) FROM uncontracted_candidates").fetchone()[0],
                "recipe_endpoints": con.execute("SELECT count(*) FROM recipe_endpoint").fetchone()[0],
                "role_assignments": con.execute("SELECT count(*) FROM candidate_role").fetchone()[0],
                "rights_flags": con.execute("SELECT count(*) FROM candidate_rights_flag").fetchone()[0],
                "reviewed_contract_status_assignments": con.execute("SELECT count(*) FROM candidate_access_status").fetchone()[0],
            }
            if (counts["candidates"] != report["candidate_count"]
                    or counts["manifests"] != report["manifest_count"]
                    or counts["recipes"] != report["manual_linkage_recipe_count"]
                    or counts["uncontracted"] != report["candidate_without_access_contract_count"]):
                raise CAT4Error("CAT4 counts disagree with derived source register")
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CAT4Error("CAT4 SQLite integrity check failed")
        canon = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        return {
            "profile": PROFILE, "application_id": CAT4_APP_ID,
            "report_sha256": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
            **counts, "provider_bytes_persisted": False,
            "scientific_source_joins_executed": False,
            "model_inputs_admitted": False,
        }
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New absolute *.cat.sqlite path outside Git checkout.")
    args = parser.parse_args(argv)
    try:
        report = build_crosswalk(build_inventory(), build_audit(load_landscape_shards()))
        result = export_crosswalk_sqlite(args.out, report)
    except (CAT4Error, CrosswalkError, ValueError, OSError, sqlite3.Error) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
