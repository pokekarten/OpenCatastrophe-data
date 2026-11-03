<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Research-only original-source preflight: Groundsource, DLR landslides, NOAA MRMS (2026-11-04)

**Scope and authority:** This is a bounded source-discovery/research note for issue #1227, not an admission, original-asset acquisition, rights determination, production DB update, model-input approval, or evidence that all repository candidates have been checked. Primary publisher *pages* and a government/open-data catalog were readable by Exa/web content intermediaries. Original dataset bytes were **not** fetched, hashed, or inspected. Dataset identities in `landscape/`, `access/`, `manifests/` and accepted reviews retain their separate canonical status.

## Current-repository overlap check

- GitHub code search on current `OpenCatastrophe-data` main found **no exact matches** for `Groundsource`, `18647054`, `17007637`, or `noaa-mrms-pds` in the searched indexed files. This does **not** prove absence from every non-indexed branch or every semantic synonym; open PR title searches for the candidates returned none at the time of review.
- Existing `landscape/sources-severe-convective-weather.json` and `landscape/sources-hazard-monitoring-services.json` already reference **MRMS MESH**. Therefore its S3 access channel is **not a new independent source** and must be attached to the existing exact source identity, not cloned into a second candidate.
- Existing `access/nasa.coolr.landslides.json` references NASA COOLR; DLR S1/S2 labeled polygons are a **different original product**, not independent evidence when individual labels may themselves be sourced from reports also used elsewhere.
- Existing flood discovery includes several satellite and event catalogs. Groundsource's news/LLM-derived point/event reports have a distinct observation mechanism, but overlap and dependencies with GDACS, EM-DAT, original news articles and other catalogs must be quantified before a holdout or frequency task.

## A. Groundsource v1: flood reports derived from news

| Item | Exact observed publisher-page fact / limitation |
| --- | --- |
| Provider, version | Google Research and coauthors; Zenodo record `10.5281/zenodo.18647054`, published February 2026, v1 |
| Landing/asset | https://zenodo.org/records/18647054 ; named `groundsource_2026.parquet` |
| Described size | 667.1 MB on publisher record; publisher-provided **MD5** `cd1b5de6508f7aad8e1d1d0dd4cecea6` (not independently computed, no SHA-256) |
| Publisher's reach | 2.6 million **records** extracted from news across 150+ countries; these are not independently verified physical flood events or unique insured claims |
| Displayed publisher license | CC BY 4.0 on original Zenodo record; exact asset rights/attribution and source-article downstream constraints require review |
| Intended research role | Detection, temporal/spatial plausibility, candidate validation/holdout design of observed urban flash flood reports |
| Unsuitable immediate role | Direct annual flood event frequency calibration, event footprints or ground-up/insured losses |

Original Google Research article (2026-03-12): https://research.google/blog/introducing-groundsource-turning-news-reports-into-data-with-gemini/ reports **60%** accuracy in both location and timing in its described manual review and **82%** sufficient for its stated practical tolerance; those are provider-defined review outcomes, not independent external model validation. An EGU conference abstract describes **~800,000 events**, which differs from the published **2.6 million records**; field cardinality, duplicate/news-story clustering, event-vs-record unit and sample denominator must be verified on a bounded, schema-only or small reproducible slice. News/geocoding selection is heavily affected by location, language, internet access and economic/population coverage.

**Next falsifiable check:** obtain Zenodo record JSON/asset identity through the original provider; verify SHA-256 over a complete original Parquet outside public Git, exact row schema, event deduplication key, coordinate/time precision, country distributions, multiple-news-to-single-event relationships and original license. Establish region/time stratified external holdout before any frequency use.

## B. DLR/GFZ landslide supervised reference v3

| Item | Exact observed publisher-page fact / limitation |
| --- | --- |
| Provider, version | Orynbaikyzy et al., German Aerospace Center (DLR), GFZ and Leibniz University Hannover; **Zenodo v3** `10.5281/zenodo.17007637`, dated 2025-08-30 |
| Landing/asset | https://zenodo.org/records/17007637 ; `s1s2_landslide_reference_data.zip` |
| Described size | 6.0 GB (displayed publisher size); publisher MD5 `ca50582a596ad6a88ada97488f037692` for the v3 asset, not independently verified |
| Content described | `original_scenes/` Sentinel-1/2 and DEM; `reference_data/` H5 labeled 125x125 patches; `vector_data/` GeoPackage with landslide polygons/events |
| Intended research role | Event polygon/landslide detector validation and explicit held-out observations, conditional on independently verified dates and polygon semantics |
| Unsuitable immediate role | Globally exhaustive landslide rates, fully independent labels, physical flow/runout intensities or insured losses |

