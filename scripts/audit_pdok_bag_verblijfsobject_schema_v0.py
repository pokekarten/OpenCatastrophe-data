# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Audit official PDOK BAG verblijfsobject JSON Schema without reading feature rows.

Metadata-only, offline, fail-closed scientific intake contract. A public BAG
schema describes address fields as well as usable area and building references.
Only the source schema may be inspected. This tool never retrieves, normalises
or redistributes address/customer feature records, nor creates exposure/TIV.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

SCHEMA_ID = "https://api.pdok.nl/kadaster/bag/ogc/v2/collections/verblijfsobject/schema"
SCHEMA_VERSION = "https://json-schema.org/draft/2020-12/schema"
MAX_BYTES = 500_000
SAFE_FIELDS = ("identificatie", "oppervlakte", "pand", "status", "gebruiksdoel")
SENSITIVE_FIELDS = (
    "postcode", "huisnummer", "huisletter", "toevoeging",
    "hoofdadres_identificatie", "hoofdadres_status",
    "openbare_ruimte_naam", "openbare_ruimte_naam_kort",
    "woonplaats_naam", "provincie_naam",
)


class BagSchemaError(ValueError):
    """Unreviewed version or changed semantics of an official BAG schema."""


def _distinct(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise BagSchemaError("duplicate JSON schema key")
        out[key] = value
    return out


def read_schema(path):
    data = Path(path).read_bytes()
    if len(data) > MAX_BYTES:
        raise BagSchemaError("schema metadata exceeds bounded read budget")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_distinct,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              BagSchemaError("nonfinite schema metadata")))
    except UnicodeDecodeError as exc:
        raise BagSchemaError("not UTF-8 JSON schema") from exc


def audit(doc):
    if not isinstance(doc, dict):
        raise BagSchemaError("expected JSON schema object")
    if doc.get("$id") != SCHEMA_ID or doc.get("$schema") != SCHEMA_VERSION:
        raise BagSchemaError("unexpected provider schema URL or schema version")
    if doc.get("type") != "object" or doc.get("title") != "Verblijfsobject":
        raise BagSchemaError("wrong BAG source object class")
    props = doc.get("properties")
    if not isinstance(props, dict) or not (set(SAFE_FIELDS) | set(SENSITIVE_FIELDS)) <= set(props):
        raise BagSchemaError("missing required metadata fields or privacy warnings")
    if doc.get("required") != ["id"]:
        raise BagSchemaError("schema-required identity semantics changed")
    for key in ("identificatie", "status", "gebruiksdoel"):
        if props[key].get("type") != "string":
            raise BagSchemaError(key + " changed type")
    if props["oppervlakte"].get("type") != "integer":
        raise BagSchemaError("oppervlakte no longer a whole-m2 integer")
    p = props["pand"]
    if not isinstance(p, dict) or p.get("type") != "array":
        raise BagSchemaError("pand no longer an array of building references")
    items = p.get("items")
    if not isinstance(items, dict) or items.get("type") != "string" or (
        items.get("x-ogc-role") != "reference"
        or items.get("x-ogc-collectionId") != "pand"
    ):
        raise BagSchemaError("pand reference collection/type semantics changed")
    for key in ("postcode", "huisnummer", "hoofdadres_identificatie"):
        if not isinstance(props[key], dict):
            raise BagSchemaError("privacy-sensitive field contract changed")

    # A public schema is allowed to DESCRIBE address fields. Never copy
    # property names from the provider into a later per-building export.
    # The audit result is wholly non-identifying, not an exposure record.
    return {
        "schema": "pdok-bag-verblijfsobject-official-schema-audit-v0",
        "research_only": True,
        "source_schema_verified": True,
        "original_feature_records_queried": False,
        "property_count": len(props),
        "unit_identification_type": "string",
        "unit_area_type": "integer",
        "unit_area_semantics": "BAG verblijfsobject usable area m2, not footprint/volume",
        "pand_relation": "array of reference strings to BAG pand collection",
        "pand_relationship_cardinality": "zero_to_many_in_schema",
        "building_id_identity_or_mapping_verified": False,
        "status_and_gebruiksdoel_types_verified": True,
        "source_contains_address_fields": True,
        "address_fields_permitted_in_exposure_export": False,
        "source_admitted": False,
        "licence_or_reuse_reviewed": False,
        "replacement_cost_verified": False,
        "insured_tiv_verified": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, required=True,
                        help="Downloaded PUBLIC official schema metadata JSON, not feature data")
    args = parser.parse_args(argv)
    try:
        doc = read_schema(args.schema)
        raw = args.schema.read_bytes()
        result = audit(doc)
        result["schema_metadata_sha256"] = hashlib.sha256(raw).hexdigest()
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
