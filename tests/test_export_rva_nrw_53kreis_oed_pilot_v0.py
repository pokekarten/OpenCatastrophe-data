# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent stdlib-only source-integrity and NRW sample-conservation checks."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research_runners'))
from export_rva_nrw_53kreis_oed_pilot_v0 import (
    _hamilton, _source_files, validate_context, allocate_nrw_sample,
    export_nrw_pilot, StagingError
)
from decimal import Decimal


class TestNRWOriginalSourcePilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs,cls.hashes=_source_files()
        cls.cells,cls.county=validate_context(cls.inputs)

    def test_authenticated_nrw_53_2022_2026_source_not_insurer_observed(self):
        self.assertEqual(len(self.cells),530)
        self.assertEqual(len(self.county),53)
        self.assertEqual(sum(x['zensus2022_published_buildings_with_living_space'] for x in self.county.values()),4042220)
        self.assertEqual(sum(x['building_PV_generating_units'] for x in self.county.values()),876684)
        self.assertTrue(all(x['ags'].startswith('05') for x in self.cells))

    def test_two_distinct_ecological_prior_scenarios_preserve_same_nrw_sample(self):
        base=allocate_nrw_sample(self.cells,self.county,'no_pv_reweight',10000)
        pv=allocate_nrw_sample(self.cells,self.county,'hypothetical_pv_density_affinity_0_5',10000)
        self.assertEqual((sum(base),sum(pv)),(10000,10000))
        self.assertEqual(len(base),530)
        self.assertNotEqual(base,pv)
        self.assertEqual(pv,allocate_nrw_sample(self.cells,self.county,'hypothetical_pv_density_affinity_0_5',10000))
        self.assertTrue(all(0<=n<=c['count'] for c,n in zip(self.cells,base)))
        self.assertTrue(all(0<=n<=c['count'] for c,n in zip(self.cells,pv)))

    def test_hamilton_negative_and_tie_break(self):
        self.assertEqual(_hamilton(5,[Decimal('1'),Decimal('1'),Decimal('1')]),[2,2,1])
        self.assertEqual(sum(_hamilton(7,[Decimal('1'),Decimal('2'),Decimal('6')])),7)
        for n,w in ((0,[Decimal(1)]),(2,[Decimal(0)]),(2,[Decimal(-1)]),(2,[])):
            with self.assertRaises(StagingError):
                _hamilton(n,w)

    def test_nrw_oed_coordinates_not_inferred_and_all_counts_reconcile(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'nrw'
            receipt=export_nrw_pilot(out,'no_pv_reweight','age_archetype',1000,
                                      loaded=(self.inputs,self.hashes))
            self.assertEqual(receipt['NRW_2022_real_county_count'],53)
            self.assertEqual(receipt['NRW_fictional_conditional_sample_contracts'],1000)
            self.assertEqual(receipt['observed_2025_national_year_end_building_contracts'],1060546)
            self.assertFalse(receipt['NRW_company_county_distribution_observed'])
            self.assertFalse(receipt['germany_peril_model_lookup_allowed'])
            with (out/'location.csv').open(newline='',encoding='utf8') as f:
                loc=list(csv.DictReader(f))
            with (out/'account.csv').open(newline='',encoding='utf8') as f:
                acc=list(csv.DictReader(f))
            with (out/'cohort_receipt.csv').open(newline='',encoding='utf8') as f:
                cohorts=list(csv.DictReader(f))
            with (out/'kreis_summary.csv').open(newline='',encoding='utf8') as f:
                county=list(csv.DictReader(f))
            self.assertEqual((len(loc),len(acc),len(cohorts),len(county)),(1000,1000,530,53))
            self.assertEqual({x['LocNumber'] for x in loc},{x['AccNumber'] for x in acc})
            self.assertEqual(len({x['LocNumber'] for x in loc}),1000)
            self.assertTrue(all(x['LocGroup']=='KREIS-'+x['LocNumber'].split('-')[2] for x in loc))
            self.assertTrue(all(x['Latitude']=='' and x['Longitude']=='' for x in loc))
            self.assertEqual(sum(int(x['BuildingTIV']) for x in loc),receipt['exported_fictional_building_TIV_eur'])
            self.assertEqual(sum(int(x['FictionalExportedTIVEUR']) for x in cohorts),receipt['exported_fictional_building_TIV_eur'])
            self.assertEqual(sum(int(x['NRWConditional2025FictionalSampleContracts']) for x in county),1000)
            self.assertTrue(all(x['RealCompanyCountyShareObserved']=='false' for x in county))
            self.assertTrue(all(x['Real2026PVUnitsNotBuildings']=='true' for x in county))

    def test_fail_closed_on_admission_or_source_mutation(self):
        tamper=list(self.inputs)
        registry=dict(tamper[3])
        registry['company_RV_insurer_county_policies_observed']=True
        tamper[3]=registry
        with self.assertRaises(StagingError):
            validate_context(tamper)
        bad=list(self.inputs)
        r=dict(bad[3]);r['kreise']=[dict(v) for v in r['kreise']]
        r['kreise'][0]['building_PV_generating_units']+=1
        bad[3]=r
        with self.assertRaises(StagingError):
            validate_context(bad)
        for pv_case in ('actual_rv_pv_building','arbitrary'):
            with self.assertRaises(StagingError):
                allocate_nrw_sample(self.cells,self.county,pv_case,1000)
        for n in (0,10001,-1):
            with self.assertRaises(StagingError):
                allocate_nrw_sample(self.cells,self.county,'no_pv_reweight',n)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'exists';out.mkdir()
            with self.assertRaises(StagingError):
                export_nrw_pilot(out,'no_pv_reweight','flat',1000,loaded=(self.inputs,self.hashes))


if __name__=='__main__':
    unittest.main()
