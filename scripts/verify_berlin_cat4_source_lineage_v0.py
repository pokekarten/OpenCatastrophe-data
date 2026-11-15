#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only identity check between CAT4 research metadata and isolated BLD4 sample.

No source bytes, geometry, private original IDs, claims or model permissions are
created, downloaded, joined at object level, or exported by this script.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import quote

from scripts.source_landscape_contract import load_landscape_shards

CANDIDATE_ID = "de.berlin.alkis-gebaeude.wfs"
CATALOGUE = "https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a"
PUBLISHER = "Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin"
CANONICAL_SHARD = "landscape/sources-berlin-alkis-pilot-20261101.json"
WFS_ROOT = "https://gdi.berlin.de/services/wfs/alkis_gebaeude"
WFS_LAYER = "alkis_gebaeude:gebaeude"
RESEARCH_CAT4_APP = 0x43415434  # CAT4; derived non-admission source metadata
BUILDING_BLD4_APP = 0x424C4434  # BLD4; source-derived, temporary polygons
BUILDING_PROFILE = "berlin_alkis_five_derived_footprints_cat4_staging_v0"
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class LineageError(ValueError):
    """Provenance cannot be corroborated within strict non-admission limits."""


def _read_only(path: Path, app_id: int) -> sqlite3.Connection:
    if (not isinstance(path, Path) or not path.is_absolute()
            or path.suffix != ".sqlite" or not path.name.endswith(".cat.sqlite")
            or path.is_symlink() or not path.is_file()):
        raise LineageError("require existing absolute, regular, unsymlinked .cat.sqlite")
    if not 0 < path.stat().st_size <= 64 * 1024 * 1024:
        raise LineageError("missing, empty or oversized CAT research database")
    # URI percent-encoding keeps ?/# in valid file names from becoming SQL
    # URI parameters. Query-only mode is set before inspecting any tables.
    uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, timeout=3.0)
    try:
        db.execute("PRAGMA query_only=ON")
        if (db.execute("PRAGMA application_id").fetchone()[0] != app_id
                or db.execute("PRAGMA user_version").fetchone()[0] != 1):
            raise LineageError("CAT4/BLD4 application identity or schema version mismatch")
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise LineageError("SQLite quick integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise LineageError("SQLite foreign key violations")
        return db
    except BaseException:
        db.close()
        raise


def verify(registry: Path, buildings: Path) -> dict:
    """Compare independent source-identity metadata; never join building rows."""
    if registry.resolve() == buildings.resolve():
        raise LineageError("CAT4 registry and BLD4 building sample must be distinct")
    found = [entry for _path, shard in load_landscape_shards()
             for entry in shard["entries"] if entry["candidate_id"] == CANDIDATE_ID]
    if len(found) != 1:
        raise LineageError("canonical Berlin ALKIS candidate missing or duplicated")
    candidate = found[0]
    if (candidate["provider"] != PUBLISHER or candidate["authoritative_url"] != CATALOGUE
            or candidate["admission_status"] != "not_admitted"
            or candidate["rights_review_status"] != "not_reviewed"
            or candidate["scientific_review_status"] != "not_reviewed"):
        raise LineageError("Berlin source authority was silently promoted or changed")

    with closing(_read_only(registry, RESEARCH_CAT4_APP)) as research:
        rows = research.execute(
            """SELECT candidate_id,provider,authoritative_url,canonical_shard,
                      join_proven,model_admitted
                 FROM candidate WHERE candidate_id=?""", (CANDIDATE_ID,)
        ).fetchall()
        if len(rows) != 1 or rows[0] != (
            CANDIDATE_ID, PUBLISHER, CATALOGUE, CANONICAL_SHARD, 0, 0
        ):
            raise LineageError("CAT4 research candidate identity/admission mismatch")

    with closing(_read_only(buildings, BUILDING_BLD4_APP)) as building:
        p = building.execute(
            """SELECT schema_id,source_service,source_feature_type,
                      source_response_sha256,retrieved_at_utc,source_rights,
                      building_vintage,boundary_vintage,region_source,model_admitted
                 FROM provenance WHERE singleton=1"""
        ).fetchall()
        if len(p) != 1:
            raise LineageError("missing or repeated source provenance")
        (profile, service, layer, sha, utc, rights, vintage,
         boundary_year, region_source, admitted) = p[0]
        if (profile != BUILDING_PROFILE or service != WFS_ROOT or layer != WFS_LAYER
                or rights != "dl-de-zero-2.0"
                or vintage != "current_mutable_unknown_feature_date"
                or boundary_year != 2021
                or region_source != "geoBoundaries 2021 + Eurostat NUTS2021 10M independently verified"
                or admitted != 0):
            raise LineageError("BLD4 source/vintage/rights/model authority mismatch")
        if not isinstance(sha, str) or HEX_SHA256.fullmatch(sha) is None:
            raise LineageError("no full source response SHA-256 receipt")
        try:
            moment = datetime.fromisoformat(utc)
        except (TypeError, ValueError) as exc:
            raise LineageError("invalid provenance UTC timestamp") from exc
        if moment.tzinfo is None or moment.utcoffset() != timezone.utc.utcoffset(moment):
            raise LineageError("source retrieval time is not UTC")
        rows = building.execute(
            """SELECT count(*),count(DISTINCT nuts1_region),
                      min(nuts1_region),max(nuts1_region),
                      min(footprint_area_m2),min(length(projected_epsg25833_geometry_wkb))
                 FROM building_sample"""
        ).fetchone()
        if (rows is None or not 1 <= rows[0] <= 5 or rows[1] != 1
                or rows[2] != "DE3" or rows[3] != "DE3"
                or rows[4] is None or rows[4] <= 0
                or rows[5] is None or rows[5] < 9):
            raise LineageError("BLD4 rows/region/area/geometry shape not consistent")

    return {
        "profile": "berlin-alkis-cat4-bld4-readonly-source-identity-v0",
        "candidate_id": CANDIDATE_ID,
        "source_response_sha256": sha,
        "retrieved_at_utc": moment.isoformat(),
        "staged_building_polygon_count": rows[0],
        "region_code": "DE3",
        "canonical_candidate_found": True,
        "sqlite_application_ids_distinct": True,
        "source_identity_metadata_consistent": True,
        "source_bytes_revalidated_by_this_report": False,
        "physical_building_identity_proven": False,
        "independent_scientific_validation_proven": False,
        "insurer_exposure_or_tiv_inferred": False,
        "model_input_admitted": False,
        "database_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry-cat4", type=Path, required=True)
    parser.add_argument("--building-bld4", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = verify(args.registry_cat4, args.building_bld4)
    except (LineageError, OSError, sqlite3.Error, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
