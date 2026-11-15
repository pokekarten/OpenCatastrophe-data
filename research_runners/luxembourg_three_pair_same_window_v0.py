#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Combine THREE independently computed aggregate research original-source pairs.

Only accepts known schema reports with frozen 2023/2026/EUBUCCO source SHA,
one identical 100-m central-Luxembourg window, and consistent source counts.
No source-row join, coordinates, matching IDs, geometries, or model admission.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ACT_SHA="9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf"
GEO_SHA="ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676"
EBU_SHA="d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c"
EXPECTED_WINDOW_HALFWIDTH=50.0
MAX_REPORT_BYTES=64*1024
EXPECTED_KEYS=("act_eubucco","act_geobase","geobase_eubucco")


class TriangulationError(ValueError):
    """Unmatched source receipt, window, population, or scientific admission flag."""


def _nonnegative(value,label):
    if type(value) is not int or value < 0 or value > 500:
        raise TriangulationError("invalid bounded count: "+label)
    return value


def _exact_keys(a,b,expected,label):
    if a != b or a != expected:
        raise TriangulationError("original source receipt mismatch: "+label)


def _window(value,label):
    if type(value) not in (int,float) or not math.isfinite(value) or value != EXPECTED_WINDOW_HALFWIDTH:
        raise TriangulationError("source-pair study window differs: "+label)


