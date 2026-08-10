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

## Why this source closes a current gap

OpenCatastrophe already admits ESHM20 as a **modelled seismic-hazard** source plus ESRM20 exposure and vulnerability. ISC-GEM adds an independently maintained **observed/post-analysed instrumental event-history** reference, enabling bounded historical-event selection and model-versus-observation checks without confusing occurrence with ground motion or loss.

## Source identity and scientific semantics

The authoritative ISC page identifies version **12.1** dated 27 November 2025. The catalogue is distributed as a main catalogue, supplementary catalogue and mapping material.

The supplementary catalogue contains events believed large enough for the project scope but with comparatively uncertain location, magnitude or both because source arrival-time or amplitude/period evidence is sparse or contradictory. This distinction must remain explicit; supplementary events must not be silently promoted to the same evidential status as the main catalogue.

Catalogue completeness is not uniform through time, region and magnitude. Version 12 extended the reviewed endpoint to 2021 and the 12.1 release corrected event parameters. Workflows must therefore pin the exact release rather than use an unversioned current download.

## Access and rights assessment

ISC's authoritative download/legal page licenses v12.1 under CC BY-SA 3.0 Unported and explicitly extends that treatment to relevant neighbouring/database rights.

Engineering interpretation:

- commercial use: allowed by the reviewed Creative Commons licence;
- redistribution/adaptation: allowed subject to attribution and ShareAlike;
- repository review scope: metadata only;
- database-right/share-alike conditions remain visible in downstream derived-data decisions.

## Suitable initial OpenCatastrophe uses

- historical earthquake-event selection for the admitted earthquake stack;
- independent event-history comparison around ESHM20 hazard studies;
- magnitude/time/location quality and completeness experiments with explicit methodology;
- linking events to separately reviewed ground-motion, deformation or ground-failure evidence.

The catalogue is not a ShakeMap, fragility model, exposure layer or loss catalogue.

## Requirements before raw admission

Select exact v12.1 files; preserve main-versus-supplementary semantics, uncertainty/quality fields and licence conditions; record hashes/sizes outside Git; and obtain asset-specific review. Filtering, magnitude conversion, declustering or regional subsetting must be explicit transformations rather than undocumented preprocessing.

## Authoritative public references

- Download/legal/version: `https://www.isc.ac.uk/iscgem/download.php`
- Update log: `https://ftp.isc.ac.uk/iscgem/update_log/`
- DOI: `https://doi.org/10.31905/D808B825`
