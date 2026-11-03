# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression tests for loss-multiplying joins and source drift."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from research_runners import noaa_storm_events_relational_audit_v0 as audit

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    detail = dict.fromkeys(audit.HEADERS['details'], '')
    detail.update(EVENT_ID='1', EPISODE_ID='10', DEATHS_DIRECT='2',
                  DEATHS_INDIRECT='0', DAMAGE_CROPS='0.00K',
                  EVENT_TYPE='Thunderstorm Wind', MAGNITUDE_TYPE='MG',
                  EVENT_NARRATIVE='Synthetic unpublishable narrative')
    return {
        'details': [detail],
        'fatalities': [dict(EVENT_ID='1', FATALITY_ID=str(i), FATALITY_TYPE='D',
                            FATALITY_AGE='Synthetic unpublishable attribute')
                       for i in (1, 2)],
        'locations': [dict(EVENT_ID='1', EPISODE_ID='10', LOCATION_INDEX=str(i))
                      for i in (1, 2, 3)],
    }


def blobs_for(tables):
    blobs = {}
    for kind, rows in tables.items():
        text = io.StringIO(newline='')
        writer = csv.DictWriter(text, fieldnames=audit.HEADERS[kind])
        writer.writeheader()
        writer.writerows(rows)
        blobs[kind] = gzip.compress(text.getvalue().encode(), mtime=0)
    return blobs


def digest(blobs):
    return {kind: hashlib.sha256(blob).hexdigest() for kind, blob in blobs.items()}


def run(tables):
    blobs = blobs_for(tables)
    return audit.audit_tables(blobs, digest(blobs))


class StormRelationalAuditTests(unittest.TestCase):
    def test_join_multiplication_and_unknown_damage_are_not_hidden(self):
        result = run(fixture())
        self.assertTrue(result['selected_checks_passed'])
        self.assertEqual(result['join_cardinality'], dict(
            parent_rows=1, naive_left_join_rows=6, duplicated_parents=1,
            max_parent_multiplicity=6))
        self.assertEqual(result['damage_field_status']['DAMAGE_PROPERTY']['missing'], 1)
        self.assertEqual(result['damage_field_status']['DAMAGE_CROPS']['reported_zero'], 1)
        self.assertEqual(result['thunderstorm_wind_magnitude_types'], {'MG': 1})
        self.assertFalse(result['source_admission_granted'])
        self.assertFalse(result['scientific_fitness_established'])
        self.assertNotIn('unpublishable', json.dumps(result))

    def test_compensating_death_mismatches_cannot_pass_on_global_totals(self):
        tables = fixture()
        first = tables['details'][0]
        first['DEATHS_DIRECT'] = '1'
        tables['details'].append(dict(first, EVENT_ID='2'))
        result = run(tables)
        summary = result['fatality_reconciliation']['D']
        self.assertEqual(summary['reported_in_details'], summary['matched_child_rows'])
        self.assertEqual(summary['mismatched_events'], 2)
        self.assertFalse(result['selected_checks_passed'])

    def test_duplicate_parent_and_child_keys_are_rejected(self):
        for kind in audit.HEADERS:
            with self.subTest(kind=kind):
                tables = fixture()
                tables[kind].append(dict(tables[kind][0]))
                with self.assertRaises(audit.StormAuditError):
                    run(tables)

    def test_orphan_children_do_not_disappear_from_reconciliation(self):
        for kind, diagnostic in [('fatalities', 'fatality_orphan_rows'),
                                 ('locations', 'location_orphan_rows')]:
            tables = fixture()
            tables[kind][0]['EVENT_ID'] = '99'
            result = run(tables)
            self.assertEqual(result['problems'][diagnostic], 1)
            self.assertEqual(result['status'], 'inconsistent')

    def test_location_episode_identity_must_match(self):
        tables = fixture()
        tables['locations'][0]['EPISODE_ID'] = '99'
        result = run(tables)
        self.assertEqual(result['problems']['location_episode_mismatch_rows'], 1)
        self.assertFalse(result['selected_checks_passed'])

    def test_compressed_hash_is_independently_supplied_and_checked(self):
        blobs = blobs_for(fixture())
        for bad in ['0' * 64, 'not-a-sha', 'A' * 64]:
            hashes = dict(digest(blobs), details=bad)
            with self.assertRaises(audit.StormAuditError):
                audit.audit_tables(blobs, hashes)

    def test_gzip_crc_and_decoded_resource_bound(self):
        blobs = blobs_for(fixture())
        bad = bytearray(blobs['details'])
        bad[-8] ^= 1
        blobs['details'] = bytes(bad)
        with self.assertRaises(audit.StormAuditError):
            audit.audit_tables(blobs, digest(blobs))
        with patch.object(audit, 'MAX_DECODED', 10):
            with self.assertRaises(audit.StormAuditError):
                run(fixture())

    def test_schema_drift_and_short_rows_rejected(self):
        for text in ['EVENT_ID\n1\n', ','.join(audit.HEADERS['details']) + '\n1,10\n']:
            blobs = blobs_for(fixture())
            blobs['details'] = gzip.compress(text.encode())
            with self.assertRaises(audit.StormAuditError):
                audit.audit_tables(blobs, digest(blobs))

    def test_empty_event_set_does_not_pass_vacuously(self):
        tables = fixture()
        tables['details'] = []
        with self.assertRaises(audit.StormAuditError):
            run(tables)

    def test_unknown_type_negative_or_fractional_counts_rejected(self):
        for kind, field, value in [('fatalities', 'FATALITY_TYPE', 'unknown'),
                                   ('details', 'MAGNITUDE_TYPE', 'unknown'),
                                   ('details', 'DEATHS_DIRECT', '-1'),
                                   ('details', 'DEATHS_DIRECT', '1.5'),
                                   ('details', 'DEATHS_DIRECT', '1' * 5000)]:
            tables = fixture()
            tables[kind][0][field] = value
            with self.assertRaises(audit.StormAuditError):
                run(tables)

    def test_damage_encodings_and_invalid_quantities(self):
        for raw in ['0', '0.00K', '0M']:
            self.assertEqual(audit.damage_status(raw), 'reported_zero')
        for raw in ['1', '1.25K', '2M', '1B']:
            self.assertEqual(audit.damage_status(raw), 'reported_positive')
        for raw in ['NaN', '-1K', '1e3', 'unknown']:
            with self.assertRaises(audit.StormAuditError):
                audit.damage_status(raw)

    def test_cli_exit_one_emits_diagnostics_not_false_success(self):
        tables = fixture()
        tables['details'][0]['DEATHS_DIRECT'] = '3'
        blobs = blobs_for(tables)
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(ROOT / 'research_runners' /
                       'noaa_storm_events_relational_audit_v0.py')]
            for kind, blob in blobs.items():
                path = Path(directory) / (kind + '.gz')
                path.write_bytes(blob)
                command += ['--' + kind, str(path), '--' + kind + '-sha256',
                            digest(blobs)[kind]]
            result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'inconsistent')


if __name__ == '__main__':
    unittest.main()
