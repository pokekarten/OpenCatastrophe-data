#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-byte BKG/GADM/MaterialCities/Destatis German district CODE preflight.

This checks administrative code coverage; it DOES NOT prove geometry, temporal
equivalence, area weights, insurer geography or commercial source rights.
Original provider files and 402-row derived crosswalks must stay OUTSIDE Git.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import tomllib
import zipfile

BKG_URL = "https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/vg250_12-31.gk3.shape.ebenen.zip"
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_DEU_2.json.zip"
MATERIALCITIES_URL = "https://zenodo.org/records/22306604"
BKG_SHA256 = "dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de"
GADM_SHA256 = "add290173fedaca349d9bd312523d63bf7f9ef9389d473a78e1ce530c3450d7a"
MATERIALCITIES_SHA256 = "ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38"
CENSUS_ORIGINAL_XLSX_SHA256 = "82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551"
BKG_KRS_DBF = "VG250_KRS.dbf"
GADM_JSON = "gadm41_DEU_2.json"
MC_ADM2_CSV = "MaterialCities_adm_gfa_ADM2.csv"
SOURCE_SIZE_CAPS = {"BKG": 75_000_000, "GADM": 3_000_000, "MaterialCities": 12_000_000}
EXPECTED_BKG_RECORDS = 430
EXPECTED_BKG_AGS = 400
EXPECTED_GADM_RECORDS = 403
EXPECTED_MATERIALCITIES_GIDS = 402
EXCEPTIONAL_OLD_TO_2022_AGS = {
    "03152": "03159",  # Old Göttingen, merged with Osterode as of 2016-11-01.
    "03156": "03159",  # Old Osterode am Harz, same 2016 merged county.
    "16056": "16063",  # Old Eisenach, in Wartburgkreis since 2021-07-01.
}
AGS_RE = re.compile(r"[0-9]{5}\Z")
GADM_GID_RE = re.compile(r"DEU\.\d{1,2}\.\d+_\d+\Z")


class CodeCrosswalkError(ValueError):
    """A source identity or administrative identity conclusion is unsafe."""


def _source_zip(data: bytes, label: str, expected_sha: str, *, exact_pin: bool) -> zipfile.ZipFile:
    if not isinstance(data, bytes) or not 0 < len(data) <= SOURCE_SIZE_CAPS[label]:
        raise CodeCrosswalkError(f"{label}: source archive exceeds expected bounds")
    if exact_pin and hashlib.sha256(data).hexdigest() != expected_sha:
        raise CodeCrosswalkError(f"{label}: exact original SHA256 changed")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        info = archive.infolist()
        if len(info) > 100 or not info:
            raise CodeCrosswalkError(f"{label}: unexpected ZIP inventory")
        seen = set()
        for entry in info:
            name = entry.filename
            if (name in seen or not name or name.startswith("/") or
                    ".." in PurePosixPath(name).parts or "\\" in name or
                    entry.flag_bits & 1 or entry.file_size > 45_000_000):
                raise CodeCrosswalkError(f"{label}: unsafe ZIP source member")
            seen.add(name)
        return archive
    except (OSError, zipfile.BadZipFile) as exc:
        raise CodeCrosswalkError(f"{label}: unreadable source ZIP") from exc


