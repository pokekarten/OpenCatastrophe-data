#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, read-only original-service probe for flood-defence source *access*.

Inputs are separately and manually captured tiny official HTTP response bytes,
never downloaded by this program or committed into Git. Rijkswaterstaat WFS
formal NBPW dike trajectories and Bavarian LfU ATOM ZIP headers are NOT risk
transformation inputs, building assignment, crest-height measurements or
licensing/scientific admission receipts.

Do not transform Dutch NORM_SW / NORM_OG legal failure-probability norms into
a point flood depth, guaranteed annual flooding threshold or insurer loss.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

NL_WFS = ("https://geo.rijkswaterstaat.nl/services/ogc/wvp/"
          "wvp/wfs?service=WFS&version=1.1.0&request=GetCapabilities")
NL_FEATURE = "wvp:nbpw_dijktrajecten_formeel"
NL_CRS = "urn:ogc:def:crs:EPSG::28992"
NL_WFS_DESCRIBE = ("https://geo.rijkswaterstaat.nl/services/ogc/wvp/wvp/wfs?"
                   "service=WFS&version=1.1.0&request=DescribeFeatureType"
                   "&typeName=wvp:nbpw_dijktrajecten_formeel")
NL_WFS_ONE = ("https://geo.rijkswaterstaat.nl/services/ogc/wvp/wvp/wfs?"
              "service=WFS&version=1.1.0&request=GetFeature"
              "&typeName=wvp:nbpw_dijktrajecten_formeel"
              "&maxFeatures=1&outputFormat=application%2Fjson")
NL_WFS_HITS = ("https://geo.rijkswaterstaat.nl/services/ogc/wvp/wvp/wfs?"
               "service=WFS&version=1.1.0&request=GetFeature"
               "&typeName=wvp:nbpw_dijktrajecten_formeel&resultType=hits")
NL_STALE_CATALOGUE_URL = (
    "https://geo.rijkswaterstaat.nl/services/ogc/wvp/ows/wfs?"
    "version=1.1.0&request=GetCapabilities"
)
BAVARIA_ATOM = "https://www.lfu.bayern.de/gdi/dls/hwsa.xml"
BAVARIA_ZIPS = {
    "25832": "https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg25832_shp.zip",
    "4258": "https://www.lfu.bayern.de/gdi/dls/daten/hwsa/hwsa_epsg4258_shp.zip",
}
INPUT_LIMITS = {
    "nl_capabilities": 120000,
    "nl_schema": 16000,
    "nl_hits": 12000,
    "nl_one_feature": 20000,
    "bavaria_atom": 60000,
    "bavaria_zip_25832_head": 512,
    "bavaria_zip_4258_head": 512,
}
PROFILE = "wri-flood-defence-sources-read-only-access-v0"


class DefenceSourceGateError(ValueError):
    """Insufficient access, identity, coordinate-system or source proof."""


def read_bounded(path: Path, key: str) -> bytes:
    if key not in INPUT_LIMITS:
        raise DefenceSourceGateError("unknown provider original HTTP response")
    maximum = INPUT_LIMITS[key]
    with path.open("rb") as source:
        raw = source.read(maximum + 1)
    if not 0 < len(raw) <= maximum:
        raise DefenceSourceGateError(key + " empty or exceeds bounded HTTP response cap")
    if key.endswith("_head") and len(raw) != 512:
        raise DefenceSourceGateError(key + ": the exact first 512 bytes are required")
    return raw


def safe_xml(raw: bytes, key: str) -> ET.Element:
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise DefenceSourceGateError(key + ": reject DTD/entity declarations")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise DefenceSourceGateError(key + ": invalid XML") from exc


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1]


def inspect_nl_capabilities(raw: bytes) -> dict:
    root = safe_xml(raw, "NL WFS GetCapabilities")
    if local(root.tag) != "WFS_Capabilities":
        raise DefenceSourceGateError("NL WFS returned no successful capabilities")
    if root.attrib.get("version") != "1.1.0":
        raise DefenceSourceGateError("NL WFS version mismatch")
    names = []
    for candidate in root.iter():
        if local(candidate.tag) != "FeatureType":
            continue
        for child in candidate:
            if local(child.tag) == "Name" and child.text:
                names.append(child.text.strip())
    if NL_FEATURE not in names:
        raise DefenceSourceGateError("formal NBPW layer missing from corrected service")
    return {
        "canonical_2017_catalogue_link": NL_STALE_CATALOGUE_URL,
        "working_service_getcapabilities_url": NL_WFS,
        "advertises_required_formal_layer": True,
        "advertised_feature_types": len(names),
    }


