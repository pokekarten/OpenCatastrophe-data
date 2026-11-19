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
        "dwd-catrare-2026-threshold-overlap",
        ("dwd.radklim.rw.v2017.002", "dwd.catrare.w3-eta.v2026.01", "dwd.catrare.t5-eta.v2026.01"),
        "shared_lineage_distinct_detection_thresholds",
        "RADKLIM input version, CatRaRE v2026.01 variant-qualified KEY_FIELD and Event_ID, UTC interval, projection and event polygon",
        "W3 and T5 select overlapping extreme-rainfall objects by different thresholds; compare matching spatial/time objects only after inspecting both original product bytes and event definitions.",
        "Do not sum W3 plus T5 event counts, call them independent observations or infer downstream flood loss from rain maxima.",
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
        "usgs-gfid-original-versus-derived-flood-lineage",
        ("usgs.gfid.original-contributed-files.2026", "usgs.gfid.geocoded-aggregated-duplicate-screen.2026", "dfo.floodrecords.v0.9.0", "hanze.historical-flood-impacts.v3.0.2-beta"),
        "reused_upstream_records_and_unconfirmed_duplicate_screen",
        "GFID Source_ID and provider tags; original DFO/HANZE file version and SHA256; event interval, country source fields, geocoding method and representative EPSG4326 location",
        "Compare GFID original DFO_FloodData.csv/HANZE_Events_v3.csv schemas, vintage and file hashes to our separately pinned releases. Inspect Potential_Duplicate_Events.csv 30-day/25-km methodology, third-party licences and resulting one-to-many identity hypotheses.",
        "USGS GFID derived, geocoded and source-original files are NOT independent evidence; 30-day/25-km flags are NOT confirmed duplicate events and point coordinates are NOT flood footprints or insured losses.",
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
        "calfire-dins-frap-incident-identity-candidate",
        ("us.calfire.dins.structure-damage", "us.calfire.frap.historical-fire-perimeters.firep25-1"),
        "same_fire_possible_but_incident_identity_unverified",
        "DINS INCIDENTNUM, CALFIREUNIT, INCIDENTSTARTDATE and HAZARDTYPE=Fire versus FRAP INC_NUM, UNIT_ID, ALARM_DATE, YEAR_ and optional IRWINID; both exact provider snapshot SHA256",
        "Resolve official two-system incident-number crosswalk, one-to-many or duplicate perimeter cases and exact event dates. The offline calfire_dins_frap_identity_preflight_v0.py only flags synthetic or externally prepared header-level candidates; it never proves identity or fetches features. Check FRAP firep25_1 revision, mapped geometry and DINS survey selection before any spatial test.",
        "Do not join events on names, stripped incident suffixes alone or spatial proximity; do not equate final perimeters with observed building burn intensity, missing DINS records with zero damage, inspected counts with total building exposure, or any damage class with paid or insured loss.",
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
        "luxembourg-act2013-eubucco-versus-act2023v2-rooflineage",
        ("eubucco.buildings.v0.2", "lu.act.bd-l-bati3d-2023"),
        "same_provider_family_different_vintages_independence_unproven",
        "Luxembourg EUBUCCO LU00/NUTS2016 source code gov-luxembourg and upstream ACT 2013 Bâtiments 3D LoD1 metadata; ACT2023v2 original buildingid/gml_id and 2023 roof extent; versioned provider SHA256, geometry-source family, CRS EPSG3035 versus EPSG2169, observed date and crosswalk/match uncertainty",
        "Provider-hosted EUBUCCO v0.2 original metadata workbook identifies gov-luxembourg as Administration du cadastre et de la topographie Bâtiments 3D (LoD1), 2013, CC0, EPSG2169. Its harmonised LU00 Parquet includes 144088 government-labelled geometry records of 186171 total. ACT2023v2 has 238189 roof-derived polygons from 2023 surveys. Confirm exact historical raw ACT LoD1 source and common geometry lineage, EUBUCCO ODbL downstream obligations, native coordinate axis via independent controls, observation-vintage and roof-vs-ground segmentation. Source-family relationship is verified; individual building equivalence or shared source bytes are NOT verified.",
        "Do not treat EUBUCCO gov-luxembourg geometries and ACT2023v2 as independent observations, equate older ground/LoD1 polygons with newer roof extents, subtract counts as missing buildings, infer stable building identity from nearest overlap, or promote either to insurer exposure, insured TIV, vulnerability or validation holdout without separate reviews.",
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

    (
        "jrc-flood-depth-versus-gfm-shared-source",
        ("ec.jrc.satellite-flood-depth-europe.2015-2024", "copernicus.cems.gfm.v4.1.1"),
        "same_sentinel1_extent_lineage_derived_depth",
        "Event identity/date window, Sentinel-1 scene and acquisition, footprint, valid pixel mask, depth centimetres, original GFM extent and exact product release",
        "JRC depth reconstruction uses GFM-derived extents and a topographic adjustment; official JRC catalogue currently documents 2015-2024 while third-party EuroFlood reports later archive coverage. Check 9999 water-body mask, changes in year coverage, resampling, and original artifact hashes before a comparison.",
        "Do not claim independent flood observations, treat centimetres as metres, read dummy 9999 as a valid depth, or infer insured losses from derived water depths.",
    ),
    (
        "openbuildingmap-overture-ghsl-common-upstream",
        ("gfz.openbuildingmap.global.2025", "overture.maps.buildings", "ec-jrc.ghsl.ghs-obat.r2024a"),
        "partly_shared_footprints_and_ghsl_derived_attributes",
        "Exact OSM/Google/Microsoft/Overture release and tile identity, original geometry source family, Overture GERS or documented original building ID, CRS and polygon overlap with adjudicated splits",
        "OpenBuildingMap conflates OSM, Google and Microsoft footprints; Overture has potentially overlapping building origins and GHS-OBAT carries Overture-linked GHSL-derived attributes. Verify each lineage path and per-field source; no independent validation from a second ML-derived height.",
        "Do not sum input and derivative footprint counts, assume shared OSM IDs survive conflation, infer property-level insured TIV or treat modelled height as observed surveying.",
    ),
    (
        "aqueduct-v2-versus-jrc-flood-hazard",
        ("wri.aqueduct-flood-hazard.v2.2020", "ec-jrc.cems.global-river-flood-hazard-maps.2026"),
        "distinct_modelled_return_period_surface_challenge",
        "Hazard mechanism riverine only, matching return period, climate epoch, defended/undefended assumption, depth metres, grid/CRS, shoreline and exact model release",
        "WRI Aqueduct 2020 river maps were bias-corrected in October 2020 and omit flood defence; JRC 2026 has different basins, models and spatial gaps. Use a frozen intersection sample, with observed high-quality events only as separate holdout.",
        "Do not treat return-period rasters as historical event loss observations, sum modelled flood occurrences, or assume separate hazards have independent underlying model assumptions.",
    ),
    (
        "gem-global-seismic-exposure-vulnerability",
        ("gem.global-seismic-hazard-map.v2026.1", "gem.global-exposure-model.v2026.0.0", "gem.global-vulnerability-model.v2026.0.0"),
        "three_component_hazard_exposure_vulnerability_model_dependency",
        "Hazard PGA in g on Vs30 800m/s reference rock at 10% exceedance in 50y, exposure replacement cost and GEM taxonomy, vulnerability intensity measure, regional release and model mapping",
        "A single exceedance probability map is not a complete stochastic event set and cannot directly produce AAL or exceedance curves. Map soil conditions and taxonomy with uncertainty, freeze separate product rights and avoid circular validation of a GEM model with another GEM derivative.",
        "Do not equate replacement cost with insured values, interpret a map exceedance value as an event loss, or redistribute NC-SA data for commercial CAT services without a licence.",
    ),
    (
        "iris-ibtracs-storm-dependence",
        ("imperial.iris.synthetic-tropical-cyclones.2024", "noaa.ncei.ibtracs.v04r01", "noaa.ncei.hursat-b1.v06"),
        "synthetic_tracks_share_observational_input_family",
        "IRIS input IBTrACS v04r00 1980-2021, independent current v04r01 identity, storm and basin/year labels, 3-hour track timestamps, wind averaging period and record inclusion rules",
        "IRIS fits post-maximum-intensity storms using IBTrACS and ERA5; HURSAT is also storm-centred on IBTrACS. Validate different vintages and TC life-cycle coverage and compare STORM v4 only after matched basin/year/wind definitions.",
        "Do not mistake independent simulated years for interannual temporal dependence, treat synthetic IRIS events as observed, or call reprocessed IBTrACS products independent ground truth.",
    ),
    (
        "aqueduct-water-risk-versus-aqueduct-floods",
        ("wri.aqueduct.water-risk-atlas.v4.0", "wri.aqueduct-flood-hazard.v2.2020"),
        "same_provider_distinct_product_not_direct_event_join",
        "WRI product/version, hydrologic basin topology, climate horizon, indicator name and units versus flood GeoTIFF return-period and coastal/riverine parametrization",
        "Aqueduct 4.0 Water Risk Atlas indicators and Aqueduct Floods v2 raster hazard are separate methods, scales and eras. Review any shared upstream hydrological models and explicit spatial crosswalk before using one as a covariate for the other.",
        "Do not substitute water-stress indices for flood depths, use country rankings as site measurements, or assume WRI 4.0 labels update Aqueduct Floods v2 data.",
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
