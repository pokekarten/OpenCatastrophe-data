# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic regression of the read-only insurer-directory SQL audit."""
from pathlib import Path
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / 'research_runners/sql/insurer_directory_provenance_invariants_v0.sql').read_text(encoding='utf-8')

FIELDS = ('source_slug','country_slug','display_name','dataset_version',
          'provider_verification_claim','review_status','model_input_approved',
          'source_terms_url','license_spdx','source_dataset_url','raw_provider_sha256')


def clean_row(**changes):
    row = dict(zip(FIELDS, ('insurer-123','germany','Synthetic insurer',
        'synthetic-test-snapshot','verified',
        'secondary_source_pending_regulator_reconciliation',0,
        'https://example.test/terms','CC-BY-4.0',
        'https://example.test/original-index.json','a' * 64)))
    row.update(changes)
    return row


def checks(rows):
    with sqlite3.connect(':memory:') as db:
        db.execute("ATTACH DATABASE ':memory:' AS research")
        db.execute('CREATE TABLE research.insurer_directory_candidate_v0 (' +
                   ', '.join(f'{x} TEXT' if x != 'model_input_approved' else
                             'model_input_approved INTEGER' for x in FIELDS) + ')')
        placeholders = ','.join('?' for _ in FIELDS)
        db.executemany('INSERT INTO research.insurer_directory_candidate_v0 VALUES ('+
                       placeholders+')', [tuple(row.get(f) for f in FIELDS) for row in rows])
        return dict(db.execute(SQL).fetchall())


class InsurerDirectoryProvenanceTests(unittest.TestCase):
    def test_clean_synthetic_fixture_passes_all_checks(self):
        self.assertTrue(all(checks([clean_row()]).values()))

    def test_missing_and_placeholder_urls_are_blocked(self):
        for value in ('', 'undefined', 'null', None, 'http://example.test/a'):
            with self.subTest(value=value):
                result = checks([clean_row(source_dataset_url=value)])
                self.assertEqual(result['original_dataset_url_is_not_missing_or_placeholder'],
                                 int(value == 'http://example.test/a'))
                self.assertEqual(result['original_dataset_url_is_https'], 0)
                self.assertEqual(result['model_input_never_approved_from_secondary_directory'], 1)

    def test_missing_or_malformed_original_hash_is_blocked(self):
        for value in (None, '', 'b' * 63, 'G' * 64, 'A' * 64):
            with self.subTest(value=value):
                self.assertEqual(checks([clean_row(raw_provider_sha256=value)])
                                 ['original_bytes_have_sha256_evidence'], 0)

    def test_duplicate_source_slug_cannot_pass(self):
        self.assertEqual(checks([clean_row(),clean_row(display_name='Other synthetic')])
                         ['source_slugs_unique'], 0)

    def test_provider_verified_does_not_authorize_model_use(self):
        result = checks([clean_row(model_input_approved=1)])
        self.assertEqual(result['model_input_never_approved_from_secondary_directory'], 0)
        self.assertEqual(result['provider_claim_is_not_a_regulator_decision'], 1)

    def test_unreviewed_status_and_claims_fail_closed(self):
        for patch in ({'review_status':'regulator_verified'},
                      {'provider_verification_claim':'regulator_verified'},
                      {'model_input_approved':None}):
            result=checks([clean_row(**patch)])
            self.assertIn(0,result.values())

    def test_licence_and_terms_are_independent_of_data_access(self):
        result=checks([clean_row(source_terms_url='http://example.test/terms',
                                  license_spdx='')])
        self.assertEqual(result['terms_url_is_https'],0)
        self.assertEqual(result['declared_license_is_reviewable'],0)
        self.assertEqual(result['original_dataset_url_is_https'],1)

    def test_empty_staging_cannot_pass_vacuously(self):
        self.assertEqual(checks([])['staging_nonempty'],0)


if __name__ == '__main__':
    unittest.main()
