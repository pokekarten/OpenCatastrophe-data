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
