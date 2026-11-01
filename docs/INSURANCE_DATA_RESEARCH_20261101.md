# Insurance and catastrophe-source research import — 2026-11-01

**Scope:** Separate CAT-only Neon project `insurance-risk-core`, database `insurance`, default branch `main`. This is a research inventory, **not** certified CAT model input.

## Verified Neon read-back

| Research table | Records | Scientific restriction |
| --- | ---: | --- |
| `research.insurer_directory_candidate_v0` | 18,180 | Third-party directory candidates from 181 country/market slugs, not independently regulator-verified |
| `research.usgs_comcat_origin_observation_v0` | 1,333 | Historical magnitude >=6 earthquake origins, 2016–2025, **not** shaking footprints, catalogues, or insured losses |
| `entity.organization` | 22 | Pre-existing independently verified records, not modified |

The [Insurers Global name-index](https://insurers.global/api/v1/insurers/names.json) is pinned to `2026-09-08+97f331e66662`. Its own classification is 16,224 `verified`, 1,920 `partial`, and 36 `unverified`; these are **provider claims** only, never our regulator verification. The publisher claims [CC BY 4.0 terms](https://insurers.global/terms/) and requires attribution: **KAFS North America, insurers.global (https://insurers.global)**. The collection is a secondary directory, not an official register. Source's supplied class codes remain uninterpreted until its vocabulary is independently checked.

USGS [ComCat FDSN Event API](https://earthquake.usgs.gov/fdsnws/event/1/) supplied ten annual GeoJSON requests for 2016–2025 with `minmagnitude=6`. Stored event IDs, UTC timestamps, coordinates, magnitude, depth, status and provider URLs. These are **event-origin observations**, not physical hazard intensities or insurer claims.

Both research tables enforce `model_input_approved=false` / `model_admitted=false`. The original raw HTTP byte stream and SHA256 were not captured through this tool-mediated acquisition: do **not** label source original bytes verified. No original third-party data is published in this repository.

## Reproducible source receipt

`scripts/insurer_directory_source_receipt_v0.py` validates an independently acquired **local** JSON snapshot against reviewed source URL, exact version, count, unique nonblank slugs, provider verification categories and CC BY attribution; it prints summary-only JSON and SHA256 of those **local file bytes**. No network, Neon write or model admission. Seven tests with independently synthetic fixtures in `tests/test_insurer_directory_source_receipt_v0.py`.

## Primary identity sources to reconcile

- [EIOPA Register of Insurance Undertakings](https://register.eiopa.europa.eu/registers/register-of-insurance-undertakings) for EU/EEA legal entity, activity and LEI fields.
- [NAIC publications](https://content.naic.org/publications) for US company and group identifiers; company counts/listings are not unique legal groups.
- [PRA insurer register](https://www.bankofengland.co.uk/prudential-regulation/authorisations/which-firms-does-the-pra-regulate) for UK firm reference numbers and licensed activities.
- [APRA licensed general insurers](https://www.apra.gov.au/registers/list-registered-general-insurers) for Australia.
- [GLEIF terms](https://www.gleif.org/en/meta/lei-data-terms-of-use) for legal entity identification, not insurance exposures or contractual ownership stakes.

## Hazard, exposure, vulnerability, finance: next original inputs

[NOAA IBTrACS](https://www.ncei.noaa.gov/products/international-best-track-archive), [Copernicus CEMS](https://mapping.emergency.copernicus.eu/), [ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), [JRC GHSL](https://human-settlement.emergency.copernicus.eu/), [Oasis OED/ORD](https://oasislmf.org/open-data-standards), [GEM Global Exposure Model](https://www.globalquakemodel.org/product/global-exposure-model). Check source-version-specific rights and scientific semantics; a modelled building stock or replacement value is **not** an insured portfolio value. GEM's publicly available Global Exposure version can have non-commercial share-alike licensing restrictions requiring additional review.

## Promotion gates

1. Legal identifier matching with official registries; corporate groups, branches, licensed carriers and sidecars remain distinct.
2. Source original bytes / SHA, exact product and terms review, timestamp, coverage granularity, raw-vs-derivative rights and lineage.
3. True hazard footprints, exposure, vulnerability, loss benchmarks and scenario correlation / secondary uncertainty.
4. Insured coverage terms, portfolio aggregation, CAT XL and retrocession, annual loss order and reinstatement treatment.
5. Version-pinned reproducible multi-insurer 10,000-year runs and independent holdouts.

Keep the separate pre-existing Neon validation branch's Florida/Texas/NAIC research data until tested reconciliation; do not overwrite it or claim that it is already merged into production.
