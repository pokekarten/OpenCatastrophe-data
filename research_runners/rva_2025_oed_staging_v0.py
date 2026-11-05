# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic fictional R+V-like 2025 county/age -> OED staging exporter.

NO carrier site geography, valuation, insurance contract or CAT model is observed.
Missing coordinates intentionally BLOCK a German peril model lookup.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / 'research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml'
AGES = ROOT / 'research/observations/zensus2022_400_kreis_original_building_age_cohorts_v0.toml'
HGB = ROOT / 'research/observations/rva_solo_hgb_property_2019_2025_v0.toml'
CASES = ('PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY', 'HISTORIC_PRE1950_AFFINITY_1_5X', 'MODERN_POST2000_AFFINITY_1_5X')
VALUES = {'low': 250_000, 'central': 450_000, 'high': 750_000}
NATIONAL = 1_060_546
GWP_CENTS = 99_771_000_000
PORT = 'RVA-LIKE-2025-SYNTHETIC-RESEARCH'
LOC = ('PortNumber','AccNumber','LocNumber','LocGroup','CountryCode','Latitude','Longitude','LocCurrency','LocPerilsCovered','BuildingTIV','ContentsTIV','BITIV','OtherTIV','NumberOfBuildings','OEDVersion')
ACC = ('PortNumber','AccNumber','PolNumber','AccCurrency','PolPerilsCovered','OEDVersion')
CELL = ('KreisAGS2022','AgeBandIndex','Published2022BuildingAgeCount','Fictional2025FullContractCount','Fictional2025ExportedContractCount')

class StagingError(ValueError):
    pass