**Rights contradiction is blocking:** the Zenodo record shows **CC BY 4.0**, but the associated paper's data availability text at https://doi.org/10.1080/15481603.2025.2502214 says **CC-BY-NC-4.0**. Do not select the more permissive license or redistribute any data until the exact v3 asset/license is resolved with the publisher. Scope is curated examples, not a population-complete event inventory; satellite observation/label-source leakage and event/time/region-split uncertainty require examination. Different Zenodo versions (v0.1, v1.0, v3) must not be silently conflated.

**Next falsifiable check:** capture exact publisher license metadata and author clarification; then build a version-pinned provider receipt, inspect file listing/CRS/polygon and H5 split semantics with external local storage. Compare to known COOLR/Copernicus lineage before treating a label as an independent holdout.

## C. NOAA MRMS MESH access-route discovery

- Existing scientific family: NOAA/NSSL MRMS radar/multisensor hail products, including Maximum Estimated Size of Hail (MESH). The scientific **hazard estimate** is neither a physical hailstone measurement at a building nor an insured roof damage claim.
- Public distribution: https://registry.opendata.aws/noaa-mrms-pds/ documents `s3://noaa-mrms-pds/` in `us-east-1`, anonymous bucket listing via `aws s3 ls --no-sign-request s3://noaa-mrms-pds/`; the public bucket is an **access route**, not a separate observational dataset.
- NOAA/NCEP near-real-time MESH GRIB2 product index: https://mrms.ncep.noaa.gov/2D/MESH/ ; the catalog is dynamic. The original current directory was visible during external index retrieval but no original GRIB payload was read or hashed.
- Version boundary: MRMS v11 vs v12 transition on 2020-10-14 affects comparability. NSSL describes rolling operational data from October 2020; neither this nor 2-minute real-time product updates guarantees a complete long-duration archive of MESH objects in the bucket.
- Rights boundary: the open NOAA *data* terms do not mean the University of Oklahoma MRMS *software* is freely commercially licensed. Preserve data/software separation, attribution and modified-data labeling.

**Next falsifiable check:** enumerate only a bounded prefix in the public bucket; verify exact MESH product, timestamp, grid, units, GRIB fields, version and retention. Compare provider sample CRC/SHA and NCEP reference with trusted direct-access runner. Maintain independent hail reports as possible validation only after provenance/measurement distinctions are explicit.

## D. Low-priority additional candidate: empirical tsunami candidate extents

Exa surfaced a Figshare dataset published 2026-10-13 at https://doi.org/10.6084/m9.figshare.34369794 titled *Global historical tsunami candidate inundation extents at nominal 30 m resolution*. Its searchable landing description claims empirical terrain/connectivity-based candidate rasters derived from screened NOAA historical observations (816 event-linked nonempty raster products in 1,103 tiles). **Original Figshare landing and file rights could not be directly verified in this run**. This is neither observed per-event inundation nor a hydrodynamic PTHA depth distribution, may share input lineage with already cataloged NOAA tsunami products, and stays discovery-only until rights and original-file verification.

## Prioritised implementation order and check status

1. **P1 Groundsource**: small original-provider schema/identity receipt, then news-record/event deduplication and spatiotemporal uncertainty diagnostics.
2. **P1 DLR v3**: resolve publisher rights conflict *before* download, extraction or redistribution; design scene/event disjoint holdout.
3. **P2 MRMS**: enhance existing access record with anonymous bucket route after exact product-version, retention, physical units and direct probe review; no duplicate landscape entry.
4. **P3 Tsunami Figshare**: original landing/API rights verification and independent science review before registering.

No Git data-source bytes, synthetic/insurer positions, claims, credentials, model runs or Neon writes are part of this note. No full original asset download, file checksum verification or repository `check_all.py` execution was performed in this review environment. This Markdown-only research update should be evaluated in CI and with a proper checkout before accepting, and should not be mistaken for production readiness.
