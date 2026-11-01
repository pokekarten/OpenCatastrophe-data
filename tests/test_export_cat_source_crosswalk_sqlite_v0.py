# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Isolated CAT3 SQLite is a derived queryable source research view, never model input."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.build_cat_source_crosswalk_v0 import build_crosswalk
from scripts.build_source_access_inventory import build_inventory
from scripts.source_landscape_contract import load_landscape_shards
from scripts.source_linkage_audit_v0 import build_audit
from scripts.export_cat_source_crosswalk_sqlite_v0 import (
    CAT3_APP_ID, CAT3_VERSION, CAT3Error, export_crosswalk_sqlite,
)


def synthetic_report():
    source_rows = []
    access_rows = []
    for name in ("synthetic.a", "synthetic.b"):
        source_rows.append({
            "candidate_id": name, "landscape_shard": "sources-test.json",
            "provider": "Synthetic", "authoritative_url": "https://example.org/catalog",
            "spatial_scope": "no real geography", "temporal_scope": "synthetic only",
            "categories": ["building", "risk"], "potential_roles": ["test"],
            "admission_status": "not_admitted",
            "automated_model_import_allowed_by_this_audit": False,
        })
        access_rows.append({
            "source_id": name, "record_type": "landscape_candidate",
            "provider": "Synthetic", "authoritative_url": "https://example.org/catalog",
            "source_registry_path": "landscape/sources-test.json",
            "contract_ids": ["synthetic.fixed"] if name == "synthetic.a" else [],
            "contract_statuses": ["documented_only"] if name == "synthetic.a" else [],
            "operational_readiness": "contract_documentation_only" if name == "synthetic.a" else "no_concrete_access_contract",
            "rights_posture": "license_review_required",
            "automation_decision": "document_only",
            "license_or_terms_flags": ["synthetic_no_authority"],
            "next_action": "Review independently",
        })
    accesses = {
        "entry_count": 3, "landscape_entry_count": 2, "manifest_entry_count": 1,
        "entries": access_rows + [{
            "source_id": "synthetic.a", "record_type": "admitted_manifest",
            "source_registry_path": "manifests/synthetic.a.json",
            "contract_ids": [], "operational_readiness": "unknown",
            "next_action": "Review old separate manifest",
        }],
    }
    audits = {
        "source_count": 2, "source_inventory": source_rows,
        "this_report_is_a_model_input_allowlist": False,
        "linkage_recipe_count": 1,
        "linkage_hypotheses": [{
            "recipe_id": "synthetic-review", "source_candidate_ids": ["synthetic.a", "synthetic.b"],
            "relationship": "unknown_shared_lineage",
            "required_join_evidence": "compare original hashes",
            "unverified_prerequisites": "no original bytes",
            "prohibited_inferences": "no model input",
            "validation_only": True, "automatic_source_join_allowed": False,
            "scientific_independence_proven": False, "model_input_admitted": False,
        }],
    }
    return build_crosswalk(accesses, audits)


