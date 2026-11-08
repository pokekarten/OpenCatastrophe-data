#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only BKG-original historical municipality geometry audit, 2018 vs 2022.

Four Thüringen 2018 Gemeinde source polygons are compared with their official
county targets' 2018-to-2022 newly added land. This uses BKG-only source
geometry and independently documents its attribution, with NO GADM material,
insurer asset locations, transferable GFA or CAT-model admission.

Requires original BKG ZIPs provided offline, plus optional pyshp/shapely/pyproj
for the original polygon execution. Pure numeric tests need only stdlib.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import zipfile

BKG_2018_URL = (
    "https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2018/"
    "vg250_12-31.gk3.shape.ebenen.zip"
)
BKG_2022_URL = (
    "https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/"
    "vg250_12-31.gk3.shape.ebenen.zip"
)
BKG_2018_SHA256 = "481d33de5c133fa55bcdc9f2964c48b2f5c21682acd3ec0885ec6d88bc2e75e7"
BKG_2022_SHA256 = "dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de"
BKG_2018_DATE = "2018-12-31"
BKG_2022_DATE = "2022-12-31"
AREA_CRS = "EPSG:3035"
ORIGINAL_CRS_CODE = 31467
CASES = {
    "Suhl": {
        "recipient_ags": "16054",
        "donor_ags": "16070",
        "former_municipalities": {
            "16070017": "Gehlberg",
            "16070046": "Schmiedefeld am Rennsteig",
        },
    },
    "Sonneberg": {
        "recipient_ags": "16072",
        "donor_ags": "16073",
        "former_municipalities": {
            "16073049": "Lichte",
            "16073066": "Piesau",
        },
    },
}


class BKGTransferError(ValueError):
    """Fail-closed source version, geometry or temporal transfer evidence."""


def polygon_transfer_summary(
    former_area_m2: float,
    recipient_new_area_m2: float,
    former_intersection_recipient_new_m2: float,
    donor_lost_area_m2: float,
    former_intersection_donor_lost_m2: float,
    former_intersection_recipient_2022_m2: float,
) -> dict:
    """Quantify independently measured area overlap; never infer GFA/TIV.

    The gain and lost regions are differences of official source polygons.
    They are not the old municipality polygons, and intersections are not
    assumed equal. Keep both area-denominator directions visible.
    """
    vals = (
        former_area_m2,
        recipient_new_area_m2,
        former_intersection_recipient_new_m2,
        donor_lost_area_m2,
        former_intersection_donor_lost_m2,
        former_intersection_recipient_2022_m2,
    )
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in vals):
        raise BKGTransferError("non-finite or nonnumeric official area")
    if any(v <= 0 for v in (former_area_m2, recipient_new_area_m2, donor_lost_area_m2)):
        raise BKGTransferError("empty original BKG geometry or no transfer region")
    if any(v < 0 for v in (former_intersection_recipient_new_m2,
                            former_intersection_donor_lost_m2,
                            former_intersection_recipient_2022_m2)):
        raise BKGTransferError("negative original source intersection")
    checks = (
        (former_intersection_recipient_new_m2, former_area_m2),
        (former_intersection_recipient_new_m2, recipient_new_area_m2),
        (former_intersection_donor_lost_m2, former_area_m2),
        (former_intersection_donor_lost_m2, donor_lost_area_m2),
        (former_intersection_recipient_2022_m2, former_area_m2),
    )
    if any(over > maximum * (1 + 1e-8) for over, maximum in checks):
        raise BKGTransferError("source municipality overlap cannot exceed total area")
    union = former_area_m2 + recipient_new_area_m2 - former_intersection_recipient_new_m2
    if union <= 0:
        raise BKGTransferError("invalid official polygon union")
    return {
        "bkg_2018_former_municipality_union_km2": former_area_m2 / 1e6,
        "bkg_2018_to_2022_recipient_new_area_km2": recipient_new_area_m2 / 1e6,
        "bkg_2018_to_2022_donor_lost_area_km2": donor_lost_area_m2 / 1e6,
        "former_municipality_intersection_recipient_new_km2":
            former_intersection_recipient_new_m2 / 1e6,
        "former_municipality_intersection_donor_lost_km2":
            former_intersection_donor_lost_m2 / 1e6,
        "former_municipality_intersection_recipient_2022_km2":
            former_intersection_recipient_2022_m2 / 1e6,
        "portion_of_recipient_gain_covered_by_old_municipalities":
            min(former_intersection_recipient_new_m2 / recipient_new_area_m2, 1.0),
        "portion_of_old_municipalities_in_new_recipient_gain":
            min(former_intersection_recipient_new_m2 / former_area_m2, 1.0),
        "portion_of_old_municipalities_in_recipient_2022":
            min(former_intersection_recipient_2022_m2 / former_area_m2, 1.0),
        "former_municipality_vs_recipient_gain_iou":
            former_intersection_recipient_new_m2 / union,
        "official_2018_and_2022_source_geometry_overlaps_measured": True,
        "exact_equality_of_2018_and_2022_polygons_proven": False,
        "gadm4_1_or_materialcities_join_approved": False,
        "real_insurer_exposure_locations_proven": False,
        "transfer_of_region_level_building_gfa_authorized": False,
        "carrier_tiv_or_insured_replacement_value_inferred": False,
        "cat_model_input_admitted": False,
        "research_only": True,
    }


