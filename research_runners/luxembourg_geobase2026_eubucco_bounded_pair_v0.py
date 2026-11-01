#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only, original-byte-pinned Luxembourg 2026 GeoBase / EUBUCCO comparison.

A third source-pair in the SAME fixed central-city 100m-square used by the
ACT2023↔GeoBase2026 pilot. Aggregate geometric candidate diagnostics ONLY.
ACT2013 lineage of EUBUCCO gov geometry and the 2026 ACT publisher family
mean this is NOT independent verification, building identity, or CAT exposure.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import tempfile

from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, inspect as inspect_geobase, sample as sample_geobase,
)
from research_runners.eubucco_lu00_lineage_preflight_v0 import (
    EubuccoPreflightError, inspect as inspect_eubucco,
)
from research_runners.luxembourg_act_eubucco_bounded_overlap_v0 import (
    OverlapPilotError, _export_eubucco,
)
from scripts.building_footprint_overlap_v0 import FootprintError, compare

GEOBASE_SHA = "ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676"
EUBUCCO_SHA = "d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c"
GEOBASE_LAYER = "Buildings_BU_Building"
GEOBASE_COUNT = 230353
EUBUCCO_COUNT = 186171
MAX_PER_SOURCE = 400


class CrosscheckError(ValueError):
    """Reject unsafe/unverified dataset, region, or source identity."""


def run(geobase: Path, eubucco: Path, *, lon: float = 6.1319,
        lat: float = 49.6116, halfwidth: float = 50.0,
        cap: int = MAX_PER_SOURCE, geobase_sha: str = GEOBASE_SHA,
        eubucco_sha: str = EUBUCCO_SHA,
        geobase_layer: str = GEOBASE_LAYER,
        geobase_id: str = "BU_BuildingID") -> dict:
    if not (all(isinstance(v, (float,int)) and math.isfinite(v)
                for v in (lon,lat,halfwidth))
            and 5.6 <= lon <= 6.7 and 49.2 <= lat <= 50.4
            and 20 <= halfwidth <= 125 and isinstance(cap,int)
            and 1 <= cap <= MAX_PER_SOURCE):
        raise CrosscheckError("window or sample exceeds Luxembourg research bounds")
    if geobase_sha != GEOBASE_SHA or eubucco_sha != EUBUCCO_SHA:
        raise CrosscheckError("only original previously observed full-source SHA pins supported")
    try:
        from pyproj import Transformer
        from shapely.geometry import box
    except ImportError as exc:
        raise CrosscheckError("reviewed PyProj/Shapely runtime required") from exc

    tf = Transformer.from_crs(4326,3035,always_xy=True)
    native = Transformer.from_crs(3035,2169,always_xy=True)
    cx,cy = tf.transform(lon,lat)
    extent = box(cx-halfwidth,cy-halfwidth,cx+halfwidth,cy+halfwidth)
    corners = [native.transform(x,y) for x,y in (
        (cx-halfwidth,cy-halfwidth),(cx+halfwidth,cy-halfwidth),
        (cx+halfwidth,cy+halfwidth),(cx-halfwidth,cy+halfwidth)
    )]
    bounds = (min(x for x,_ in corners),min(y for _,y in corners),
              max(x for x,_ in corners),max(y for _,y in corners))
    if not all(math.isfinite(x) for x in (*bounds,cx,cy)):
        raise CrosscheckError("transformed native bounding box invalid")

    try:
        meta, connection = inspect_geobase(geobase, expected_sha256=geobase_sha)
        try:
            layer = next((x for x in meta["layers"] if x["table"] == geobase_layer),None)
            if (layer is None or layer["feature_count"] != GEOBASE_COUNT
                    or layer["srs_id"] != 2169):
                raise CrosscheckError("2026 original source layer/count/CRS mismatch")
            other_meta = inspect_eubucco(eubucco, expected_sha256=eubucco_sha)
            if other_meta["total_buildings"] != EUBUCCO_COUNT:
                raise CrosscheckError("EUBUCCO original population drift")
            with tempfile.TemporaryDirectory(prefix="lu-2026-2013-lineage-research-") as tmp:
                f1,f2 = Path(tmp)/"geobase.geojson",Path(tmp)/"eubucco.geojson"
                n_geo = sample_geobase(
                    connection,layer,id_field=geobase_id,bbox=bounds,
                    limit=cap,output=f1,
                )
                n_ebu = _export_eubucco(eubucco,extent,f2,cap=cap)["sample_features"]
                cmp = compare(f1,f2,
                    left_crs="EPSG:2169",right_crs="EPSG:3035",
                    left_source="lu.act.bd-l-geobase-2026",
                    right_source="eubucco.buildings.v0.2",
                    min_iou=0.60,overlap_warning_fraction=0.20,
                    max_features=cap,
                )
        finally:
            connection.close()
    except (GeoPackageGateError,EubuccoPreflightError,OverlapPilotError,
            FootprintError) as exc:
        raise CrosscheckError("original source rejected: "+str(exc)) from exc
    counts = cmp["counts"]
    parts = (
        counts["high_iou_unique_matches"],
        counts["ambiguous_split_or_merge_left"],
        counts["single_candidate_below_iou"],
        counts["left_no_substantial_overlap"],
    )
    if sum(parts) != n_geo or counts["right_features"] != n_ebu:
        raise CrosscheckError("polygon classification/source population not conserved")
    return {
        "schema_version":"lu-geobase2026-eubucco-v0.2-original-pair-v0",
        "original_receipts":{
            "geobase2026_gpkg_sha256":geobase_sha,
            "eubucco_v0_2_parquet_sha256":eubucco_sha,
        },
        "region":"fixed Luxembourg-city CRS3035 100m square when default parameters used",
        "halfwidth_metres":halfwidth,
        "original_pair_features":{
            "geobase2026":n_geo,
            "eubucco_v0_2":n_ebu,
        },
        "geobase2026_roof_unspecified_polygon_classification":{
            "unique_candidates_iou_gte_0_60":parts[0],
            "ambiguous_geobase_polygons":parts[1],
            "single_candidate_iou_lt_0_60":parts[2],
            "without_substantial_overlap":parts[3],
            "bbox_spatial_candidate_pairs_checked":counts["spatial_candidate_pairs_checked"],
            "unique_candidate_iou_median":cmp["matched_iou_median"],
        },
        "source_pair_independent_ground_truth":False,
        "eubucco_gov_luxembourg_original_act2013_family":True,
        "geobase2026_act_source_family":True,
        "certified_2169_coordinate_order":False,
        "historical_building_identity_crosswalk_verified":False,
        "change_or_demolition_inferred":False,
        "raw_geometries_or_building_ids_exported":False,
        "commercial_rights_and_scientific_admission_approved":False,
        "model_input_admitted":False,
        "warning":(
            "Original ACT2026 and EUBUCCO gov-luxembourg ACT2013 share upstream "
            "publisher-family lineage; cross-vintage shape overlap does not "
            "demonstrate independent ground truth, equal building ID namespaces, "
            "construction/demolition, insured value, legal reuse or CAT admission."
        ),
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--geobase-gpkg",required=True,type=Path)
    p.add_argument("--eubucco-lu00",required=True,type=Path)
    a=p.parse_args(argv)
    try:
        result=run(a.geobase_gpkg,a.eubucco_lu00)
    except (CrosscheckError,OSError) as exc:
        p.exit(2,"BLOCKED: "+str(exc)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
