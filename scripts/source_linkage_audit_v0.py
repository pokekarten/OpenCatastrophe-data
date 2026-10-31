#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic, offline source-landscape inventory and conservative linkage audit.

This scans *all* canonical landscape shards. It does not download providers,
approve rights, validate source bytes, or authorize any CAT model input.
Relationship recipes are hypotheses for subsequent scientific/source review.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.parse import urlsplit

if __package__:
    from .source_landscape_contract import DEFAULT_LANDSCAPE_DIR, load_landscape_shards
else:
    from source_landscape_contract import DEFAULT_LANDSCAPE_DIR, load_landscape_shards


# Non-exhaustive researched examples: every endpoint must exist in the canonical
# source landscape. "lineage" is not independent model validation.
RECIPES = (
    (
        "dwd-radklim-catrare",
        ("dwd.radklim.rw.v2017.002", "dwd.catrare.w3-eta.v2025.01"),
        "shared_lineage",
        "CatRaRE catalogue KEY_FIELD and release; RADKLIM grid cell, UTC hour and projection",
        "Confirm exact RADKLIM correction files, CatRaRE event polygon/CSV ID, threshold W3 and version; current 2026.01 release differs from pinned 2025.01 candidate.",
        "Do not count a CatRaRE event as independent confirmation of its parent RADKLIM precipitation or infer insured flood loss.",
    ),
    (
        "usgs-event-products",
        ("usgs.anss.comcat", "usgs.shakemap", "usgs.comcat.dyfi", "usgs.comcat.losspager"),
        "same_event_mixed_observed_modelled",
        "ComCat event ID and product source/type/code/update-time; spatial geometry and shaking intensity units",
        "Preserve DYFI response counts and spatial aggregation, preferred-product revisions, ShakeMap measured/modelled masks and PAGER input dependencies.",
        "PAGER modelled economic losses are not observed or insured losses; DYFI crowd intensities are not building damage or independent exposure.",
    ),
    (
        "noaa-spc-ncei",
        ("noaa.ncei.storm-events", "noaa.spc.svrgis.2025"),
        "same_underlying_reporting_lineage",
        "NWS report/event provenance, UTC/local time interpretation, year, hazard class, location and release changelog",
        "SPC GIS originates in Storm Data; versions and reported identifiers change; artificial short tornado paths are not real swaths.",
        "Never call SPC versus Storm Events an independent validation or add reports as distinct events without reconciliation.",
    ),
    (
        "dfo-hanze-flood-events",
        ("dfo.floodrecords.v0.9.0", "hanze.historical-flood-impacts.v3.0.2-beta"),
        "candidate_event_reconciliation",
        "Country/region, interval overlap, flood mechanism, event identity and provenance",
        "Check DFO v0.9.0 claimed end-2023 versus CSV January-2024 rows, M/D/YY dates, multi-country events and HANZE historical event definitions.",
        "Affected area and fatalities are not observed flood depth or insured loss; non-matches are not zero events.",
    ),
    (
        "dfo-gfm-flood-validation",
        ("dfo.floodrecords.v0.9.0", "copernicus.cems.gfm.v4.1.1"),
        "manual_spatiotemporal_event_challenge",
        "Event date window, satellite acquisition time, geographic polygon, flood type and observation quality",
        "Only compare periods and locations with actual Sentinel-1 acquisition; preserve cloud/urban/layover exclusions and DFO event definitions.",
        "Do not interpret uncovered footprint as dry or compare a catalogue area to a depth raster.",
    ),
    (
        "openfema-nfip-policy-claims",
        ("fema.openfema.nfip-redacted-policies.v3", "fema.openfema.nfip-redacted-claims.v3"),
        "aggregate_only_insurance",
        "County or census tract, loss date, policy-effective/termination interval and covered peril",
        "Policy counts require in-force reconstruction; anonymized geocoordinates are rounded and not property keys; monitor censoring and changes to public metadata.",
        "Do not match individual homes, equate reporting year with payment year, or treat NFIP as all US insurers.",
    ),
    (
        "nfip-building-context",
        ("fema.openfema.nfip-redacted-claims.v3", "usace.nsi.base.2026"),
        "aggregate_only_exposure_context",
        "Common county/census tract or separately validated region geometry and comparable building classes",
        "NSI is a modelled structure inventory; avoid using rounded claim coordinates as a point-to-building join.",
        "Do not manufacture property-level claims, real insurance sums or insurer-specific portfolios.",
    ),
    (
        "fire-observation-lineage",
        ("nasa.lance.firms.active-fire", "nasa.modis.mcd64a1.v6.1", "global.fire-atlas.v20260408"),
        "partly_shared_remote_sensing_lineage",
        "Sensor/platform, detection or burn day UTC, pixel footprint, QA and exact product release",
        "Global Fire Atlas reconstructs individual fires from burned-area data; do not append releases or regard derived tiles as independent truth.",
        "Hotspots are not full burned polygons, radiative power is not insured loss and derived fire counts must not be double-counted.",
    ),
    (
        "tropical-cyclone-track-footprint",
        ("noaa.ncei.ibtracs.v04r01", "noaa.ncei.hursat-b1.v06", "compass.tc.affected-areas.d1p4.v1"),
        "shared_track_lineage",
        "IBTrACS storm identifiers, basin, UTC timestamps, center trajectory, track version and hazard-specific footprint grid",
        "HURSAT storm centering and COMPASS modeled fields depend on IBTrACS; preserve method-specific wind, rain and surge estimates separately.",
        "Do not assume three independent event observations or sum wind, rain and surge impacts as separate insured events.",
    ),
    (
        "flood-satellite-product-comparison",
        ("copernicus.cems.gfm.v4.1.1", "cloudtostreet.global-flood-database.v1"),
        "manual_footprint_holdout",
        "Only temporally overlapping flood IDs, satellite footprint, CRS, valid-pixel masks and land/water baseline",
        "Historical MODIS maximum-water composites and Sentinel-1 event masks have different revisit time, quality limits and reuse rights.",
        "Never treat a non-overlapping year, missing pixel or data gap as proof of model error.",
    ),
    (
        "europe-wind-building-context",
        ("climk.winds.storm-footprints.v2", "eubucco.buildings.v0.2"),
        "spatial_exposure_proxy_only",
        "Exact event footprint, projection, building footprint, construction vintage and 10 m gust definition",
        "Check individual storm source/model selections, EUBUCCO country licences, geometry vintages and building uncertainty.",
        "Building count is not insured TIV; neither weather intensity nor a building geometry alone provides claims.",
    ),
    (
        "earthquake-shaking-vulnerability",
        ("usgs.shakemap", "gem.global-vulnerability-model", "gem.global-exposure-model"),
        "model_compatibility_requires_science_rights",
        "Seismic intensity measure and units, GEM taxonomy, occupancy, value basis, event/asset location",
        "ShakeMap versions can change; GEM noncommercial licenses and separate high-resolution rights require explicit review; check intensity measure conversion and exposed value definitions.",
        "No automatic translation of MMI to PGA/SA, model replacement cost to insured value, or output to historical claims.",
    ),
    (
        "coastal-tide-gauge-comparison",
        ("gesla.global-extreme-sea-level.v3", "noaa.coops.water-levels"),
        "station_time_datum_alignment",
        "Station identity/position, UTC time, sampling interval, vertical datum, quality flags and observation period",
        "GESLA has differently licensed Part 1/Part 2; NOAA preliminary versus verified series and datum conversions must be controlled.",
        "Do not add sea levels with mismatched datums or assume co-located records are independent observations.",
    ),
    (
        "building-lineage-overture-ghsl",
        ("overture.maps.buildings", "ec-jrc.ghsl.ghs-obat.r2024a"),
        "derived_building_attributes",
        "Exact 2024-07-22 Overture release, footprint identity, country, building attributes and geometries",
        "GHSL GHS-OBAT integrates an Overture snapshot; prove release IDs and per-representation rights before a direct object-level join.",
        "Do not double count identical buildings, assume all attributes measured, or infer replacement values and insured TIV.",
    ),
    (
        "heavy-rain-versus-flood-impacts",
        ("dwd.catrare.w3-eta.v2025.01", "hanze.historical-flood-impacts.v3.0.2-beta"),
        "candidate_event_reconciliation",
        "Event date interval, German municipality/NUTS vintage, precipitation polygon and documented flood mechanism",
        "Cross-hazard causal link requires hydrology and lag analysis; HANZE impact region is not a CatRaRE storm footprint.",
        "Do not assert one-to-one events or infer causality from date/country proximity.",
    ),
)


