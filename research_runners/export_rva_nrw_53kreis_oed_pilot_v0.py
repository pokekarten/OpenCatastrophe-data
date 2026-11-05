# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""NRW-only R+V-like fictional OED 5.0 pilot, constrained by real 53-Kreis public context.

Actual observations: Zensus 2022 residential-use building/age county aggregates,
MaStR-derived PV generating-unit county aggregates 2026, and R+V Allgemeine
solo national year-end building contracts and annual written HGB premium 2025.
None is a joined real insurer-site observation. PV UNIT density is not roofs,
insured PV buildings, PV policy take-up, rooftop fragility or R+V market share.

No physical building/geometry, true site coordinate, cover or TIV is observed.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, getcontext
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tomllib

from rva_2025_oed_staging_v0 import (
    CENSUS, AGES, HGB, CASES, LOC, ACC, NATIONAL, GWP_CENTS, PORT,
    hypothetical_value, rows_from_validated_sources, StagingError,
)

ROOT=Path(__file__).resolve().parents[1]
NRW=ROOT/'research/observations/rva_nrw_53_kreis_census2022_pv2026_source_bridge_v0.toml'
CASE='PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY'
SAMPLE_N=10000
PV_SENSITIVITY=('no_pv_reweight','hypothetical_pv_density_affinity_0_5')
COHORT=('KreisAGS2022','AgeBandIndex','Real2022PublishedAgeCount','Full2025FictionalCountyAgeContracts',
        'NRWConditional2025FictionalSampleContracts','FictionalExportedTIVEUR')
COUNTY=('KreisAGS2022','Real2022BuildingsWithLivingSpace','Real2026RegisteredBuildingPVGeneratingUnits',
        'Full2025FictionalCountyContractsFromNationalPrior','NRWConditional2025FictionalSampleContracts',
        'FictionalExportedTIVEUR','Real2026PVUnitsNotBuildings','RealCompanyCountyShareObserved')
getcontext().prec=50


def _hamilton(total:int, weights:list[Decimal]) ->list[int]:
    if type(total) is not int or total<=0 or not weights or any(w<0 or not w.is_finite() for w in weights):
        raise StagingError('invalid weighted conditional sample')
    s=sum(weights)
    if s<=0:
        raise StagingError('all conditional weights zero')
    real=[Decimal(total)*w/s for w in weights]
    alloc=[int(x) for x in real]   # all weights >=0 -> truncation=floor
    remainder=total-sum(alloc)
    if not 0<=remainder<len(weights):
        raise StagingError('invalid conditional allocation remainder')
    rank=sorted(range(len(weights)),key=lambda i:(-(real[i]-alloc[i]),i))
    for i in rank[:remainder]:alloc[i]+=1
    if sum(alloc)!=total or any(x<0 for x in alloc):
        raise StagingError('NRW sample count conservation failed')
    return alloc


def _source_files():
    paths=(CENSUS,AGES,HGB,NRW)
    blobs=[p.read_bytes() for p in paths]
    if any(len(b)>1_000_000 for b in blobs):
        raise StagingError('source size outside bound')
    return [tomllib.loads(b.decode('utf8')) for b in blobs], {
        p.name:hashlib.sha256(blob).hexdigest() for p,blob in zip(paths,blobs)
    }


def validate_context(inputs:list[dict])->tuple[list[dict],dict[str,dict]]:
    if len(inputs)!=4:raise StagingError('expected exact 4 source families')
    c,a,h,nrw=inputs
    # SHA-bound original Zensus and legal solo HGB guards from the existing allocator.
    cells=rows_from_validated_sources([c,a,h],CASE)
    reference={r['ags']:r for r in c['kreise'] if r['ags'].startswith('05')}
    ages={r['ags']:r for r in a['kreise'] if r['ags'].startswith('05')}
    observed=nrw.get('kreise',[])
    bycode={r['AGS_Kreis']:r for r in observed}
    if (nrw.get('schema_version')!='RVA_NRW_53_KREIS_REAL_2022_BUILDINGS_2026_DERIVED_PV_CONTEXT_V0'
        or nrw.get('original_census_date')!='2022-05-15'
        or nrw.get('secondary_mastr_registry_date')!='2026-10-02'
        or nrw.get('original_census_publisher_sha256')!='82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551'
        or nrw.get('secondary_MaStR_derived_pinned_sha256')!='32678e605fb6cc9c80e6b9dbce01b8ba2fcfc2f88fea4fcde8ddf97e1478b7dd'
        or nrw.get('official_NRW_roof_potential_sha256')!='a9730f844159781c0747a4eb816f88382924239d0cc1874ea69d7a70ce912071'
        or nrw.get('source_data_are_public_county_aggregates') is not True
        or nrw.get('no_individual_municipality_or_pv_operator_rows') is not True
        or nrw.get('nrw_original_census_county_rows')!=53
        or nrw.get('nrw_secondary_pv_municipality_rows')!=396
        or nrw.get('company_RV_insurer_county_policies_observed') is not False
        or nrw.get('company_RV_insured_pv_geography_or_TIV_observed') is not False
        or nrw.get('insured_pv_policy_coverage_vulnerability_or_loss_known') is not False
        or nrw.get('native_cat_and_RI_model_admitted') is not False):
        raise StagingError('NRW original/public source admission changed')
    if len(reference)!=53 or len(ages)!=53 or len(observed)!=53 or len(bycode)!=53 or set(bycode)!=set(reference):
        raise StagingError('53 original NRW Kreis population incomplete')
    total_buildings=total_pv=0
    for ags,row in bycode.items():
        if not re.fullmatch(r'05[0-9]{3}',ags):
            raise StagingError('non-NRW county')
        buildings=reference[ags]['geb_mit_wohnraum']
        if (row['zensus2022_published_buildings_with_living_space']!=buildings
            or row['zensus2022_pre1950_age_cells']!=sum(ages[ags]['age_bands_source_order'][:2])
            or row['zensus2022_2000plus_age_cells']!=sum(ages[ags]['age_bands_source_order'][7:])
            or type(row['building_PV_generating_units']) is not int
            or row['building_PV_generating_units']<0):
            raise StagingError('2022 county/age/2026 independent PV context does not match original')
        total_buildings+=buildings
        total_pv+=row['building_PV_generating_units']
    if (total_buildings!=4_042_220 or total_pv!=876_684
        or nrw.get('national_NRW_zensus2022_published_buildings_with_living_space')!=total_buildings
        or nrw.get('national_NRW_building_PV_generating_units')!=total_pv):
        raise StagingError('NRW 53 official physical / public PV context totals drift')
    subset=[c for c in cells if c['ags'].startswith('05')]
    if len(subset)!=530 or sum(x['count'] for x in cells)!=NATIONAL:
        raise StagingError('national and NRW source-inferred fictional population wrong')
    return subset,bycode


