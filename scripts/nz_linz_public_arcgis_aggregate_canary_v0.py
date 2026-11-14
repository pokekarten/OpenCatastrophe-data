# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only aggregate canary for LINZ's public ArcGIS property/building services.

Manual invocation: python scripts/nz_linz_public_arcgis_aggregate_canary_v0.py --live

This tool deliberately requests only metadata, count-only summaries and five
provider-defined source-category totals. It does not fetch source features,
addresses, valuation amounts, people, geometries, insured records or policy
data; output is aggregate-only and never constitutes an admitted model input.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

HOST = "services.arcgis.com"
ROOT = (
    "https://services.arcgis.com/xdsHIIxuCWByZiCB/ArcGIS/rest/services/"
)
PROPERTY = ROOT + "LINZ_NZ_Property_Boundaries/FeatureServer/0"
BUILDING = ROOT + "LINZ_NZ_Building_Outlines/FeatureServer/0"
BOUND = {
    "geometry": json.dumps(
        {"xmin": 1749000, "ymin": 5427000, "xmax": 1750000, "ymax": 5428000,
         "spatialReference": {"wkid": 2193}}, separators=(",", ":")
    ),
    "geometryType": "esriGeometryEnvelope",
    "spatialRel": "esriSpatialRelIntersects",
    "inSR": "2193",
}
CATEGORIES = (
    "NZ Unit of Property",
    "NZ Property Titles",
    "NZ Primary Parcels",
    "NZ Primary Parcels - Road",
    "NZ Primary Parcels - Hydro",
)


class CanaryError(ValueError):
    """Provider schema, network or aggregate integrity gate failed."""


def _query(base: str, params: dict[str, str]) -> str:
    return base + "/query?" + urlencode({"f": "json", **params})


def _provider_json(url: str) -> tuple[dict[str, object], dict[str, object]]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != HOST or not parsed.path.startswith(
        "/xdsHIIxuCWByZiCB/ArcGIS/rest/services/LINZ_NZ_"
    ):
        raise CanaryError("unexpected provider URL")
    try:
        request = Request(url, headers={"User-Agent": "OpenCatastrophe-research-aggregate-canary/0.1"})
        with urlopen(request, timeout=20) as response:
            if urlsplit(response.geturl()).hostname != HOST:
                raise CanaryError("redirected off official public ArcGIS host")
            raw = response.read(262145)
            if len(raw) > 262144:
                raise CanaryError("provider metadata/aggregate response exceeded 256KiB")
            if response.status != 200:
                raise CanaryError("unexpected HTTP status")
        decoded = json.loads(raw)
    except CanaryError:
        raise
    except (OSError, ValueError, UnicodeError) as exc:
        raise CanaryError("provider did not return a valid bounded JSON response") from exc
    if not isinstance(decoded, dict) or "error" in decoded:
        raise CanaryError("ArcGIS provider returned an error payload")
    receipt = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "url": url,
    }
    return decoded, receipt


def _getcount(value: dict[str, object]) -> int:
    n = value.get("count")
    if type(n) is not int or n < 0 or n > 30_000_000:
        raise CanaryError("missing or invalid count-only response")
    return n


