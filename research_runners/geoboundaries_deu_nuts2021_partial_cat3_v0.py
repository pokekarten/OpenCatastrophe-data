#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed partial independent DEU ADM1 / NUTS2021 polygon-source gate.

The existing all-16 CAT2 gate remains STRICT and BLOCKED. This tool stages
ONLY 14 independently geometry-supported provisional joins in isolated CAT3
SQLite. Berlin DE3 and Bremen DE5 are explicitly withheld. No geocoded
building, insurance source, CAT input or legal/official match is admitted.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

from research_runners.geoboundaries_deu_adm1_cat_sqlite_v0 import (
    _check_destination, open_cat_index, lookup_admin1,
)
from research_runners.geoboundaries_deu_adm1_original_geojson_v0 import (
    BOUNDARY_ID, EXPECTED_FEATURES, SOURCE_LFS_OID_SHA256, SOURCE_LFS_SIZE,
    inspect_geojson_bytes,
)
from research_runners.geoboundaries_deu_adm1_nuts2021_crosswalk_v0 import (
    EUROSTAT_SHA256, EUROSTAT_SIZE, EUROSTAT_COMMIT, EXPECTED_NUTS,
    EUROSTAT_TOTAL_NUTS1, MIN_BIDIRECTIONAL_OVERLAP,
    _parse_eurostat, CrosswalkError,
)

CAT3_ID=0x43415433
CAT3_SCHEMA="deu-adm1-nuts2021-provisional-14-state-withhold-2-v0"
ALLOWED_EXPECTED_COUNT=14
WITHHELD_CODES=frozenset({"DE3","DE5"})
MAX_RUNNER_UP_SHARE=0.10


def decide_best(intersections, source_area:float):
    """Return conservative one-to-one candidate or explicit reason.

    Each intersection is (official NUTS1 code, common area in EPSG3035 m2,
    Eurostat NUTS1 polygon area in EPSG3035 m2). This function accepts only
    already validated projected positive-area source polygons.
    """
    if (not isinstance(intersections,list) or len(intersections)!=len(EXPECTED_NUTS)
        or type(source_area) not in (float,int)
        or not math.isfinite(source_area) or source_area<=0):
        raise CrosswalkError("invalid projected source region")
    codes=[x[0] for x in intersections]
    if set(codes)!=EXPECTED_NUTS or len(set(codes))!=len(codes):
        raise CrosswalkError("unexpected independent NUTS1 candidate codes")
    for code,overlap,area in intersections:
        if (type(overlap) not in (float,int) or type(area) not in (float,int)
            or not math.isfinite(overlap) or not math.isfinite(area)
            or overlap<0 or area<=0 or overlap>min(float(source_area),float(area))*(1+1e-7)):
            raise CrosswalkError("invalid independent projected NUTS1 area")
    ranked=sorted(intersections,key=lambda x:x[1],reverse=True)
    code,best,target=ranked[0]
    second=ranked[1][1]
    src_cov=best/source_area
    ref_cov=best/target
    share=(second/best) if best else 0.0
    # Keep the preexisting strict 75% bidirectional and <10% runner-up
    # limits EXACTLY. Never loosen constraints to force 16 of 16 through.
    ok=(src_cov>=MIN_BIDIRECTIONAL_OVERLAP
        and ref_cov>=MIN_BIDIRECTIONAL_OVERLAP
        and share<MAX_RUNNER_UP_SHARE)
    reason=("polygon_supported_provisional"
            if ok else "low_bidirectional_coverage"
            if (src_cov<MIN_BIDIRECTIONAL_OVERLAP or
                ref_cov<MIN_BIDIRECTIONAL_OVERLAP)
            else "ambiguous_runner_up_ge_10pct")
    return {"nuts1":code,"source_coverage":src_cov,
            "nuts_coverage":ref_cov,"runner_up_share":share,
            "status":reason,"eligible":ok}


