# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fake ZIPs only; does not assert original provider has been executed."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile,ZIP_DEFLATED

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.dwd_kyrill_2007_berlin_original_v0 import OriginalDWDGateError
from scripts.dwd_kyrill_2007_munich_original_v0 import (
    audit_station,compare_munich,STATIONS,CONTRACT)

HEADER='STATIONS_ID;MESS_DATUM;QN;FX_10;EXTRA\n'
WINDOW=['200701162350','200701170000','200701171200','200701180000',
        '200701181200','200701190000','200701200000','200701202350','200701210000']

def fake_zip(station='01262', *, rows=None, head=HEADER, extra=None):
    if rows is None:
        rows=[(station,stamp,'2' if i%2 else '1',str(10+i)) for i,stamp in enumerate(WINDOW)]
    out=BytesIO()
    with ZipFile(out,'w',compression=ZIP_DEFLATED) as z:
        z.writestr('produkt_extrema_wind_20000101_20091231_'+station+'.txt',
                   head+''.join(';'.join(item)+';RESEARCH\n' for item in rows))
        z.writestr('INFO.txt','Synthetic fixture, not original DWD data')
        for k,v in (extra or {}).items():z.writestr(k,v)
    return out.getvalue()

class MunichKyrillOriginalTests(unittest.TestCase):
    def test_station_exact_ids_and_two_archives(self):
        self.assertEqual(tuple(STATIONS),('01262','03379'))
        a,b=fake_zip(),fake_zip('03379')
        r=compare_munich(airport=a,city=b)
        self.assertEqual(r['contract'],CONTRACT)
        self.assertEqual([s['dwd_station_id'] for s in r['stations']],['01262','03379'])
        self.assertFalse(r['fitted_vulnerability'])
        self.assertIsNone(r['annual_AEP'])

    def test_four_day_window_counts_and_separated_quality(self):
        r=audit_station(fake_zip(),station_id='01262')
        daily=r['four_day_window_utc']
        self.assertEqual(len(daily),4)
        self.assertEqual([x['observed_10minute_records'] for x in daily],[2,2,1,2])
        self.assertEqual(daily[1]['max_3second_gust_mps_all_quality'],'14')
        self.assertEqual(daily[1]['max_3second_gust_mps_qn2_or_qn3'],'13')
        self.assertFalse(r['measuring_height_and_location_in_2007_source_metadata_verified'])

    def test_digest_changed_source_rejected(self):
        x=fake_zip()
        self.assertEqual(audit_station(x,station_id='01262',expected_sha256=sha256(x).hexdigest())['original_archive_sha256'],sha256(x).hexdigest())
        with self.assertRaisesRegex(OriginalDWDGateError,'SHA256'):
            audit_station(x,station_id='01262',expected_sha256='0'*64)

    def test_provider_archive_wrong_station_rejected(self):
        with self.assertRaisesRegex(OriginalDWDGateError,'station'):
            audit_station(fake_zip('03379'),station_id='01262')

    def test_station_names_cannot_be_invented(self):
        with self.assertRaisesRegex(OriginalDWDGateError,'station ID'):
            audit_station(fake_zip(),station_id='03376x')

    def test_input_type_and_nonzip_rejected(self):
        for input_data in (b'',b'bad'*50,None,{},'zip'):
            with self.subTest(item=str(type(input_data))),self.assertRaises(OriginalDWDGateError):
                audit_station(input_data,station_id='01262')

    def test_duplicate_and_reordered_clock_blocked(self):
        rows=[('01262',t,'2','10') for t in WINDOW]
        for invalid in (rows[:4]+[rows[3]]+rows[4:],rows[:3]+[rows[4],rows[3]]+rows[5:]):
            with self.assertRaisesRegex(OriginalDWDGateError,'nonmonotone'):
                audit_station(fake_zip(rows=invalid),station_id='01262')

    def test_missing_sentinel_does_not_become_zero(self):
        rows=[('01262',t,'2','-999' if t=='200701181200' else '10') for t in WINDOW]
        r=audit_station(fake_zip(rows=rows),station_id='01262')
        d=r['four_day_window_utc'][1]
        self.assertEqual(d['missing_value_records'],1)
        self.assertEqual(d['valid_gust_records'],1)

    def test_invalid_qn_never_silently_promoted(self):
        rows=[('01262',t,'0' if i==4 else '1','10') for i,t in enumerate(WINDOW)]
        with self.assertRaisesRegex(OriginalDWDGateError,'quality'):
            audit_station(fake_zip(rows=rows),station_id='01262')

    def test_timestamps_must_bracket_storm(self):
        rows=[('01262',t,'1','10') for t in WINDOW[:3]]
        with self.assertRaisesRegex(OriginalDWDGateError,'bracket'):
            audit_station(fake_zip(rows=rows),station_id='01262')

    def test_1999_prelude_is_not_used_for_kyrill(self):
        rows=[('01262','199912312300','1','70'),
              *[('01262',t,'1','10') for t in WINDOW]]
        r=audit_station(fake_zip(rows=rows),station_id='01262')
        self.assertEqual(r['pre_2000_local_clock_prelude_excluded'],1)
        self.assertFalse(r['first_source_clock_is_utc'])
        self.assertEqual(r['four_day_window_utc'][1]['max_3second_gust_mps_all_quality'],'10')

    def test_pair_archive_aliasing_blocked(self):
        a=fake_zip()
        with self.assertRaises(OriginalDWDGateError):
            compare_munich(airport=a,city=a)

    def test_discard_original_measurement_rows(self):
        r=compare_munich(airport=fake_zip(),city=fake_zip('03379'))
        content=json.dumps(r,sort_keys=True)
        self.assertNotIn('200701181200',content)
        self.assertNotIn('RESEARCH;\n',content)
        self.assertFalse(r['same_historical_storm_attribution_proven'])
        self.assertFalse(r['same_measurement_height_verified'])

    def test_malformed_product_and_duplicate_member_rejected(self):
        with self.assertRaises(OriginalDWDGateError):
            audit_station(fake_zip(head='STATIONS_ID;MESS_DATUM;QN\n'),station_id='01262')
        with self.assertRaisesRegex(OriginalDWDGateError,'exactly one'):
            audit_station(fake_zip(extra={'second.txt':HEADER+'01262;200701181200;2;5;R\n'}),station_id='01262')

    def test_no_annual_loss_from_valid_real_station_shape(self):
        r=compare_munich(airport=fake_zip(),city=fake_zip('03379'))
        for key in ('annual_AAL','annual_AEP','annual_OEP','annual_event_rate'):
            self.assertIsNone(r[key])
        self.assertFalse(r['all_original_sources_independently_prior_pinned'])
        self.assertFalse(r['both_2007_instrument_histories_verified'])

if __name__=='__main__':unittest.main()
