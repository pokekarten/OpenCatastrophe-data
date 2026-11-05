<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EuroCropsV2 original crop-code / HCAT4 crosswalk: bounded source audit

Review date: 2026-11-05. RESEARCH-ONLY. No data admission, insured parcels, commercial-rights approval, spatial hazard modelling, or model calibration. Findings describe original public **taxonomy tables**, not individual agricultural fields.

## Exact original source

- Publisher-maintained mapping repository: https://github.com/Martincccc/EuroCropsV2
- Pin original repository tree to commit b556d10651b98684d5d5269916f8f34c9e017151 (not mutable main).
- Original mapping file: https://github.com/Martincccc/EuroCropsV2/blob/b556d10651b98684d5d5269916f8f34c9e017151/data/cropcodemapping/eurocrops.csv
  - Git blob SHA-1 (GitHub source content identity): 37a58061df29036300862dc680c769a1b2727e15.
- Original hierarchy file: https://github.com/Martincccc/EuroCropsV2/blob/b556d10651b98684d5d5269916f8f34c9e017151/data/cropcodemapping/hcat4.csv
  - Git blob SHA-1: 7b4a7d1b5f3312d011958d0a1943c1324c3610ca.
- The EU/JRC source's distinct CC BY 4.0 text is at https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/copyright.txt. This does not by itself complete a separate review of the GitHub repository's mapping file rights or downstream redistribution terms.

## Actual original codebook analysis (read-only through GitHub)

Both exact source files were fetched and read as text. Results from a quote-aware CSV parser, with no farmer rows or source CSV committed:

| Measure | Exact observation |
| --- | --- |
| Mapping header | nuts, original_code, original_name, translated_name, hcat4_code, hcat4_name, usage_code, usage_name |
| Mapping rows | 5,772 total: **5,754 joinable regional crop codes** and **18 exact blank-code unknown-crop sentinels** |
| Source-region keys in mapping | 18 |
| Duplicated (nuts, original_code) pairs | 0 |
| Malformed mapping column widths | 0 |
| Distinct HCAT4 hierarchy codes | 353 |
| Mapping rows pointing to absent HCAT4 code | **3** |
| DE4 (Brandenburg) mapping rows / joinable nonblank source codes | **300 / 299** |
| DEA (North Rhine-Westphalia) mapping rows / joinable nonblank source codes | **289 / 288** |

Missing joins, not missing parcels:

| NUTS key | Original crop code | Label in mapping | Missing hierarchy code |
| --- | --- | --- | --- |
| de4 | 429 | Esparsette (Onobrychis) | 3310201050 |
| dea | 429 | Esparsette (Onobrychis) | 3310201050 |
| dea | 776 | Veilchen und Stiefmütterchen (violets and pansies) | 3310851000 |

The same absent HCAT4 code 3310201050 occurs in two **different regional** mapping rows. Thus there are 3 unmatched mapping rows but only 2 distinct missing HCAT4 hierarchy identifiers. These are taxonomy integrity findings; the mapping file supplies a human-readable name but the standalone hierarchy has no row for that key. Preserve the unmapped status; never quietly join it to an arbitrary parent class or drop a field from the crop exposure model.

The **18 sentinel lines** have empty original_code/original_name/translated_name and contain the exact unknown classification HCAT4 3390000000, label `not_known_and_other`, usage_code 0. These are source-level *unknown* sentinels, not joinable field crop codes; the audited runner now explicitly validates and skips them instead of treating an empty string as a crop type. [The 285,606-row original DE4 2023 census](eurocrops-v202-de4-2023-original-full-qc-20261105.md) encountered **6 actual field records** mapped to DE4 crop code 429 / missing HCAT4 reference, while all remaining **285,600** source rows resolved to an existing HCAT4 code. This does not certify the agricultural value or completeness of any crop.

## Reproducible offline check

Runner: research_runners/eurocrops_codebook_qc_v0.py (Python standard library only). It:
1. reads only two local bounded public CSV files (never downloads);
2. checks exact independently-pinned **Git blob SHA-1** identities (not to be confused with SHA-256 of original file bytes), expected columns, duplicate-code and code-width constraints;
3. reports source totals, per-region mapping counts and missing hierarchy key references; no original rows, insurer details or polygons copied to Git;
4. always reports RESEARCH-ONLY, CAT-model NO-GO.

To reproduce after downloading the original CSVs to an **external working directory** using the exact pinned original commit:

    python research_runners/eurocrops_codebook_qc_v0.py \
      --mapping /external-originals/eurocrops.csv \
      --mapping-git-blob-sha1 37a58061df29036300862dc680c769a1b2727e15 \
      --hierarchy /external-originals/hcat4.csv \
      --hierarchy-git-blob-sha1 7b4a7d1b5f3312d011958d0a1943c1324c3610ca

Offline synthetic tests (do not need the source CSVs):

    python -m unittest discover -s tests -p test_eurocrops_codebook_qc_v0.py -q

## Next scientific and rights gates

- Obtain a source-rights confirmation for original taxonomy CSV, explicit linkage to JRC distributable source/release; do not infer code rights from JRC data license without verification.
- The exact **DE4 2023** gpqtv202 original GeoParquet has now been downloaded, repeat-hashed and fully quality scanned; see [the complete original source report](eurocrops-v202-de4-2023-original-full-qc-20261105.md). The full **DEA** original source has not been checked here; keep its geometry and source vintage separate.
- For each Parquet row, join by **(nuts, original_code)** with original_code kept as a string, preserving leading zeros and source-year provenance; never join on original_code alone.
- Report unknown/missing crop taxonomy as explicit undecided fraction; do not infer crop type from nearest taxonomy code or produce insured values from crop declarations alone.
- Cross-check JRC, national paying agency, Copernicus WorldCereal and independent historical yields without treating correlated upstream observations as independent. No source is admitted into a CAT pipeline by this taxonomy check.