def allocate_nrw_sample(cells:list[dict],county:dict[str,dict],pv_case:str,
                        sample_size:int=SAMPLE_N)->list[int]:
    if pv_case not in PV_SENSITIVITY or type(sample_size) is not int or not 1<=sample_size<=10000:
        raise StagingError('unsupported PV hypothesis or bounded research sample')
    bycounty={}
    for i,c in enumerate(cells):
        if c['ags'] not in county or c['age'] not in range(10) or c['count']<0:
            raise StagingError('invalid NRW county/age')
        bycounty.setdefault(c['ags'],[]).append(i)
    if len(bycounty)!=53 or len(cells)!=530 or any(len(v)!=10 for v in bycounty.values()):
        raise StagingError('wrong NRW source county-age cells')
    counts={ags:sum(cells[i]['count'] for i in indexes) for ags,indexes in bycounty.items()}
    if min(counts.values())<=0:
        raise StagingError('a NRW county has no fictional building contracts')
    full=sum(counts.values())
    if full<=sample_size:raise StagingError('NRW fictional book smaller than pilot')
    keys=sorted(counts)
    weights=[]
    for ags in keys:
        prior=Decimal(counts[ags])
        if pv_case=='no_pv_reweight':
            factor=Decimal(1)
        else:
            # Pure hypothetical ecological sensitivity: 0.5 * relative registered
            # PV generating-unit density, not actual roof PV or carrier propensity.
            obs=county[ags]
            relative=(Decimal(obs['building_PV_generating_units'])*Decimal(4_042_220) /
                      (Decimal(obs['zensus2022_published_buildings_with_living_space'])*Decimal(876_684)))
            factor=max(Decimal('0.75'),min(Decimal('1.50'),(Decimal(1)+relative)/2))
        weights.append(prior*factor)
    picked=_hamilton(sample_size,weights)
    result=[0]*len(cells)
    for ags,number in zip(keys,picked):
        indexes=bycounty[ags]
        if number>counts[ags]:raise StagingError('county oversampled')
        splits=_hamilton(number,[Decimal(cells[i]['count']) for i in indexes])
        for i,n in zip(indexes,splits):
            if n>cells[i]['count']:raise StagingError('age sampled beyond fictional population')
            result[i]=n
    if sum(result)!=sample_size:
        raise StagingError('regional/age conditional conservation failed')
    return result