def classify_pinned_originals(geo_raw:bytes,nuts_raw:bytes, *,
                              geo_sha=SOURCE_LFS_OID_SHA256,
                              nuts_sha=EUROSTAT_SHA256):
    """Validate both originals; return internal 14+2 source record mapping.

    Source identifiers are used only within temporary CAT3 storage; the
    public log is category totals and official Eurostat NUTS codes only.
    """
    inspect_geojson_bytes(geo_raw,expected_sha256=geo_sha,
                          expected_size=len(geo_raw))
    if len(geo_raw)!=SOURCE_LFS_SIZE and geo_sha==SOURCE_LFS_OID_SHA256:
        raise CrosswalkError("original geoBoundaries length mismatch")
    if len(nuts_raw)!=EUROSTAT_SIZE and nuts_sha==EUROSTAT_SHA256:
        raise CrosswalkError("original Eurostat original length mismatch")
    refs=_parse_eurostat(nuts_raw,expected_sha256=nuts_sha,
                         expected_size=len(nuts_raw))
    from shapely.geometry import shape
    from shapely.ops import transform
    from pyproj import Transformer
    tr=Transformer.from_crs(4326,3035,always_xy=True,
                            allow_ballpark=False,only_best=True)
    rawgeo=json.loads(geo_raw.decode("utf-8"))["features"]
    original=[(z["properties"]["shapeID"],
               transform(tr.transform,shape(z["geometry"]))) for z in rawgeo]
    external=[(z["code"],transform(tr.transform,shape(z["geometry"])))
              for z in refs]
    if (len(original)!=EXPECTED_FEATURES or len(external)!=len(EXPECTED_NUTS)
        or any(g.is_empty or not g.is_valid or
               not math.isfinite(g.area) or g.area<=0
               for _,g in original+external)):
        raise CrosswalkError("original independent projected polygon source invalid")
    accepted=[]
    blocked=[]
    all_best=[]
    for source_id,source_poly in original:
        intersections=[(code,float(source_poly.intersection(other).area),float(other.area))
                       for code,other in external]
        score=decide_best(intersections,float(source_poly.area))
        row={"source_shape_id":source_id,**score}
        all_best.append(score["nuts1"])
        if score["eligible"]:
            accepted.append(row)
        else:
            blocked.append(row)
    # No duplicate best code or missing region can pass as partial evidence.
    if (len(set(all_best))!=16 or set(all_best)!=EXPECTED_NUTS
        or len(accepted)!=ALLOWED_EXPECTED_COUNT
        or {x["nuts1"] for x in blocked}!=WITHHELD_CODES
        or {x["status"] for x in blocked}!={"ambiguous_runner_up_ge_10pct"}):
        raise CrosswalkError("real original 14-supported/2-withheld review set changed")
    return accepted,blocked


def aggregate_receipt(accepted,blocked):
    if (len(accepted)!=ALLOWED_EXPECTED_COUNT
        or len(blocked)!=len(WITHHELD_CODES)
        or {x["nuts1"] for x in blocked}!=WITHHELD_CODES):
        raise CrosswalkError("unsupported partial sample")
    return {
        "schema_version":CAT3_SCHEMA,
        "original_geoboundaries_sha256":SOURCE_LFS_OID_SHA256,
        "original_eurostat_nuts2021_sha256":EUROSTAT_SHA256,
        "nuts_vintage":"2021",
        "eurostat_cartographic_scale":"20M_simplified",
        "area_crs":"EPSG3035",
        "original_de_admin1_states":16,
        "polygon_supported_provisional_count":len(accepted),
        "polygon_supported_provisional_nuts_codes":sorted(x["nuts1"] for x in accepted),
        "withheld_count":len(blocked),
        "withheld_diagnostic":sorted([
            {"nuts1_code":x["nuts1"],"reason":x["status"],
             "source_coverage_rounded":round(x["source_coverage"],6),
             "nuts_coverage_rounded":round(x["nuts_coverage"],6),
             "runner_up_share_rounded":round(x["runner_up_share"],6)}
            for x in blocked],key=lambda x:x["nuts1_code"]),
        "all_16_crosswalk_admitted":False,
        "withheld_berlin_and_bremen_automatically_joinable":False,
        "source_family_independence_implies_legal_boundary_equivalence":False,
        "nuts2016_eubucco_relation_proven":False,
        "building_or_insurer_records_joined":False,
        "source_geometry_or_provider_shape_ids_emitted":False,
        "insurance_model_input_admitted":False,
        "warning":(
          "Only 14/16 preliminary area-supported 2021 NUTS1 relationships; "
          "DE3 Berlin and DE5 Bremen overlap competitor NUTS polygons too much "
          "under the unchanged strict 10-percent criterion. All 16 CAT2 "
          "matching remains blocked. NUTS geometries are cartographic 20M "
          "generalizations, not official border-survey precision or EUBUCCO "
          "NUTS2016 relations. Local CAT3 research staging is not production."
        ),
    }


