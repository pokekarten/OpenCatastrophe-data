# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""All 64 Louisiana parish shapes from one SHA-pinned 2026 Census ZIP.

No external fetch, GIS repair, reproject, database write or model-data
admission. Assesses exact source-level ring validity and pairwise intersection,
not independent statewide coverage or completeness versus another source.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from research_runners.us_census_2026_county_zip_audit_v0 import (
    CensusZipError, MAX_ZIP_BYTES, STEM, audit_original_zip,
)
from research_runners.us_census_2026_parish_spatial_pilot_v0 import (
    PINNED_ORIGINAL_SHA256, OVERLAP_THRESHOLD_SQDEG, PilotGeometryError,
    _column_schema, _reconstruct_shape,
)

EXPECTED_LA_PARISHES = 64
LA_STATEFP = b"22"


class Louisiana64Error(ValueError):
    pass


def _la_positions(dbf):
    head,record_bytes,records,fields = _column_schema(dbf)
    if "STATEFP" not in fields or "GEOID" not in fields:
        raise Louisiana64Error("required original state and parish IDs missing")
    s_pos,s_width=fields["STATEFP"]
    id_pos,id_width=fields["GEOID"]
    matches={}
    for idx in range(records):
        row=dbf[head+idx*record_bytes:head+(idx+1)*record_bytes]
        state=row[s_pos:s_pos+s_width].strip(b" ")
        geoid=row[id_pos:id_pos+id_width].strip(b" ")
        if state != LA_STATEFP:
            continue
        if not re.fullmatch(rb"22[0-9]{3}",geoid) or geoid in matches:
            raise Louisiana64Error("duplicate/malformed Louisiana original GEOID")
        matches[geoid.decode("ascii")]=idx
    if len(matches)!=EXPECTED_LA_PARISHES:
        raise Louisiana64Error("not exactly 64 Louisiana parishes in original source")
    if not {"22051","22071","22087"}.issubset(matches):
        raise Louisiana64Error("known New Orleans parishes missing")
    return matches


def inspect_all_louisiana(raw, *, expected_sha256=PINNED_ORIGINAL_SHA256):
    identity=audit_original_zip(raw,independently_pinned_sha256=expected_sha256)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        dbf=archive.read(f"{STEM}.dbf")
        shx=archive.read(f"{STEM}.shx")
        shp=archive.read(f"{STEM}.shp")
    matches=_la_positions(dbf)
    shapes={}
    stats={}
    for geoid,ordinal in sorted(matches.items()):
        try:
            geom,summary=_reconstruct_shape(shp,shx,ordinal)
        except PilotGeometryError as exc:
            raise Louisiana64Error(f"original source parish {geoid} fails geometry QC: {exc}") from exc
        shapes[geoid]=geom
        stats[geoid]=summary
    # Pairwise geometries only; shared boundaries are allowed, overlapping
    # interiors above the diagnostic threshold must be reported and blocked.
    overlaps=0
    for i,left in enumerate(sorted(shapes)):
        for right in sorted(shapes)[i+1:]:
            a,b=shapes[left],shapes[right]
            if not a.intersects(b):
                continue
            overlap=float(a.intersection(b).area)
            if overlap>OVERLAP_THRESHOLD_SQDEG:
                raise Louisiana64Error(
                    f"material overlap between source parishes {left} and {right}")
            if overlap>0:
                overlaps+=1
    return {
        "profile":"OC_CENSUS_2026_LA_ALL_64_PARISH_SOURCE_QC_V0",
        "original_source_sha256":identity["source_zip_sha256_observed"],
        "source_sha256_matches_pinned_independent_receipt":
            identity["sha256_matched_independent_pin"],
        "original_us_county_equivalents":identity["dbf_feature_count"],
        "louisiana_state_fips":"22",
        "exact_original_parish_geoid_count":len(matches),
        "geometry_valid_original_parish_count":len(shapes),
        "nonempty_source_shell_count":sum(x["outer_shells"] for x in stats.values()),
        "source_interior_hole_count":sum(x["interior_holes"] for x in stats.values()),
        "original_polygon_coordinate_count":sum(
            x["original_coordinate_count"] for x in stats.values()),
        "source_parish_pairs_checked":len(shapes)*(len(shapes)-1)//2,
        "subthreshold_intersection_pairs":overlaps,
        "material_source_parish_overlap":False,
        "source_level_la_64_geometry_qc_pass":True,
        "independent_state_boundary_completeness_verified":False,
        "historical_parish_boundary_mapping_verified":False,
        "insured_assets_or_policy_terms_present":False,
        "original_geometry_persisted":False,
        "scientifically_admitted_cat_region_layer":False,
        "model_input_admitted":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",type=Path,required=True)
    args=p.parse_args(argv)
    file=args.source_zip
    if file.is_symlink() or not file.is_file() or file.stat().st_size>MAX_ZIP_BYTES:
        raise Louisiana64Error("expected bounded original non-symlink Census ZIP")
    print(json.dumps(inspect_all_louisiana(file.read_bytes()),sort_keys=True,indent=2))


if __name__=="__main__":
    try:
        main()
    except (OSError,CensusZipError,PilotGeometryError,Louisiana64Error) as exc:
        print("BLOCKED:",exc,file=sys.stderr)
        sys.exit(2)
