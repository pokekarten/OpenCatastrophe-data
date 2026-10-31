# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline read-only company-identity reconciliation, no Neon credentials."""
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from scripts.gleif_neon_readonly_identity_audit_v0 import (
    IdentityAuditError, audit_readonly_neon_dedup,
)
from scripts.gleif_level1_insurer_identity_pilot import (
    PILOT_LEIS, ingest_verified_lei_pilot,
)
from tests.test_gleif_level1_insurer_identity_pilot import (
    build_db, payload,
)


LEIS = sorted(PILOT_LEIS)


def snapshot(leicoes=None, *, allowed=False, status="cc0_verified",
             schema="GLEIF_LEI", verified=True):
    if leicoes is None:
        leicoes = LEIS[:5]
    return json.dumps({
        "schema_version": "oc-gleif-neon-readonly-export-v0",
        "feed": {
            "feed_id": "gleif_global",
            "rights_status": status,
            "automated_import_allowed": allowed,
        },
        "identifiers": [
            {"identifier_scheme": schema, "identifier_value": lei,
             "is_verified": verified} for lei in leicoes
        ],
    }, sort_keys=True).encode("utf-8")


def staged_database(root):
    db = build_db(root)
    ingest_verified_lei_pilot(
        db, {lei:payload(lei, name="Synthetic LEI row "+str(i))
             for i,lei in enumerate(LEIS)}, "2026-10-31T21:00:00+00:00")
    return db


class GLEIFNeonReadonlyIdentityTests(unittest.TestCase):
    def test_five_existing_and_one_missing_explicit_review(self):
        with TemporaryDirectory() as d:
            db=staged_database(Path(d))
            before=db.read_bytes()
            report=audit_readonly_neon_dedup(db,snapshot())
            self.assertEqual(report["cat_lei_count"],6)
            self.assertEqual(report["already_verified_lei_count"],5)
            self.assertEqual(report["missing_lei_count"],1)
            self.assertEqual(report["missing_leis_pending_manual_review"],[LEIS[5]])
            self.assertEqual(set(report["source_sha256_by_lei"]),set(LEIS))
            for key in ("automatic_import_allowed","neon_updated",
                        "pokemon_database_accessed","new_organizations_created",
                        "parent_or_treaty_inferred","insured_exposure_created",
                        "model_source_admitted"):
                self.assertFalse(report[key])
            self.assertEqual(db.read_bytes(),before)

    def test_deterministic_idempotent_report(self):
        with TemporaryDirectory() as d:
            db=staged_database(Path(d))
            self.assertEqual(audit_readonly_neon_dedup(db,snapshot()),
                             audit_readonly_neon_dedup(db,snapshot()))

    def test_all_six_present_means_no_import_needed(self):
        with TemporaryDirectory() as d:
            result=audit_readonly_neon_dedup(staged_database(Path(d)),
                                            snapshot(LEIS))
            self.assertEqual(result["missing_leis_pending_manual_review"],[])
            self.assertFalse(result["neon_updated"])

    def test_empty_identifier_set_is_not_automatically_imported(self):
        with TemporaryDirectory() as d:
            report=audit_readonly_neon_dedup(staged_database(Path(d)),snapshot([]))
            self.assertEqual(report["missing_lei_count"],6)
            self.assertFalse(report["automatic_import_allowed"])

    def test_duplicate_existing_identifier_is_blocked(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(staged_database(Path(d)),
                                         snapshot([LEIS[0],LEIS[0]]))

    def test_unknown_source_lei_is_blocked(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(staged_database(Path(d)),
                                         snapshot(["0"*20]))

    def test_unverified_or_wrong_scheme_cannot_reconcile(self):
        with TemporaryDirectory() as d:
            db=staged_database(Path(d))
            for params in ({"schema":"LEI"},{"verified":False}):
                with self.subTest(params=params),self.assertRaises(IdentityAuditError):
                    audit_readonly_neon_dedup(db,snapshot(**params))

    def test_import_policy_enabled_is_rejected_not_autorun(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(staged_database(Path(d)),
                                         snapshot(allowed=True))

    def test_unreviewed_feed_is_rejected(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(staged_database(Path(d)),
                                         snapshot(status="not_reviewed"))

    def test_unexpected_snapshot_fields_are_rejected(self):
        with TemporaryDirectory() as d:
            obj=json.loads(snapshot())
            obj["company_owner_email"]="disallowed"
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(staged_database(Path(d)),
                                         json.dumps(obj).encode())

    def test_duplicate_json_object_key_is_rejected(self):
        with TemporaryDirectory() as d:
            text=snapshot().decode().replace('"feed":', '"feed":null,"feed":',1)
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(staged_database(Path(d)),text.encode())

    def test_reject_wrong_database_without_creating_tables(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            db=root/"pokemon.sqlite"
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE cards(name TEXT)")
                con.execute("INSERT INTO cards VALUES ('Pikachu')")
            before=db.read_bytes()
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(db,snapshot())
            self.assertEqual(db.read_bytes(),before)

    def test_sqlite_symlink_rejected(self):
        with TemporaryDirectory() as d:
            root=Path(d);db=staged_database(root)
            alias=root/"alias.sqlite"
            alias.symlink_to(db)
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(alias,snapshot())

    def test_missing_source_database_never_created(self):
        with TemporaryDirectory() as d:
            db=Path(d)/"nonexistent.sqlite"
            with self.assertRaises(IdentityAuditError):
                audit_readonly_neon_dedup(db,snapshot())
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
