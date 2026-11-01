# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_insurance_access_sync_v0 import compare, main


SHA_A = "a" * 40
SHA_B = "b" * 40


def git(path="access/example.source.json", sha=SHA_A):
    return {"type": "file", "path": path, "sha": sha}


def db(path="access/example.source.json", sha=SHA_A,
       classification="access_contract", source_key="access:example.source"):
    return {"git_path": path, "git_blob_sha": sha,
            "classification": classification, "source_key": source_key}


class AccessSyncTests(unittest.TestCase):
    def test_clean_exact_blob(self):
        r = compare([git()], [db()])
        self.assertEqual(r["github_access_contracts"], 1)
        self.assertEqual(r["exact_blob_matches"], 1)
        self.assertFalse(r["review_needed"])
        self.assertFalse(r["automatic_sync_authorized"])
        self.assertFalse(r["source_rights_or_model_admission_authorized"])

    def test_realistic_missing_drift_and_noncanonical_research(self):
        g = [git(), git("access/new.source.json", SHA_B)]
        n = [db(sha=SHA_B),
             db("docs/research/not-a-contract.md", classification="access_contract",
                source_key="historical:receipt")]
        r = compare(g, n)
        self.assertEqual(r["missing_in_neon"], ["access/new.source.json"])
        self.assertEqual(r["git_blob_drift"], ["access/example.source.json"])
        self.assertEqual(r["neon_canonical_access_contracts"], 1)
        self.assertEqual(r["exact_blob_matches"], 0)
        self.assertEqual(r["noncanonical_contract_classification"],
                         ["docs/research/not-a-contract.md"])
        self.assertTrue(r["review_needed"])

    def test_stale_neon_row_and_wrong_key(self):
        r = compare([git()], [db(source_key="other:key"),
                              db("access/removed.json", source_key="access:removed")])
        self.assertEqual(r["not_on_github"], ["access/removed.json"])
        self.assertEqual(r["wrong_type_or_key"], ["access/example.source.json"])

    def test_non_access_research_receipt_not_counted_as_contract(self):
        r = compare([git()], [db(),
                   db("research/market/receipt.json", classification="access_contract")])
        self.assertEqual(r["neon_canonical_access_contracts"], 1)
        self.assertFalse(r["review_needed"])
        self.assertEqual(r["noncanonical_contract_classification"],
                         ["research/market/receipt.json"])

    def test_wrong_classification_inside_access(self):
        r = compare([git()], [db(classification="landscape_candidate")])
        self.assertEqual(r["wrong_type_or_key"], ["access/example.source.json"])

    def test_fail_closed_on_duplicate_inventory_paths(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare([git(), git()], [db()])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare([git()], [db(), db()])

    def test_fail_closed_on_bad_shas_and_nonfile(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            compare([git(sha="invalid")], [db()])
        with self.assertRaisesRegex(ValueError, "invalid"):
            compare([git()], [db(sha="invalid")])
        with self.assertRaisesRegex(ValueError, "invalid"):
            compare([dict(git(), type="dir")], [db()])

    def test_reject_path_traversal_as_canonical(self):
        with self.assertRaisesRegex(ValueError, "no access"):
            compare([git("access/../escaped.json")], [db()])
        with self.assertRaisesRegex(ValueError, "no access"):
            compare([git("other/example.json")], [db()])

    def test_reject_empty_or_malformed_inventory(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            compare([], [db()])
        with self.assertRaisesRegex(ValueError, "expected a JSON array"):
            compare({"path": "access/x.json"}, [db()])

    def test_cli_return_codes_without_network_or_sql(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            g = root / "github.json"
            n = root / "neon.json"
            g.write_text(json.dumps([git()]), encoding="utf-8")
            n.write_text(json.dumps([db()]), encoding="utf-8")
            args = ["--github-inventory", str(g), "--neon-export", str(n)]
            self.assertEqual(main(args), 0)
            n.write_text(json.dumps([db(sha=SHA_B)]), encoding="utf-8")
            self.assertEqual(main(args), 2)
            n.write_text("{bad", encoding="utf-8")
            self.assertEqual(main(args), 1)


if __name__ == "__main__":
    unittest.main()