class CAT3ExportTests(unittest.TestCase):
    def test_sqlite_schema_references_and_non_admission(self):
        report = synthetic_report()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "cat3-research.cat.sqlite"
            receipt = export_crosswalk_sqlite(target, report)
            self.assertEqual(receipt["profile"], "opencatastrophe-cat3-derived-source-research-v0")
            self.assertEqual(receipt["candidates"], 2)
            self.assertEqual(receipt["manifests"], 1)
            self.assertEqual(receipt["recipes"], 1)
            self.assertEqual(receipt["uncontracted"], 1)
            self.assertEqual(receipt["recipe_endpoints"], 2)
            self.assertEqual(receipt["role_assignments"], 2)
            self.assertEqual(receipt["rights_flags"], 2)
            self.assertEqual(receipt["reviewed_contract_status_assignments"], 1)
            self.assertFalse(receipt["provider_bytes_persisted"])
            self.assertFalse(receipt["scientific_source_joins_executed"])
            self.assertFalse(receipt["model_inputs_admitted"])
            with sqlite3.connect(target) as con:
                self.assertEqual(con.execute("PRAGMA application_id").fetchone()[0], CAT3_APP_ID)
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], CAT3_VERSION)
                self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(con.execute("SELECT count(*) FROM candidate").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT count(*) FROM candidate_category").fetchone()[0], 4)
                self.assertEqual(con.execute("SELECT count(*) FROM source_access_assignment").fetchone()[0], 1)
                self.assertEqual(con.execute("SELECT contract_status FROM candidate_access_status").fetchone()[0], "documented_only")
                self.assertEqual(con.execute("SELECT count(*) FROM candidate_rights_flag").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT count(*) FROM candidate_role").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT count(*) FROM candidate_rights_review_queue").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT category, uncontracted_candidates FROM uncontracted_by_category ORDER BY category").fetchall(), [("building", 1), ("risk", 1)])
                self.assertEqual(con.execute("SELECT count(*) FROM shared_provider_page").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT count(*) FROM recipe_endpoint").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT count(*) FROM uncontracted_candidates").fetchone()[0], 1)
                self.assertEqual(con.execute("SELECT count(*) FROM candidate WHERE model_admitted<>0 OR join_proven<>0").fetchone()[0], 0)
                self.assertEqual(con.execute("SELECT count(*) FROM source_link_recipe WHERE auto_join_allowed<>0").fetchone()[0], 0)
                self.assertEqual(con.execute("SELECT count(*) FROM existing_manifest_separate WHERE new_authority_granted<>0").fetchone()[0], 0)

    def test_no_overwrite_and_no_mutation_of_other_cat_db(self):
        report = synthetic_report()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cat3.cat.sqlite"
            with sqlite3.connect(path) as con:
                con.execute("PRAGMA application_id=1128354865")  # CAT1
                con.execute("CREATE TABLE guard(original TEXT)")
                con.execute("INSERT INTO guard VALUES ('untouched')")
            with self.assertRaisesRegex(CAT3Error, "overwrite"):
                export_crosswalk_sqlite(path, report)
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA application_id").fetchone()[0], 1128354865)
                self.assertEqual(con.execute("SELECT original FROM guard").fetchone()[0], "untouched")

    def test_requires_new_absolute_outside_repo_destination(self):
        report = synthetic_report()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(CAT3Error, "explicit absolute"):
                export_crosswalk_sqlite(Path("cat.cat.sqlite"), report)
            with self.assertRaisesRegex(CAT3Error, "explicit absolute"):
                export_crosswalk_sqlite(Path(td) / "cat.db", report)
            target = Path(td) / "existing.cat.sqlite"
            target.symlink_to(Path(td) / "missing")
            with self.assertRaisesRegex(CAT3Error, "overwrite"):
                export_crosswalk_sqlite(target, report)

    def test_fail_closed_on_report_mutation_before_file_creation(self):
        for field in ("external_provider_data_downloaded", "new_rights_or_admission_granted"):
            report = synthetic_report()
            report[field] = True
            with tempfile.TemporaryDirectory() as td:
                target = Path(td) / "bad.cat.sqlite"
                with self.assertRaisesRegex(CAT3Error, "authority boundary"):
                    export_crosswalk_sqlite(target, report)
                self.assertFalse(target.exists())

        report = synthetic_report()
        report["candidates"][0]["candidate_join_hypotheses"][0]["automatic_join_allowed"] = True
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "bad.cat.sqlite"
            with self.assertRaisesRegex(CAT3Error, "scientific linkage promoted"):
                export_crosswalk_sqlite(target, report)
            self.assertFalse(target.exists())

    def test_missing_rights_or_ambiguous_contract_status_fails_before_write(self):
        for field, bad in (
            ("license_or_terms_flags", None),
            ("license_or_terms_flags", ["ok", "ok"]),
            ("potential_roles", ["test", "test"]),
            ("access_contract_statuses", ["probe_ready", "probe_ready"]),
        ):
            with self.subTest(field=field, bad=bad):
                report = synthetic_report()
                report["candidates"][0][field] = bad
                with tempfile.TemporaryDirectory() as td:
                    target = Path(td) / "invalid.cat.sqlite"
                    with self.assertRaisesRegex(CAT3Error, "missing or invalid"):
                        export_crosswalk_sqlite(target, report)
                    self.assertFalse(target.exists())

        report = synthetic_report()
        report["candidates"][1]["access_contract_statuses"] = ["probe_ready"]
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "orphan.cat.sqlite"
            with self.assertRaisesRegex(CAT3Error, "orphan access-contract status"):
                export_crosswalk_sqlite(target, report)
            self.assertFalse(target.exists())

    def test_licence_flags_are_not_inferred_as_approved(self):
        report = synthetic_report()
        report["candidates"][0]["rights_posture"] = "source_rights_verified"
        report["candidates"][0]["license_or_terms_flags"] = ["redistribution_restricted"]
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "terms.cat.sqlite"
            export_crosswalk_sqlite(db, report)
            with sqlite3.connect(db) as con:
                queue = con.execute("SELECT candidate_id FROM candidate_rights_review_queue ORDER BY candidate_id").fetchall()
                self.assertEqual(queue, [("synthetic.a",), ("synthetic.b",)])
                self.assertEqual(con.execute("SELECT terms_flag FROM candidate_rights_flag WHERE candidate_id='synthetic.a'").fetchone()[0], "redistribution_restricted")
                self.assertEqual(con.execute("SELECT sum(model_admitted) FROM candidate").fetchone()[0], 0)

    def test_missing_reciprocal_endpoint_is_never_accepted(self):
        report = synthetic_report()
        report["candidates"][1]["candidate_join_hypotheses"] = []
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "missing-edge.cat.sqlite"
            with self.assertRaisesRegex(CAT3Error, "missing reciprocal"):
                export_crosswalk_sqlite(target, report)
            self.assertFalse(target.exists())

    def test_inconsistent_recipe_endpoint_sets_fail_closed(self):
        report = synthetic_report()
        report["candidates"][1]["candidate_join_hypotheses"][0]["other_source_ids"] = ["synthetic.c"]
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mismatch.cat.sqlite"
            with self.assertRaisesRegex(CAT3Error, "inconsistent endpoint"):
                export_crosswalk_sqlite(target, report)
            self.assertFalse(target.exists())

    def test_real_discovery_registry_is_queryable_without_provider_data(self):
        report = build_crosswalk(build_inventory(), build_audit(load_landscape_shards()))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "full.cat.sqlite"
            result = export_crosswalk_sqlite(path, report)
            self.assertGreaterEqual(result["candidates"], 263)
            self.assertEqual(result["candidates"], report["candidate_count"])
            self.assertEqual(result["manifests"], report["manifest_count"])
            self.assertEqual(result["recipes"], report["manual_linkage_recipe_count"])
            self.assertEqual(result["uncontracted"], report["candidate_without_access_contract_count"])
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(con.execute("SELECT count(*) FROM candidate WHERE join_proven=1 OR model_admitted=1").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
