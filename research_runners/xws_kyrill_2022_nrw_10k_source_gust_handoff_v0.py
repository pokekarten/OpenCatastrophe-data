# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Kyrill original rotated-grid gust -> 10k publicly geocoded FICTIONAL NRW policies.

Source source: four SHA-pinned real XWS 2007 storm NetCDF files (single event).
Exposure source: one SHA-pinned 2022 NRW HU OED derived artifact, 10k fictional
policies. Never use these as actual insurer sites, GUL or annual CAT estimates.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from xws_kyrill_original_netcdf_hazard_receipt_v0 import (
    ROOT, PRODUCTS, ORIGINAL_SHA256, download, inspect, SourceBlocked
)

EXPECTED_OED_ZIP_SHA = "5b0055ce71314f7d7baf4f67008cd4abba3df28a4bce0690bbe9521a3cc35757"
EXPECTED_HU_ORIGINAL_SHA = "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da"
EXPECTED_MANIFEST_SHA = "b4713a9a09a55193d39b64550bc1408ba588303d8a4e658f05536b3dbe14b416"
EXPECTED_SYNTH_TIV = 4826029500
SITE_COUNT = 10000
COUNTIES = 53
FIELDS = (
    "FictionalLocNumber","KreisAGS2022",
    "SourceXWSRotatedCellRow","SourceXWSRotatedCellColumn",
    "KyrillRecalMeanGustMS","KyrillLower95GustMS",
    "KyrillUpper95GustMS","KyrillRawUncontaminatedGustMS",
    "IsActualRVInsuredSite","WindVulnerabilityCalibrated"
)