def export_nrw_pilot(out:Path,pv_case:str,pattern:str='age_archetype',sample_size:int=SAMPLE_N,
                     loaded=None)->dict:
    if pv_case not in PV_SENSITIVITY or pattern not in ('flat','age_archetype'):
        raise StagingError('unknown hypothetical sensitivity')
    inputs,hashes=loaded if loaded is not None else _source_files()
    cells,county=validate_context(inputs)
    allocated=allocate_nrw_sample(cells,county,pv_case,sample_size)
    if out.exists() or not out.parent.is_dir():
        raise StagingError('outdir exists or parent unavailable')
    out.mkdir(mode=0o700)
    try:
        sums={ags:{'n':0,'tiv':0,'full':0} for ags in county}
        total_tiv=0
        with (out/'location.csv').open('x',encoding='utf-8',newline='') as lf, \
             (out/'account.csv').open('x',encoding='utf-8',newline='') as af, \
             (out/'cohort_receipt.csv').open('x',encoding='utf-8',newline='') as cf, \
             (out/'kreis_summary.csv').open('x',encoding='utf-8',newline='') as kf:
            lw=csv.DictWriter(lf,LOC,lineterminator='\n');lw.writeheader()
            aw=csv.DictWriter(af,ACC,lineterminator='\n');aw.writeheader()
            cw=csv.DictWriter(cf,COHORT,lineterminator='\n');cw.writeheader()
            kw=csv.DictWriter(kf,COUNTY,lineterminator='\n');kw.writeheader()
            for c,n in zip(cells,allocated):
                ags,age=c['ags'],c['age']
                s=sums[ags]
                s['full']+=c['count']
                s['n']+=n
                cell_tiv=0
                for serial in range(1,n+1):
                    ident=f'SYN-NRW-{ags}-{age+1:02d}-{serial:06d}'
                    tiv,_=hypothetical_value(450000,age,ident,pattern)
                    s['tiv']+=tiv
                    cell_tiv+=tiv
                    total_tiv+=tiv
                    lw.writerow({'PortNumber':PORT+'-NRW-COND','AccNumber':ident,'LocNumber':ident,
                       'LocGroup':'KREIS-'+ags,'CountryCode':'DE','Latitude':'','Longitude':'',
                       'LocCurrency':'EUR','LocPerilsCovered':'WW2','BuildingTIV':str(tiv),
                       'ContentsTIV':'0','BITIV':'0','OtherTIV':'0','NumberOfBuildings':'1','OEDVersion':'5.0.0'})
                    aw.writerow({'PortNumber':PORT+'-NRW-COND','AccNumber':ident,'PolNumber':ident,
                                'AccCurrency':'EUR','PolPerilsCovered':'WW2','OEDVersion':'5.0.0'})
                cw.writerow(dict(zip(COHORT,(ags,age+1,c['published_2022'],c['count'],n,cell_tiv))))
            for ags in sorted(sums):
                obs=county[ags];s=sums[ags]
                kw.writerow(dict(zip(COUNTY,(ags,obs['zensus2022_published_buildings_with_living_space'],
                    obs['building_PV_generating_units'],s['full'],s['n'],s['tiv'],
                    'true','false'))))
        if sum(s['n'] for s in sums.values())!=sample_size or sum(s['tiv'] for s in sums.values())!=total_tiv:
            raise StagingError('NRW sample/TIV conservation failed')
        receipt={
            'schema':'RVA_NRW_53_KREIS_2025_FICTIONAL_CONDITIONAL_OED_V0',
            'status':'RESEARCH_NOT_GEOLOCATED_NOT_MODEL_READY',
            'issuer_reference':'R+V Allgemeine Versicherung AG solo national 2025',
            'observed_2025_national_year_end_building_contracts':NATIONAL,
            'observed_2025_national_building_HGB_annual_GWP_eur_cents':GWP_CENTS,
            'NRW_company_county_distribution_observed':False,
            'NRW_full_book_is_only_fictional_national_scenario_subset':True,
            'NRW_fictional_full_prior_contract_count':sum(s['full'] for s in sums.values()),
            'NRW_fictional_conditional_sample_contracts':sample_size,
            'NRW_2022_real_county_count':53,'NRW_2022_real_buildings_with_living_space':4042220,
            'NRW_2026_real_registered_building_PV_generating_units':876684,
            '2026_PV_units_are_roofs_or_insured_properties':False,
            'NRW_company_PV_rooftop_policy_probability_observed':False,
            'fictional_PV_ecological_affinity_case':pv_case,
            'fictional_2025_geography_case':CASE,'fictional_valuation_pattern':pattern,
            'exported_fictional_building_TIV_eur':total_tiv,
            '2022_2025_2026_populations_statistically_equivalent':False,
            'real_building_coordinates_verified':False,'actual_RV_insured_building_sites':False,
            'native_Germany_Oasis_hazard_vulnerability_financial_run_verified':False,
            'germany_peril_model_lookup_allowed':False,
            'input_sha256':hashes,
            'output_sha256':{
                fname:hashlib.sha256((out/fname).read_bytes()).hexdigest()
                for fname in ('location.csv','account.csv','cohort_receipt.csv','kreis_summary.csv')
            }
        }
        (out/'manifest.json').write_text(json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        return receipt
    except Exception:
        shutil.rmtree(out)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('outdir',type=Path)
    parser.add_argument('--pv-case',choices=PV_SENSITIVITY,default=PV_SENSITIVITY[0])
    parser.add_argument('--valuation-pattern',choices=('flat','age_archetype'),default='age_archetype')
    parser.add_argument('--sample-size',type=int,default=SAMPLE_N)
    args=parser.parse_args()
    print(json.dumps(export_nrw_pilot(args.outdir,args.pv_case,args.valuation_pattern,args.sample_size),
                     sort_keys=True,indent=2,ensure_ascii=False))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,ZeroDivisionError) as exc:
        print('NRW_PILOT_BLOCKED: '+str(exc),file=sys.stderr)
        sys.exit(2)
