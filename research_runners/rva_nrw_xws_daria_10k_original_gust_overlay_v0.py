# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-public XWS Daria 1990 maximum 3s gust -> NRW 2022 building sites.

Historical 1990 storm replayed on a DIFFERENT-VINTAGE 2022 physical building
sample with hypothetical 2025 insurer values. This is ONLY event-conditional
wind HAZARD exposure, not physical damage, actual insurer-site loss, a valid
Germany-calibrated 3-second-gust VLT, financial contract, yearly frequency,
Oasis/NextGen native model or OEP/AEP.

Original source WGS84 grid location CSV is attached by grid ID (rotated-pole
~0.22 degree native) and nearest great-circle grid point. NEVER use the
fictional C3S-like 0.25-degree grid or reinterpret XWS as Copernicus data.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile

from rva_nrw_hu22_to_nextgen_c3s_spatial_v0 import (
    _source as _original_nrw_oed_source,
    SITES, COUNTIES, SOURCE_SHA
)
from rva_nrw_hu_gfk_residential_candidate_v0 import classify_gfk
from xws_daria_1990_original_csv_preflight_v0 import (
    validate_original_bundle, _grid as _xws_grid,
    _gusts as _xws_gusts, ALLOWED_SOURCE_IDS, XWSSourceBlocked
)

MAX_DISTANCE_KM = 45.0
EARTH_RADIUS_KM = 6371.0088
NAMES = {
    "grid": "grid.csv",
    "daria_lower95": "daria_lower95.csv",
    "daria_mean": "daria_mean.csv",
    "daria_upper95": "daria_upper95.csv",
}
SITE_FIELDS = (
    "FictionalSiteId", "Original2022KreisAGS", "XWS1990DariaNearestSourceGridId",
    "NearestXWSGridPointKm", "Daria1990Lower95GustMps",
    "Daria1990MeanGustMps", "Daria1990Upper95GustMps",
    "Fictional2025BuildingTIVEUR", "ActualRVInsuredSiteObserved",
)
COUNTY_FIELDS = (
    "KreisAGS2022", "FictionalSiteCount", "FictionalBuildingTIVEUR",
    "TIVWeightedDaria1990MeanGustMps", "FictionalBuildingsWithMeanGustGE25Mps",
    "FictionalTIVWithMeanGustGE25MpsEUR",
)
SCHEMA = "RVA_NRW_2022_HU10K_XWS_DARIA1990_ORIGINAL_3S_GUST_HAZARD_ONLY_V0"


class OverlayBlocked(ValueError):
    pass


def _cartesian(lon:float,lat:float):
    radlat = math.radians(lat)
    radlon = math.radians(lon)
    return (math.cos(radlat)*math.cos(radlon),
            math.cos(radlat)*math.sin(radlon),
            math.sin(radlat))


def _nearest_index(grid:dict[int,tuple[Decimal,Decimal]]):
    buckets = defaultdict(list)
    for ident,(longitude,latitude) in grid.items():
        lon=float(longitude);lat=float(latitude)
        coord=_cartesian(lon,lat)
        buckets[(math.floor(lon*2),math.floor(lat*2))].append((ident,coord))
    if len(grid)!=sum(len(x) for x in buckets.values()):
        raise OverlayBlocked("duplicate official XWS grid ID in geometric source")
    return buckets


def _match(lon:float,lat:float,buckets:dict)->tuple[int,float]:
    p=_cartesian(lon,lat)
    bx,by=math.floor(lon*2),math.floor(lat*2)
    best=None
    for xi in range(bx-1,bx+2):
        for yi in range(by-1,by+2):
            for ident,q in buckets.get((xi,yi),()):
                chord=sum((a-b)*(a-b) for a,b in zip(p,q))
                value=(chord,ident)
                if best is None or value<best:
                    best=value
    if best is None:
        raise OverlayBlocked("NRW source building lies beyond original XWS grid neighborhood")
    chord,ident=best
    km=EARTH_RADIUS_KM*2*math.asin(min(1,math.sqrt(chord)/2))
    if km>MAX_DISTANCE_KM:
        raise OverlayBlocked("original physical source grid too distant: "+str(round(km,2)))
    return ident,km


def _rows_bytes(rows:list[dict],fieldnames)->bytes:
    buf=io.StringIO(newline="")
    writer=csv.DictWriter(buf,fieldnames=fieldnames,lineterminator="\n")
    writer.writeheader();writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def original_source_files(path:Path)->dict[str,bytes]:
    if path.is_symlink() or not path.is_dir():
        raise OverlayBlocked("explicit ORIGINAL XWS source-files ephemeral directory required")
    if {p.name for p in path.iterdir()} != set(NAMES.values()):
        raise OverlayBlocked("exact four validated XWS original source CSVs required")
    result={}
    for name,filename in NAMES.items():
        p=path/filename
        if p.is_symlink() or p.stat().st_size>24_000_000:
            raise OverlayBlocked("untrusted XWS CSV source symlink or size")
        result[name]=p.read_bytes()
    return result