def _bkg_codes(dbf: bytes) -> tuple[list[str], int]:
    if not isinstance(dbf, bytes) or not 32 <= len(dbf) <= 1_000_000:
        raise CodeCrosswalkError("BKG: unbounded Kreis DBF bytes")
    count = struct.unpack_from("<I", dbf, 4)[0]
    header_length = struct.unpack_from("<H", dbf, 8)[0]
    row_length = struct.unpack_from("<H", dbf, 10)[0]
    if not 1 <= count <= 1000 or row_length <= 1 or header_length < 65:
        raise CodeCrosswalkError("BKG: invalid DBF header")
    if len(dbf) < header_length + count * row_length:
        raise CodeCrosswalkError("BKG: truncated DBF records")
    fields = {}
    offset = 1
    for pos in range(32, header_length - 1, 32):
        descriptor = dbf[pos:pos + 32]
        if len(descriptor) < 32 or descriptor[0] == 13:
            break
        name = descriptor[:11].split(b"\x00")[0].decode("ascii", "replace")
        length = descriptor[16]
        if name in fields or not length or offset + length > row_length:
            raise CodeCrosswalkError("BKG: duplicate or malformed field")
        fields[name] = (offset, length)
        offset += length
    if "AGS" not in fields or "GEN" not in fields or "BEGINN" not in fields:
        raise CodeCrosswalkError("BKG: no source AGS/name/edition field")
    codes = []
    for i in range(count):
        record = dbf[header_length + i * row_length:header_length + (i + 1) * row_length]
        if record[:1] == b"*":
            raise CodeCrosswalkError("BKG: deleted geometry record in original")
        pos, length = fields["AGS"]
        ags = record[pos:pos + length].decode("ascii", "replace").strip()
        if not AGS_RE.fullmatch(ags):
            raise CodeCrosswalkError("BKG: invalid source five-digit AGS")
        codes.append(ags)
    return codes, count


def _gadm_features(data: dict) -> list[dict]:
    if type(data) is not dict or data.get("type") != "FeatureCollection":
        raise CodeCrosswalkError("GADM: invalid GeoJSON feature collection")
    features = data.get("features")
    if type(features) is not list or not 1 <= len(features) <= 600:
        raise CodeCrosswalkError("GADM: unexpected record count")
    out = []
    for feature in features:
        p = feature.get("properties") if type(feature) is dict else None
        if type(p) is not dict or p.get("GID_0") != "DEU":
            raise CodeCrosswalkError("GADM: non-German or malformed level-2 feature")
        gid, code = p.get("GID_2"), p.get("CC_2")
        if type(gid) is not str or not GADM_GID_RE.fullmatch(gid):
            raise CodeCrosswalkError("GADM: invalid GID_2")
        if not isinstance(code, str) or not (AGS_RE.fullmatch(code) or code == "NA"):
            raise CodeCrosswalkError("GADM: unexpected AGS/CC2 source field")
        out.append({"gid": gid, "code": code})
    return out


def _materialcities_gids(csv_bytes: bytes) -> list[str]:
    if not isinstance(csv_bytes, bytes) or len(csv_bytes) > 20_000_000:
        raise CodeCrosswalkError("MaterialCities: unbounded CSV bytes")
    try:
        reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"), newline=""))
        head = reader.fieldnames
        if not head or len(head) != len(set(head)) or not {"GID_0", "GID_2", "GFA_NR_C"}.issubset(head):
            raise CodeCrosswalkError("MaterialCities: unexpected original ADM2 schema")
        gids = []
        for i, row in enumerate(reader):
            if i >= 50_000 or None in row:
                raise CodeCrosswalkError("MaterialCities: malformed/unbounded ADM2 row")
            if row.get("GID_0") == "DEU":
                gid = (row.get("GID_2") or "").strip()
                if not GADM_GID_RE.fullmatch(gid):
                    raise CodeCrosswalkError("MaterialCities: German source lacks GID_2")
                gids.append(gid)
        return gids
    except (UnicodeError, csv.Error) as exc:
        raise CodeCrosswalkError("MaterialCities: unreadable original CSV") from exc


