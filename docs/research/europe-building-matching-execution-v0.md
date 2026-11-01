<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# European building data: metadata registry to reproducible geometric pilot v0

**Date:** 2026-11-01. **Scope:** research-only; NO real source bytes admitted.

## Current foundation

- Main repository now contains the five discovery catalogue shards merged from PRs #900–#904, totalling 87 extra candidates. These are NOT licensed raw inputs.
- The dedicated insurance Neon project remains separate from TCG/Pokémon data.
- Five GitHub-blob-pinned canonical JSON metadata documents were added to `registry.source_record` at main commit `c3a9924047d4ceb52a58f10025fa91e13e4f403b`, all with `classification=landscape_candidate`, `review_status=non_admission_discovery_only`, `rights_status=not_reviewed`, `admissible_for_raw=false`.
- Post-sync observed Neon counts: 94 source documents; 249 distinct landscape candidates; 0 real exposure units; no unreviewed model-input promotions.
- The repository SQL contract `research/sql/building_source_shortlist_v0.sql` creates the read-only view `research.building_source_shortlist_v0` over original raw metadata. This is not a second source of truth. The view was executed and verified in the dedicated insurance Neon DB, with 65 building-relevant research candidates, 19 possible height lanes, zero unsafe promotions and zero missing Git blob/commit lineage, as of 2026-11-01. These counts will change with later canonical synchronization.

## Explore without approving sources

Example read-only SQL, with no customer or policy records:

```sql
SELECT candidate_id, candidate_name, spatial_scope,
       possible_id_or_attribute_lane, possible_footprint_lane,
       possible_height_lane, possible_attributes_lane,
       rights_review_status, model_input_ready,
       canonical_path, canonical_blob_sha, canonical_commit_sha
FROM research.building_source_shortlist_v0
WHERE possible_id_or_attribute_lane OR possible_height_lane
ORDER BY candidate_id;
```

The flags are **heuristic research discovery tags**, not proof that attributes exist in a file or that matching is safe. All the displayed sources have unreviewed rights and are excluded from model input. A catalogue ID may describe an ODbL polygon subset or a noncommercial 3D height dataset: check *file-level* licensing.

## Diagnostic algorithms and safe limits

**Exact common-building-ID diagnostic** (already on main):

```bash
python scripts/building_id_enrichment_v0.py \
  --base /tmp/synthetic-base.csv \
  --supplement /tmp/synthetic-registry.csv \
  --base-source-id synthetic.reference \
  --supplement-source-id synthetic.register
```

This only applies where the two columns are **documented as using the exact same building-ID namespace**; do not pass RNB, EHR, BAG, address, apartment, EPC or arbitrary EUBUCCO identifiers as though they were universal. It reports observed/modelled fills and conflicts without changing rows.

**Polygon-to-polygon exploratory match** (this PR, 2D GeoJSON only):

```bash
python -m pip install -r requirements-eu-flood-spatial.txt

python scripts/building_footprint_overlap_v0.py \
  --left /tmp/synthetic-eubucco.geojson --left-crs EPSG:3035 \
  --left-source synthetic.eubucco \
  --right /tmp/synthetic-cadastre.geojson --right-crs EPSG:4326 \
  --right-source synthetic.reference \
  --iou 0.60 --warning-overlap 0.20 \
  --out /tmp/building-overlap-diagnostic.json
```

Input contract: exactly one local GeoJSON FeatureCollection per side with **unique** `properties.building_id` and valid Polygon or MultiPolygon geometries. Declare actual input CRS explicitly. Per-file cap 5 MB and per-side maximum 1,500 features; no provider API operations, personal identifiers, downloads or source-data exports. The comparator reprojects into European equal-area `EPSG:3035` (metres) and uses STRtree candidate search, polygon overlap and intersection-over-union.

Only a unique high-IoU pair *without* another substantial overlapping neighbor is counted as a **candidate high-IoU unique geometric match**. Potential 1-to-many/many-to-one splits, low-IoU candidates and nonmatches are reported separately. The diagnostic never outputs local building IDs, correspondence tables, raw geometry or assumed replacement costs, and it never claims cadastral or insurer identity. The overlap and IoU thresholds are **illustrative** and require human adjudicated calibration (urban density, rows, agricultural annexes, footprint vintages) before real-data analysis. A high IoU is *not* an admitted matching decision.

No automatic copy of EUBUCCO rows to Neon or any derived value propagation is permitted merely by successful geometry overlap. The height field is a separate task: ground-normalized LiDAR roof elevation and vertical datum, observation date and geometry matching need validation first.

## First source-licensed field test

1. Freeze exact official Luxembourg BD-L-BATI3D 2D licence (CC0 claimed by provider), GeoPackage resource version and file checksum; compare bounded polygon subset to EUBUCCO Luxembourg **only after** the EUBUCCO country/tile rights and same reference period are checked. Convert sources to local GeoJSON **outside Git**, with original source bytes and confidential data excluded from Git/Neon.
2. Calibrate geometry overlap quality against a manually audited sample stratified urban/rural, split/merge building constructions, coordinate precision and building size; use false-match and missing-building counts, not just total matches.
3. Repeat with Estonian EHR + TalTech material sample for documented building-ID and construction-attribute evidence after licence/privacy review.
4. Stage only aggregated validation results and SHA-256 original asset receipts until exact-source data rights and scientific admission gates are complete. Store large spatial tiles in versioned external object storage, NOT in the lightweight metadata Neon project.

## Acceptance and blockers

A real measurable advancement requires: original asset receipt with SHA256 and licence, file/record schema and CRS, provider building-object identity semantics, source timing and lineage, manual spatial match precision/recall, safe dimension-specific nonnull-rate changes, independently measured height comparisons, and explicit suppression of customer/private building links.

The SQL view and diagnostic code are reproducible and offline; **no original third-party building bytes, true insured values, or productive CAT simulation inputs were imported as part of this change.**
