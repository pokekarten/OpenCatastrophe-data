<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Google Open Buildings v3

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/google.open-buildings.v3.json`
- Provider: Google Research
- Product: Open Buildings
- Version: `v3`

## Why this source is useful

Open Buildings v3 is an independent public building-footprint source for exposure-geometry validation. Google reports about 1.8 billion building detections over roughly 58 million km² across Africa, South Asia, South-East Asia, Latin America and the Caribbean.

Its value here is comparative: independently generated footprints can reveal coverage, omission and geometry uncertainty that a single-source exposure workflow can hide.

## Version and asset structure

The reviewed dataset is explicitly `v3`; Google documents v3 inference as May 2023. Polygon and point data are sharded into CSV files by S2 level-4 cell, with separate tile metadata and score-threshold files.

A future raw admission must select exact v3 assets rather than treating a cloud prefix as one immutable artifact. No Open Buildings bytes are admitted here.

## Rights assessment

Google states that Open Buildings is dual-licensed under CC BY 4.0 and ODbL 1.0, at the user's choice. This OpenCatastrophe admission explicitly selects **CC-BY-4.0** so ODbL database-share-alike obligations are not silently introduced into the native data contract.

Commercial use, sharing and adaptation are allowed under the selected CC BY 4.0 path subject to attribution, licence linking and change indication. The underlying high-resolution imagery is not part of the released dataset and is outside this admission.

## Scientific semantics

### ML detections are not authoritative records

Google documents omission/commission errors, false detections, inaccurate shapes and spatially varying quality. A detected polygon must not be re-labelled as cadastral/legal geometry, verified address, occupancy/use, construction class, insured location, replacement value or insured value.

### Version 3 fields and confidence

The public v3 documentation describes centroid latitude/longitude, `area_in_meters` in square metres, confidence in the range 0.65 to 1.0, WKT polygon/multipolygon geometry for polygon records and a Plus Code at the centroid.

Separate tile-level score-threshold metadata provide thresholds for estimated precision levels. Any filtering threshold is a transformation choice: preserve the original confidence and record the filter rather than hiding it in acquisition.

### Freshness and completeness

Google states that source imagery freshness varies by location and may be several years old or unavailable. Dataset absence is therefore not proof that a building is absent, and the May 2023 inference date is not a universal observation date for each footprint.

## Suitable initial uses

Suitable uses include independent exposure-geometry comparison, coverage/omission diagnostics, confidence-threshold research, hazard-overlay experiments with separately admitted sources and public provenance-contract validation.

Not sufficient by itself for cadastral truth, occupancy, construction, insured value, vulnerability, claims or portfolio completeness.

## Requirements before raw admission

A future proposal must re-check v3 and CC BY 4.0 terms; select exact S2 tile/companion assets; acquire bytes outside Git; record size and SHA-256; preserve field/confidence/filter semantics and freshness limitations; keep source imagery outside scope; record transformations explicitly; and obtain asset-specific publication review.

Until then, no raw or derived Open Buildings bytes belong in this repository.

## Authoritative public references

- Google Open Buildings: `https://sites.research.google/gr/open-buildings/`
- Creative Commons Attribution 4.0: `https://creativecommons.org/licenses/by/4.0/`