def build_audit(shards, recipes=RECIPES):
    """Return reproducible discovery audit; never an input allow-list."""
    rows = []
    for path, payload in shards:
        for e in payload["entries"]:
            rows.append({
                "candidate_id": e["candidate_id"],
                "landscape_shard": path.name,
                "provider": e["provider"],
                "authoritative_url": e["authoritative_url"],
                "host": urlsplit(e["authoritative_url"]).hostname,
                "categories": e["categories"],
                "potential_roles": e["potential_roles"],
                "spatial_scope": e["spatial_scope"],
                "temporal_scope": e["temporal_scope"],
                "access_class_hint": e["access_class_hint"],
                "candidate_status": e["candidate_status"],
                "rights_review_status": e["rights_review_status"],
                "scientific_review_status": e["scientific_review_status"],
                "admission_status": e["admission_status"],
                "original_bytes_sha256_verified_by_this_audit": False,
                "external_licence_verified_by_this_audit": False,
                "scientific_harmonization_verified_by_this_audit": False,
                "automated_model_import_allowed_by_this_audit": False,
            })
    rows.sort(key=lambda e: e["candidate_id"])
    ids = {e["candidate_id"] for e in rows}
    if len(ids) != len(rows):
        raise ValueError("duplicate source candidate_id; no join audit")
    links = []
    rule_ids = set()
    for rule_id, endpoints, relation, keys, proof, prohibited in recipes:
        if rule_id in rule_ids or len(endpoints) < 2 or len(endpoints) != len(set(endpoints)):
            raise ValueError("duplicate or malformed source linkage recipe")
        rule_ids.add(rule_id)
        missing = set(endpoints) - ids
        if missing:
            raise ValueError("unknown source candidate IDs in " + rule_id + ": " + ", ".join(sorted(missing)))
        links.append({
            "recipe_id": rule_id,
            "source_candidate_ids": list(endpoints),
            "relationship": relation,
            "required_join_evidence": keys,
            "unverified_prerequisites": proof,
            "prohibited_inferences": prohibited,
            "validation_only": True,
            "automatic_source_join_allowed": False,
            "scientific_independence_proven": False,
            "model_input_admitted": False,
        })
    return {
        "schema_version": "source-linkage-audit-v0",
        "scope": "Canonical non-admission landscape metadata only; no real source download, entitlement check or model-ready scientific join",
        "source_count": len(rows),
        "shard_count": len(shards),
        "sources_not_admitted": sum(r["admission_status"] == "not_admitted" for r in rows),
        "source_reviews_not_completed": sum(r["rights_review_status"] == "not_reviewed" or r["scientific_review_status"] == "not_reviewed" for r in rows),
        "source_host_counts": dict(sorted(Counter(r["host"] for r in rows).items())),
        "linkage_recipe_count": len(links),
        "source_inventory": rows,
        "linkage_hypotheses": sorted(links, key=lambda x: x["recipe_id"]),
        "this_report_is_a_model_input_allowlist": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landscape-dir", type=Path, default=DEFAULT_LANDSCAPE_DIR)
    parser.add_argument("--out", type=Path, help="Optional report destination; otherwise stdout")
    args = parser.parse_args()
    audit = build_audit(load_landscape_shards(args.landscape_dir))
    output = json.dumps(audit, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.out is None:
        print(output, end="")
    else:
        args.out.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