def inspect_nl_schema(raw: bytes) -> dict:
    root = safe_xml(raw, "NL WFS DescribeFeatureType")
    if local(root.tag) != "schema":
        raise DefenceSourceGateError("no WFS feature type schema")
    fields = {}
    for element in root.iter():
        if local(element.tag) != "element":
            continue
        name = element.attrib.get("name")
        if name:
            fields[name] = element.attrib.get("type", "")
    expected = {
        "TRAJECT_ID": "xsd:string", "VERSIE": "xsd:string",
        "NORM_SW": "xsd:int", "NORM_OG": "xsd:int",
        "NORM_THB": "xsd:int", "NORM_NS": "xsd:int",
        "geom": "gml:MultiLineStringPropertyType",
    }
    if any(fields.get(k) != v for k, v in expected.items()):
        raise DefenceSourceGateError("Dutch NBPW formal feature schema changed")
    return {"formal_layer": NL_FEATURE, "schema_fields_checked": expected,
            "legal_norm_is_not_crest_height": True}


def inspect_nl_hits(raw: bytes) -> dict:
    root = safe_xml(raw, "NL WFS GetFeature hits")
    if local(root.tag) != "FeatureCollection":
        raise DefenceSourceGateError("NL feature hits did not yield WFS collection")
    count = root.attrib.get("numberOfFeatures", "")
    if not count.isdecimal() or int(count) < 1:
        raise DefenceSourceGateError("missing positive numberOfFeatures")
    return {
        "observed_formal_trajectory_count_at_probe_time": int(count),
        "count_is_live_and_not_globally_pinned": True,
    }


def inspect_nl_one_feature(raw: bytes) -> dict:
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise DefenceSourceGateError("NL WFS one-feature JSON invalid") from exc
    if (not isinstance(payload, dict) or payload.get("type") != "FeatureCollection"
            or not isinstance(payload.get("features"), list)
            or len(payload["features"]) != 1):
        raise DefenceSourceGateError("NL WFS must return exactly one feature")
    crs = payload.get("crs") or {}
    if (not isinstance(crs, dict) or
            (crs.get("properties") or {}).get("name") != NL_CRS):
        raise DefenceSourceGateError("NL source CRS is not proven EPSG:28992")
    feature = payload["features"][0]
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise DefenceSourceGateError("one NBPW feature missing")
    geom = feature.get("geometry") or {}
    if geom.get("type") != "MultiLineString":
        raise DefenceSourceGateError("NBPW source geometry not a MultiLineString")
    coords = geom.get("coordinates") or []
    if (not isinstance(coords, list) or not coords or
            not isinstance(coords[0], list) or not coords[0] or
            not isinstance(coords[0][0], list) or len(coords[0][0]) < 2):
        raise DefenceSourceGateError("NBPW feature geometry has no coordinate pair")
    x, y = coords[0][0][:2]
    if not (isinstance(x, (int, float)) and isinstance(y, (int, float))
            and 0 < x < 300000 and 250000 < y < 650000):
        raise DefenceSourceGateError("unexpected Netherlands RD New native coordinates")
    props = feature.get("properties") or {}
    if (not isinstance(props, dict) or not isinstance(props.get("TRAJECT_ID"), str)
            or not props["TRAJECT_ID"] or not isinstance(props.get("VERSIE"), str)):
        raise DefenceSourceGateError("formal trajectory ID/version not available")
    norms = ("NORM_SW", "NORM_OG", "NORM_THB", "NORM_NS")
    if any(type(props.get(k)) is not int or props[k] < 0 for k in norms):
        raise DefenceSourceGateError("NBPW code/norm fields invalid")
    if props.get("NORMTYP_O") != "Overstromingskans":
        raise DefenceSourceGateError("NBPW norm type is not the expected legal category")
    return {
        "formal_trajectory_id_example": props["TRAJECT_ID"],
        "formal_version_example": props["VERSIE"],
        "observed_norm_sw_example": props["NORM_SW"],
        "observed_norm_og_example": props["NORM_OG"],
        "formal_norm_type_description": props["NORMTYP_O"],
        "native_crs": "EPSG:28992",
        "sample_multilinestring_confirmed": True,
        "crs_reprojection_must_be_explicit": True,
        "norms_not_interpreted_as_hazard_return_periods": True,
    }


