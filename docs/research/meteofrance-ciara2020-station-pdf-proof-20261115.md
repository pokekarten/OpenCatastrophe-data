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
