#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Compare original HANZE S2 2024 region IDs with original ZIP's DBF Code.

This is exact publisher-file *attribute lineage*, NOT polygon topology,
observed inundation, physical event identity, insured TIV, or loss attribution.
The report holds aggregate counts only; no original regional IDs/geometry.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import re
import struct
import zipfile

if __package__:
    from .hanze_regions2024_geometry_zip_audit_v0 import (
        inspect_hanze_region_geometry_zip, RegionArchiveError,
    )
    from .hanze_native_regions2024_source_audit_v0 import (
        read_hanze_original_regions, _parts,
    )
    from .historical_cat_benchmark_csv_preflight_v0 import (
        HANZE_COLUMNS, inspect_hanze_v302,
    )
else:
    from hanze_regions2024_geometry_zip_audit_v0 import (
        inspect_hanze_region_geometry_zip, RegionArchiveError,
    )
    from hanze_native_regions2024_source_audit_v0 import (
        read_hanze_original_regions, _parts,
    )
    from historical_cat_benchmark_csv_preflight_v0 import (
        HANZE_COLUMNS, inspect_hanze_v302,
    )

CODE = re.compile(r"[A-Z]{2}[A-Z0-9]{3}\Z")


def read_original_region_dbf_codes(archive: bytes,
                                   expected_zip_sha256: str | None = None):
    archive_receipt = inspect_hanze_region_geometry_zip(
        archive, expected_sha256=expected_zip_sha256)
    all_codes = Counter()
    empty = invalid = deleted = 0
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        dbfs = [x.filename for x in zf.infolist() if x.filename.lower().endswith(".dbf")]
        if len(dbfs) != 1:
            raise RegionArchiveError("expected exactly one verified 2024 regions DBF")
        blob = zf.read(dbfs[0])
    if len(blob) < 65:
        raise RegionArchiveError("original shapefile DBF too short")
    records, hlen, rlen = struct.unpack_from("<IHH", blob, 4)
    if hlen > len(blob) or not rlen or records != archive_receipt["shapefile_component_groups"][0]["dbf"]["declared_record_count"]:
        raise RegionArchiveError("original DBF headers disagree with ZIP profile")
    fields = {}
    offset = 1
    for cursor in range(32, hlen-1, 32):
        spec = blob[cursor:cursor+32]
        name = spec[:11].split(b"\x00", 1)[0].decode("ascii")
        width = spec[16]
        if name in fields:
            raise RegionArchiveError("duplicate source DBF field")
        fields[name] = (offset, width, spec[11])
        offset += width
    if offset > rlen or "Code" not in fields:
        raise RegionArchiveError("DBF source has no readable Code field")
    pos, width, type_code = fields["Code"]
    if type_code != ord("C") or width < 4 or width > 20:
        raise RegionArchiveError("original region Code not bounded DBF text")
    if hlen + records * rlen > len(blob):
        raise RegionArchiveError("DBF original data is truncated")
    for i in range(records):
        record = blob[hlen+i*rlen:hlen+(i+1)*rlen]
        if record[:1] == b"*":
            deleted += 1
            continue
        if record[:1] != b" ":
            raise RegionArchiveError("unknown DBF deleted record flag")
        raw = record[pos:pos+width]
        try:
            code = raw.decode("ascii").strip()
        except UnicodeError:
            invalid += 1
            continue
        if not code:
            empty += 1
        elif not CODE.fullmatch(code):
            invalid += 1
        else:
            all_codes[code] += 1
    return all_codes, {
        "original_geometry_archive_sha256": archive_receipt["observed_sha256"],
        "geometry_source_original_sha256_pinned": archive_receipt["original_sha256_independently_pinned"],
        "dbf_region_feature_records": records,
        "dbf_distinct_canonical_code_count": len(all_codes),
        "dbf_repeated_code_surplus_features": sum(n-1 for n in all_codes.values() if n > 1),
        "dbf_deleted_features": deleted,
        "dbf_empty_code_features": empty,
        "dbf_noncanonical_code_features": invalid,
        "code_to_polygon_attribute_link_is_not_inundation": True,
        "geometry_coordinates_or_codes_exported": False,
        "commercial_geometry_use_approved": False,
        "model_input_admitted": False,
    }


