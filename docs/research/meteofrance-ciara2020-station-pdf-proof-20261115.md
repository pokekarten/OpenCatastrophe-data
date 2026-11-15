<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara 2020: verify official source PDFs for French full-72h gust stations

**Research date:** 2026-11-15. The original provider hourly archives from the four departments are pinned and the [Ciara 72-hour window audit](meteofrance-ciara2020-four-original-event-envelope-20261115.md) showed only **nine stations** with a complete accepted FXI3S series in four departments (0/3/4/2 for 02/62/76/80).

## Authoritative station metadata source

Météo-France publishes official [station information PDF sheets](https://www.data.gouv.fr/datasets/fiches-dinformations-sur-les-stations) listing the geographic site, successive locations, measurement/site class, instrumentation and history, under an Open Licence v2 label. The exact official catalogue API `https://www.data.gouv.fr/api/1/datasets/fiches-dinformations-sur-les-stations/` publishes each station PDF with a distinct resource UUID, station ID in the title, declared original bytes, and an official publisher object under `https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/INFOS_POSTES/`.

**Substantive goal:** independently re-check the original hourly SHA-256, calculate eligible exact 72h qualified station-ID set *in ephemeral memory only*, use those IDs to locate exactly one official station PDF per eligible station, download and verify the exact official PDF original length/signature/SHA, and emit counts and a private-ID-bound cohort digest. No raw source PDFs, station names, coordinates, individual IDs or hourly observations enter Git or CI log.

## Critical scientific boundary

This stage **proves only PDF identity, access and byte receipt**, not that the actual PDF text/history has been read, that an anemometer was installed on the February 2020 site, or that the physical 3-second gust measurement is exactly comparable to ERA5 postprocessed gust. The site time-series and instrument classes still must be reviewed in the original PDFs before any matched model skill/calibration. No production/source admission or annual OEP/AEP/AAL is authorized. The provider catalogue is mutable; its original byte SHA is logged for rerun integrity but is not treated as an immutable resource release.

An exact-branch one-off PR workflow tests the catalog and eligible-source PDF receipts; after success, change the provider download workflow to manual-only to prevent repeat downloads. The source-identity and byte-gate regression tests are offline/synthetic.

## Original provider catalogue coverage exception (15 November 2026)

The first four-job original station-sheet read passed for dept 02 (zero eligible station PDFs), **three original PDF assets in dept 62**, and **two original PDF assets in dept 80**. The department 76 job **blocked** with a non-identifying reason: at least one of its four qualified stations lacked a unique resource matched by the official `Departement_DD_station_NNNNNNNN_commune_...` title convention. This is not evidence that a PDF does not exist; the official provider may use another naming convention or a complementary sheet resource. The strict parser has **not** been relaxed to guess a different station identity. Instead, exact missing-title matches are now reported as `eligible_station_pdf_unmatched_exact_title_count`, `eligible_station_pdf_exact_match_complete=false`, retaining all source-admission and hazard-calibration prohibitions. Ambiguous *multiple* matching PDFs remain a hard block.

## Distinct official complementary station-sheet source (15 November 2026)

Météo-France also publishes the separate [complementary station information sheets dataset](https://www.data.gouv.fr/datasets/fiches-dinformations-sur-les-stations-complementaires) under an Open Licence 2.0 label, with **796 distinct partner-station PDF resources** visible on the provider page. Its original PDF URL objects have the different publisher prefix `BASE/INFOS_POSTES_COMP/`, not `BASE/INFOS_POSTES/`. The exact source URI is `https://www.data.gouv.fr/api/1/datasets/fiches-dinformations-sur-les-stations-complementaires/`. The runner now searches **only stations with zero exact-title matches in the primary official catalogue** in this independently named complementary provider dataset, requiring the same exact department, station ID, UUID, declared PDF size and publisher-path constraints. This is not fuzzy matching, and does not treat stations as direct Météo-France instruments without historical site verification. Missing stations remain explicitly unmatched; duplicate identities remain blocked.

## Strict ambiguous-originals and historical identity boundary

The exact-ID fallback still found **multiple source PDF metadata records** for at least one eligible Seine-Maritime (76) station in the complementary/primary lookup. An ambiguous station is now reported as an **unresolved multiple-source identity**, counted separately from an absent exact-title match. It is explicitly excluded from original-PDF byte proofs; **no newest-file or first-file guess is permitted**, and the cohort's `eligible_station_pdf_exact_match_complete` remains false until a reviewed unique identity is shown. Verified unambiguous PDF sources can still be hashed and counted.

Météo-France [announced a 16 April 2026 station identifier harmonization](https://confluence-meteofrance.atlassian.net/wiki/spaces/OpenDataMeteoFrance/pages/1603796993): some `num_poste` identifiers and department association changed, with no period of parallel old/new identifiers. Therefore a 2026 PDF catalogue ID matching a 2020 original-hour record is only a **current-catalogue identity match**, not automatically proof that the same site/instrument existed or had that canonical ID during the February 2020 storm. Original event use requires independently time-scoped station-site/instrument records and any affected original/renamed station lineage before physical model comparison.

## Executed official PDF original-byte evidence (15 November 2026)

The [successful original-provider GitHub Actions run 43743317214](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43743317214) rechecked all four SHA-pinned Ciara hourly original sources, then matched each full-72h quality-approved station identifier to the primary official Météo-France station PDF catalogue. A public Météo-France **complementary station** catalogue was configured as a distinct exact-ID fallback; the observed station cohort did **not** require a fallback PDF because the remaining unresolved source was an *ambiguity*, not a missing title. Future replays fetch the complementary catalogue only when a primary source has an exact-title **miss**, not an ambiguous duplicate.

| Department | 72h quality-approved station IDs | Verified original PDF files | Primary PDFs | Complementary PDFs | No exact title | Multiple candidate resources | Verified PDF bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Aisne (02) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pas-de-Calais (62) | 3 | 3 | 3 | 0 | 0 | 0 | 3,494,855 |
| Seine-Maritime (76) | 4 | 3 | 3 | 0 | 0 | **1** | 2,729,497 |
| Somme (80) | 2 | 2 | 2 | 0 | 0 | 0 | 2,111,877 |
| **Total** | **9** | **8** | **8** | **0** | **0** | **1** | **8,336,229** |

The official Météo-France station-PDF catalogue original SHA-256 was `d0b465ae592e1d1a586f87aed4f29292bc063c3ca3d73d489f42af1d3b913a6b` at source acquisition. Only **cohort SHA-256** values combining privately held station IDs, official PDF resource UUIDs and the full original PDF byte digests are published. These receipts are reproducible by authorized original-source reinspection without storing source PDFs or individually identifying stations in Git.

- 62 cohort digest: `16e0ee52a7a0b40bc88a7663ea488c311eb43bb9695e4c4f010c4643a9450ad0`.
- 76 cohort digest (three unique original PDFs only): `ab0cc23e582d237ea41472fcc5e3897740ff5414637f46e73efcf3b5b31feb65`.
- 80 cohort digest: `9881f7fb57cd4c86c58f79d881f12ffd8c2b955db01311f85cc6f7f1ef3a2a2b`.

**Precisely unresolved:** one of four eligible Seine-Maritime station identities had multiple original PDF metadata records. We did **not** choose a record, claim those copies are identical, certify 2020 instrument exposure or deem the cohort 9/9 complete. A separate review needs to compare exact original PDF copies, station identifier harmonization and the 2020 historical anemometer/site record. Eight original PDF files were byte-verified; **zero individual historical wind-sensor histories have yet been formally validated**. Production ERA5-vs-observation skill and insured loss calibration are therefore still blocked.

The source network job is now **manual-only** after its successful bounded one-off evidence run, with all test fixtures remaining deterministic and synthetic.