def build_cat3(accepted,blocked,destination:Path):
    """Create isolated, non-overwriting CAT3 staging with hard withheld rows."""
    if (len(accepted)!=14 or len(blocked)!=2
        or {x["nuts1"] for x in blocked}!=WITHHELD_CODES
        or len({x["source_shape_id"] for x in accepted+blocked})!=16
        or len({x["nuts1"] for x in accepted+blocked})!=16):
        raise CrosswalkError("CAT3 must contain exactly 14 supported plus 2 withheld")
    output=_check_destination(destination)
    fd,tmp=tempfile.mkstemp(prefix=".cat3-independent-",
                             suffix=".sqlite",dir=output.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(tmp)) as db:
            db.execute(f"PRAGMA application_id={CAT3_ID}")
            db.execute("PRAGMA user_version=1")
            db.executescript("""
            CREATE TABLE source_provenance(
              schema_id TEXT NOT NULL,
              gb_sha256 TEXT NOT NULL,
              nuts_sha256 TEXT NOT NULL,
              nuts_vintage INTEGER NOT NULL CHECK(nuts_vintage=2021),
              total_source_regions INTEGER NOT NULL CHECK(total_source_regions=16),
              accepted INTEGER NOT NULL CHECK(accepted=14),
              withheld INTEGER NOT NULL CHECK(withheld=2),
              model_input_approved INTEGER NOT NULL CHECK(model_input_approved=0)
            );
            CREATE TABLE provisional_region(
              source_shape_id TEXT PRIMARY KEY,
              nuts1_code TEXT NOT NULL UNIQUE,
              status TEXT NOT NULL CHECK(status='polygon_supported_research_only'),
              src_overlap_fraction REAL NOT NULL CHECK(src_overlap_fraction>=0.75),
              ref_overlap_fraction REAL NOT NULL CHECK(ref_overlap_fraction>=0.75)
            );
            CREATE TABLE withheld_region(
              source_shape_id TEXT PRIMARY KEY,
              best_nuts1_code TEXT NOT NULL UNIQUE CHECK(best_nuts1_code IN ('DE3','DE5')),
              reason TEXT NOT NULL CHECK(reason='ambiguous_runner_up_ge_10pct')
            );
            """)
            with db:
                db.execute("INSERT INTO source_provenance VALUES (?,?,?,?,16,14,2,0)",
                    (CAT3_SCHEMA,SOURCE_LFS_OID_SHA256,EUROSTAT_SHA256,2021))
                db.executemany("INSERT INTO provisional_region VALUES (?,?,?,?,?)",[
                    (x["source_shape_id"],x["nuts1"],"polygon_supported_research_only",
                     x["source_coverage"],x["nuts_coverage"]) for x in accepted])
                db.executemany("INSERT INTO withheld_region VALUES (?,?,?)",[
                    (x["source_shape_id"],x["nuts1"],x["status"]) for x in blocked])
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise CrosswalkError("CAT3 integrity check failed")
        os.link(tmp,output)
    finally:
        Path(tmp).unlink(missing_ok=True)


def resolve_cat3_point(cat1_path:Path,cat3_path:Path,lon:float,lat:float):
    """Research-only exact CAT1 point -> 14-provisional or 2-blocked status."""
    from urllib.parse import quote
    with closing(open_cat_index(cat1_path)) as gb:
        source=lookup_admin1(gb,lon,lat)
    if source is None:
        return None
    cat3=Path(cat3_path)
    if not cat3.is_file() or cat3.is_symlink():
        raise CrosswalkError("missing or unsafe isolated CAT3 research database")
    uri="file:"+quote(str(cat3.resolve()),safe="/")+"?mode=ro"
    with closing(sqlite3.connect(uri,uri=True)) as conn:
        if (conn.execute("PRAGMA application_id").fetchone()[0]!=CAT3_ID
            or conn.execute("PRAGMA user_version").fetchone()[0]!=1):
            raise CrosswalkError("foreign CAT3 version")
        if conn.execute("SELECT * FROM source_provenance").fetchall()!=[
            (CAT3_SCHEMA,SOURCE_LFS_OID_SHA256,EUROSTAT_SHA256,2021,16,14,2,0)
        ]:
            raise CrosswalkError("CAT3 original sources or model admission changed")
        if (conn.execute("SELECT count(*) FROM provisional_region").fetchone()[0]!=14
            or conn.execute("SELECT count(*) FROM withheld_region").fetchone()[0]!=2):
            raise CrosswalkError("CAT3 14/2 cohort corrupted")
        found=conn.execute("SELECT nuts1_code FROM provisional_region WHERE source_shape_id=?",
                           (source["shape_id"],)).fetchone()
        held=conn.execute("SELECT best_nuts1_code FROM withheld_region WHERE source_shape_id=?",
                          (source["shape_id"],)).fetchone()
        if bool(found)==bool(held):
            raise CrosswalkError("source region neither exclusively provisional nor withheld")
    return {
        "status":("provisional_polygon_supported_not_model_admitted"
                  if found else "blocked_independent_geometry_review"),
        "candidate_nuts2021_code":found[0] if found else None,
        "withheld_nuts2021_best_code":held[0] if held else None,
        "point_source_year":2021,
        "official_boundary_equivalence_verified":False,
        "insurance_model_input_admitted":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gb-original",required=True,type=Path)
    p.add_argument("--nuts2021-original",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args(argv)
    try:
        if (any(not z.is_file() or z.is_symlink() for z in
                (a.gb_original,a.nuts2021_original))
            or a.gb_original.stat().st_size!=SOURCE_LFS_SIZE
            or a.nuts2021_original.stat().st_size!=EUROSTAT_SIZE):
            raise CrosswalkError("source original sizes, symlinks or paths rejected")
        accepted,blocked=classify_pinned_originals(
            a.gb_original.read_bytes(),a.nuts2021_original.read_bytes())
        build_cat3(accepted,blocked,a.output)
        report=aggregate_receipt(accepted,blocked)
        report["isolated_cat3_research_sqlite_created"]=True
        report["source_bytes_or_original_shape_ids_exported"]=False
        print(json.dumps(report,sort_keys=True,indent=2,allow_nan=False))
        return 0
    except (CrosswalkError,OSError,sqlite3.Error,ValueError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