def overlay(xws:dict[str,bytes],nrw_zip:Path,
            *,expected_sites:int=SITES,expected_counties:int=COUNTIES,
            expected_tiv:int=4_826_029_500)->dict:
    if (type(expected_sites) is not int or not 1<=expected_sites<=10000
        or type(expected_counties) is not int or not 1<=expected_counties<=53
        or type(expected_tiv) is not int or not 1<=expected_tiv<=10**15):
        raise OverlayBlocked("bounded research site / county / TIV controls required")
    source_receipt=validate_original_bundle(xws)
    original_grid=_xws_grid(xws["grid"])
    gusts={k:_xws_gusts(xws[k],len(original_grid),source_name=k)
           for k in ("daria_lower95","daria_mean","daria_upper95")}
    buckets=_nearest_index(original_grid)
    if (nrw_zip.is_symlink() or not nrw_zip.is_file() or nrw_zip.stat().st_size>30_000_000):
        raise OverlayBlocked("existing source-authenticated original NRW OED research ZIP required")
    with zipfile.ZipFile(nrw_zip) as z:
        if set(z.namelist())!={"location.csv","account.csv","physical_candidate_evidence.csv","manifest.json"} or z.testzip() is not None:
            raise OverlayBlocked("NRW 10k archive member population or CRC changed")
        locations,physical,source_meta=_original_nrw_oed_source(z,expected_sites,expected_counties)
    if source_meta["source_original_2022_HU_complete_archive_SHA256"]!=SOURCE_SHA:
        raise OverlayBlocked("independently pinned full HU22 original source identity mismatch")
    bycounty=defaultdict(lambda: {"count":0,"tiv":0,"weighted_mean":Decimal(0),
                                  "n_ge25":0,"tiv_ge25":0})
    sites=[]
    grids_seen=Counter()
    max_distance=0
    gross_hypothetical_tiv=0
    for loc in locations:
        ident=loc["LocNumber"]
        p=physical[ident]
        if (p["SourcePhysicalCandidateNotInsuredSite"]!="true"
            or classify_gfk(p["SourceGFK"])[0]!="residential_function_candidate_only"
            or p["KreisAGS2022"]!=loc["LocGroup"][6:]
            or loc["CountryCode"]!="DE" or loc["OEDVersion"]!="5.0.0"
            or loc["AccNumber"]!=ident):
            raise OverlayBlocked("original source building taxonomy, insurance nonadmission or county changed")
        try:
            lat=Decimal(loc["Latitude"]);lon=Decimal(loc["Longitude"])
            tiv=int(loc["BuildingTIV"])
        except (InvalidOperation,ValueError,TypeError) as exc:
            raise OverlayBlocked("source OED geographical or fictional TIV type invalid") from exc
        if (not lat.is_finite() or not lon.is_finite()
            or not Decimal("50")<lat<Decimal("52.8")
            or not Decimal("5.5")<lon<Decimal("10")
            or not 1<=tiv<=500_000_000
            or str(tiv)!=loc["BuildingTIV"]):
            raise OverlayBlocked("nonphysical source coordinates or false hypothetical TIV")
        grid_id,distance=_match(float(lon),float(lat),buckets)
        lower=gusts["daria_lower95"][grid_id]
        mean=gusts["daria_mean"][grid_id]
        upper=gusts["daria_upper95"][grid_id]
        if not lower<=mean<=upper:
            raise OverlayBlocked("XWS Daria uncertainty order mismatch")
        county=p["KreisAGS2022"]
        count=bycounty[county]
        count["count"]+=1;count["tiv"]+=tiv
        count["weighted_mean"]+=Decimal(tiv)*mean
        if mean>=25:
            count["n_ge25"]+=1;count["tiv_ge25"]+=tiv
        grids_seen[grid_id]+=1
        max_distance=max(max_distance,distance)
        gross_hypothetical_tiv+=tiv
        sites.append({
            "FictionalSiteId":ident,
            "Original2022KreisAGS":county,
            "XWS1990DariaNearestSourceGridId":grid_id,
            "NearestXWSGridPointKm":format(Decimal(str(distance)).quantize(Decimal("0.001"),rounding=ROUND_HALF_UP),".3f"),
            "Daria1990Lower95GustMps":str(lower),
            "Daria1990MeanGustMps":str(mean),
            "Daria1990Upper95GustMps":str(upper),
            "Fictional2025BuildingTIVEUR":tiv,
            "ActualRVInsuredSiteObserved":"false",
        })
    if (len(sites)!=expected_sites or gross_hypothetical_tiv!=expected_tiv
        or len(bycounty)!=expected_counties or len({r["FictionalSiteId"] for r in sites})!=expected_sites):
        raise OverlayBlocked("XWS historical replay missing or duplicated source sites/counties/TIV")
    summary=[]
    for county in sorted(bycounty):
        group=bycounty[county]
        summary.append({
            "KreisAGS2022":county,
            "FictionalSiteCount":group["count"],
            "FictionalBuildingTIVEUR":group["tiv"],
            "TIVWeightedDaria1990MeanGustMps":str(
                (group["weighted_mean"]/Decimal(group["tiv"])).quantize(Decimal("0.001"),rounding=ROUND_HALF_UP)),
            "FictionalBuildingsWithMeanGustGE25Mps":group["n_ge25"],
            "FictionalTIVWithMeanGustGE25MpsEUR":group["tiv_ge25"],
        })
    receipt={
        "schema":SCHEMA,
        "status":"REAL_XWS_HISTORICAL_WIND_HAZARD_ON_PUBLIC_GEOSITES_WITH_FICTIONAL_INSURANCE_ONLY",
        "provider_original_four_XWS_CSV_source_receipt":source_receipt,
        "original_NRW_HU22_full_archived_SHA256":SOURCE_SHA,
        "original_NRW_source_derived_OED_artifact_SHA256":hashlib.sha256(nrw_zip.read_bytes()).hexdigest(),
        "real_original_XWS_historical_storm":"Daria 1990",
        "storm_uncertainty_variants_are_same_physical_event":True,
        "source_weather_maximum_3sec_gust_at_10m_mps":True,
        "source_grid_IS_original_rotated_0p22_degree_not_C3S_0p25":True,
        "source_physical_building_site_count":len(sites),
        "source_2022_NRW_Kreise_count":len(bycounty),
        "unique_nearest_original_XWS_source_grid_points":len(grids_seen),
        "largest_building_to_original_XWS_grid_km":round(max_distance,3),
        "fictional_building_TIV_eur":gross_hypothetical_tiv,
        "fictional_buildings_with_mean_wind_ge25_mps":sum(v["n_ge25"] for v in bycounty.values()),
        "fictional_TIV_exposed_to_mean_wind_ge25_mps_eur":sum(v["tiv_ge25"] for v in bycounty.values()),
        "site_wind_gust_not_insured_damage_or_loss":True,
        "actual_1990_RV_insured_geographies_or_2025_RV_coverage_known":False,
        "German_wind_vulnerability_by_material_roof_construction_validated":False,
        "XWS_extreme_storm_selection_is_valid_annual_frequency_model":False,
        "native_Oasis_or_NextGen_GUL_IL_RI_OEP_AEP_executed":False,
        "required_XWS_CC_BY_4_0_attribution":source_receipt["required_attribution"],
    }
    return {"site_rows":sites,"county_rows":summary,"receipt":receipt}


