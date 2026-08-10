<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: NOAA NCEI IBTrACS v04r01

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/noaa.ncei.ibtracs.v04r01.json`
- Provider: NOAA National Centers for Environmental Information (NCEI)
- Product: International Best Track Archive for Climate Stewardship (IBTrACS)
- Version: `v04r01`
- DOI: `10.25921/82ty-9e16`
- Release model: versioned but rolling; v04r01 is updated multiple times per week

## Why this source is useful

IBTrACS provides the observed tropical-cyclone event-history counterpart to the already admitted synthetic STORM v4 catalogue. It merges best-track data from multiple agencies into a unified global dataset and exposes source-agency information needed to study inter-agency differences rather than hiding them behind one synthetic truth value.

For OpenCatastrophe this creates a useful validation pair: IBTrACS supplies observed/post-analysed multi-agency best-track evidence, while STORM v4 supplies a synthetic present-climate tropical-cyclone catalogue. The two datasets remain scientifically distinct.

## Version identity and mutability

NCEI identifies the reviewed release as IBTrACS `v04r01`, DOI `10.25921/82ty-9e16`. NCEI states that v04r01 was released in June 2024 and is updated several times each week as new or corrected best-track information is incorporated.

Therefore `v04r01` is a product/revision identity, not a frozen byte snapshot. A reproducible raw acquisition must additionally pin the access timestamp, exact subset (`ALL`, `since1980`, basin or other documented selection), distribution format, exact file/locator and companion documentation, byte size and SHA-256.

No IBTrACS bytes are admitted by this review.

## Rights assessment

NCEI's IBTrACS Terms of Use state that the data policy follows the World Data Center for Meteorology approach of full and open access and that contributing Regional Specialized Meteorological Centers have agreements allowing IBTrACS data to be open for distribution. NCEI states that WMO Resolution 40 is used as the guide for commercial use.

The NCEI v4.01 metadata record lists citation and liability language under Use Constraints and does not state an additional product-specific non-commercial restriction.

Engineering interpretation for this metadata admission:

- licence/terms identity: NCEI IBTrACS Terms of Use, WDC full/open-access policy, with WMO Resolution 40 commercial-use guidance;
- commercial use: allowed for the reviewed IBTrACS distribution subject to the stated policy/guidance and any applicable source conditions;
- redistribution: the IBTrACS page explicitly describes the dataset as open for distribution;
- attribution/citation: use the NCEI versioned dataset citation, identify subset and access date, and cite the core IBTrACS publication where applicable;
- repository review scope: metadata only.

WMO Resolution 40 distinguishes essential from additional meteorological data and allows some additional data to carry commercial re-export conditions. A future raw-publication proposal must therefore re-check the then-current IBTrACS Terms of Use and selected-file metadata instead of treating this metadata review as a permanent provider-wide licence shortcut.

This is an engineering rights assessment, not legal advice.

## Scientific semantics

### Best track is post-analysed evidence, not error-free ground truth

IBTrACS combines tropical-cyclone tracks and intensity estimates from multiple agencies. NCEI documents uncertainty in source lineage and differences in agency processing, identification and intensity-estimation practices. A best-track value is a curated scientific estimate, not direct instrumental truth at every timestamp.

### Agency wind conventions are not automatically homogeneous

NCEI documents differences between agency wind-speed practices, including averaging-period differences. A future adapter must preserve source-agency fields and wind conventions. Any normalization to a common wind convention is a transformation with its own method, provenance and uncertainty.

### Provisional and final information must remain distinguishable

Version 4r01 can contain both provisional and best-track information for a storm when applicable. A reproducible workflow must preserve that status and must not silently treat a provisional recent track as equivalent to a finalized post-season best track.

### Historical completeness and known issues vary over time

NCEI documents temporal/source limitations and known issues. The current v04r01 page specifically notes unmatched early pre-1950 storms that can inflate storm counts in parts of the early record.

The full historical record is therefore not uniformly complete or homogeneous. Early-century event counts should not be compared mechanically with the modern satellite era, and a `since1980` subset must be selected only when scientifically justified.

### Tracks are not spatial hazard footprints

IBTrACS provides storm position/intensity and additional provider-dependent parameters. It is not a complete wind, surge, wave, rainfall or flood footprint at exposed locations. Track-to-footprint modelling requires a separately reviewed model/transformation, inputs, parameters, grid and validation evidence.

### Observed years do not define future climate

The historical/post-analysed record is evidence about past tropical-cyclone activity. It must not be relabelled as a future-climate event set or used to infer climate-change impacts without an explicit method and additional evidence.

## Suitable initial OpenCatastrophe uses

Good initial uses include validation of synthetic tropical-cyclone catalogues such as STORM v4, observed storm-track and occurrence-history research, basin/frequency/intensity diagnostics with explicit source conventions, inter-agency uncertainty research, reproducible event/subset identity tests, and input to separately reviewed track-to-hazard transformations.

It is not sufficient by itself for error-free historical truth, building-level hazard footprints, vulnerability/insured loss, future-climate projections, or automatic cross-peril dependence.

## Requirements before raw admission

Before any IBTrACS bytes can move beyond metadata-only status, a proposal must:

1. re-check the current v04r01 product page, Terms of Use, metadata constraints and change log;
2. freeze the exact subset, format, retrieval timestamp and file identity;
3. acquire bytes outside Git and record byte size plus SHA-256;
4. preserve storm/event identifiers, agency/source fields, provisional/final status, wind conventions, units and missing-value semantics;
5. document known issues and the scientific reason for the selected time/basin subset;
6. keep normalization, filtering, event selection or track-to-footprint conversion as explicit transformation lineage;
7. preserve required dataset/scientific citations; and
8. obtain explicit asset-specific publication review.

Until then, no raw or derived IBTrACS bytes belong in this repository.

## Authoritative public references

- IBTrACS product, documentation, access and Terms of Use: `https://www.ncei.noaa.gov/products/international-best-track-archive`
- v4.01 NCEI metadata record: `https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc%3AC01552`
- Dataset DOI: `https://doi.org/10.25921/82ty-9e16`
- WMO Resolution 40: `https://community.wmo.int/resolution-40`