def reconcile_codes(
    bkg_physical_ags: list[str], gadm_features: list[dict],
    materialcities_gids: list[str], zensus_ags: set[str],
    *, original_counts: bool,
) -> dict:
    """Fail-closed source-key analysis, *not* a geographic allocation."""
    if not bkg_physical_ags or not gadm_features or not materialcities_gids or not zensus_ags:
        raise CodeCrosswalkError("missing required independent source evidence")
    bkg = set(bkg_physical_ags)
    if any(not isinstance(x, str) or not AGS_RE.fullmatch(x) for x in bkg_physical_ags):
        raise CodeCrosswalkError("BKG AGS invalid")
    if bkg != zensus_ags:
        raise CodeCrosswalkError("BKG 2022 and original Zensus 2022 AGS rosters differ")
    ids = {row["gid"] for row in gadm_features}
    if len(ids) != len(gadm_features):
        raise CodeCrosswalkError("duplicate GADM ID")
    mc = set(materialcities_gids)
    if len(mc) != len(materialcities_gids) or not mc <= ids:
        raise CodeCrosswalkError("MaterialCities GID missing/duplicate relative to GADM")
    by_gid = {row["gid"]: row["code"] for row in gadm_features}
    excluded = [x for x in gadm_features if x["gid"] not in mc]
    if any(x["code"] != "NA" for x in excluded):
        raise CodeCrosswalkError("coded GADM feature absent from MaterialCities")
    if any(by_gid[gid] == "NA" for gid in mc):
        raise CodeCrosswalkError("MaterialCities contains unmappable GADM CC_2")
    codes = [by_gid[gid] for gid in mc]
    if len(set(codes)) != len(codes):
        raise CodeCrosswalkError("GADM CC_2 ambiguous across MaterialCities rows")
    direct = {code for code in codes if code in bkg}
    unexpected = set(codes) - bkg
    if unexpected - set(EXCEPTIONAL_OLD_TO_2022_AGS):
        raise CodeCrosswalkError("unreviewed historical AGS code not in BKG")
    mapped = [code if code in bkg else EXCEPTIONAL_OLD_TO_2022_AGS[code] for code in codes]
    if set(mapped) != bkg:
        raise CodeCrosswalkError("2022 AGS target coverage incomplete or invented")
    if any(target not in bkg for target in EXCEPTIONAL_OLD_TO_2022_AGS.values()):
        raise CodeCrosswalkError("historical AGS correction target absent")
    groups = Counter(mapped)
    if original_counts:
        if not (len(bkg_physical_ags) == EXPECTED_BKG_RECORDS and
                len(bkg) == EXPECTED_BKG_AGS and len(gadm_features) == EXPECTED_GADM_RECORDS and
                len(mc) == EXPECTED_MATERIALCITIES_GIDS and len(direct) == 399 and
                unexpected == set(EXCEPTIONAL_OLD_TO_2022_AGS) and
                len(excluded) == 1 and excluded[0] == {"gid": "DEU.1.5_1", "code": "NA"} and
                sorted(n for n in groups.values() if n > 1) == [2, 2] and
                set(groups) == bkg):
            raise CodeCrosswalkError("version-pinned German 2022/4.1 code scenario drift")
    return {
        "source_bkg_2022_shape_rows": len(bkg_physical_ags),
        "source_bkg_distinct_official_ags": len(bkg),
        "source_zensus_2022_distinct_official_ags": len(zensus_ags),
        "source_bkg_zensus_2022_ags_identity_exact": True,
        "source_gadm_4_1_features": len(gadm_features),
        "source_materialcities_2026_9_gadm_ids": len(mc),
        "gadm_features_excluded_by_materialcities": len(excluded),
        "gadm_valid_unique_cc2_exact_2022_ags_matches": len(direct),
        "historical_obsolete_ags_codes_needing_review": len(unexpected),
        "historical_code_candidates": dict(sorted((c, EXCEPTIONAL_OLD_TO_2022_AGS[c]) for c in unexpected)),
        "candidate_2022_ags_targets_reached_by_all_source_codes": len(groups),
        "multiple_historical_source_codes_to_2022_target_groups": sum(1 for n in groups.values() if n > 1),
        "same_ags_not_proof_same_polygons": True,
        "gadm_bkg_geometry_overlap_proven": False,
        "source_vintages_spatially_equivalent": False,
        "materialcities_to_official_ags_join_admitted": False,
        "source_commercial_rights_cleared": False,
        "original_provider_geometry_or_crosswalk_exported": False,
        "real_insurer_exposures_inferred": False,
        "research_only": True,
    }


