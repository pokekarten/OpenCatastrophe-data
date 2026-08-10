<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: Overture Maps Buildings

- Review date: **2026-08-10**
- Admission state: **metadata only / not admitted**
- Provider: Overture Maps Foundation
- Product: Buildings theme
- Reviewed release state: official release calendar identified `2026-06-17.0` / schema `v1.17.0` as the current release at review time; `2026-07-22.0` was listed as proposed rather than confirmed
- Theme licence: **ODbL 1.0**

## Why this source is useful

Overture Maps Buildings is a global conflated building dataset assembled from multiple open sources rather than a single detection or cadastral feed. Overture documents the Buildings theme as containing billions of building footprints and provides stable Global Entity Reference System (GERS) identifiers for linking real-world entities across datasets.

For catastrophe modelling, the strongest value is therefore not treating Overture as a new building truth layer. It is a candidate **exposure entity-resolution and interoperability layer**: GERS identifiers, standardized schema and cross-source conflation can help connect hazard overlays, alternative building inventories and external exposure attributes while preserving the distinction between source observations and derived joins.

## Source composition and licensing

Overture documents the Buildings theme under ODbL 1.0. Its attribution page identifies upstream building sources including OpenStreetMap, Esri Community Maps, Microsoft Global ML Building Footprints and Google Open Buildings, with upstream licences that Overture treats as compatible with the ODbL Buildings theme.

The ODbL share-alike and attribution obligations are materially different from permissive metadata-only research. OpenCatastrophe must therefore not silently ingest Overture Buildings into a differently licensed canonical database or redistribute derived database material without a dedicated rights review.

This review records discovery and scientific utility only. No Overture data bytes, release artifacts, GERS registry bytes, bridge files or changelog files are admitted.

## Release and reproducibility boundary

Overture releases data on a recurring cadence and publishes release-specific GeoParquet datasets together with changelogs, GERS registry material, bridge files and other artifacts. The official release documentation also states that public data releases are retained for a limited period, while historical release notes remain available.

That makes exact release identity a hard reproducibility requirement. A future admission must freeze the exact data release, schema version, theme/type, geographic subset or partition set, acquisition path, byte size and SHA-256 before analysis. It must not rely on a moving `latest` alias or assume that a historical release will remain downloadable indefinitely.

At this review date, Overture's official release calendar identified `2026-06-17.0` as the current release and listed `2026-07-22.0` as a proposed future release. Because the proposed date had already passed by the review date without an official July release note located in the reviewed documentation, this review deliberately does not infer that the July release exists. Re-check the authoritative release calendar immediately before any acquisition.

## Scientific semantics

### Conflation is useful but not ground truth

A conflated building feature may combine or reconcile information from multiple upstream datasets with different observation dates, detection methods, completeness and error modes. Overture quality controls improve interoperability, but an Overture building must not be relabelled as cadastral/legal geometry, verified occupancy, construction class, replacement value, insured value or portfolio membership unless those semantics come from a separately reviewed source.

### Stable identifiers are a join mechanism

GERS identifiers are particularly useful for repeatable joins and cross-release/entity mapping. They should be treated as identifiers and linkage infrastructure, not as evidence that all upstream descriptive attributes are simultaneously correct or contemporaneous.

### Coverage and provenance remain heterogeneous

The theme incorporates community, authoritative and machine-learning-derived sources. Coverage, freshness and attribute availability therefore vary spatially. Missing buildings are not proof of absence, and overlapping upstream coverage does not imply independent observations.

## Suitable initial uses

Suitable metadata-first or later admitted uses include:

- exposure entity resolution across independently admitted building datasets;
- standardized building-footprint comparison and coverage diagnostics;
- hazard-to-building spatial joins using separately admitted hazard data;
- cross-release change research using release changelogs and bridge artifacts;
- linking external public attributes to stable GERS identities where rights and semantics permit;
- interoperability research for AI agents that need stable, machine-readable geospatial entity references.

Not sufficient by itself for cadastral truth, occupancy, vulnerability class, construction year, insured value, replacement value, claims, policy exposure or portfolio completeness.

## Requirements before raw or derived admission

A future proposal must:

1. re-check the exact current Overture release and Buildings-theme attribution/licensing;
2. document ODbL obligations for the intended database, derivative and publication path;
3. freeze exact release/schema/theme/type and selected partitions or geographic subset;
4. acquire bytes outside Git and record exact byte size and SHA-256 receipts;
5. preserve source/provenance fields needed to understand conflation and upstream origin;
6. record any filtering, deduplication, spatial clipping, GERS joining or cross-release mapping as explicit transformations;
7. keep Overture-derived database material separate from differently licensed canonical data until compatibility is explicitly reviewed;
8. validate scientific limitations against at least one independent building/exposure source before using the layer as model input.

Until those conditions are satisfied, Overture Maps Buildings remains a high-value discovery/interoperability candidate only.

## Authoritative public references

- Overture Buildings guide: `https://docs.overturemaps.org/guides/buildings/`
- Overture attribution and licensing: `https://docs.overturemaps.org/attribution/`
- Overture release calendar: `https://docs.overturemaps.org/release-calendar/`
- Overture documentation / data access: `https://docs.overturemaps.org/`
- Overture FAQ: `https://overturemaps.org/about/faq/`