def validate(
    pmeta: dict[str, object],
    bmeta: dict[str, object],
    counts: dict[str, int],
    grouped: dict[str, object],
) -> dict[str, object]:
    """Validate complete count partition and provider field/CRS identities."""
    for meta, required in (
        (pmeta, {"OBJECTID", "source", "unit_of_property_id"}),
        (bmeta, {"OBJECTID", "building_id", "capture_source_to"}),
    ):
        fields = meta.get("fields")
        if not isinstance(fields, list) or not required.issubset(
            {v.get("name") for v in fields if isinstance(v, dict)}
        ):
            raise CanaryError("provider schema differs from expected field contract")
        crs = (meta.get("extent") or {}).get("spatialReference") or {}
        if crs.get("wkid") != 2193:
            raise CanaryError("provider CRS must be New Zealand Transverse Mercator EPSG:2193")
    mandatory = (
        "properties_all", "properties_with_unit_id", "properties_without_unit_id",
        "buildings_all", "buildings_with_building_id", "buildings_without_building_id",
        "bbox_properties_all", "bbox_properties_rateable", "bbox_buildings_all",
    )
    if any(key not in counts for key in mandatory) or any(
        type(counts[key]) is not int or counts[key] < 0 or counts[key] > 30_000_000
        for key in mandatory
    ):
        raise CanaryError("missing, negative or invalid count")
    if counts["properties_all"] != counts["properties_with_unit_id"] + counts["properties_without_unit_id"]:
        raise CanaryError("property identifier partition does not conserve records")
    if counts["buildings_all"] != counts["buildings_with_building_id"] + counts["buildings_without_building_id"]:
        raise CanaryError("building identifier partition does not conserve records")
    if not (0 <= counts["bbox_properties_rateable"] <= counts["bbox_properties_all"] <= counts["properties_all"]):
        raise CanaryError("bounded property count contradicts global population")
    if counts["bbox_buildings_all"] > counts["buildings_all"]:
        raise CanaryError("bounded building count contradicts global population")
    feats = grouped.get("features")
    if not isinstance(feats, list) or len(feats) != len(CATEGORIES):
        raise CanaryError("unknown or incomplete provider source categories")
    sources: dict[str, int] = {}
    for entry in feats:
        a = entry.get("attributes") if isinstance(entry, dict) else None
        if not isinstance(a, dict) or not isinstance(a.get("source"), str):
            raise CanaryError("invalid source-group aggregate structure")
        name, n = a["source"], a.get("n")
        if name not in CATEGORIES or name in sources or type(n) is not int or n < 0:
            raise CanaryError("unknown or malformed source-category count")
        sources[name] = n
    if set(sources) != set(CATEGORIES) or sum(sources.values()) != counts["properties_all"]:
        raise CanaryError("source groups do not conserve the property population")
    if sources["NZ Unit of Property"] != counts["properties_with_unit_id"]:
        raise CanaryError("only rated-unit source is expected to carry the LINZ unit ID")
    return {
        "profile": "nz-linz-public-arcgis-aggregate-canary-v0",
        "scope": "public_original_provider_count_only_metadata_non_admission",
        "source_categories": {name: sources[name] for name in CATEGORIES},
        "counts": {key: counts[key] for key in mandatory},
        "service_data_last_edit_ms": {
            "properties": (pmeta.get("editingInfo") or {}).get("dataLastEditDate"),
            "buildings": (bmeta.get("editingInfo") or {}).get("dataLastEditDate"),
        },
        "spatial_probe": {
            "crs": "EPSG:2193", "bbox": [1749000, 5427000, 1750000, 5428000],
            "spatial_predicate": "intersects",
            "warning": "Same-bbox property and roof counts are not linked property-building pairs.",
        },
        "admission": {
            "rights_review_completed": False,
            "physical_building_id_join_observed": False,
            "valuation_to_roof_join_observed": False,
            "insured_exposure_admitted": False,
            "cat_model_input_admitted": False,
        },
    }


def live() -> dict[str, object]:
    """Read only original provider count-only/metadata responses, no features."""
    receipts: dict[str, dict[str, object]] = {}
    def read(name: str, url: str) -> dict[str, object]:
        response, receipt = _provider_json(url)
        receipts[name] = receipt
        return response

    pmeta = read("property_metadata", PROPERTY + "?f=json")
    bmeta = read("building_metadata", BUILDING + "?f=json")
    specs = {
        "properties_all": (PROPERTY, {"where": "1=1", "returnCountOnly": "true"}),
        "properties_with_unit_id": (
            PROPERTY, {"where": "unit_of_property_id IS NOT NULL", "returnCountOnly": "true"}
        ),
        "properties_without_unit_id": (
            PROPERTY, {"where": "unit_of_property_id IS NULL", "returnCountOnly": "true"}
        ),
        "buildings_all": (BUILDING, {"where": "1=1", "returnCountOnly": "true"}),
        "buildings_with_building_id": (
            BUILDING, {"where": "building_id IS NOT NULL", "returnCountOnly": "true"}
        ),
        "buildings_without_building_id": (
            BUILDING, {"where": "building_id IS NULL", "returnCountOnly": "true"}
        ),
        "bbox_properties_all": (PROPERTY, {"where": "1=1", "returnCountOnly": "true", **BOUND}),
        "bbox_properties_rateable": (
            PROPERTY, {"where": "source = 'NZ Unit of Property'", "returnCountOnly": "true", **BOUND}
        ),
        "bbox_buildings_all": (BUILDING, {"where": "1=1", "returnCountOnly": "true", **BOUND}),
    }
    counts: dict[str, int] = {}
    for name, (base, params) in specs.items():
        counts[name] = _getcount(read(name, _query(base, params)))
    grouped = read(
        "property_source_group",
        _query(PROPERTY, {
            "where": "1=1", "returnGeometry": "false", "groupByFieldsForStatistics": "source",
            "outFields": "source", "orderByFields": "source",
            "outStatistics": json.dumps([{
                "statisticType": "count", "onStatisticField": "OBJECTID",
                "outStatisticFieldName": "n"
            }], separators=(",", ":")),
        }),
    )
    output = validate(pmeta, bmeta, counts, grouped)
    output["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
    output["provider_response_receipts"] = receipts
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly permit read-only public service calls")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("no provider requests by default; use --live")
    try:
        print(json.dumps(live(), sort_keys=True))
        return 0
    except CanaryError as exc:
        print("BLOCKED: original-source aggregate preflight failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