def _read(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_REPORT_BYTES:
        raise TriangulationError("only small regular local aggregate reports allowed")
    def unique_pairs(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise TriangulationError("duplicate source-report JSON key")
            result[key]=value
        return result
    def invalid_number(value):
        raise TriangulationError("NaN/infinite source-report number not accepted")
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=unique_pairs,
                          parse_constant=invalid_number)
    except (UnicodeError,json.JSONDecodeError,OSError) as exc:
        raise TriangulationError("invalid aggregate source report") from exc


def combine(act_ebu,act_geo,geo_ebu):
    if not all(type(x) is dict for x in (act_ebu,act_geo,geo_ebu)):
        raise TriangulationError("expected three aggregate report objects")
    if act_ebu.get("schema_version")!="lu-act-eubucco-bounded-original-roof-overlap-v0":
        raise TriangulationError("ACT-EUBUCCO schema mismatch")
    if act_geo.get("profile")!="lu-act2023-geobase2026-bounded-geometry-v0":
        raise TriangulationError("ACT-GeoBase schema mismatch")
    if geo_ebu.get("schema_version")!="lu-geobase2026-eubucco-v0.2-original-pair-v0":
        raise TriangulationError("GeoBase-EUBUCCO schema mismatch")

    _window(act_ebu["research_window"]["half_width_metres"],"act_eubucco")
    _window(act_geo["roi_halfwidth_metres"],"act_geobase")
    _window(geo_ebu["halfwidth_metres"],"geobase_eubucco")
    if (act_ebu["research_window"]["approximate_location"]
        != "central Luxembourg city / fixed research pilot"
        or act_geo["roi_type"]!="fixed 2D EPSG:3035 research window"
        or geo_ebu["region"]!="fixed Luxembourg-city CRS3035 100m square when default parameters used"):
        raise TriangulationError("noncanonical geographic reference")
    a=act_ebu["source_receipts"]
    b=act_geo["original_sha256"]
    c=geo_ebu["original_receipts"]
    _exact_keys(a["act_gpkg_sha256"],b["act2023"],ACT_SHA,"ACT")
    _exact_keys(b["geobase2026"],c["geobase2026_gpkg_sha256"],GEO_SHA,"GeoBase")
    _exact_keys(a["eubucco_parquet_sha256"],c["eubucco_v0_2_parquet_sha256"],EBU_SHA,"EUBUCCO")
    if (a["act_entire_source_count"]!=238189 or a["eubucco_entire_source_count"]!=186171):
        raise TriangulationError("original national source population drift")
    for obj,fields in (
        (act_ebu,("model_input_admitted","per_building_data_exported",
                  "insured_building_exposure_imported","eubucco_upstream_independence_proven")),
        (act_geo,("CAT_model_input_admitted","original_id_pairs_or_geometry_exported",
                  "independent_ground_truth_proven","insured_exposure_or_building_stock_change_inferred")),
        (geo_ebu,("model_input_admitted","raw_geometries_or_building_ids_exported",
                  "source_pair_independent_ground_truth","change_or_demolition_inferred")),
    ):
        if any(obj.get(f) is not False for f in fields):
            raise TriangulationError("scientific/source nonadmission flags changed")

    a1=act_ebu["original_local_sample"]
    b1=act_geo["source_counts"]
    c1=geo_ebu["original_pair_features"]
    act=_nonnegative(a1["act_roof_features"],"ACT")
    ebu=_nonnegative(a1["eubucco_footprint_features"],"EUBUCCO")
    geo=_nonnegative(b1["geobase_building_polygons"],"GeoBase")
    if (act != _nonnegative(b1["act_roof_polygons"],"ACT second")
        or ebu != _nonnegative(c1["eubucco_v0_2"],"EUBUCCO second")
        or geo != _nonnegative(c1["geobase2026"],"GeoBase second")
        or min(act,ebu,geo)==0):
        raise TriangulationError("same-window original source sample counts differ")

    c_ae=act_ebu["overlap_candidate_diagnostics"]
    c_ag=act_geo
    c_ge=geo_ebu["geobase2026_roof_unspecified_polygon_classification"]
    categories={
       "act2023_vs_eubucco":{
          "unique_high_iou":c_ae["matched_unique_at_iou_0_60"],
          "ambiguous_first_source":c_ae["ambiguous_split_or_merge_roofs"],
          "weak_unique":c_ae["low_iou_unique"],
          "no_substantial_overlap":c_ae["no_substantial_overlap_roofs"],
          "first_source_count":act,
          "second_source_count":ebu,
          "candidate_pairs":c_ae["candidate_pairs_checked"],
       },
       "act2023_vs_geobase2026":{
          "unique_high_iou":c_ag["iou_0_60_unique_candidates"],
          "ambiguous_first_source":c_ag["ambiguous_roof_polygons"],
          "weak_unique":c_ag["weak_unique_roof_polygons"],
          "no_substantial_overlap":c_ag["no_substantial_overlap_roofs"],
          "first_source_count":act,
          "second_source_count":geo,
          "candidate_pairs":c_ag["spatial_candidate_pairs_checked"],
       },
       "geobase2026_vs_eubucco":{
          "unique_high_iou":c_ge["unique_candidates_iou_gte_0_60"],
          "ambiguous_first_source":c_ge["ambiguous_geobase_polygons"],
          "weak_unique":c_ge["single_candidate_iou_lt_0_60"],
          "no_substantial_overlap":c_ge["without_substantial_overlap"],
          "first_source_count":geo,
          "second_source_count":ebu,
          "candidate_pairs":c_ge["bbox_spatial_candidate_pairs_checked"],
       },
    }
    for name,counts in categories.items():
        for field,value in counts.items():
            _nonnegative(value,name+"."+field)
        if sum(counts[f] for f in ("unique_high_iou","ambiguous_first_source",
               "weak_unique","no_substantial_overlap")) != counts["first_source_count"]:
            raise TriangulationError("first-source classification does not conserve count")
    return {
        "schema_version":"lu-three-original-pairs-same-window-aggregate-reconciliation-v0",
        "window":"same frozen central-Luxembourg 100m x 100m area",
        "halfwidth_metres":EXPECTED_WINDOW_HALFWIDTH,
        "original_source_sha256":{
            "act2023":ACT_SHA,"geobase2026":GEO_SHA,"eubucco_v0_2":EBU_SHA,
        },
        "unique_source_polygon_counts":{
            "act2023_roofs":act,"geobase2026_buildings":geo,
            "eubucco_v0_2_footprints":ebu,
        },
        "pairwise_aggregate_candidate_diagnostics":categories,
        "cross_pair_transitivity_or_same_physical_building_proven":False,
        "independent_ground_truth_proven":False,
        "manual_precision_recall_measured":False,
        "triple_source_per_building_match_generated":False,
        "real_insurance_exposure_imported":False,
        "original_geometry_or_building_id_exported":False,
        "cat_model_input_admitted":False,
        "warning":(
            "Same area makes aggregate counts comparable, NOT transitive matches; "
            "three pairwise IoU>0.60 overlaps do not establish a common building, "
            "independent validation or changes in building stock. Source-vintage, "
            "segmentation, roof-versus-ground and ACT source-family dependence persist."
        ),
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for key in EXPECTED_KEYS:
        parser.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        result=combine(_read(args.act_eubucco),_read(args.act_geobase),
                       _read(args.geobase_eubucco))
    except (TriangulationError,KeyError,TypeError,IndexError) as exc:
        parser.exit(2,"BLOCKED: inconsistent aggregate source pair: "+str(exc)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
