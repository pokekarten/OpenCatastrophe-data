# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only contract tests, NOT an original NetCDF re-execution."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.dwd_climk_kyrill_station_grid_holdout_v0 import (
    STATIONS, MARKERS, DOCUMENTS, GridHoldoutBlocked,
    _haversine_km, parse_source_doc, verified_station_lines,
    validate_sampled_grid,
)


def fake_documents():
    hist=[]
    for sid,item in STATIONS.items():
        hist.append({'station_id':sid,'geography_latitude_deg':item['lat'],
                     'geography_longitude_deg':item['lon'],
                     'maxwind_instrument_sensor_height_over_ground_m':item['height'],
                     'source_original_metadata_zip_sha256':item['metadata_sha'],
                     'valid_for_complete_2007_01_17_through_2007_01_20':True,
                     'historical_2007_station_sensor_source_join_verified':True,
                     'QN1_data_reclassified_as_QN3':False,
                     'physical_wind_calibrated':False})
    def daily(sid):
        return [{'day_utc':f'2007-01-{i}',
                 'observed_10minute_records':144,'valid_gust_records':144,
                 'missing_value_records':0,'unobserved_10minute_slots':0,
                 'quality_flag_record_counts':{STATIONS[sid]['qn']:144},
                 'max_3second_gust_within_10minutes_mps_all_quality':(
                     STATIONS[sid]['peak'] if i==18 else '8.0'),
                 'max_3second_gust_mps_all_quality':(
                     STATIONS[sid]['peak'] if i==18 else '8.0')}
                for i in range(17,21)]
    return {
      'history':{'contract':'OC_DWD_KYRILL_2007_THREE_STATION_TIME_VALID_SOURCE_HISTORY_V0',
                 'scientific_model_admitted':False,'stations':hist},
      'berlin':{'contract':'OC_DWD_2007_KYRILL_BERLIN_TEMPELHOF_ORIGINAL_GUST_PREFLIGHT_V0',
                'dwd_station_id':'00433',
                'original_archive_sha256':'56d4e4d64958ca1dc926af58dabed796c550e2ff4969f81868cfb797b1ed891e',
                'daily_10minute_gust_aggregates':daily('00433')},
      'munich':{'contract':'OC_DWD_KYRILL_2007_TWO_MUNICH_STATION_GUST_HOLDOUT_V0',
                 'stations':[{'dwd_station_id':sid,
                              'original_archive_sha256':digest,
                              'four_day_window_utc':daily(sid)} for sid,digest in (
                     ('01262','ca273211d92b48449c1e92e140a3b6c5b4c99999307aa1ef2fad4fcb6c486fca'),
                     ('03379','4a5abf0fdfbf073cee91179f018863e871a496e23199d8c9476d96ff934f0ff7'))]}}


def fake_sample():
    points=[]
    station_cells={'00433':(142,79,31.3),'01262':(135,96,32.5),'03379':(134,95,33.976)}
    for sid,s in STATIONS.items():
        lon,lat=float(s['lon']),float(s['lat'])
        x,y,g=station_cells[sid]
        points.append({'point_id':'DWD_'+sid,'longitude_deg':lon,'latitude_deg':lat,
                       'native_cell_x':x,'native_cell_y':y,
                       'grid_center_lon_deg':lon,'grid_center_lat_deg':lat,
                       'original_era5_storm_gust_mps':g})
    for name,(lon,lat,x,y,mm) in MARKERS.items():
        points.append({'point_id':name,'longitude_deg':lon,'latitude_deg':lat,
                       'native_cell_x':x,'native_cell_y':y,
                       'grid_center_lon_deg':lon,'grid_center_lat_deg':lat,
                       'original_era5_storm_gust_mps':mm/1000})
    return {'source_sha256':'92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102',
            'source_storm_name':'KYRILL','source_storm_date_label':'20070118',
            'source_storm_index_zero_based':0,'source_event_key':'climk-winds:v2:ERA5:storm-index:0',
            'physical_intensity_unit':'m s**-1','source_points_sampled':5,
            'samples':points}