def original_fictional_oed(path:Path) -> tuple[list[dict],dict]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size>2_000_000:
        raise SourceBlocked("bounded existing original-derived synthetic OED required")
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_OED_ZIP_SHA:
        raise SourceBlocked("fictional OED source artifact byte SHA changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        expected={"location.csv","account.csv","physical_candidate_evidence.csv","manifest.json"}
        if set(z.namelist())!=expected or z.testzip() is not None:
            raise SourceBlocked("unexpected or corrupted original derived OED ZIP")
        manifest_bytes=z.read("manifest.json")
        if hashlib.sha256(manifest_bytes).hexdigest()!=EXPECTED_MANIFEST_SHA:
            raise SourceBlocked("original fictional scenario manifest SHA drift")
        manifest=json.loads(manifest_bytes)
        if (manifest.get("source_original_2022_HU_complete_archive_SHA256")!=EXPECTED_HU_ORIGINAL_SHA
            or manifest.get("source_original_2022_HU_full_CRCs_verified") is not True
            or manifest.get("fictional_policy_count")!=SITE_COUNT
            or manifest.get("real_source_counties_represented")!=COUNTIES
            or manifest.get("physical_building_footprints_are_actual_RV_insured_sites") is not False
            or manifest.get("model_input_approved") is not False):
            raise SourceBlocked("source, population or insurer identity boundary changed")
        for file in ("location.csv","account.csv","physical_candidate_evidence.csv"):
            if hashlib.sha256(z.read(file)).hexdigest()!=manifest["output_file_SHA256"][file]:
                raise SourceBlocked("original OED inner CSV SHA mismatch: "+file)
        sites=list(csv.DictReader(io.StringIO(z.read("location.csv").decode("utf-8"))))
        accounts=list(csv.DictReader(io.StringIO(z.read("account.csv").decode("utf-8"))))
        evidence=list(csv.DictReader(io.StringIO(z.read("physical_candidate_evidence.csv").decode("utf-8"))))
    if len(sites)!=SITE_COUNT or len(accounts)!=SITE_COUNT or len(evidence)!=SITE_COUNT:
        raise SourceBlocked("fictional source OED population changed")
    site_ids=[r.get("LocNumber") for r in sites]
    if (len(set(site_ids))!=SITE_COUNT
        or set(site_ids)!={r.get("AccNumber") for r in accounts}
        or set(site_ids)!={r.get("LocNumber") for r in evidence}
        or any(r.get("SourcePhysicalCandidateNotInsuredSite")!="true" for r in evidence)
        or len({r.get("SourceOiSHA256") for r in evidence})!=SITE_COUNT):
        raise SourceBlocked("fictional policy and physical source provenance not one-to-one")
    return sites,manifest


def nearest_rotated_position(transformer, source_lon, source_lat, lon:float, lat:float):
    """Nearest centre of true XWS rotated grid, never a C3S WGS84 cell."""
    import numpy as np
    if not (5.5<lon<10 and 50<lat<52.8):
        raise SourceBlocked("original public NRW OED coordinate out of source region")
    rotated_lon,rotated_lat=transformer.transform(lon,lat)
    if not (np.isfinite(rotated_lon) and np.isfinite(rotated_lat)):
        raise SourceBlocked("rotated georeference transformation nonfinite")
    # Original XWS rotated longitudes are stored as 350.64 ... 389.58
    # whereas PROJ uses an equivalent -180 ... +180 representation.
    x=float(rotated_lon)%360
    if x<float(source_lon[0])-0.5:x+=360
    j=int(np.abs(source_lon-x).argmin())
    i=int(np.abs(source_lat-rotated_lat).argmin())
    if (abs(float(source_lon[j])-x)>0.111 or
        abs(float(source_lat[i])-rotated_lat)>0.111):
        raise SourceBlocked("fictional site has no corresponding original XWS grid cell")
    return i,j


def join(sites:list[dict],original_netcdf:dict[str,bytes]) -> tuple[list[dict],dict]:
    import numpy as np
    from scipy.io import netcdf_file
    from pyproj import CRS, Transformer
    if set(original_netcdf)!=set(PRODUCTS):
        raise SourceBlocked("all four original Kyrill variants required")
    originals={}
    for name,data in original_netcdf.items():
        originals[name]=inspect(name,data)
    attrs={(r["rotated_north_pole_lat"],r["rotated_north_pole_lon"],
            r["source_rotated_grid_nlat"],r["source_rotated_grid_nlon"])
           for r in originals.values()}
    if len(attrs)!=1:
        raise SourceBlocked("XWS original variants have inconsistent physical grid")
    pole_lat,pole_lon,_,_=next(iter(attrs))
    projection=CRS.from_cf({"grid_mapping_name":"rotated_latitude_longitude",
                            "grid_north_pole_latitude":pole_lat,
                            "grid_north_pole_longitude":pole_lon})
    transformer=Transformer.from_crs("EPSG:4326",projection,always_xy=True)
    fields={}
    coords=None
    for key,raw in original_netcdf.items():
        with netcdf_file(io.BytesIO(raw),mmap=False) as ds:
            x=np.asarray(ds.variables["lon"][:],dtype=float).copy()
            y=np.asarray(ds.variables["lat"][:],dtype=float).copy()
            if coords is None:
                coords=(x,y)
            elif not (np.array_equal(coords[0],x) and np.array_equal(coords[1],y)):
                raise SourceBlocked("XWS alternatives not on the exact same coordinate axes")
            v=np.asarray(ds.variables["wind_speed_of_gust"][:],dtype=float)
            if v.size != len(x)*len(y):
                raise SourceBlocked("XWS physical footprint shape inconsistent")
            fields[key]=v.reshape((len(y),len(x))).copy()
    rows=[]
    county_counts=Counter()
    lost=Counter()
    total_tiv=0
    covered_sites=0
    means=[]
    for site in sites:
        if (site.get("CountryCode")!="DE" or site.get("LocPerilsCovered")!="WW2"
            or site.get("OEDVersion")!="5.0.0"
            or not site.get("LocGroup","").startswith("KREIS-05")):
            raise SourceBlocked("original fictional OED peril or county identity drift")
        ags=site["LocGroup"][6:]
        if len(ags)!=5 or not ags.isdecimal():
            raise SourceBlocked("incorrect Kreis code")
        try:
            lon,lat=float(site["Longitude"]),float(site["Latitude"])
            tiv=int(site["BuildingTIV"])
        except (ValueError,TypeError,KeyError) as exc:
            raise SourceBlocked("fictional OED numeric exposure invalid") from exc
        if not (tiv>0 and site["BuildingTIV"]==str(tiv)):
            raise SourceBlocked("fictional TIV not a positive exact integer")
        i,j=nearest_rotated_position(transformer,coords[0],coords[1],lon,lat)
        gust={}
        for k in PRODUCTS:
            v=float(fields[k][i,j])
            if not np.isfinite(v) or not (0<=v<=150):
                gust[k]=None
                lost[k]+=1
            else:
                gust[k]=v
        if gust["recalibrated_mean"] is None:
            raise SourceBlocked("missing historical Kyrill mean gust at an NRW physical location")
        means.append(gust["recalibrated_mean"])
        county_counts[ags]+=1
        total_tiv+=tiv
        covered_sites+=1
        rows.append({
            "FictionalLocNumber":site["LocNumber"],"KreisAGS2022":ags,
            "SourceXWSRotatedCellRow":i,"SourceXWSRotatedCellColumn":j,
            "KyrillRecalMeanGustMS":format(gust["recalibrated_mean"],".6f"),
            "KyrillLower95GustMS":"" if gust["recalibrated_lower_95"] is None else format(gust["recalibrated_lower_95"],".6f"),
            "KyrillUpper95GustMS":"" if gust["recalibrated_upper_95"] is None else format(gust["recalibrated_upper_95"],".6f"),
            "KyrillRawUncontaminatedGustMS":"" if gust["uncontaminated_raw"] is None else format(gust["uncontaminated_raw"],".6f"),
            "IsActualRVInsuredSite":"false",
            "WindVulnerabilityCalibrated":"false",
        })
    if len(rows)!=SITE_COUNT or covered_sites!=SITE_COUNT or len(county_counts)!=COUNTIES or total_tiv!=EXPECTED_SYNTH_TIV:
        raise SourceBlocked("source physical site, county or fictional TIV conservation failed")
    rows.sort(key=lambda v:v["FictionalLocNumber"])
    receipt={
        "schema":"XWS_KYRILL_2007_TRUE_ROTATED_GRID_NRW_FICTITIOUS_10K_HAZARD_ONLY_V0",
        "status":"HISTORICAL_SOURCE_GUST_SITE_CROSSWALK_NOT_GERMANY_CAT_LOSS",
        "source_xws_original_NetCDF_SHA256":ORIGINAL_SHA256,
        "source_original_2022_HU_SHA256":EXPECTED_HU_ORIGINAL_SHA,
        "fictional_OED_zip_SHA256":EXPECTED_OED_ZIP_SHA,
        "fictional_OED_manifest_SHA256":EXPECTED_MANIFEST_SHA,
        "historical_physical_storm_count":1,
        "source_rotated_pole":[pole_lon,pole_lat],
        "mapping":"WGS84_synthetic_OED_site_to_nearest_original_rotated_XWS_grid_center",
        "original_wind_gust_unit":"metres per second",
        "fictional_geocoded_source_physical_site_count":covered_sites,
        "fictional_Kreis_count":len(county_counts),
        "fictional_TIV_eur_conserved_not_real_RV":total_tiv,
        "mean_Kyrill_gust_at_fictional_sites_m_s":float(np.mean(means)),
        "median_Kyrill_gust_at_fictional_sites_m_s":float(np.median(means)),
        "min_max_Kyrill_gust_at_fictional_sites_m_s":[float(min(means)),float(max(means))],
        "historical_field_missing_or_out_of_domain_sites_by_variant":dict(lost),
        "count_by_Kreis":dict(sorted(county_counts.items())),
        "three_source_variants_do_not_mean_multiple_annual_events":True,
        "actual_RV_insured_site_identity_or_tiv_observed":False,
        "WGS84_XWS_true_rotated_geocode_projection_used":True,
        "source_hazard_footprint_not_station_observation":True,
        "wind_vulnerability_or_building_material_mapped":False,
        "real_insurer_policy_terms_and_reinsurance":False,
        "native_Oasis_GUL_IL_RI_ran_for_Kyrill":False,
        "annual_Gross_Net_OEP_AEP_authorized":False,
        "historical_catalogue_selected_extremes_no_unbiased_year_frequency":True,
        "external_original_NetCDF_bytes_redistributed":False,
    }
    return rows,receipt


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_oed_artifact_zip",type=Path)
    p.add_argument("derived_csv",type=Path)
    p.add_argument("derived_receipt_json",type=Path)
    a=p.parse_args()
    for out in (a.derived_csv,a.derived_receipt_json):
        if out.exists() or not out.parent.is_dir():
            raise SourceBlocked("new output paths in existing directories required")
    sites,_=original_fictional_oed(a.original_oed_artifact_zip)
    originals={name:download(ROOT+filename) for name,filename in PRODUCTS.items()}
    rows,receipt=join(sites,originals)
    out=io.StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=FIELDS,lineterminator="\n")
    writer.writeheader();writer.writerows(rows)
    blob=out.getvalue().encode("utf-8")
    receipt["site_hazard_csv_SHA256"]=hashlib.sha256(blob).hexdigest()
    try:
        a.derived_csv.write_bytes(blob)
        a.derived_receipt_json.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    except Exception:
        a.derived_csv.unlink(missing_ok=True)
        a.derived_receipt_json.unlink(missing_ok=True)
        raise
    print(json.dumps({k:receipt[k] for k in (
        "status","fictional_geocoded_source_physical_site_count","fictional_Kreis_count",
        "fictional_TIV_eur_conserved_not_real_RV","mean_Kyrill_gust_at_fictional_sites_m_s",
        "median_Kyrill_gust_at_fictional_sites_m_s","site_hazard_csv_SHA256",
        "annual_Gross_Net_OEP_AEP_authorized")},sort_keys=True))
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except (SourceBlocked,OSError,ValueError,KeyError,zipfile.BadZipFile) as e:
        print("XWS_KYRILL_NRW10K_SOURCE_GUST_JOIN_BLOCKED: "+str(e)[:180],file=sys.stderr)
        raise SystemExit(2)