def allocate_sample(cells: list[dict], size: int) -> list[int]:
    """Exact largest remainder, deterministic ties, never exceed cell populations."""
    if not cells or any(type(c.get('count')) is not int or c['count'] < 0 for c in cells):
        raise StagingError('invalid fictional county/age count')
    total = sum(c['count'] for c in cells)
    if total != NATIONAL or type(size) is not int or size < 0 or size > total:
        raise StagingError('national count or sample-size mismatch')
    if size == 0:
        return [c['count'] for c in cells]  # 0 selects full book
    result = [c['count'] * size // total for c in cells]
    remainder = size - sum(result)
    order = sorted(range(len(cells)), key=lambda i: (-(cells[i]['count'] * size % total), i))
    for idx in order[:remainder]:
        result[idx] += 1
    if sum(result) != size or any(n > c['count'] for n,c in zip(result,cells)):
        raise StagingError('sample allocation failed conservation')
    return result


def rows_from_validated_sources(inputs: list[dict], case: str) -> list[dict]:
    # The existing runner authenticates full original aggregate SHA, row hashes,
    # legal-person scope, all 400 counties, 10 age classes and national HGB controls.
    from rva_2025_kreis_age_source_sensitivity_v0 import simulate_age_prior
    if case not in CASES:
        raise StagingError('unknown explicit fictional geography scenario')
    result = simulate_age_prior(*inputs)
    if (result['observed_national_2025_contracts'] != NATIONAL
        or result['observed_national_2025_annual_gwp_eur_cents'] != GWP_CENTS
        or result['admission']['model_input_approved'] is not False):
        raise StagingError('issuer or admission gate mismatch')
    county = result['cases'][case]['hypothetical_county_rows']
    source_ages = {r['ags']: r['age_bands_source_order'] for r in inputs[1]['kreise']}
    if len(county) != 400 or len(source_ages) != 400:
        raise StagingError('incomplete county population')
    cells = []
    for c in sorted(county, key=lambda r:r['kreis_ags_2022']):
        ags = c['kreis_ags_2022']
        values = c['hypothetical_age_contracts_2025']
        if len(values) != 10 or sum(values) != c['hypothetical_contracts_2025']:
            raise StagingError('cohort insurance mass mismatch')
        for age in range(10):
            cells.append({'ags':ags, 'age':age, 'count':values[age],
                          'published_2022':source_ages[ags][age]})
    if len(cells) != 4000 or sum(c['count'] for c in cells) != NATIONAL:
        raise StagingError('national cohort total mismatch')
    return cells


def export(cells: list[dict], out: Path, case: str, valuation: str,
           requested_sample_size: int, input_hashes: dict[str,str]) -> dict:
    if case not in CASES or valuation not in VALUES:
        raise StagingError('unapproved fictional scenario')
    selected = allocate_sample(cells,requested_sample_size)
    nrows = sum(selected)
    if out.exists() or not out.parent.is_dir():
        raise StagingError('output directory must not exist; parent must exist')
    out.mkdir(mode=0o700)
    files = ('location.csv','account.csv','cohort_receipt.csv','manifest.json')
    try:
        with (out/files[0]).open('x',encoding='utf8',newline='') as lf, \
             (out/files[1]).open('x',encoding='utf8',newline='') as af, \
             (out/files[2]).open('x',encoding='utf8',newline='') as cf:
            lw=csv.DictWriter(lf,LOC,lineterminator='\n'); lw.writeheader()
            aw=csv.DictWriter(af,ACC,lineterminator='\n'); aw.writeheader()
            cw=csv.DictWriter(cf,CELL,lineterminator='\n'); cw.writeheader()
            for c,n in zip(cells,selected):
                ags,age=c['ags'],c['age']
                cw.writerow(dict(zip(CELL,(ags,str(age+1),str(c['published_2022']),str(c['count']),str(n)))))
                for serial in range(1,n+1):
                    ident=f'SYN-{ags}-{age+1:02d}-{serial:06d}'
                    lw.writerow({'PortNumber':PORT,'AccNumber':ident,'LocNumber':ident,
                                 'LocGroup':'KREIS-'+ags,'CountryCode':'DE',
                                 'Latitude':'','Longitude':'','LocCurrency':'EUR',
                                 'LocPerilsCovered':'WW2','BuildingTIV':str(VALUES[valuation]),
                                 'ContentsTIV':'0','BITIV':'0','OtherTIV':'0',
                                 'NumberOfBuildings':'1','OEDVersion':'5.0.0'})
                    aw.writerow({'PortNumber':PORT,'AccNumber':ident,'PolNumber':ident,
                                 'AccCurrency':'EUR','PolPerilsCovered':'WW2','OEDVersion':'5.0.0'})
        receipt = {
            'schema':'RVA_LIKE_OED_RESEARCH_STAGING_V0','status':'NOT_GEOLOCATED_NOT_MODEL_READY',
            'legal_entity_accounting_anchor':'R+V Allgemeine Versicherung AG solo 2025',
            'company_2025_national_year_end_building_contracts_observed':NATIONAL,
            'company_2025_national_annual_building_gwp_eur_cents_observed':GWP_CENTS,
            'observed_2022_building_age_opportunities_only':True,
            'fictional_county_age_allocation_case':case,'fictional_per_site_valuation_case':valuation,
            'fictional_per_site_building_tiv_eur':VALUES[valuation],
            'requested_sample_size_0_means_full':requested_sample_size,
            'exported_fictional_locations_and_policies':nrows,
            'exported_fictional_building_tiv_eur':nrows*VALUES[valuation],
            'full_fictional_2025_book_exported':nrows==NATIONAL,
            'sample_not_a_financially_scaled_full_portfolio':nrows!=NATIONAL,
            'physical_site_coordinates_observed':False,
            'physical_county_geocodes_provided':False,
            'insured_carrier_locations_observed':False,
            'carrier_policy_terms_observed':False,
            'carrier_outward_treaties_observed':False,
            'germany_peril_model_lookup_allowed':False,
            'gross_net_oep_aep_calibrated':False,
            'data_model_warning':'2022 physical building age weights != R+V policy age; 2025 policy counts != buildings; assumed TIV not observed; no real geocodes.',
            'input_sha256':input_hashes,
            'output_sha256':{f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in files[:3]},
        }
        (out/files[3]).write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n',encoding='utf8')
        return receipt
    except Exception:
        shutil.rmtree(out)
        raise


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('outdir',type=Path)
    parser.add_argument('--case',choices=CASES,default=CASES[0])
    parser.add_argument('--valuation',choices=tuple(VALUES),default='central')
    parser.add_argument('--sample-size',type=int,default=10000,help='0 exports the full 1,060,546 fictional policy set')
    args=parser.parse_args()
    try:
        paths={'census_2022':CENSUS,'age_2022':AGES,'hgb_2019_2025':HGB}
        blobs={key:path.read_bytes() for key,path in paths.items()}
        if any(len(b)>1_000_000 for b in blobs.values()):
            raise StagingError('source outside strict local file limit')
        inputs=[tomllib.loads(b.decode('utf8')) for b in blobs.values()]
        cells=rows_from_validated_sources(inputs,args.case)
        receipt=export(cells,args.outdir,args.case,args.valuation,args.sample_size,
                       {k:hashlib.sha256(b).hexdigest() for k,b in blobs.items()})
        print(json.dumps(receipt,sort_keys=True,indent=2))
    except (OSError,ValueError,KeyError,ImportError) as exc:
        parser.exit(2,f'BLOCKED: {exc}\n')
    return 0

if __name__=='__main__':
    sys.exit(main())
