<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Actual original USFS FPA FOD v7 bytes: ZIP + GeoPackage + 2024 read-only SQL

**5 November 2026. Both complete original release ZIPs downloaded read-only, SHA-256 independently computed and matched primary publisher checksums.** The large ZIP and extracted database were analyzed only on an isolated temporary execution machine and **both deleted** after the verified aggregate read. No source data bytes, fire IDs, ignition points, customer information or original GPKG were committed to this public repository.

## Original version and provenance

- Original publisher: [USFS Research Data Archive 7th edition](https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.7), edition FPA_FOD_20260615 (1992–2024), DOI [10.2737/RDS-2013-0009.7](https://doi.org/10.2737/RDS-2013-0009.7).
- Original publisher states US-government-funded use without further permission or fee, with scholarly attribution guidance and no source access restriction. This general source reuse statement does **not** validate an insurer CAT hazard/loss engine or an MTBS perimeter join.
- [CurrentEdition ArcGIS REST](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer) is mutable; use the exact archived source SHA listed below to preserve physical source identity.

## 1. Original publisher metadata ZIP: COMPLETE MATCH

File: [RDS-2013-0009.7_Metadata_Fileindex.zip](https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7/RDS-2013-0009.7_Metadata_Fileindex.zip)

- HTTP HEAD 200, original file length 31,583 bytes; exact complete ranged GET returned 206, Content-Range bytes 0-31582/31583.
- Full original bytes hashed SHA-256 **1e94a5cab0cdcf77ed92d3b5810dbe1960e704422363ee731367646ac9781a49** — identical to the official published checksum; original ZIP CRC check successful.
- Three original metadata members inspected safely in memory:
  - _fileindex_RDS-2013-0009.7.html: 4,290 bytes; SHA-256 26c0039f0f3960a405ca8a492d999cb7c301f26f7e7f526758c2f2fc5cfd6bb8
  - _metadata_RDS-2013-0009.7.html: 107,109 bytes; SHA-256 79332a9da451489d733159a3a83b43cb776fdcc060aba4de5003f3e1b3c74b83
  - _metadata_RDS-2013-0009.7.xml: 62,911 bytes; SHA-256 e1fd959e8c429cef4ba6c458e77840f95517b9656a0cf48cda9a00e27158ac14
- File index confirms original FPA_FOD_20260615.gpkg and describes the source as an OGC GeoPackage using SQLite.

## 2. Original publisher GeoPackage ZIP: COMPLETE MATCH

File: [RDS-2013-0009.7_Data_Format3_GPKG.zip](https://www.fs.usda.gov/rds/archive/products/RDS-2013-0009.7/RDS-2013-0009.7_Data_Format3_GPKG.zip)

- HTTP HEAD 200 and exact 16-byte range GET 206 both proved endpoint reachability.
- **The complete 238,170,979 source ZIP bytes were actually streamed** via an original HTTP 206 Content-Range 0–238170978/238170979. The full local SHA-256 was **9e36ecd0d70dd5fa126be7b5ce5b02003867da04c41f3bd137f5ccdfca81b9b2**, exactly matching the official catalog's original publisher checksum.
- The actual ZIP central directory contains three members:
  - Data/ (folder)
  - Data/FPA_FOD_20260615.gpkg — **1,082,466,304 uncompressed bytes**, 238,166,464 compressed, Deflate
  - Data/_variable_descriptions.csv — **31,310 uncompressed bytes**, 4,033 compressed, Deflate
- The original GPKG was temporarily extracted; its first 16 bytes were the SQLite format 3 file signature. The database opened read-only with immutable SQLite URI.
- Actual GPKG tables included Fires and NWCG_UnitIdActive_20200123, plus expected GeoPackage and spatial-index system tables. The actual Fires schema includes FOD_ID, FPA_ID, MTBS_ID, FIRE_YEAR, STATE and FIRE_SIZE_CLASS, alongside original geometry/location columns. No source event or coordinate values were written to logs/repository.
- Both original ZIP and extracted GPKG were removed from the temporary machine immediately after the aggregate analysis.

## 3. Independent reproducibility test against full original 2024 event data

Direct read-only original SQLite query:

    SELECT STATE, FIRE_SIZE_CLASS, COUNT(*),
           SUM(CASE WHEN MTBS_ID IS NOT NULL THEN 1 ELSE 0 END)
    FROM Fires
    WHERE FIRE_YEAR = 2024
    GROUP BY STATE, FIRE_SIZE_CLASS;

Results from the **actual archived original**:

| Measure | Archived GPKG SQL | Independently queried live ArcGIS |
| --- | ---: | ---: |
| 2024 FPA source records | 87,708 | 87,708 |
| 2024 records with MTBS_ID | 415 | 415 |
| Distinct state × size-class groups | 299 | 299 |
| State/territory codes | 53 | 53 |
| Size A total / MTBS linked | 43,445 / 1 | 43,445 / 1 |
| Size B total / MTBS linked | 34,441 / 0 | 34,441 / 0 |
| Size C total / MTBS linked | 7,296 / 0 | 7,296 / 0 |
| Size D total / MTBS linked | 1,263 / 6 | 1,263 / 6 |
| Size E total / MTBS linked | 640 / 31 | 640 / 31 |
| Size F total / MTBS linked | 388 / 224 | 388 / 224 |
| Size G total / MTBS linked | 235 / 153 | 235 / 153 |

**The entire archived 2024 national A–G marginal population and linked counts agree exactly with the separate original ArcGIS queries.** This authenticates the source-to-service aggregate cohort for that release, not the physical MTBS event mapping. It materially reduces the uncertainty identified in the [state × size source-key selection study](us-wildfire-2024-state-size-mtbs-original-20261105.md).

## Executable repeatable offline gates

The new runner pins both complete original ZIP sizes and publisher SHA-256, enforces bounded and safe original ZIP member identities, checks metadata CRC/version/citation/rights, validates the second archive's original Data/FPA_FOD_20260615.gpkg plus original Data/_variable_descriptions.csv, and checks the SQLite file signature.

With a private local authorized copy of the original ZIPs, the last option additionally extracts the fully SHA-verified original GPKG to a temporary directory, queries only original 2024 grouped counts read-only, validates A–G national marginals and 53/299 state/size groups, and removes the temporary database automatically.

    python -m research_runners.us_fpa_v7_original_archive_receipt_v0 \
      --metadata-zip /private/RDS-2013-0009.7_Metadata_Fileindex.zip \
      --data-gpkg-zip /private/RDS-2013-0009.7_Data_Format3_GPKG.zip \
      --audit-2024-sqlite

    python -m unittest tests.test_us_fpa_v7_original_archive_receipt_v0 -v
    python scripts/check_all.py

Tests use **synthetic ZIPs and synthetic SQLite rows only**; provider data are not checked into Git. The original external download/SQL analysis and its true SHA/aggregate results were separately executed on 2026-11-05, as documented above.

## What is STILL not admitted or proven

- **MTBS_ID presence** is not itself an observed physical MTBS FIRE_ID match. A corresponding source wildfire boundary, vintage, burn severity map and correct prescribed-fire classification must still be confirmed.
- FPA reports are historical wildfire-occurrence point records, not event footprint rasters, unbiased all-event frequency models, insured damage, or losses for R+V, ENV, TWIA or any other insurer.
- No ground-up insured losses, OEP/AEP or net reinsurance/IP curve may be inferred from the aggregate here.
- Next action: hash the actual MTBS 2024 vintage and perform a **bounded original event-ID and wildfire-type join** against the now byte-verified FPA source before any full CAT exposure overlay. Source rights, geographic/temporal definition, missingness and event multiplicity must remain explicit.