def inspect_exact_sources(bkg_bytes: bytes, gadm_bytes: bytes, mc_bytes: bytes,
                          zensus_toml: bytes, *, exact_pin: bool = True,
                          original_counts: bool = True) -> dict:
    with _source_zip(bkg_bytes, "BKG", BKG_SHA256, exact_pin=exact_pin) as bkg_zip:
        names = [entry.filename for entry in bkg_zip.infolist() if entry.filename.endswith("/" + BKG_KRS_DBF)]
        if len(names) != 1:
            raise CodeCrosswalkError("BKG: expected VG250_KRS DBF absent/ambiguous")
        bkg_codes, _ = _bkg_codes(bkg_zip.read(names[0]))
    with _source_zip(gadm_bytes, "GADM", GADM_SHA256, exact_pin=exact_pin) as gadm_zip:
        if gadm_zip.namelist() != [GADM_JSON]:
            raise CodeCrosswalkError("GADM: source JSON member changed")
        try:
            gf = _gadm_features(json.loads(gadm_zip.read(GADM_JSON).decode("utf-8")))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CodeCrosswalkError("GADM: malformed original GeoJSON") from exc
    with _source_zip(mc_bytes, "MaterialCities", MATERIALCITIES_SHA256, exact_pin=exact_pin) as mc_zip:
        names = [entry.filename for entry in mc_zip.infolist() if entry.filename == MC_ADM2_CSV]
        if len(names) != 1:
            raise CodeCrosswalkError("MaterialCities: expected ADM2 CSV absent/ambiguous")
        gids = _materialcities_gids(mc_zip.read(MC_ADM2_CSV))
    try:
        census = tomllib.loads(zensus_toml.decode("utf-8"))
        if (census.get("schema_version") != "ZENSUS2022_400_KREIS_ORIGINAL_BUILDING_AGGREGATES_V0" or
                census.get("original_full_file_sha256") != CENSUS_ORIGINAL_XLSX_SHA256 or
                census.get("source_event_date") != "2022-05-15"):
            raise CodeCrosswalkError("Zensus: original source identity/vintage changed")
        census_ags = {x["ags"] for x in census["kreise"]}
        if len(census_ags) != len(census["kreise"]):
            raise CodeCrosswalkError("Zensus: duplicate source Kreis")
    except (UnicodeError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise CodeCrosswalkError("Zensus: malformed source observation") from exc
    result = reconcile_codes(bkg_codes, gf, gids, census_ags, original_counts=original_counts)
    result["original_sha256"] = {
        "bkg_vg250_2022_12_31": hashlib.sha256(bkg_bytes).hexdigest(),
        "gadm_4_1_deu_level2": hashlib.sha256(gadm_bytes).hexdigest(),
        "materialcities_2026_9": hashlib.sha256(mc_bytes).hexdigest(),
    }
    result["official_historical_sources"] = [
        "https://www.statistik.niedersachsen.de/presse/zahl-der-kreise-und-gemeinden-in-niedersachsen-geht-zurueck-148228.html",
        "https://statistik.thueringen.de/datenbank/gebiet1.asp?auswahl=krs",
    ]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bkg-zip", required=True, type=Path)
    parser.add_argument("--gadm-zip", required=True, type=Path)
    parser.add_argument("--materialcities-zip", required=True, type=Path)
    parser.add_argument("--zensus-toml", default=Path("research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"), type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise CodeCrosswalkError("no overwriting existing diagnostic receipts")
        result = inspect_exact_sources(args.bkg_zip.read_bytes(), args.gadm_zip.read_bytes(),
                                       args.materialcities_zip.read_bytes(), args.zensus_toml.read_bytes())
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, CodeCrosswalkError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print("CODE-ONLY RESEARCH PASS: 402 GADM-coded records map to 400 AGS CANDIDATES;"
          " GEOMETRY/VINTAGE/RIGHTS/INSURER ADMISSION NOT PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
