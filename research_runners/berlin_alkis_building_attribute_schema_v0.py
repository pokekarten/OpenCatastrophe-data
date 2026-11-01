#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two bounded Berlin ALKIS WFS operations: schema and five-feature field counts.

Public receipt only: field names preapproved from Berlin's official
technical documentation, schema availability and *aggregate non-null counts*.
No source feature properties, codes, IDs, addresses or geometry are persisted
or printed. Not a complete Berlin building inventory or CAT model admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from typing import Any, Callable
from urllib import parse, request, error
from xml.etree import ElementTree

from research_runners.berlin_alkis_gebaeude_five_feature_join_v0 import (
    URL as FEATURE_URL, MAX_BYTES as FEATURE_MAX_BYTES,
    inspect_building_geojson,
)

BASE = "https://gdi.berlin.de/services/wfs/alkis_gebaeude"
DESCRIBE_URL = BASE + "?" + parse.urlencode([
    ("service", "WFS"), ("version", "2.0.0"),
    ("request", "DescribeFeatureType"), ("typeNames", "alkis_gebaeude:gebaeude"),
])
SOURCE_DOC = "https://gdi.berlin.de/data/alkis/docs/datenformatbeschreibung_alkis_berlin.pdf"
SCHEMA_MAX_BYTES = 2_097_152
TOTAL_MAX_REQUESTS = 2
TIMEOUT = 35
PROFILE = "oc-berlin-alkis-official-attribute-schema-and-five-features-v0"
# Only non-personal descriptive attribute *field names* from Berlin official
# ALKIS technical documentation, June 2022. No uuid/gkn/address/owner fields.
SAFE_FIELDS = (
    "gfk", "bezgfk", "ofl", "bezofl", "aog", "aug", "hoh",
    "bat", "bezbat", "baw", "bezbaw", "zus", "bezzus",
)
OTHER_RESEARCH_FIELDS = ("bja", "hoehe", "role_txt", "dachart", "geschosse")
# Those fields belong to other providers/datasets and must NOT be assumed
# available, or be automatically filled by external data.
ALL_SAFE_NAMES = frozenset(SAFE_FIELDS + OTHER_RESEARCH_FIELDS)


class AttributeAuditError(ValueError):
    """Source, schema, property payload or evidence mismatch."""


