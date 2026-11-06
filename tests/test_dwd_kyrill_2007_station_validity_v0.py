# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Artificial ZIP fixtures verify date intersection; no original data claim."""
import hashlib
import io
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.dwd_kyrill_2007_station_validity_v0 import (
 validate_station_metadata,DWDStationHistoryBlocked,_date,_on_window,CONTRACT,
 EXPECTED_2007,STATIONS,
)

def fake(station,*,geo=None,device=None,parameter=None):
 lat,lon,alt,height,model=EXPECTED_2007[station];sid=str(int(station))
 geo=geo if geo is not None else (
    f'Stations_id;Stationshoehe;Geogr.Breite;Geogr.Laenge;von_datum;bis_datum;Stationsname\n'
    f'{sid};{alt};{lat};{lon};20060101;20081231;TEST\n')
 device=device if device is not None else (
    f'Stations_ID;Stationsname;Geo. Laenge [Grad];Geo. Breite [Grad];Stationshoehe [m];Geberhoehe ueber Grund [m];Von_Datum;Bis_Datum;Geraetetyp Name;Messverfahren;eo\n'
    f'{sid};TEST;{lon};{lat};{alt};{height};20060101;20081231;{model};wind;eo;\n')
 parameter=parameter if parameter is not None else (
    'Stations_ID;Von_Datum;Bis_Datum;Stationsname;Parameter;Parameterbeschreibung;Einheit\n'
    f'{sid};20060101;20081231;TEST;FX_10;Maxwind;m/s\n')
 mem={f'Metadaten_Geographie_{station}.txt':geo,
      f'Metadaten_Geraete_Windgeschwindigkeit_Maxwind_{station}.txt':device,
      f'Metadaten_Parameter_{station}.txt':parameter}
 z=io.BytesIO()
 with ZipFile(z,'w') as f:
  for k,v in mem.items():f.writestr(k,v)
 return z.getvalue()

class TestKyrill2007StationHistory(unittest.TestCase):
 def test_date_validation(self):
  self.assertEqual(_date('20070118'),'20070118')
  for x in ('20070230','2007111','abc10101','200701180','2007011x'):
   with self.subTest(x=x),self.assertRaises(DWDStationHistoryBlocked):_date(x)

 def test_all_three_fake_stations_no_provenance_promotion(self):
  for station in STATIONS:
   with self.subTest(station=station):
    raw=fake(station);r=validate_station_metadata(raw,station=station,
                              override_digest=hashlib.sha256(raw).hexdigest())
    self.assertEqual(r['contract'],CONTRACT)
    self.assertFalse(r['historical_2007_station_sensor_source_join_verified'])
    self.assertEqual(r['maxwind_instrument_sensor_height_over_ground_m'],EXPECTED_2007[station][3])
    self.assertTrue(r['valid_for_complete_2007_01_17_through_2007_01_20'])
    self.assertFalse(r['QN1_data_reclassified_as_QN3'])
    self.assertIsNone(r['annual_AEP'])

 def test_unpinned_fake_source_rejected(self):
  with self.assertRaisesRegex(DWDStationHistoryBlocked,'SHA256'):
   validate_station_metadata(fake('03379'),station='03379')

 def test_missing_valid_date_gap_fails(self):
  station='03379';sid='3379'
  geo='Stations_id;Stationshoehe;Geogr.Breite;Geogr.Laenge;von_datum;bis_datum;Stationsname\n'
  geo+=f'{sid};515.37;48.1632;11.5429;20060101;20070117;TEST\n'
  geo+=f'{sid};515.37;48.1632;11.5429;20070119;20081231;TEST\n'
  raw=fake(station,geo=geo)
  with self.assertRaisesRegex(DWDStationHistoryBlocked,'missing or multiple'):
   validate_station_metadata(raw,station=station,override_digest=hashlib.sha256(raw).hexdigest())

 def test_overlapping_2007_instrument_rows_fail(self):
  station='00433';sid='433';lat,lon,alt,height,model=EXPECTED_2007[station]
  header='Stations_ID;Stationsname;Geo. Laenge [Grad];Geo. Breite [Grad];Stationshoehe [m];Geberhoehe ueber Grund [m];Von_Datum;Bis_Datum;Geraetetyp Name;Messverfahren;eo\n'
  row=f'{sid};TEST;{lon};{lat};{alt};{height};20060101;20081231;{model};wind;eo;\n'
  raw=fake(station,device=header+row+row)
  with self.assertRaisesRegex(DWDStationHistoryBlocked,'missing or multiple'):
   validate_station_metadata(raw,station=station,override_digest=hashlib.sha256(raw).hexdigest())

 def test_modified_sensor_height_fails(self):
  station='03379';raw=fake(station)
  with ZipFile(io.BytesIO(raw)) as f:
   members={n:f.read(n).decode() for n in f.namelist()}
  target=f'Metadaten_Geraete_Windgeschwindigkeit_Maxwind_{station}.txt'
  members[target]=members[target].replace(';29.28;',';10;')
  b=io.BytesIO()
  with ZipFile(b,'w') as f:
   for k,v in members.items():f.writestr(k,v)
  forged=b.getvalue()
  with self.assertRaisesRegex(DWDStationHistoryBlocked,'height or type changed'):
   validate_station_metadata(forged,station=station,override_digest=hashlib.sha256(forged).hexdigest())

 def test_invalid_parameter_fx10_fails(self):
  station='01262';raw=fake(station,parameter='Stations_ID;Von_Datum;Bis_Datum;Stationsname;Parameter;Parameterbeschreibung;Einheit\n1262;20060101;20081231;TEST;DX_10;Direction;deg\n')
  with self.assertRaisesRegex(DWDStationHistoryBlocked,'missing or multiple'):
   validate_station_metadata(raw,station=station,override_digest=hashlib.sha256(raw).hexdigest())

if __name__=='__main__':unittest.main()
