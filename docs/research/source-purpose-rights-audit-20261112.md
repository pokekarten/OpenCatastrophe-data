<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Product-specific data rights and Neon metadata preflight — 2026-11-12

**Evidence snapshot, not source admission or legal advice.** The canonical `landscape/` and `manifests/` records remain the public dataset authority. This note records a date-specific, purpose-specific rights distinction and existing research-only metadata evidence; it does **not** grant source rights, automate acquisition or approve CAT model inputs.

## Three separate permissions to assess

For each product and **exact version**, record research/education use, commercial training/calibration/scoring, internal API/sample storage, raw/derived redistribution, attribution and third-party/geospatial/personal rights **separately**. Metadata visibility and a successful API GET are not a raw-file reuse licence. A sampled geospatial raster is not automatically an insurer building/TIV or a validated hazard.

| Product / scope | Original publisher right evidence | Non-commercial research | Commercial insurer CAT use | External raw dissemination | API/sample gate |
| --- | --- | --- | --- | --- | --- |
| E-OBS, Europe-wide | [ECMWF combined terms, section 1](https://cds.climate.copernicus.eu/licences/licence-to-use-E-OBS-and-E-OBS-EU-products) | Explicitly restricted to research/education | **Not permitted under public product licence** | Do not presume permission | Registration/licence acceptance and separately reviewed acquisition |
| **E-OBS_EU**, EU + Norway + Switzerland + Iceland + UK | [ECMWF combined terms, section 2](https://cds.climate.copernicus.eu/licences/licence-to-use-E-OBS-and-E-OBS-EU-products) | CC BY 4.0, with attribution | **Permitted by product licence**, subject to attribution and further internal provenance/scientific checks | CC BY 4.0 source-rights ceiling; review exact assets, attribution, any other provider controls | New CDS request syntax; authentication/accepted licence; no API GET or actual fields yet tested |
| ERA5-Land hourly | [Original CDS STAC entry](https://cds.climate.copernicus.eu/stac-browser/collections/reanalysis-era5-land) | CC BY 4.0 | CC BY 4.0 permits commercial data reuse | Licence-level right with credit; exact response, API conditions and original product/version to freeze | No source data retrieved in this note |
| ESWD public report subset | [ESSL original access terms](https://www.essl.org/cms/european-severe-weather-database/) and [existing access contract](../../access/essl.eswd.public-subset.documented.json) | Public browsing and separate academic access subject to User Agreement | **Not permitted by public User Agreement**; professional arrangements require ESSL | No bulk/redistribution entitlement assumed | `do_not_automate`; no API/data probe permitted |
| GEM Global Exposure Model ADM1 v2026.0.0 | [GEM original model product](https://www.globalquakemodel.org/t-products/global-exposure-model?rc=test-site) | CC BY-NC-SA 4.0, conditions apply | **Separate commercial licence required** | Only to extent open NC-SA scope permits; high-res licensed separately | No ingestion under commercial-use contract |
| GEM Global Vulnerability Model open XML | [GEM original product](https://www.globalquakemodel.org/t-products/global-vulnerability-model?rc=test-site) | CC BY-NC-SA 4.0, conditions apply | **Separate commercial licence required** | Share-alike/noncommercial restrictions apply | Do not consume open XML as commercial loss curves |
| HydroATLAS v1 | [HydroATLAS original product terms](https://www.hydrosheds.org/hydroatlas) | DB advertises CC BY 4.0 | Product-level CC BY, but check component attributes and associated [site terms](https://www.hydrosheds.org/terms-of-use) | Exact asset and underlying attributes require verification | Bounded official Figshare metadata preflight first |

**Important non-equivalence:** On **2026-11-04**, ECMWF announced the newly separated **E-OBS_EU** product under CC BY 4.0, while the larger E-OBS remains non-commercial. Both derive from related observational inputs; E-OBS_EU is not an independent validation source for E-OBS and API request recipes changed. [ECMWF announcement](https://forum.ecmwf.int/t/e-obs-daily-gridded-data-new-dataset-implementation-to-support-open-data/15543).

## Original Zenodo catalogue tests and existing Neon research samples

On 2026-11-12 three *original* `zenodo.org/api/records/<record-id>` JSON catalogue GETs were obtained, with the original response SHA-256, strictly bounded public record metadata and publisher file inventory recorded in the **private** Neon insurance database `research.source_sample_v0`. This note reproduces only identifiers and audit receipts, **not raw provider payload bytes or sensitive file contents**.

| Source ID | Original record | Publisher-declared dataset licence | Files referenced | Neon sample | Original-response SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| `eu.eo4flood.multibasin-hydrology.v2` | [21699983](https://zenodo.org/api/records/21699983) | CC BY 4.0 | 11 | 32 | `ce328a1d2c1d20aeb7f8c5e61f2dba0d153d1c50d5be9d278af0bb1f1db7f460` |
| `deltares.gtsm-era5-e.extreme-sea-level-statistics.v2` | [14671593](https://zenodo.org/api/records/14671593) | CC BY 4.0 | 1 | 33 | `5c0a05117a71d1bee4fa592e3fa7d80f28c4bffb2cb13365356e12b039595668` |
| `ihcantabria.transclima.tc-surge-hydrographs.2026` | [18170693](https://zenodo.org/api/records/18170693) | CC BY 4.0 | 13 | 34 | `ae993672fe64098b0193937dc377345ff6d685435aa7be34048952ed9398983f` |

Neon rows have canonical JSONB SHA-256 checks verified. They are `sample_kind=public_metadata`, `research_only=true`, `model_input_approved=false`, `source_byte_persistence_authorized=false`. No data archive files were obtained, no sensor time series, GeoTIFF pixels, hydrodynamic hindcast values, loss records, coordinates or third-party underlay copied. The **metadata** itself is CC0 according to Zenodo; the *declared dataset licence* is a separate field and does **not** supersede file-level rights/attribution, privacy or provider terms.

## API coverage is not API success

The existing [source-api-readiness workflow](../../.github/workflows/source-api-readiness.yml) audits **all registered sources offline**, and permits a fixed allowlist of **18** explicitly reviewed live probe programs only when manually dispatched with `probe_mode=reviewed_18`. A green offline audit says nothing about actual provider reachability. None of the 18 are claimed to have been freshly run by this note. The three Zenodo *catalogue* GETs above are the actual fresh tested API calls.

Do not call all 692 candidates blindly: many are landing pages, publication citations, third-party/restricted providers or DOI catalogs rather than execution-ready APIs. For each candidate, first bind exact assets and licence/terms, public API operations, rate limits, authentication and legal collection rights; add a narrow `access/*.json` contract and deterministic synthetic tests; run a **bounded, receipt-only** original provider probe; then decide whether a sample may be persisted in Neon. Preserve version, request identity, retrieval UTC, content-type, byte size, response SHA-256, units/CRS/temporal context and data protection limits. Retain source bytes only after explicit permission.

## Next causal actions

1. Review E-OBS_EU exact field/version and new CDS API form; obtain account/licence acceptance in an authorized environment. Keep the present new candidate `not_admitted` and its source rights `not_reviewed` until full source/API/scientific checks.
2. Independently check the referenced archive files and upstream layers in the three Zenodo records before any actual values are sampled.
3. For ESWD and GEM, document/seek provider-specific commercial agreements rather than automatically acquiring restricted material.
4. Continue the existing allowlisted live probes separately from offline CI, preserving provider failure as **failure**, not as an admission.

## Additional 2026-11-12 bounded original-provider smoke reads (Neon receipt rows 1–5)

Five already-reviewed exact URLs from the **existing** fixed public-probe allowlist were fetched as one-shot read-only requests. The independent strict Python repository runner was **not** invoked; these are **smoke checks only**, never science/model approval or equivalent to the full GitHub Action probe. Transient original response bodies were discarded; only non-sensitive outcomes were stored as `research.source_api_smoke_receipt_v0` in Neon.

| Fixed source ID | Observed original response | JSON smoke outcome | Limitation |
| --- | --- | --- | --- |
| `geoboundaries.gbopen` | 1812 bytes | PASS: DEU/ADM1 licence metadata shape | Frozen original source ID not independently asserted |
| `gfz.geomagnetic-kp` | 361 bytes | PASS: nonempty JSON object | Kp scientific values/time semantics not validated |
| `wsv.pegelonline.rest-v2.dresden` | 722 bytes | PASS: station metadata JSON | Full UUID/Q parser not executed |
| `emsc.seismicportal.fdsn-event` | 602 bytes | PASS: one-or-zero-event GeoJSON | Magnitude/origin scientific suitability not validated |
| `noaa.swpc.real-time-solar-wind` | about 59 KB | INCONCLUSIVE: web-scrape transport returned a non-parseable trailing byte sequence | Do not claim provider failure or success; rerun existing trusted Python probe |

These receipts explicitly set `strict_repository_runner_executed=false`, `provider_bytes_persisted=false`, `model_input_approved=false`. The individual endpoint permissions are checked by the corresponding `access/*.json` contracts. The three Zenodo catalogue requests reported above are additional, independently verified metadata GETs.

## Second rights/use-case batch — 2026-11-12 (five source products)

The existing private `insurance-risk-core` Neon database now has a **non-destructive, reproducible** SQL contract `research.source_usage_rights_v0` ([SQL schema](../../sql/research_source_usage_rights_v0.sql)). It stores *separate* outcomes for seven intended uses rather than treating a provider download as a blanket grant:

- `internal_research`;
- `commercial_cat_modelling`;
- `automated_api_access`;
- `internal_neon_metadata`;
- `internal_neon_source_sample`;
- `external_raw_redistribution`;
- `published_derived_results`.

The first **35** source × use-case observations are written in Neon, for these **exact** products and versions. `allowed` on a use case denotes a published **source-licence ceiling**, not source acquisition, science approval or publication admission. Any `conditional` or `unknown` entry is **not permission** to download, store or distribute underlying source files.

| Exact product | Commercial modelling under source rights | Material boundary and original publisher |
| --- | --- | --- |
| [EUBUCCO v0.2](https://docs.eubucco.com/v0.2/license/) | **conditional** | ODbL 1.0 base with geometry-specific exceptions: `gov-italy-abruzzo` = CC BY-NC (no base-licence commercial use); `gov-czechia-prague` = CC BY-SA (share-alike). Preserve `geometry_source` and attribute provenance; filter/review both exceptions rather than releasing the mixed raw product wholesale |
| [Eurostat GISCO Census population grid 2021](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution) | **allowed**, CC BY 4.0 | Specific to **2021 census** grid (including May 2026 update), not old GEOSTAT 2006/2011 data or separately restricted EuroGeographics administrative boundaries. Counts are disclosure-controlled and not building-level household truth |
| [DWD RADKLIM RW2017.002](https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_RADKLIM_RW_V2017.002-en.html) | **allowed**, CC BY 4.0 | [DWD CDC Terms](https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf). Original DOI data and the corrected 2021 NetCDF `supplement` are separate identities; pin exact period and source-file/quality metadata |
| [JRC GHSL GHS-AGE R2025A](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/copyright.txt) | **allowed**, CC BY 4.0 | Exact original product copyright; estimated age surface is not per-building known construction date or insured value |
| [JRC Global Surface Water v1.5](https://global-surface-water.appspot.com/download) | **allowed** by official direct-source Copernicus terms | 1984–2024; citation/attribution required. On **2026-11-10**, original provider corrected >100% occurrence anomalies; known Monthly Recurrence undercount issue still open in v1.4/v1.5. Never mix deprecated v1.4 and updated v1.5 without explicit asset/version identity |

All five remain source candidates `not_admitted` and broad `rights_review_status=not_reviewed`; the narrower evidence is saved in the new use-case table and `original_license_evidence` without falsely promoting total review status. Automated API access was left `unknown` for all five: provider dataset rights alone do not establish unconditional unrestricted automation or data volume.

### Three original publisher-rights metadata receipts inserted to Neon

Small original public HTTP responses were directly fetched, scanned for source identity/terms and hashed. Only source-authored metadata summaries are stored (research-only), not original response HTML/text or geospatial/measurement content:

| Source | Neon sample ID | Exact original response SHA-256 |
| --- | ---: | --- |
| EUBUCCO v0.2 original licence page | 36 | `0a0255784a637c6d90edea13851562b89af042f19055c6da5ee0afaedf8889c2` |
| DWD RADKLIM RW original DOI landing metadata | 37 | `f7a5f0bbde0220906dcf75e8e8747d60db4af364184385579e54e10c3399947b` |
| JRC GHS-AGE R2025A original copyright text | 38 | `f20723519a580fb35b3499870f0b1baea54f483195105416e547f0014f1610d2` |

Neon independently verifies each canonical JSONB sample SHA-256. These three rows have `sample_kind=public_metadata`, `research_only=true`, `model_input_approved=false` and `source_byte_persistence_authorized=false`. The original HTTP page evidence supports only terms/metadata; **no** DWD hourly rain cell, EU population, original building object, GHSL age pixel or JRC water raster was sampled here.

For GISCO, the 2021 census is **not** synonymous with the earlier noncommercial GEOSTAT grid nor the separately restricted EuroGeographics NUTS/LAU boundary geometry. Do not collapse or deduplicate these legal products by provider name. For EUBUCCO, a filter on just `geometry_source` is a necessary first step but not sufficient to resolve inferred attributes and source lineage.

### Strictly bounded next acquisition gates

1. Execute the already reviewed fixed-source GitHub probe suite separately, with result per source (provider HTTP success and JSON contract verification) rather than inferring reachability from offline CI.
2. For EUBUCCO, resolve a specific ODbL-only NUTS subset after checking all geometry and non-geometry lineage; then bounded projected-column preflight in a controlled DB, with no raw building geometries made public.
3. For GISCO 2021, confirm May 2026 exact archive/metadata, population disclosure rules and country coverage, before one bounded grid value sample; never silently join a noncommercial EuroGeographics boundary.
4. For DWD RADKLIM, select a **single original/corrected 2021** file and verify the matching source-version DOI/supplement boundary before decoding any pixel.
5. For GHSL AGE and JRC GSW v1.5, freeze one exact pixel asset, compare source version/time and quality caveats; collect hashes/CRS/units first, then only permitted and scientifically defensible sample bytes in private Neon.

The five use-case rights records do not override `access/*.json`, original provider agreements, or independent scientific suitability checks.
