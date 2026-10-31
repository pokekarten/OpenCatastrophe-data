#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Import a bounded CC0 GLEIF LEI identity pilot into a dedicated CAT SQLite DB.

Identity discovery is not evidence of underwriting, CAT exposure, insured value
or accounting group ownership. Keep original response bytes outside the repo.
The repository's CAT source-registry exporter must initialize the DB first.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.request import Request, urlopen

try:
    from .export_cat_source_registry_sqlite import CAT_APP_ID, CAT_SCHEMA_VERSION
except ImportError:
    from export_cat_source_registry_sqlite import CAT_APP_ID, CAT_SCHEMA_VERSION

LEI_RE = re.compile(r"[0-9A-Z]{20}\Z", re.ASCII)
CODE_RE = re.compile(r"[A-Z]{2}\Z", re.ASCII)
API_BASE = "https://api.gleif.org/api/v1/lei-records/"
SOURCE_TERMS = "https://www.gleif.org/en/meta/lei-data-terms-of-use"
SOURCE_LICENSE = "CC0-1.0"
MAX_BYTES = 2_000_000

# Legal-entity identifiers published in the issuers' own imprint/legal pages;
# the legal-entity names/statuses still come from a fresh GLEIF response.
PILOT_LEIS = {
    "529900K9B0N5BT694847": "https://www.allianz.com/de/impressum-allianz-se.html",
    "529900MUF4C20K50JS49": "https://www.munichre.com/de/allgemein/impressum.html",
    "529900KIN5BE45V5KB18": "https://www.hannover-re.com/de/impressum",
}


class GLEIFPilotError(ValueError):
    """Unverified entity identity or unsupported storage/request boundary."""


def valid_lei(lei: str) -> bool:
    if not isinstance(lei, str) or not LEI_RE.fullmatch(lei):
        return False
    digitized = "".join(str(ord(c) - 55) if c.isalpha() else c for c in lei)
    return int(digitized) % 97 == 1


