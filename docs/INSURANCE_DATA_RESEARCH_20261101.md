<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

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

Both research tables enforce `model_input_approved=false` / `model_admitted=false`. The initial database import did **not** preserve the exact aggregate original HTTP response bytes or its SHA-256. We have since independently verified all 46 original public names-index page bodies and their hashes, as detailed below. Those page hashes do **not** recreate the original aggregate `names.json` file hash or establish regulatory approval. No original third-party rows are published in this repository.

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

## Paged source equality spot-check (2026-11-01)

Two complete JSON index pages were retrieved from the publisher and compared with the CAT-only Neon research table in read-only queries. Both report version `2026-09-08+97f331e66662`, aggregate count 18,180 and page count 46.

| Public names index page | Original bytes | SHA-256 of page response | Exact Neon matches |
| --- | ---: | --- | ---: |
| `https://insurers.global/api/v1/insurers/names/pages/1.json` | 55,474 | `e926e1377a4a6e6d1f62a087ff1908619baedfb3bec5d867e69af8d0209cd92e` | 400/400 |
| `https://insurers.global/api/v1/insurers/names/pages/46.json` | 31,743 | `2f961b423a9b11b6ff662c15579c233ea7ccac8a9c325f076d9754563806f9de` | 180/180 |

No mismatches in exact slug, country, name, class code or publisher verification claim in these 580 records. The SHA-256 implementation was checked with the standard `abc` test vector. No database rows were changed.

**Limits:** Only 580/18,180 records have been compared this way. The full `names.json` file was not acquired completely and has no established original-byte SHA-256. The above hashes belong to individual pages, not to the historical database import or every source row. The staging URL/hash gaps and independent regulator verification remain unresolved; model admission is blocked. Next step: verify all 46 pages and preserve per-page provenance before any permitted metadata repair.


## Complete original-page receipt runner

`scripts/insurer_directory_paged_source_receipt_v0.py` implements a strict 46-page enumeration of the public index. It checks source version, navigation, declared and actual counts, publication metadata, duplicates within/across pages, exact HTTPS origin and per-page SHA-256. It outputs only metadata and hashes, without raw names or database writes. Validation has synthetic offline tests in `tests/test_insurer_directory_paged_source_receipt_v0.py`.

Run with `python -m scripts.insurer_directory_paged_source_receipt_v0 --page-dir /path/to/private/pages` for existing local pages named `page-001.json` through `page-046.json`. The alternative `python -m scripts.insurer_directory_paged_source_receipt_v0 --live` explicitly enables bounded public HTTP requests. There is no implicit network access. Store any command output outside Git until its scope is reviewed.

The chat-side original-byte extraction interface truncated some pages beyond approximately 59 KB, so the full 46-page receipt was **not completed here**. Do not confuse the executable runner with an executed full-source proof. The connected remote Mac was offline during this check.


## Completed 46-page original provider verification and exact Neon five-field comparison

The complete evidence is pinned in the **canonical metadata-only machine receipt**
[`docs/research/insurer-directory-original-page-receipt-20261101.json`](research/insurer-directory-original-page-receipt-20261101.json).
The verified [GitHub Actions source run](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41325317453)
successfully retrieved **46 of 46** exact public page URLs, totaling **2,995,068 original
bytes** and **18,180 distinct source slugs**, with full page lengths, version,
count, pagination, cross-page duplicate rejection and individual **SHA-256 hashes**.
A publisher-identifying user agent and bounded request cadence were necessary:
the initial unlabelled GitHub-runner API request returned HTTP 403. The final
audited retrieval complied with the provider's documented fair-use requirements.

An independently executed read-only Neon query in
[`research_runners/sql/insurer_directory_field_digest_readonly_v0.sql`](../research_runners/sql/insurer_directory_field_digest_readonly_v0.sql)
computed the sorted UTF-8 SHA-256 digest of `source_slug`, `country_slug`,
`display_name`, `class_code`, `provider_verification_claim` across the
**18,180** Neon research entries. The original provider's corresponding
fields across all 46 pages produced **the exact same digest**:
`4bc5f71de226e5e19f1ece179754c440546e808beed46f9f8e55509ba05b8178`.
The Neon hash query reports **0** missing required fields, **0** reserved
delimiter collisions and **0** CAT model-input approvals. This is
complete **five-field parity**, not original aggregate byte-equivalence,
independent regulator licensing, unique legal-entity identification or
insured CAT exposure.

A separate read-only identity ambiguity audit
[`research_runners/sql/insurer_directory_identity_ambiguity_v0.sql`](../research_runners/sql/insurer_directory_identity_ambiguity_v0.sql)
confirms **18,180 distinct slugs but only 17,784 distinct global
case-normalized name strings**. There are **two** repeated
market/name groups comprising four excess same-market rows, and **31**
lexical matches to **19 of 22** existing verified organizations (only 20
matches in their explicitly mapped DE, FR or SG home market). This lexical
comparison creates **no new identity links**. Another **45 of 58** official
licence observations remain unlinked; **four** regulator crosswalk entries
lack independently verified LEI-to-registration evidence.

The aggregate `names.json` original byte hash remains **unknown** and the
previous `source_dataset_url` placeholders and `raw_provider_sha256` nulls
in Neon remain **unmodified**. Repairing provenance requires an exact reviewed
row-to-paginated-source lineage, not copying any page hash into the wrong
field. Publisher data must be attributed to KAFS North America,
[insurers.global](https://insurers.global), under CC BY 4.0. All modelling
admission, licence verification, group identification and synthetic exposure
gates remain closed until their own supporting evidence exists.
