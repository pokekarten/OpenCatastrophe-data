<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: manifests/copernicus.cems.gfm.v4.1.1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Dataset manifest: `copernicus.cems.gfm.v4.1.1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Dataset id:** copernicus.cems.gfm.v4.1.1

**Provider:** Copernicus Emergency Management Service (CEMS) / European Commission Joint Research Centre

**Product name:** Global Flood Monitoring (GFM)

**Version or release:** 4.1.1 (released 2026-06-11)

**Canonical source:** <https://extwiki.eodc.eu/GFM/GFMVersioning>

**Retrieved at:** 2026-08-12T19:17:00Z

**Retrieval query or filters:** Metadata-only review of current GFM v4.1.1 versioning, Product User Manual/Product Definition documentation, dissemination documentation and CEMS Early Warning Data Store terms. No GFM REST, WMS-T or STAC request was executed and no provider bytes were acquired.

**Access class:** open

**Modelling layer:** hazard

**Intended use:** Satellite-derived observed flood/water extent evidence for bounded flood-footprint validation and model challenge. Preserve GFM version, Sentinel-1 acquisition metadata, Reference Water Mask, Exclusion Mask, Likelihood Values and Advisory Flags. Do not reinterpret GFM as river discharge, flood depth or velocity, return-period hazard intensity, surveyed damage, vulnerability, insured loss or universal ground truth.

**Raw artifact:** `null`

**Derived artifact:** `null`

## Licensing

**Status:** verified

**Spdx expression:** `null`

**Licence name:** Terms of use of the CEMS Early Warning Data Store (rev. 11)

**Terms reference:** <https://ewds.climate.copernicus.eu/licences/terms-of-use-cems>

**Terms reviewed at:** 2026-08-12T19:17:00Z

**Terms version or date:** rev. 11; page states last modified 2023-06-07; reviewed 2026-08-12

**Terms content sha256:** `null`

**Commercial use status:** allowed

**Attribution requirements:** When communicating or distributing covered CEMS early-warning/monitoring data, identify the source using the required Copernicus Emergency Management Service notice or similar; adapted or modified data require a modified-information notice.

**Share alike or derivative requirements:** The reviewed CEMS terms permit reproduction, distribution, public communication, adaptation, modification and combination. No share-alike requirement is recorded; source/modification notices, restricted-data rules and third-party terms still apply.

**Notes:** The CEMS terms explicitly describe the early-warning and monitoring systems as including Global Flood Monitoring. Some CEMS data can be restricted and third-party information may have separate terms, so rights are not generalized beyond covered GFM information. Dataset reuse rights are kept separate from service/API automation policy. This is an engineering rights assessment, not legal advice.

## Redistribution

**Status:** allowed

**Scope:** raw

**Conditions:** The reviewed CEMS terms support redistribution of covered GFM information subject to required source/modification notices and restricted/third-party caveats. This manifest records repository review status approved_metadata_only. At the manifest review time, no exact GFM scene, API response or product asset had been selected, acquired, hashed or approved for Git publication.

## Privacy

**Personal data status:** none

**Confidential or proprietary status:** none

**Notes:** The admitted role concerns satellite-derived flood/water products and associated geospatial metadata, not person-, policy-, claims- or portfolio-level data. Derived affected-population/land-cover layers have separate semantics and are not the primary validation evidence admitted here.

## Spatial

**Crs:** `null`

**Extent:** Global Sentinel-1 IW coverage; current PUM states GFM processing uses the 20 m spatial resolution of the Sentinel-1 pre-processed data cube. Exact CRS, footprint and pixel/grid semantics must be frozen from the selected product asset.

## Temporal

**Extent:** GFM version 4.1.1 is operational from 2026-06-11. Exact Sentinel-1 acquisition time and product version must be frozen per validation asset; GFM documentation states data layers from different MAJOR versions are incompatible and must not be silently combined.

## Variables and units

### Item 1

**Name:** Observed Flood Extent

**Unit:** `null`

**Description:** Ensemble Sentinel-1 SAR-derived classification of floodwater extent, excluding normal permanent/seasonal water via the Reference Water Mask and subject to masking/quality limitations.

### Item 2

**Name:** Observed Water Extent

**Unit:** `null`

**Description:** Sentinel-1 SAR-derived open/calm water extent; distinct from flood-only extent.

### Item 3

**Name:** Reference Water Mask

**Unit:** `null`

**Description:** Reference permanent/seasonal water context used to distinguish normal water from observed flooding.

### Item 4

**Name:** Exclusion Mask

**Unit:** `null`

**Description:** Mask identifying locations where robust SAR flood/water classification is not technically feasible because of static surface, topographic, shadow or coverage effects.

### Item 5

**Name:** Likelihood Values

**Unit:** %

**Description:** GFM appraisal of flood-classification confidence on a 0-100 scale; preserve exact product semantics and masking behavior.

### Item 6

**Name:** Advisory Flags

**Unit:** `null`

**Description:** Flags for conditions such as wind, frozen conditions, snow or dry soil that may impair flood/water detection; flagged pixels are not necessarily excluded.

### Item 7

**Name:** Sentinel-1 Footprint and Metadata

**Unit:** `null`

**Description:** Scene footprint and acquisition metadata required to bind a GFM observation to the underlying Sentinel-1 acquisition.


**Transformation:** `null`

## Review

**Status:** approved_metadata_only

**Reviewed at:** 2026-08-12T19:17:00Z

**Reviewer:** OpenCatastrophe source audit

**Notes:** Metadata-only admission for a bounded flood-observation validation role. No GFM provider request or external byte was executed or persisted. Any future raw/API sample must freeze the exact GFM version, Sentinel-1 scene/acquisition, AOI, requested layer(s), Exclusion Mask/Advisory context, response/file hashes and current service/API terms, with independent science/rights review before publication.
