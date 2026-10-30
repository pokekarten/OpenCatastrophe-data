# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic fixtures; no copied Copernicus dataset rows."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.c3s_wind_annual_summary_v0 import AnnualSummaryError, parse_annual_csv

HEADER = 'year,region,threshold,storm_number,mean_wind_gust,ssi,normalised_ssi,area_ratio,wind_gust_ratio,algorithm\n'
ROWS = '2020,DE21,0,5,18.3,1200000,0.5,0.8,1.2,Hodges\n2020,DE21,15.6,3,19.3,650000,0.2,0.6,1.3,Hodges\n2020,DE21,20,1,25.2,500000,0.1,0.3,1.5,Hodges\n2020,DE21,25,0,,,,,,Hodges\n'


def csv(rows=ROWS, header=HEADER):
    return (header + rows).encode()


class AnnualCsvTests(unittest.TestCase):
    def test_c3s_schema_and_data(self):
        output = parse_annual_csv(csv())
        self.assertEqual(output['observed_row_count'], 4)
        self.assertEqual(output['nuts_vintage'], 'unverified_from_csv')
        self.assertFalse(output['automatic_nuts_join_permitted'])
        self.assertFalse(output['records_are_individual_cat_events'])
        self.assertFalse(output['insured_losses_calculated'])
        self.assertEqual(output['observed_nuts_levels'], [2])
        self.assertEqual(output['rows'][3]['missing_hazard_metric_fields'],
                         ['area_ratio','mean_wind_gust','normalised_ssi','ssi','wind_gust_ratio'])
    def test_source_sha_deterministic(self):
        self.assertEqual(parse_annual_csv(csv())['source_csv_sha256'], hashlib.sha256(csv()).hexdigest())
    def test_technology_no_aggregation_across_algorithms(self):
        r='2021,DE21,20,2,23,100,0.1,0.2,0.9,TempestExtremes\n2021,DE21,20,1,23,100,0.1,0.2,0.9,Hodges\n'
        output=parse_annual_csv(csv(r))
        self.assertEqual([v['storm_number'] for v in output['rows']], [1,2])
    def test_nuts_hierarchy_not_combined(self):
        r='2021,DE,20,1,23,100,0.1,0.2,0.9,Hodges\n2021,DE2,20,1,23,100,0.1,0.2,0.9,Hodges\n2021,DE21,20,1,23,100,0.1,0.2,0.9,Hodges\n'
        self.assertEqual(parse_annual_csv(csv(r))['observed_nuts_levels'], [0,1,2])
    def test_reject_wrong_columns(self):
        with self.assertRaises(AnnualSummaryError):parse_annual_csv(csv(header=HEADER.replace('area_ratio,','bad_area,')))
    def test_reject_duplicate_header(self):
        with self.assertRaises(AnnualSummaryError):parse_annual_csv(csv(header=HEADER.replace('algorithm','year')))
    def test_reject_duplicate_primary_key(self):
        row='2021,DE21,20,1,23,100,0.1,0.2,0.9,Hodges\n'
        with self.assertRaises(AnnualSummaryError):parse_annual_csv(csv(row+row))
    def test_reject_storm_count_threshold_nonmonotonic(self):
        r='2021,DE21,15.6,1,18,100,0.1,0.2,0.9,Hodges\n2021,DE21,20,2,23,100,0.1,0.2,0.9,Hodges\n'
        with self.assertRaisesRegex(AnnualSummaryError,'nested threshold'):parse_annual_csv(csv(r))
    def test_reject_nonfinite(self):
        for bad in ['Infinity', '-Infinity', '-1']:
            with self.subTest(bad=bad),self.assertRaises(AnnualSummaryError):
                parse_annual_csv(csv(f'2021,DE21,20,1,23,100,0.1,{bad},0.9,Hodges\n'))
    def test_reject_large_or_underflowing_metric(self):
        for bad in ['1e9999', '1e-9999']:
            with self.subTest(bad=bad), self.assertRaises(AnnualSummaryError):
                parse_annual_csv(csv(f'2021,DE21,20,1,23,100,0.1,{bad},0.9,Hodges\n'))
    def test_reject_ratio_over_one(self):
        with self.assertRaises(AnnualSummaryError):parse_annual_csv(csv('2021,DE21,20,1,23,100,0.1,1.01,0.9,Hodges\n'))
    def test_reject_noninteger_count(self):
        with self.assertRaises(AnnualSummaryError):parse_annual_csv(csv('2021,DE21,20,0.5,23,100,0.1,0.2,0.9,Hodges\n'))
    def test_no_silent_zero_in_missing_metrics(self):
        row = parse_annual_csv(csv('2021,FR10,20,0,,,,,,TempestExtremes\n'))['rows'][0]
        self.assertIsNone(row['mean_wind_gust'])
        self.assertIsNone(row['ssi'])
    def test_reject_invalid_year_or_region_or_threshold(self):
        for fragment in ['1939,DE21,20','2027,DE21,20','2021,D!21,20','2021,DE21,21']:
            with self.subTest(fragment=fragment),self.assertRaises(AnnualSummaryError):
                parse_annual_csv(csv(fragment+',1,23,100,0.1,0.2,0.9,Hodges\n'))
    def test_reject_empty_csv(self):
        with self.assertRaises(AnnualSummaryError):parse_annual_csv(HEADER.encode())
    def test_reject_malformed_csv_row(self):
        with self.assertRaises(AnnualSummaryError):parse_annual_csv(csv('2021,DE21,20,1\n'))
    def test_csv_bom_supported(self):
        self.assertEqual(parse_annual_csv(b'\xef\xbb\xbf'+csv())['observed_row_count'],4)
    def test_cli_digest_success(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'input.csv';out=Path(d)/'out.json';f.write_bytes(csv())
            cmd=[sys.executable,'-m','research_runners.c3s_wind_annual_summary_v0',str(f),'--out',str(out),'--expected-source-sha256',hashlib.sha256(csv()).hexdigest()]
            r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(out.read_text())['observed_row_count'],4)
    def test_cli_digest_failure_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'input.csv';out=Path(d)/'out.json';f.write_bytes(csv())
            cmd=[sys.executable,'-m','research_runners.c3s_wind_annual_summary_v0',str(f),'--out',str(out),'--expected-source-sha256','0'*64]
            r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertFalse(out.exists())
    def test_cli_never_overwrites_original_csv(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'input.csv';f.write_bytes(csv())
            cmd=[sys.executable,'-m','research_runners.c3s_wind_annual_summary_v0',str(f),'--out',str(f),'--expected-source-sha256',hashlib.sha256(csv()).hexdigest()]
            r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertEqual(f.read_bytes(),csv())

if __name__=='__main__':unittest.main()