class DWDCLIMKStationGridHoldoutTests(unittest.TestCase):
    def test_pinned_three_station_and_observation_lineage(self):
        p=verified_station_lines(fake_documents())
        self.assertEqual(set(p),{'00433','01262','03379'})
        self.assertEqual(p['03379']['sensor_height_m'],'29.28')
        self.assertEqual(p['03379']['original_QN'],'3')
        self.assertEqual(p['00433']['original_QN'],'1')

    def test_complete_four_day_window_and_daily_source_quality(self):
        for sid in STATIONS:
            p=verified_station_lines(fake_documents())
            self.assertEqual(p[sid]['observed_jan18_fx10_max_mps'],STATIONS[sid]['peak'])

    def test_independent_original_at_station_grid_sample_not_fictional_marker(self):
        got=validate_sampled_grid(stations=verified_station_lines(fake_documents()),sample=fake_sample())
        self.assertEqual(got['real_dwd_stations'],3)
        berlin=got['station_to_grid_results'][0]
        self.assertFalse(berlin['in_same_era5_cell_as_fictional_city_marker'])
        self.assertEqual(berlin['era5_native_cell_y'],79)
        self.assertEqual(berlin['source_observation_quality_level'],'1')
        self.assertFalse(got['wind_model_bias_calibrated'])
        self.assertIsNone(got['annual_AEP'])
        self.assertFalse(got['era5_sample_original_bytes_verified_in_this_pure_function'])

    def test_same_cell_does_not_imply_same_real_measurement_operator(self):
        got=validate_sampled_grid(stations=verified_station_lines(fake_documents()),sample=fake_sample())
        city=got['station_to_grid_results'][2]
        self.assertTrue(city['in_same_era5_cell_as_fictional_city_marker'])
        self.assertFalse(city['same_wind_measurement_operator_validated'])
        self.assertFalse(city['height_or_roughness_normalized'])

    def test_haversine_zero_and_small_distance(self):
        self.assertEqual(_haversine_km(52.5,13.4,52.5,13.4),0)
        self.assertTrue(5<_haversine_km(52.4675,13.4021,52.5200,13.4050)<7)

    def test_haversine_rejects_nan_and_wrong_latitude(self):
        for args in ((float('nan'),0,1,1),(100,0,0,0),(0,0,float('inf'),0)):
            with self.assertRaises(GridHoldoutBlocked):_haversine_km(*args)

    def test_reject_wrong_station_coordinates_in_history(self):
        d=fake_documents();d['history']['stations'][0]['geography_latitude_deg']='52.4676'
        with self.assertRaises(GridHoldoutBlocked):verified_station_lines(d)

    def test_reject_station_sensor_height_drift(self):
        d=fake_documents();d['history']['stations'][2]['maxwind_instrument_sensor_height_over_ground_m']='10'
        with self.assertRaises(GridHoldoutBlocked):verified_station_lines(d)

    def test_reject_relabel_qn1_as_qn3(self):
        d=fake_documents();d['berlin']['daily_10minute_gust_aggregates'][1]['quality_flag_record_counts']={'3':144}
        with self.assertRaises(GridHoldoutBlocked):verified_station_lines(d)

    def test_reject_missing_day_or_incomplete_source(self):
        d=fake_documents();d['munich']['stations'][0]['four_day_window_utc'][1]['observed_10minute_records']=143
        with self.assertRaises(GridHoldoutBlocked):verified_station_lines(d)

    def test_reject_missing_munich_source(self):
        d=fake_documents();d['munich']['stations'].pop()
        with self.assertRaises(GridHoldoutBlocked):verified_station_lines(d)

    def test_reject_unauthenticated_markdown_bytes(self):
        for name in DOCUMENTS:
            with self.subTest(name=name),self.assertRaises(GridHoldoutBlocked):
                parse_source_doc(name,b'```json\n{}\n```\n')

    def test_reject_wrong_original_era5_source_digest(self):
        s=fake_sample();s['source_sha256']='0'*64
        with self.assertRaises(GridHoldoutBlocked):validate_sampled_grid(
            stations=verified_station_lines(fake_documents()),sample=s)

    def test_reject_misidentified_fictional_grid_cell(self):
        s=fake_sample();s['samples'][3]['native_cell_x']=141
        with self.assertRaises(GridHoldoutBlocked):validate_sampled_grid(
            stations=verified_station_lines(fake_documents()),sample=s)

    def test_reject_missing_station_and_duplicate_sample_id(self):
        for change in ('missing','duplicate'):
            s=fake_sample()
            if change=='missing':s['samples'].pop()
            else:s['samples'][0]['point_id']=s['samples'][1]['point_id']
            with self.assertRaises(GridHoldoutBlocked):validate_sampled_grid(
                stations=verified_station_lines(fake_documents()),sample=s)

    def test_reject_false_2007_event_identity(self):
        s=fake_sample();s['source_storm_date_label']='20070119'
        with self.assertRaises(GridHoldoutBlocked):validate_sampled_grid(
            stations=verified_station_lines(fake_documents()),sample=s)

    def test_reject_unphysical_gust_or_coordinates(self):
        for field,value in [('original_era5_storm_gust_mps',float('nan')),
                            ('grid_center_lat_deg',99),('native_cell_x',True)]:
            s=fake_sample();s['samples'][0][field]=value
            with self.subTest(field=field),self.assertRaises(GridHoldoutBlocked):
                validate_sampled_grid(stations=verified_station_lines(fake_documents()),sample=s)

    def test_reject_wrong_source_historical_instrument_checksum(self):
        d=fake_documents();d['history']['stations'][1]['source_original_metadata_zip_sha256']='1'*64
        with self.assertRaises(GridHoldoutBlocked):verified_station_lines(d)

    def test_no_annual_or_damage_claims(self):
        got=validate_sampled_grid(stations=verified_station_lines(fake_documents()),sample=fake_sample())
        for k in ('annual_event_rate','annual_AAL','annual_AEP','annual_OEP'):
            self.assertIsNone(got[k])
        for x in got['station_to_grid_results']:
            self.assertFalse(x['observed_building_claims'])
            self.assertFalse(x['science_admitted_for_wind_model_calibration'])


if __name__=='__main__':unittest.main()
