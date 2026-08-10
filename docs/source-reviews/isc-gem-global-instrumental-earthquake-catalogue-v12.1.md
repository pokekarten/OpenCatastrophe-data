<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: ISC-GEM Global Instrumental Earthquake Catalogue v12.1

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/isc-gem.global-instrumental-earthquake-catalogue.v12.1.json`
- Provider: International Seismological Centre (ISC) / GEM Foundation
- Product: ISC-GEM Global Instrumental Earthquake Catalogue
- Version: 12.1, dated 27 November 2025
- DOI: `10.31905/D808B825`
- Licence: CC BY-SA 3.0 Unported

## Why this source is useful

ISC-GEM is purpose-built as a homogeneous global instrumental earthquake catalogue for seismic-hazard and risk research. It complements modelled hazard such as ESHM20 with an event-history reference while preserving the distinction between earthquake occurrence, ground-motion intensity and damage/loss.

## Source identity and scientific semantics

The authoritative ISC page identifies version **12.1** and an update log records the 2025 release sequence. The catalogue is distributed as a main catalogue, a supplementary catalogue and mapping material.

The supplementary catalogue contains events believed to be large enough for the project scope but whose location, magnitude or both are comparatively uncertain because of sparse or contradictory source observations. This semantic distinction must remain explicit; supplementary events must not be silently promoted to the same evidential status as the main catalogue.

Catalogue completeness is not uniform through time, region and magnitude. Version 12 extended the reviewed temporal endpoint to 2021 and the version 12.1 update corrected specific event parameters. A future workflow must therefore pin the exact release rather than using an unversioned current download.

## Access and rights assessment

ISC's authoritative download/legal page states that v12.1 may be used under CC BY-SA 3.0 Unported and explicitly extends that treatment to relevant neighbouring/database rights.

Engineering interpretation:

- commercial use: allowed by the CC licence;
- redistribution/adaptation: allowed subject to attribution/share-alike;
- repository review scope: metadata only;
- database-right/share-alike conditions must remain visible in derived-data decisions.

## Suitable initial OpenCatastrophe uses

- historical earthquake-event selection;
- independent comparison with modelled seismic hazard;
- magnitude/time/location quality research;
- catalogue-completeness experiments with explicit methodology;
- linking events to separately admitted ground-motion/deformation/ground-failure evidence.

The catalogue is not a ShakeMap, fragility model, exposure layer or loss catalogue.

## Requirements before raw admission

Select exact v12.1 files; preserve main versus supplementary semantics, all relevant uncertainty/quality fields and licence conditions; record exact hashes/sizes outside Git; and obtain an asset-specific review. Filtering, magnitude homogenization or declustering must be explicit transformations rather than undocumented preprocessing.

## Authoritative public references

- Download/legal/version: `https://www.isc.ac.uk/iscgem/download.php`
- Update log: `https://ftp.isc.ac.uk/iscgem/update_log/`
- DOI: `https://doi.org/10.31905/D808B825`