def inspect_bavaria_atom(raw: bytes) -> dict:
    root = safe_xml(raw, "Bavaria ATOM download service")
    if local(root.tag) != "feed":
        raise DefenceSourceGateError("Bavarian source was not an ATOM feed")
    links = set()
    licences = []
    for node in root.iter():
        if local(node.tag) == "link" and node.attrib.get("href"):
            links.add(node.attrib["href"])
        if local(node.tag) == "rights" and node.text:
            licences.append(node.text)
    if any(url not in links for url in BAVARIA_ZIPS.values()):
        raise DefenceSourceGateError("Bavarian EPSG:25832/4258 Shapefile links missing")
    if not any("CC BY-SA 4.0" in right for right in licences):
        raise DefenceSourceGateError("Bavarian ATOM no longer states CC BY-SA 4.0")
    return {
        "original_atom_url": BAVARIA_ATOM,
        "shapefile_archive_urls": dict(BAVARIA_ZIPS),
        "provider_declared_license": "CC-BY-SA-4.0",
        "provider_attribution_required": (
            "Datenquelle: Bayerisches Landesamt für Umwelt, www.lfu.bayern.de"
        ),
        "license_inheritance_review_complete": False,
    }


def inspect_bavaria_zip_start(raw: bytes, epsg: str) -> dict:
    if epsg not in BAVARIA_ZIPS or len(raw) != 512 or raw[:4] != b"PK\x03\x04":
        raise DefenceSourceGateError("Bavarian first-512-byte source ZIP signature invalid")
    # ZIP local file header: filename_length at 26, extra_length at 28.
    name_len, extra_len = struct.unpack_from("<HH", raw, 26)
    if not 0 < name_len <= 180 or 30 + name_len + extra_len > len(raw):
        raise DefenceSourceGateError("bad original ZIP first local file header")
    try:
        name = raw[30:30+name_len].decode("ascii")
    except UnicodeError as exc:
        raise DefenceSourceGateError("first ZIP member name invalid") from exc
    if name != f"deich_epsg{epsg}.dbf":
        raise DefenceSourceGateError("unexpected original Bavarian archive first member")
    return {
        "requested_epsg": int(epsg), "zip_signature_verified": True,
        "first_zip_member_name": name,
        "full_zip_central_directory_verified": False,
        "full_shapefile_geometry_verified": False,
        "dike_crest_or_design_standard_verified": False,
    }


def audit(inputs: dict[str, bytes]) -> dict:
    if set(inputs) != set(INPUT_LIMITS):
        raise DefenceSourceGateError("missing or extra original response files")
    for key, data in inputs.items():
        if type(data) is not bytes or not 0 < len(data) <= INPUT_LIMITS[key]:
            raise DefenceSourceGateError("original response length/identity invalid: " + key)
    nl = {
        "capabilities": inspect_nl_capabilities(inputs["nl_capabilities"]),
        "schema": inspect_nl_schema(inputs["nl_schema"]),
        "hits": inspect_nl_hits(inputs["nl_hits"]),
        "one_feature": inspect_nl_one_feature(inputs["nl_one_feature"]),
    }
    if (nl["hits"]["observed_formal_trajectory_count_at_probe_time"] <
            len([nl["one_feature"]])):
        raise DefenceSourceGateError("the NL one-feature response exceeds hit count")
    by = {
        "atom": inspect_bavaria_atom(inputs["bavaria_atom"]),
        "epsg_25832_first_512_bytes": inspect_bavaria_zip_start(
            inputs["bavaria_zip_25832_head"], "25832"),
        "epsg_4258_first_512_bytes": inspect_bavaria_zip_start(
            inputs["bavaria_zip_4258_head"], "4258"),
    }
    return {
        "profile": PROFILE,
        "review_scope": "source service availability and bounded format/provenance only",
        "original_response_sha256_at_run": {
            k: hashlib.sha256(v).hexdigest() for k, v in inputs.items()
        },
        "netherlands": nl,
        "bavaria": by,
        "netherlands_original_catalogue_wfs_url_currently_blocked": True,
        "source_wfs_live_formal_trajectories_usable_for_GIS_research": True,
        "bavaria_original_zip_magic_valid_but_full_download_not_checked": True,
        "user_access_or_public_data_not_sufficient_for_scientific_use": True,
        "spatial_inside_dike_or_protected_area_identified": False,
        "individual_dike_crest_elevation_verified": False,
        "defence_failure_probabilities_calibrated": False,
        "protection_factor_or_return_period_threshold_inferred": False,
        "third_party_derivative_redistribution_approved": False,
        "insurer_location_or_contract_enriched": False,
        "source_and_scientific_admission_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in INPUT_LIMITS:
        parser.add_argument("--" + key.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    files = {key: getattr(args, key) for key in INPUT_LIMITS}
    input_paths = [path.resolve() for path in files.values()]
    if len(set(input_paths)) != len(files) or args.out.resolve() in input_paths:
        parser.error("all exact provider response files must be distinct and read-only")
    try:
        result = audit({key: read_bounded(p, key) for key, p in files.items()})
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8")
    except (OSError, DefenceSourceGateError) as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