def _source_zip(blob: bytes, expected_sha: str, edition: str) -> zipfile.ZipFile:
    if not isinstance(blob, bytes) or not 40_000_000 <= len(blob) <= 80_000_000:
        raise BKGTransferError("original BKG ZIP size outside reviewed archive bounds")
    if hashlib.sha256(blob).hexdigest() != expected_sha:
        raise BKGTransferError(f"original BKG {edition} SHA256 mismatch")
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
        entries = z.infolist()
        if not entries or len(entries) > 160:
            raise BKGTransferError("unexpected original BKG member inventory")
        seen = set()
        for entry in entries:
            name = entry.filename
            if (name in seen or name.startswith("/") or "\\" in name or
                    ".." in PurePosixPath(name).parts or
                    entry.flag_bits & 1 or entry.file_size > 45_000_000):
                raise BKGTransferError("unsafe original BKG source ZIP member")
            seen.add(name)
        return z
    except (OSError, zipfile.BadZipFile) as exc:
        raise BKGTransferError("original BKG source ZIP unreadable") from exc


def _spatial_imports():
    try:
        import shapefile
        from shapely.geometry import shape
        from shapely.ops import transform, unary_union
        from pyproj import CRS, Transformer
    except ImportError as exc:
        raise BKGTransferError(
            "original geometry audit requires optional pyshp, shapely and pyproj"
        ) from exc
    return shapefile, shape, transform, unary_union, CRS, Transformer


def _layer_reader(z: zipfile.ZipFile, layer: str, modules):
    shapefile, shape, transform, unary_union, CRS, Transformer = modules
    paths = z.namelist()
    roots = [s[:-4] for s in paths if s.endswith("/VG250_" + layer + ".shp")]
    if len(roots) != 1:
        raise BKGTransferError("expected exactly one BKG original layer")
    root = roots[0]
    if any(root + suffix not in paths for suffix in (".shp", ".shx", ".dbf", ".prj")):
        raise BKGTransferError("BKG layer missing source geometry components")
    wkt = z.read(root + ".prj").decode("utf-8-sig")
    source = CRS.from_wkt(wkt)
    # ESRI WKT source writes authority EPSG:31467; modern PROJ can identify
    # equivalent projected axis variant EPSG:5677 instead.
    if ('AUTHORITY["EPSG",31467]' not in wkt or
            source.to_epsg() not in (ORIGINAL_CRS_CODE, 5677)):
        raise BKGTransferError("BKG original Gauss-Kruger source CRS changed")
    reproj = Transformer.from_crs(source, CRS.from_string(AREA_CRS), always_xy=True).transform
    reader = shapefile.Reader(
        shp=io.BytesIO(z.read(root + ".shp")),
        shx=io.BytesIO(z.read(root + ".shx")),
        dbf=io.BytesIO(z.read(root + ".dbf")),
        encoding="utf-8",
    )
    return reader, reproj


def _require_land_geom(geo, tag: str):
    if geo.is_empty or not geo.is_valid or geo.area <= 0:
        raise BKGTransferError(f"invalid original projected BKG {tag} polygon")
    return geo