def compare_hanze_geometry_native_glossary(
    archive: bytes, glossary: bytes, *,
    expected_zip_sha256: str | None = None,
    expected_glossary_sha256: str | None = None,
) -> dict:
    shapes, shape_receipt = read_original_region_dbf_codes(
        archive, expected_zip_sha256=expected_zip_sha256)
    s2, source_receipt = read_hanze_original_regions(
        glossary, expected_sha256=expected_glossary_sha256)
    intersection = set(shapes) & s2
    geometry_only = set(shapes) - s2
    glossary_only = s2 - set(shapes)
    return {
        "evidence_stage": "HANZE_NATIVE_S2_TO_ZIP_DBF_CODE_COVERAGE_ONLY",
        "original_geometry": shape_receipt,
        "original_region_glossary_sha256": source_receipt["observed_sha256"],
        "glossary_region_count": len(s2),
        "glossary_codes_also_in_geometry": len(intersection),
        "geometry_codes_not_in_glossary": len(geometry_only),
        "glossary_codes_not_in_geometry": len(glossary_only),
        "geometry_features_for_glossary_codes": sum(shapes[code] for code in intersection),
        "distinct_region_names_emitted": False,
        "shapefile_geometry_or_geometry_ids_exported": False,
        "full_geographic_polygon_topology_validated": False,
        "actual_inundation_or_event_identity_proven": False,
        "insured_exposure_or_loss_inferred": False,
        "model_input_admitted": False,
    }


def survey_verified_event_region_geometry_coverage(
    archive: bytes, glossary: bytes, hanze_csv: bytes, hanze_sha256: str,
    candidate_overlap: dict, *,
    expected_zip_sha256: str | None = None,
    expected_glossary_sha256: str | None = None,
) -> dict:
    if (type(candidate_overlap) is not dict
        or candidate_overlap.get("evidence_class") != "HISTORICAL_FLOOD_EVENT_CANDIDATE_LINKS_ONLY"
        or candidate_overlap.get("common_event_identity_proven") is not False
        or candidate_overlap.get("model_input_admitted") is not False
        or candidate_overlap.get("input_sha256", {}).get("hanze_csv") != hanze_sha256):
        raise RegionArchiveError("unreviewed original HANZE candidate stage")
    profile = inspect_hanze_v302(hanze_csv, hanze_sha256)
    if profile.get("source_admitted") is not False:
        raise RegionArchiveError("HANZE source unexpectedly admitted")
    codes, _ = read_original_region_dbf_codes(
        archive, expected_zip_sha256=expected_zip_sha256)
    glossary_ids, _ = read_hanze_original_regions(
        glossary, expected_sha256=expected_glossary_sha256)
    han = {}
    reader = csv.DictReader(io.StringIO(hanze_csv.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != list(HANZE_COLUMNS):
        raise RegionArchiveError("HANZE source event fields disagree")
    for row in reader:
        if row["id"] in han:
            raise RegionArchiveError("repeated original HANZE id")
        han[row["id"]] = row
    counts = Counter()
    seen = set()
    unique = set()
    for pair in candidate_overlap.get("candidate_pairs", []):
        did, hid = pair.get("dfo_event_id"), pair.get("hanze_event_id")
        if (type(did) is not str or type(hid) is not str or (did, hid) in seen
            or hid not in han or pair.get("same_event_confirmed") is not False
            or pair.get("relationship") != "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY"):
            raise RegionArchiveError("original event candidate identity changed")
        seen.add((did, hid))
        unique.add(hid)
        source_row = han[hid]
        if source_row["country_code"] != pair.get("country_iso2_from_supplied_crosswalk"):
            raise RegionArchiveError("source original country crosswalk drift")
        parts = _parts(source_row["admin_unit_code"].strip())
        if parts is None:
            counts["unparsed_hanze_region_lists"] += 1
            continue
        counts["parsed_region_token_occurrences"] += len(parts)
        if any(code[:2] != source_row["country_code"] or code not in glossary_ids for code in parts):
            counts["unverified_country_or_glossary_list"] += 1
        elif all(code in codes for code in parts):
            counts["fully_dbf_code_covered_original_candidate_lists"] += 1
        else:
            counts["glossary_valid_lists_with_missing_geometry_code"] += 1
    if len(seen) != candidate_overlap.get("candidate_pair_count"):
        raise RegionArchiveError("candidate total count drift")
    return {
        "evidence_stage": "HANZE_EVENT_REGION_CODES_IN_GEOMETRY_DBF_ONLY",
        "candidate_pair_count": len(seen),
        "distinct_hanze_event_count": len(unique),
        "region_token_occurrences": counts["parsed_region_token_occurrences"],
        "fully_dbf_code_covered_original_candidate_lists":
            counts["fully_dbf_code_covered_original_candidate_lists"],
        "glossary_valid_lists_with_missing_geometry_code":
            counts["glossary_valid_lists_with_missing_geometry_code"],
        "unparsed_hanze_region_lists": counts["unparsed_hanze_region_lists"],
        "unverified_country_or_glossary_list": counts["unverified_country_or_glossary_list"],
        "source_polygon_geometry_intersections_computed": False,
        "geographical_association_is_not_flood_extent": True,
        "common_flood_event_identity_confirmed": False,
        "insured_loss_or_tiv_estimated": False,
        "raw_ids_or_features_redistributed": False,
        "model_input_admitted": False,
    }
