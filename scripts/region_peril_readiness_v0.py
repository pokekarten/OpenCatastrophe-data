# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed evidence inventory for one administrative region x peril.

NOT a source downloader, rights/admission authority, spatial join, risk engine,
or independent attestation of user-supplied evidence. The full eight-role set
does not confer permission to run a real insured CAT model.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROLES = (
    "admin_boundary", "asset_geometry", "asset_values",
    "hazard_event_catalogue", "hazard_intensity", "vulnerability",
    "policy_terms", "validation_holdout",
)
GEOGRAPHIC_ROLES = {"admin_boundary", "asset_geometry", "asset_values"}
SCOPE_KEYS = {"country_iso3", "admin_system", "admin_level",
              "admin_id", "boundary_year", "peril"}
RECEIPT_KEYS = {"role", "source_id", "source_sha256",
                "region_key", "peril", "evidence_level"}
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9:._-]{0,80}\Z")
PERIL = re.compile(r"[a-z][a-z0-9_]{1,50}\Z")


class RegionPerilError(ValueError):
    pass


def _identifier(value, name):
    if type(value) is not str or IDENTITY.fullmatch(value) is None:
        raise RegionPerilError("invalid " + name)
    return value


def region_key(scope):
    if type(scope) is not dict or set(scope) != SCOPE_KEYS:
        raise RegionPerilError("scope fields must match v0 exactly")
    country = scope["country_iso3"]
    if (type(country) is not str or re.fullmatch(r"[A-Z]{3}", country) is None
            or not isinstance(scope["boundary_year"], int)
            or type(scope["boundary_year"]) is bool
            or not 1900 <= scope["boundary_year"] <= 2100):
        raise RegionPerilError("ISO3 and boundary vintage required")
    system = _identifier(scope["admin_system"], "admin_system")
    aid = _identifier(scope["admin_id"], "admin_id")
    level = scope["admin_level"]
    if level not in ("ADM0", "ADM1", "ADM2", "ADM3", "ADM4", "ADM5"):
        raise RegionPerilError("unsupported administrative level")
    if type(scope["peril"]) is not str or PERIL.fullmatch(scope["peril"]) is None:
        raise RegionPerilError("explicit peril ID required")
    if (system == "US_CENSUS_TIGER_2026" and
            (country != "USA" or level != "ADM2"
             or scope["boundary_year"] != 2026
             or re.fullmatch(r"[0-9]{5}", aid) is None)):
        raise RegionPerilError("2026 Census county/parish scope requires USA ADM2 five-digit GEOID")
    return f"{country}:{system}:{level}:{aid}:{scope['boundary_year']}"


def assess(payload):
    """Only reports presence of asserted source evidence; NEVER model admission."""
    if type(payload) is not dict or set(payload) != {
            "schema_version", "scope", "evidence"}:
        raise RegionPerilError("root fields must match v0 exactly")
    if payload["schema_version"] != "OC_REGION_PERIL_EVIDENCE_V0":
        raise RegionPerilError("unknown evidence schema")
    scope = payload["scope"]
    key = region_key(scope)
    records = payload["evidence"]
    if type(records) is not list or len(records) > 256:
        raise RegionPerilError("bounded explicit evidence list required")
    catalogued, observed, seen = set(), set(), set()
    for row in records:
        if type(row) is not dict or set(row) != RECEIPT_KEYS:
            raise RegionPerilError("unexpected or missing receipt fields")
        role = row["role"]
        if role not in ROLES:
            raise RegionPerilError("unknown role")
        source = _identifier(row["source_id"], "source_id")
        if row["region_key"] != key:
            raise RegionPerilError("source region/vintage does not match the exact scope")
        expected_peril = "all" if role in GEOGRAPHIC_ROLES else scope["peril"]
        if row["peril"] != expected_peril:
            raise RegionPerilError("peril-specific evidence cannot be silently reused")
        if (role, source) in seen:
            raise RegionPerilError("duplicate role/source receipt")
        seen.add((role, source))
        level = row["evidence_level"]
        if level not in ("catalogued", "original_qc_claimed"):
            raise RegionPerilError("evidence cannot self-authorize admission")
        digest = row["source_sha256"]
        if level == "catalogued" and digest is not None:
            raise RegionPerilError("catalogue metadata must not impersonate source bytes")
        if (level == "original_qc_claimed" and
                (type(digest) is not str or HEX256.fullmatch(digest) is None)):
            raise RegionPerilError("claimed original evidence requires exact SHA-256")
        catalogued.add(role)
        if level == "original_qc_claimed":
            observed.add(role)
    return {
        "status": "RESEARCH_EVIDENCE_INVENTORY_ONLY_NOT_MODEL_ADMISSION",
        "region_key": key,
        "peril": scope["peril"],
        "source_receipt_count": len(records),
        "catalogued_roles": sorted(catalogued),
        "claimed_original_qc_roles": sorted(observed),
        "missing_catalogued_roles": sorted(set(ROLES) - catalogued),
        "missing_original_qc_roles": sorted(set(ROLES) - observed),
        "automatic_model_admission_allowed": False,
        "rights_and_scientific_sufficiency_established": False,
        "untrusted_caller_claims_require_independent_verification": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reviewed_json", type=Path,
                        help="explicit local synthetic/research-scoped evidence; not arbitrary provider downloads")
    args = parser.parse_args(argv)
    raw = args.reviewed_json.read_bytes()
    if len(raw) > 1_000_000:
        raise RegionPerilError("input byte budget exceeded")
    def unique_pairs(pairs):
        doc = {}
        for k, v in pairs:
            if k in doc:
                raise RegionPerilError("duplicate JSON property")
            doc[k] = v
        return doc
    def nonfinite(value):
        raise RegionPerilError("non-finite numeric constant")
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs,
                      parse_constant=nonfinite)
    print(json.dumps(assess(data), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
