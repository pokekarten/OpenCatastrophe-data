# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import gzip
import json
import unittest
import urllib.request
from research_runners.meteofrance_hourly_gust_v0 import Blocked, _StrictSourceRedirect, audit_gzip, resolve_resource, verify_dictionary


HEADER = 'NUM_POSTE;AAAAMMJJHH;FF;FXI;FXI3S;QFXI3S;STATUS_FXI3S;LAT\n'
ROWS = '75101001;2020020914;12.0;20.0;21.5;1;0;48.7\n75101001;2020020915;11.0;19.0;20.0;1;1;48.7\n75101001;2020020916;10.0;17.0;;2;;48.7\n'


class TestOriginalGust(unittest.TestCase):
    def data(self, value=ROWS):
        return gzip.compress((HEADER + value).encode(), mtime=0)

    def test_three_second_quality_and_model_boundary(self):
        out = audit_gzip(self.data())
        self.assertEqual(out['rows'], 3)
        self.assertEqual(out['stations'], 1)
        self.assertEqual(out['quality_checked_three_second_gusts'], 2)
        self.assertEqual(out['status_calculated_three_second_gusts'], 1)
        self.assertEqual(out['status_not_calculated_three_second_gusts'], 1)
        self.assertFalse(out['annual_ep_authorized'])
        self.assertFalse(out['source_admitted'])
        self.assertNotIn('75101001', str(out))

    def test_source_sha_mismatch_blocks(self):
        with self.assertRaisesRegex(Blocked, 'SHA-256'):
            audit_gzip(self.data(), expected_sha256='0' * 64)

    def test_gzip_and_missing_fields_block(self):
        with self.assertRaises(Blocked):
            audit_gzip(b'not gzip' * 10)
        with self.assertRaisesRegex(Blocked, 'required'):
            audit_gzip(gzip.compress(b'NUM_POSTE;AAAAMMJJHH;FF\nabc;2020020100;7\n'))

    def test_reject_unknown_status_and_bad_hour(self):
        with self.assertRaises(Blocked):
            audit_gzip(self.data(ROWS.replace(';1;0;', ';1;3;')))
        with self.assertRaises(Blocked):
            audit_gzip(self.data(ROWS.replace('2020020914', '2019020914')))

    def test_real_utc_calendar_hours_including_leap_day(self):
        good = ROWS.replace('2020020914', '2020022914')
        self.assertEqual(audit_gzip(self.data(good))['rows'], 3)
        for invalid in ('2020023014', '2020130114', '2020020924', '2021022914'):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(Blocked, 'real-calendar UTC'):
                    audit_gzip(self.data(ROWS.replace('2020020914', invalid)))

    def test_redirect_is_checked_before_network_follow(self):
        request = urllib.request.Request('https://www.data.gouv.fr/api/1/datasets/example/')
        handler = _StrictSourceRedirect()
        for unsafe in (
            'http://example.net/insecure',
            'https://example.net/candidate',
            'https://www.data.gouv.fr/api/1/private?token=secret',
            'https://operator@www.data.gouv.fr/private',
        ):
            with self.subTest(unsafe=unsafe):
                with self.assertRaisesRegex(Blocked, 'source URL'):
                    handler.redirect_request(request, None, 302, 'Found', {}, unsafe)
        allowed = 'https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/safe.csv'
        result = handler.redirect_request(request, None, 302, 'Found', {}, allowed)
        self.assertEqual(result.full_url, allowed)

    def test_frozen_resource_identity(self):
        base = {'title': 'HOR_departement_75_periode_2020-2024',
                'url': 'https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_75_previous-2020-2024.csv.gz',
                'id': 'placeholder-public-resource', 'filesize': 2000000}
        resolved = resolve_resource(json.dumps({'resources': [base]}).encode())
        self.assertEqual(resolved['declared_bytes'], 2000000)
        with self.assertRaises(Blocked):
            resolve_resource(json.dumps({'resources': [base, base]}).encode())
        with self.assertRaises(Blocked):
            resolve_resource(json.dumps({'resources': [{**base, 'url': 'http://127.0.0.1/secret'}]}).encode())

    def test_dictionary_terms(self):
        d = ('FF: force du vent moyenné sur 10 mn\n'
             'FXI: force maximale du vent instantané\n'
             'FXI3S: force maximale du vent moyenné sur 3 secondes\n'
             'STATUS_FXI3S: code (0: non calculé, 1: calculé à partir d’une fonction de transfert)\n').encode()
        self.assertEqual(len(verify_dictionary(d)), 64)
        with self.assertRaises(Blocked):
            verify_dictionary(d.replace(b'3 secondes', b'10 secondes'))


if __name__ == '__main__':
    unittest.main()
