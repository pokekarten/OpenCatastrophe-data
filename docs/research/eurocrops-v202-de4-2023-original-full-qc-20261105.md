<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EuroCropsV2 corrected Brandenburg DE4 2023 — complete original-source QC

Date: 2026-11-05. **NOT_ADMITTED** for actual insurer exposure, rights-cleared CAT modelling or economic losses.

## Original identity and audit evidence

The complete JRC corrected original asset was downloaded and re-hashed in isolated GitHub Actions runners. **No original geometries, parcel-level records, IDs or source bytes were committed or uploaded.**

- Official asset: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/de4_2023.parquet
- Original file: **143,006,611 bytes**. First-seen and repeat-download SHA-256: `4fc38f688a117db6cd0821c7aafc71fbbd2e7a493044c51266ae289929d7b2b6`. It is **not a publisher-signed checksum**.
- Independently observed original 16,266-byte footer SHA-256: `3ccb9177c49914f95e63d3942977c0d95a174b8434c004ba31f523be574b8d53`.
- Original Parquet footer: **285,606** records in one row group, GeoParquet geometry field **`geometry`** (not `geom`), WKB and EPSG:3035.
- Evidence: [first full-byte receipt](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42114631274), [complete area-column QC](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42115645801), [65 zero-area original WKB diagnostic](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42116494785), [complete WKB and crop hierarchy QC](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42117394009).
- Canonical machine-readable quality observation: `research/observations/eurocrops_de4_2023_original_full_area_qc_20261105.toml`.

## Measured on all 285,606 original field records

| Independent QA property | Actual result |
| --- | ---: |
| Nonempty topologically valid polygon WKB with positive area | **285,541** |
| Empty WKB original geometry, all stored as zero hectares | **65** |
| WKB missing/unparseable, nonpolygon or invalid topology | **0** |
| Mismatch >1% between valid polygon area and `area_ha` | **0** |
| Duplicate `cropfield` IDs (subsequent occurrences) | **0** |
| Rows resolving to an HCAT4 entry | **285,600** |
| Rows mapped to a missing HCAT4 hierarchy entry | **6** |
| Missing regional original code mappings or blank field crop codes | **0** |

The **65 empty source geometries** are not spatial assets: do not replace them with invented polygons, point-centroids or insured values.

The **6 missing HCAT4 references** are a taxonomy defect, not missing parcel geometry. In the DE4 original mapping the relevant original code is **429 (Esparsette)** and the missing HCAT4 hierarchy code is **3310201050**. Do not infer another crop. The exact overlap of missing HCAT4 and valid geometry has not yet been reported as a separate number.

The sum of raw source field polygons is **1,324,692.8892 hectares**, matching the source `area_ha` sum at four printed decimals. **This is a sum of the individual source rows, NOT an overlap-de-duplicated spatial union or evidence of all cultivated land in Brandenburg.** Individual geographical overlaps, completeness of the national paying-agency crop declarations, real insurance policies and crop sums insured remain unknown.

## Publisher codebook audit

At publisher repo commit `b556d10651b98684d5d5269916f8f34c9e017151`, `eurocrops.csv` contains 5,772 rows: 5,754 joinable original regional codes and 18 exact blank original-code sentinels (one for each region) describing `not_known_and_other`. They are never joined to cropfield rows. The 353-entry `hcat4.csv` has three mapping-row gaps across DE4/DEA; the full DE4 2023 original contains six actual field records affected by its DE4 hierarchy gap. The DE4 codebook contains 299 nonblank original crop codes.

## Executable audit route and model boundary

- `research_runners/eurocrops_jrc_acquire_v0.py`: bounded official JRC file download outside Git, maximum 180 MiB.
- `research_runners/eurocrops_jrc_original_run_v0.py`: file hash/footer provenance, 1,024 uniform sample, complete area attribute QC and codebook pin.
- `research_runners/eurocrops_original_zero_area_geometry_v0.py`: read WKB only for the 65 zero-area source records.
- `research_runners/eurocrops_original_full_geometry_code_qc_v0.py`: complete original WKB topology, source area, original field-ID uniqueness and DE4 HCAT4 mapping census.
- `.github/workflows/eurocrops-de4-original-one-shot.yml`: the earlier path-triggered source runs uploaded aggregate JSON artifacts only; the workflow is now **manual dispatch only** and uses solely the repository's allowed actions, with **no artifact upload on future runs**. It deletes original raw bytes from the ephemeral runner. Prior historical aggregate receipts are still available on the linked successful GitHub run.

The original source has **technical topology and codebook QC evidence**, but still lacks independent coverage/overlap verification, legal/scientific admission for model use, real dated physical flood/hail hazards, crop valuations and vulnerability calibration, insurer contracts and stochastic event frequencies. Existing invented OEP/AEP and crop direct-value experiments remain synthetic arithmetic, **not actual insurer gross/net CAT curves**.