def inspect_schema_xml(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= SCHEMA_MAX_BYTES:
        raise AttributeAuditError("empty/oversized WFS DescribeFeatureType schema")
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise AttributeAuditError("XML document type/entities are forbidden")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise AttributeAuditError("invalid schema XML") from exc
    if root.tag != "{http://www.w3.org/2001/XMLSchema}schema":
        raise AttributeAuditError("expected an official XSD schema root")
    children = list(root.iter())
    if len(children) > 1500:
        raise AttributeAuditError("unbounded XML schema element count")
    elements = [
        item.get("name") for item in children
        if item.tag == "{http://www.w3.org/2001/XMLSchema}element"
        and isinstance(item.get("name"), str)
    ]
    if len(elements) > 450 or not elements:
        raise AttributeAuditError("no typed provider schema fields")
    names = set(elements)
    if not any("gebaeude" in n.casefold() for n in names):
        raise AttributeAuditError("official building layer absent from schema")
    declared = sorted(names & ALL_SAFE_NAMES)
    # Not all official WFS releases include a field from the older PDF;
    # record absence explicitly rather than inventing a populated source.
    return {
        "xsd_element_declarations": len(elements),
        "xsd_distinct_named_elements": len(names),
        "official_building_element_advertised": True,
        "official_documented_fields_in_xsd": sorted(names & set(SAFE_FIELDS)),
        "other_product_fields_in_xsd": sorted(names & set(OTHER_RESEARCH_FIELDS)),
        "all_xsd_field_names_exported": False,
    }


def inspect_sample_fields(raw: bytes) -> dict[str, Any]:
    # Validate all original feature envelopes and geometries via the
    # previously live-tested five-feature validator.
    validated, _ = inspect_building_geojson(raw)
    obj = json.loads(raw.decode("utf-8"))
    fields = {name: 0 for name in SAFE_FIELDS + OTHER_RESEARCH_FIELDS}
    non_null = dict(fields)
    for feature in obj["features"]:
        props = feature["properties"]
        for name in fields:
            if name in props:
                fields[name] += 1
                val = props[name]
                if val is not None and val != "":
                    # Never serialize the scalar original provider value.
                    if type(val) not in (str, int, float, bool):
                        raise AttributeAuditError("unexpected complex value in safe attribute")
                    non_null[name] += 1
    # Receipt describes actual field existence and missingness in a
    # FIVE-OBJECT SOURCE SAMPLE only, not citywide proportions.
    return {
        "sampled_valid_original_polygons": validated["sampled_feature_count"],
        "sampled_polygon_area_total_m2": validated["total_sample_polygon_area_m2_rounded"],
        "official_field_presence_counts": {k: fields[k] for k in SAFE_FIELDS},
        "official_field_non_null_counts": {k: non_null[k] for k in SAFE_FIELDS},
        "other_dataset_fields_presence_counts": {
            k: fields[k] for k in OTHER_RESEARCH_FIELDS
        },
        "other_dataset_fields_non_null_counts": {
            k: non_null[k] for k in OTHER_RESEARCH_FIELDS
        },
        "sample_is_not_a_citywide_completeness_estimate": True,
        "building_vs_part_classification_verified": False,
        "building_construction_year_verified": False,
        "height_or_roof_geometry_inferred": False,
        "raw_attribute_values_logged_or_saved": False,
    }


class RefuseRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AttributeAuditError("reviewed official source URL redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), RefuseRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def _single(
    url: str, allowed_content_types: tuple[str, ...], budget: int,
    opener: Callable[[request.Request, int], Any],
) -> bytes:
    req = request.Request(url, method="GET", headers={
        "Accept": "application/xml, text/xml" if url == DESCRIBE_URL
                  else "application/json",
    })
    try:
        with opener(req, TIMEOUT) as response:
            if response.status != 200 or response.geturl() != url:
                raise AttributeAuditError("unexpected official WFS URL or status")
            media = response.headers.get("Content-Type", "").split(";", 1)[0].lower().strip()
            if media not in allowed_content_types:
                raise AttributeAuditError("WFS returned unexpected media type")
            body = response.read(budget + 1)
    except AttributeAuditError:
        raise
    except (OSError, TimeoutError, error.URLError) as exc:
        raise AttributeAuditError("official WFS request failed") from exc
    if len(body) > budget or not body:
        raise AttributeAuditError("empty or oversize official source reply")
    return body


def probe(
    *, opener: Callable[[request.Request, int], Any] = _fetch,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    schema = _single(DESCRIBE_URL, ("application/xml", "text/xml",
                                   "application/gml+xml", "application/xsd+xml"),
                     SCHEMA_MAX_BYTES, opener)
    schema_report = inspect_schema_xml(schema)
    sample = _single(FEATURE_URL, ("application/json", "application/geo+json"),
                     FEATURE_MAX_BYTES, opener)
    fields_report = inspect_sample_fields(sample)
    utc = clock()
    if utc.tzinfo is None or utc.utcoffset() is None:
        raise AttributeAuditError("naive audit UTC time")
    xsd_fields = set(schema_report["official_documented_fields_in_xsd"])
    sampled = fields_report["official_field_presence_counts"]
    return {
        "profile": PROFILE,
        "source": "Berlin ALKIS building WFS 2.0.0",
        "official_catalogue_license_label": "dl-de-zero-2.0",
        "schema_url": DESCRIBE_URL,
        "sample_url": FEATURE_URL,
        "official_field_dictionary": SOURCE_DOC,
        "retrieved_at_utc": utc.astimezone(timezone.utc).isoformat(),
        "exact_requests_per_proof": TOTAL_MAX_REQUESTS,
        "schema_original_bytes": len(schema),
        "schema_original_sha256": hashlib.sha256(schema).hexdigest(),
        "sample_original_bytes": len(sample),
        "sample_original_sha256": hashlib.sha256(sample).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_source_bytes_persisted": False,
        "individual_building_identifiers_or_addresses_exported": False,
        "CAT_database_modified": False,
        "attributes_approved_for_insured_value_model": False,
        "field_in_schema_but_not_in_five_feature_sample": sorted(
            k for k in xsd_fields if sampled[k] == 0
        ),
        **schema_report,
        **fields_report,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    opts = p.parse_args(argv)
    if not opts.live:
        p.error("no network by default; use --live for exactly two WFS requests")
    try:
        print(json.dumps(probe(), indent=2, sort_keys=True, allow_nan=False))
    except (AttributeAuditError, ValueError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
