<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Building-topography and historical-damage evidence: US pilot (2026-11-01)

**Status:** non-admission research, metadata only. No external source bytes, assessed local buildings, insurer portfolios, loss records or model-ready inputs were acquired or imported. Canonical discovery records are in `landscape/sources-building-topography-damage-validation-2026.json`; the matching Markdown view is generated, not independently edited.

## Distinct source products and what they actually measure

| Source | Evidence type | Possible CAT model improvement | Non-negotiable limitation |
| --- | --- | --- | --- |
| USGS 3DEP seamless 1-m DEM (S1M) | Bare-earth terrain elevations, cloud-optimized 10-km tiles | Local surface-height reference for flood and topographic context | Not first-floor elevation, building height, observed flood depth, replacement value or insured location |
| USGS 3DEP original LiDAR LPC | Survey point cloud with classes and acquisition time | Building roof/ground separation; independent *from model-generated* geometry | Derived S1M DEM originates from LiDAR; those products are not mutually independent evidence |
| FEMA historic geospatial damage feature layer | Disaster-event points with assessment type and damage levels | Evaluate observed damage classifications by event and assessment method | `MOD` is **modelled damage**, not independent observed truth; `RS` is remote sensing, and `FA` is field assessed |
| xBD/xView2 | Satellite pre/post scene pairs and damage labels | Damage-state classification research and cross-event holdout design | Noncommercial rights warning; labels are not paid claims or financial damage; do not include as commercial model training input |

Official provider/documentation references:

- USGS 3DEP products and dataset distinctions: https://www.usgs.gov/3d-elevation-program/about-3dep-products-services
- USGS LiDAR LPC data-catalogue identity: https://data.usgs.gov/datacatalog/data/USGS%3Ab7e353d2-325f-4fc6-8d95-01254705638a
- USGS 1m seamless DEM catalogue: https://data.usgs.gov/datacatalog/data/USGS%3A4f34caac-f28f-4ea0-8d82-eafb2b8f9a5d
- FEMA exact public layer and schema: https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/FEMA_Historical_Geospatial_Damage_Assessment_Database/FeatureServer/0
- xBD original entry: https://xview2.org/dataset ; CMU project documentation: https://www.sei.cmu.edu/projects/xview-2-challenge/

## One scientifically bounded experiment, not a bulk import

1. Freeze one publicly documented U.S. disaster/area and event date, then enumerate actual provider availability *by exact tile or event ID*. Avoid implicit country-scale or provider-wide requests.
2. Select one versioned S1M 10-km tile and its source-work-unit metadata. Before acquisition, review exact resource URLs, provider terms, sampling bandwidth and approved storage destination; preserve byte counts/SHA-256, CRS, vertical datum, data collection time, no-data definition, pixel spacing, and lineage from source LiDAR. The terrain elevation should not be treated as a building's first-floor elevation.
3. If the same area has LiDAR, sample *one* official work unit and separate ground-class points from potential roof points, with quality flags and collection date. Never call the source LiDAR and the derived DEM two independent observations.
4. Compare only event-relevant FEMA assessment features. Keep `DIS_NUMBER`, `EVENT_DATE`, `PROD_DATE`, `IMG_DATE`, `ASMT_TYPE`, `DMG_TYPE`, `DMG_LEVEL` and `IN_DEPTH` with original source semantics. Inundation depth is in feet; conversion to metres requires a documented explicit transformation. Use `FA` field observations as candidate independent holdout only after leakage and independence checks. `MOD` cannot be used as independent observed validation.
5. Link any candidate damage point to a **separately reviewed** building polygon only through a dated spatial/identity rule that diagnoses many-to-one, missing, split and geometry-version conflicts. Never silently join `OBJECTID`, a geospatial point, insurer policy ID or USGS tile ID as if they were the same building identifier.
6. Test under separately frozen event-based training/validation splits, with uncertainty and sample-selection bias reported. Do not fit vulnerability curves or assert insurance loss correspondence from an ordinal damage label alone.

## Bounded implementation acceptance conditions

- New discoveries remain `not_admitted` until a source-specific rights and scientific review with a current model consumer exists.
- No automated retrieval, bulk layer export, imagery download, third-party bytes or model ingestion is introduced by this change.
- Reject/no-data/ambiguous elevation and any unreviewed vertical CRS/datum rather than assuming metres above mean sea level or floor height.
- The FEMA service's published edit timestamp is historical; confirm current endpoint, fields and actual available event vintages before a future probe.
- The xBD image/annotation rights require authoritative source-specific confirmation; the reported noncommercial restriction is a block for commercial model input.
- Added research-only `research_runners/fema_damage_assessment_preflight_v0.py` with nine synthetic negative/positive unit tests in `tests/test_fema_damage_assessment_preflight_v0.py`: bounds one-event projected geometry-free FeatureServer attributes, validates ArcGIS UTC epoch milliseconds, unique `OBJECTID`, FEMA `DMG_LEVEL` codes, finite nonnegative `IN_DEPTH` in **feet**, records dates and assessment codes without promoting modeled/unknown methods to observed truth; outputs aggregate counts only. Source observation-independence, commercial rights and any model use remain **not admitted**.
- Next causal PR: prove source-specific FEMA rights/currentness and a fixed source-event receipt; separately implement synthetic-only 3DEP source-lineage/vertical-datum rejection. Do not request real source bytes until exact acquisition scope and rights are reviewed.

## Source overlaps checked

Main already has `fema.usa-structures` and `usace.nsi.base.2026` as **exposure**-oriented sources plus general U.S. flood and quake observations, not this FEMA historical damage feature layer. It already registers some DEM/LiDAR research for Europe and the global Copernicus DEM; 3DEP is a distinct U.S. national product with project-specific metadata. xBD is an event damage-annotation benchmark, not a generic Microsoft/Google/EUBUCCO building-footprint feed. Search and upstream-lineage overlap should be repeated before promotion, particularly for any later FEMA/NFIP matching.