def write_zip(out:Path,study:dict)->dict:
    if out.exists() or not out.parent.is_dir():
        raise OverlayBlocked("fresh output ZIP path required")
    a=_rows_bytes(study["site_rows"],SITE_FIELDS)
    b=_rows_bytes(study["county_rows"],COUNTY_FIELDS)
    receipt=dict(study["receipt"])
    receipt["output_sha256"]={
        "daria_1990_original_source_site_gust_only.csv":hashlib.sha256(a).hexdigest(),
        "daria_1990_NRW_53kreis_event_gust_summary.csv":hashlib.sha256(b).hexdigest(),
    }
    try:
        with zipfile.ZipFile(out,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
            z.writestr("daria_1990_original_source_site_gust_only.csv",a)
            z.writestr("daria_1990_NRW_53kreis_event_gust_summary.csv",b)
            z.writestr("source_and_no_CAT_loss_manifest.json",json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    except Exception:
        out.unlink(missing_ok=True)
        raise
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-xws-csv-dir",required=True,type=Path)
    parser.add_argument("--original-geocoded-nrw-oed-zip",required=True,type=Path)
    parser.add_argument("--out-derived-gust-zip",required=True,type=Path)
    args=parser.parse_args()
    try:
        study=overlay(original_source_files(args.original_xws_csv_dir),args.original_geocoded_nrw_oed_zip)
        receipt=write_zip(args.out_derived_gust_zip,study)
        print(json.dumps({
            "status":receipt["status"],
            "storm":receipt["real_original_XWS_historical_storm"],
            "fictional_sites":receipt["source_physical_building_site_count"],
            "county_count":receipt["source_2022_NRW_Kreise_count"],
            "unique_XWS_grid_points":receipt["unique_nearest_original_XWS_source_grid_points"],
            "max_nearest_grid_distance_km":receipt["largest_building_to_original_XWS_grid_km"],
            "fictional_tiv_eur":receipt["fictional_building_TIV_eur"],
            "event_site_mean_gust_ge25_mps":receipt["fictional_buildings_with_mean_wind_ge25_mps"],
            "insurer_loss_or_annual_EP_calculated":False,
        },sort_keys=True))
    except (OSError,OverlayBlocked,XWSSourceBlocked,ValueError,zipfile.BadZipFile) as exc:
        parser.exit(2,"XWS_DARIA_NRW_HAZARD_OVERLAY_BLOCKED: "+str(exc)+"\n")
    return 0


if __name__=="__main__":
    sys.exit(main())