def inspect_original_bkg_municipal_transfers(
    zip2018: bytes, zip2022: bytes,
) -> dict:
    """Independent same-provider official 2018 GEM + 2018/2022 KRS geometry."""
    spatial = _spatial_imports()
    shapefile, shape, transform, unary_union, CRS, Transformer = spatial
    desired_municipalities = {
        code: name
        for case in CASES.values()
        for code, name in case["former_municipalities"].items()
    }
    interested_counties = {
        code for case in CASES.values()
        for code in (case["recipient_ags"], case["donor_ags"])
    }
    with _source_zip(zip2018, BKG_2018_SHA256, "2018") as z:
        gem_reader, proj_gem = _layer_reader(z, "GEM", spatial)
        members = {}
        # Scan only the original DBF records, then load exactly four
        # original municipality shapes by their fixed source row indices.
        for index, row in enumerate(gem_reader.iterRecords()):
            meta = row.as_dict()
            ags = meta.get("AGS")
            if ags not in desired_municipalities:
                continue
            if (ags in members or meta.get("GEN") != desired_municipalities[ags]
                    or type(meta.get("GF")) is not int or meta.get("GF") != 4):
                raise BKGTransferError("unreviewed 2018 old municipality source key/name/GF")
            geom = transform(proj_gem, shape(gem_reader.shape(index).__geo_interface__))
            members[ags] = _require_land_geom(geom, "2018 municipality")
        if set(members) != set(desired_municipalities):
            raise BKGTransferError("2018 original source missing former municipalities")
        krs2018, proj_krs18 = _layer_reader(z, "KRS", spatial)
        c2018 = {}
        for i, record in enumerate(krs2018.iterRecords()):
            meta = record.as_dict()
            key = meta.get("AGS")
            if key not in interested_counties or meta.get("GF") != 4:
                continue
            if key in c2018:
                raise BKGTransferError("2018 original source duplicate GF4 Kreis")
            c2018[key] = _require_land_geom(
                transform(proj_krs18, shape(krs2018.shape(i).__geo_interface__)),
                "2018 Kreis",
            )
    with _source_zip(zip2022, BKG_2022_SHA256, "2022") as z:
        krs2022, proj_krs22 = _layer_reader(z, "KRS", spatial)
        c2022 = {}
        for i, record in enumerate(krs2022.iterRecords()):
            meta = record.as_dict()
            key = meta.get("AGS")
            if key not in interested_counties or meta.get("GF") != 4:
                continue
            if key in c2022:
                raise BKGTransferError("2022 original source duplicate GF4 Kreis")
            c2022[key] = _require_land_geom(
                transform(proj_krs22, shape(krs2022.shape(i).__geo_interface__)),
                "2022 Kreis",
            )
    if set(c2018) != interested_counties or set(c2022) != interested_counties:
        raise BKGTransferError("2018/2022 original four-Kreis evidence incomplete")
    output = {}
    for case_name, case in CASES.items():
        former = unary_union([members[key] for key in case["former_municipalities"]])
        recipient = case["recipient_ags"]
        donor = case["donor_ags"]
        recipient_new = c2022[recipient].difference(c2018[recipient])
        donor_lost = c2018[donor].difference(c2022[donor])
        for name, geom in (("former municipality union", former),
                           ("recipient new land", recipient_new),
                           ("donor lost land", donor_lost)):
            _require_land_geom(geom, name)
        # Fail if identities do not resemble an actual historic transfer;
        # the percentage is diagnostic, not a commercial admission criterion.
        for former_key in case["former_municipalities"]:
            if members[former_key].intersection(c2018[donor]).area < .90 * members[former_key].area:
                raise BKGTransferError("former municipality not in official 2018 donor")
        metrics = polygon_transfer_summary(
            former.area,
            recipient_new.area,
            former.intersection(recipient_new).area,
            donor_lost.area,
            former.intersection(donor_lost).area,
            former.intersection(c2022[recipient]).area,
        )
        metrics.update({
            "recipient_ags": recipient,
            "donor_ags": donor,
            "former_2018_municipality_ags": list(case["former_municipalities"]),
            "former_2018_municipalities_verified_from_BKG_GEM": len(case["former_municipalities"]),
        })
        output[case_name] = metrics
    return {
        "source": "BKG VG250 2018/2022 official GK3 shapefile",
        "source_attribution": "© BKG (2018 und 2022) dl-de/by-2-0 (Daten verändert); Datenquellen: BKG VG250",
        "original_zip_sha256_2018": hashlib.sha256(zip2018).hexdigest(),
        "original_zip_sha256_2022": hashlib.sha256(zip2022).hexdigest(),
        "bkg_2018_edition": BKG_2018_DATE,
        "bkg_2022_edition": BKG_2022_DATE,
        "source_2018_former_GEM_found": len(members),
        "source_gf4_counties_2018": len(c2018),
        "source_gf4_counties_2022": len(c2022),
        "equal_area_crs": AREA_CRS,
        "source_polygon_transfer_cases": output,
        "independent_official_BKG_years_compared": True,
        "gadm_or_materialcities_geometries_required": False,
        "municipality_geometry_2022_hazard_or_insurer_unit_admitted": False,
        "exact_2019_effective_date_derived_from_polygon_geometry": False,
        "real_RV_sites_or_TIV_inferred": False,
        "cat_model_input_admitted": False,
        "research_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bkg-2018-zip", type=Path, required=True)
    parser.add_argument("--bkg-2022-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise BKGTransferError("refuse to overwrite existing source research receipt")
        result = inspect_original_bkg_municipal_transfers(
            args.bkg_2018_zip.read_bytes(), args.bkg_2022_zip.read_bytes())
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print("PASS: two BKG-original municipality polygon transfers; "
          "NO building or insurer source admission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