def _reject_duplicate_json(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise GLEIFPilotError("duplicate GLEIF JSON key")
        result[key] = value
    return result


def parse_lei_response(original: bytes, expected_lei: str) -> dict:
    """Return bounded Level-1 legal-entity fields and a raw-byte checksum."""
    if expected_lei not in PILOT_LEIS or not valid_lei(expected_lei):
        raise GLEIFPilotError("only officially seeded LEIs are accepted in this pilot")
    if type(original) is not bytes or not 0 < len(original) <= MAX_BYTES:
        raise GLEIFPilotError("GLEIF source bytes must be nonempty and at most 2 MB")
    try:
        obj = json.loads(original.decode("utf-8-sig"),
                         object_pairs_hook=_reject_duplicate_json,
                         parse_constant=lambda x: (_ for _ in ()).throw(GLEIFPilotError("nonfinite JSON value")))
    except (UnicodeError, json.JSONDecodeError, TypeError) as exc:
        raise GLEIFPilotError("invalid GLEIF JSON") from exc
    if not isinstance(obj, dict) or not isinstance(obj.get("data"), dict):
        raise GLEIFPilotError("expected one GLEIF JSON:API legal-entity record")
    data = obj["data"]
    attrs = data.get("attributes")
    if data.get("type") != "lei-records" or data.get("id") != expected_lei or not isinstance(attrs, dict) or attrs.get("lei") != expected_lei:
        raise GLEIFPilotError("GLEIF LEI response has an unexpected identity or type")
    entity, registration = attrs.get("entity"), attrs.get("registration")
    if not isinstance(entity, dict) or not isinstance(registration, dict):
        raise GLEIFPilotError("missing legal entity or registration information")
    legal_name = entity.get("legalName")
    address = entity.get("legalAddress")
    if not isinstance(legal_name, dict) or not isinstance(address, dict):
        raise GLEIFPilotError("missing legal name or legal jurisdiction")
    name = legal_name.get("name")
    country = address.get("country")
    entity_status, registration_status = entity.get("status"), registration.get("status")
    if not isinstance(name, str) or not 0 < len(name.strip()) <= 500:
        raise GLEIFPilotError("invalid legal entity name")
    if not isinstance(country, str) or not CODE_RE.fullmatch(country):
        raise GLEIFPilotError("invalid entity country code")
    if not isinstance(entity_status, str) or not 0 < len(entity_status) <= 80:
        raise GLEIFPilotError("invalid entity status")
    if not isinstance(registration_status, str) or not 0 < len(registration_status) <= 80:
        raise GLEIFPilotError("invalid LEI registration status")
    meta = obj.get("meta") or {}
    if not isinstance(meta, dict) or not isinstance(meta.get("goldenCopy", {}), dict):
        raise GLEIFPilotError("invalid Golden Copy metadata")
    published = meta.get("goldenCopy", {}).get("publishDate")
    if published is not None and (not isinstance(published, str) or len(published) > 40):
        raise GLEIFPilotError("invalid Golden Copy publication date")
    return {
        "lei": expected_lei, "legal_name": name.strip(), "country_code": country,
        "entity_status": entity_status, "registration_status": registration_status,
        "golden_copy_published_at": published,
        "source_api_url": API_BASE + expected_lei,
        "issuer_lei_assertion_url": PILOT_LEIS[expected_lei],
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "source_license": SOURCE_LICENSE, "source_terms_url": SOURCE_TERMS,
        "relationship_status": "not_fetched",
        "underwriting_role": "not_determined_from_lei",
        "insured_exposure_status": "not_available",
    }


def fetch_lei(lei: str) -> bytes:
    if lei not in PILOT_LEIS or not valid_lei(lei):
        raise GLEIFPilotError("only fixed public issuer-verified LEIs may be fetched")
    req = Request(API_BASE + lei, headers={"Accept": "application/vnd.api+json",
                                          "User-Agent": "OpenCatastrophe LEI research pilot (public GitHub repository)"})
    with urlopen(req, timeout=25) as res:
        if res.status != 200 or res.geturl() != API_BASE + lei:
            raise GLEIFPilotError("unexpected GLEIF API HTTP response or redirect")
        blob = res.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES:
        raise GLEIFPilotError("GLEIF API exceeded size limit")
    return blob


def ingest_verified_lei_pilot(output: Path, sources: dict[str, bytes], observed_at: str) -> dict:
    """Atomic replacement of a small CAT-only *identity* table."""
    if set(sources) != set(PILOT_LEIS):
        raise GLEIFPilotError("pilot requires exactly the three published LEIs")
    if not isinstance(observed_at, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\+00:00", observed_at):
        raise GLEIFPilotError("require explicit UTC capture timestamp")
    # Verify original bytes completely before mutating the target database.
    rows = [parse_lei_response(sources[lei], lei) for lei in sorted(PILOT_LEIS)]
    output = Path(output).expanduser()
    if output.is_symlink() or not output.is_file():
        raise GLEIFPilotError("requires an existing regular CAT registry SQLite file, not a symlink")
    with sqlite3.connect(output) as con:
        if (con.execute("PRAGMA application_id").fetchone()[0] != CAT_APP_ID or
                con.execute("PRAGMA user_version").fetchone()[0] != CAT_SCHEMA_VERSION):
            raise GLEIFPilotError("refusing unknown or non-CAT database")
        con.execute("PRAGMA foreign_keys=ON")
        if con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cat_source_candidate'").fetchone() is None:
            raise GLEIFPilotError("CAT source registry must be materialized before GLEIF identity import")
        # DDL executes separately; the three verified identities refresh together.
        con.execute("""CREATE TABLE IF NOT EXISTS cat_gleif_legal_entity (
          lei TEXT PRIMARY KEY,
          legal_name TEXT NOT NULL,
          country_code TEXT NOT NULL,
          entity_status TEXT NOT NULL,
          registration_status TEXT NOT NULL,
          golden_copy_published_at TEXT,
          source_api_url TEXT NOT NULL,
          issuer_lei_assertion_url TEXT NOT NULL,
          source_sha256 TEXT NOT NULL,
          source_license TEXT NOT NULL CHECK(source_license='CC0-1.0'),
          source_terms_url TEXT NOT NULL,
          relationship_status TEXT NOT NULL CHECK(relationship_status='not_fetched'),
          underwriting_role TEXT NOT NULL CHECK(underwriting_role='not_determined_from_lei'),
          insured_exposure_status TEXT NOT NULL CHECK(insured_exposure_status='not_available'),
          observed_at_utc TEXT NOT NULL
        )""")
        with con:
            # Do not delete other datasets or tables in this dedicated CAT DB.
            for row in rows:
                con.execute("""INSERT INTO cat_gleif_legal_entity VALUES
                 (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                 ON CONFLICT(lei) DO UPDATE SET
                 legal_name=excluded.legal_name,country_code=excluded.country_code,
                 entity_status=excluded.entity_status,registration_status=excluded.registration_status,
                 golden_copy_published_at=excluded.golden_copy_published_at,
                 source_api_url=excluded.source_api_url,
                 issuer_lei_assertion_url=excluded.issuer_lei_assertion_url,
                 source_sha256=excluded.source_sha256,source_license=excluded.source_license,
                 source_terms_url=excluded.source_terms_url,
                 relationship_status=excluded.relationship_status,underwriting_role=excluded.underwriting_role,
                 insured_exposure_status=excluded.insured_exposure_status,
                 observed_at_utc=excluded.observed_at_utc""",
                  tuple(row[k] for k in (
                      "lei","legal_name","country_code","entity_status",
                      "registration_status","golden_copy_published_at","source_api_url",
                      "issuer_lei_assertion_url","source_sha256","source_license",
                      "source_terms_url","relationship_status","underwriting_role",
                      "insured_exposure_status")) + (observed_at,))
        return {
            "evidence_class": "PUBLIC_CC0_GLEIF_LEVEL1_LEGAL_ENTITY_IDENTITY_ONLY",
            "lei_records_verified": len(rows),
            "source_sha256_by_lei": {row["lei"]: row["source_sha256"] for row in rows},
            "legal_entity_names_from_source": {row["lei"]: row["legal_name"] for row in rows},
            "source_rows_in_git": False, "parent_relationships_verified": False,
            "portfolio_exposure_created": False, "model_source_admission": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true", help="fetch 3 fixed records from official GLEIF API")
    mode.add_argument("--offline-dir", type=Path, help="directory with exactly named LEI.json files")
    parser.add_argument("--out", required=True, type=Path,
                        help="existing dedicated CAT SQLite database created by export_cat_source_registry_sqlite.py")
    args = parser.parse_args()
    blobs = ({lei: fetch_lei(lei) for lei in sorted(PILOT_LEIS)} if args.fetch else
             {lei: (args.offline_dir / (lei + ".json")).read_bytes() for lei in sorted(PILOT_LEIS)})
    observed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(ingest_verified_lei_pilot(args.out, blobs, observed),
                     sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GLEIFPilotError, OSError, sqlite3.DatabaseError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(1)
