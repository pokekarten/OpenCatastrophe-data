<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Blue Heart 2026 — original README byte receipt and temporal / quality semantics

**Review date:** 2026-11-10. **Status:** research-only, **not admitted**. This file records a bounded metadata/documentation preflight, not telemetry or insurer data, model calibration, licence approval, API automation permission or a source-derived scientific result.

## Original-source identity and byte evidence

- Canonical source entry in this PR: `uk.exeter-blueheart-hydrometric.zenodo-20699635`, [Zenodo record v1.0](https://zenodo.org/records/20699635); version-independent conceptual DOI mentioned in the [2026 ESSD preprint](https://doi.org/10.5194/essd-2026-569) is `10.5281/zenodo.20699634`.
- One original Zenodo README resource was read as HTTP response **bytes**, via an unauthenticated web-retrieval intermediary, from `https://zenodo.org/records/20699635/files/README.md?download=1`. The content is source documentation, **not measured telemetry, location features, claims, a license statement, or a signed publisher attestation**.
- Observed README length: **6,995 bytes**; SHA-256 of the retrieved bytes: `ff9b0259b579cae0a36d5f8388928f3e251cfece348be6edcd25b607f19112c7`. Hash algorithm was sanity checked against the well-known SHA-256 `abc` vector before hashing. The Zenodo record separately **advertises** `README.md` MD5 `dd4805e631f9519e1bf19472df82a13b`; this advertised MD5 has **not** been independently reconciled with the SHA-256 byte observation. Both hashes refer to a mutable download route unless record-version pinning is preserved.
- Provider record lists approximately **683 MB** across archives, an `index_telemetry_data.csv` of approximately **117.3 kB**, and the above approximately **7 kB** README. These are publisher-described file sizes, not our bulk-download receipts. No source data bytes are committed to Git and no telemetry ZIP or index CSV was downloaded in this preflight.
- Software/reference: Blue Heart data processing scripts `10.5281/zenodo.21390823` (cited by the preprint); use scripts only after their own exact licence and version review.

## Scientific interface from the original README

| Original field or product | Recorded meaning | Fail-closed CAT/ML interpretation |
| --- | --- | --- |
| `gaugeType` | Borehole, Fluvial, Sewer, Highway gully, Rain | Preserve type and observation mechanism, not interchangeable hazard sensors |
| `locationLatitude`, `locationLongitude` | Gauge location | Site inventory, not observed inundation polygons or policy locations; no individual rows in public Git |
| `dataPath`, `dataQualityFlagsPath` | Relative path to measurement CSV and separate corresponding QC-label CSV | Pair by original paths / timestamps; absence of a QA pair is **not** evidence of valid measurements |
| `gaugeParameters`, `parameterUnits` | Semicolon-associated measured variables and unit values | Match one unit per parameter, preserve exact units before comparison or conversion |
| `floodThreshold_mm` | Flood threshold in millimetres, present for Highway gully gauges | A local threshold in **mm**, not a flood depth in metres, and not an event-wide damage state |
| `bedLevelEstimate_mAOD`, `bankLevelEstimate_mAOD` | Estimated bed/bank level for Fluvial gauges | Height relative to Ordnance Datum; different physical reference from sensor depth and highway gully threshold |
| `3_...` to `7_...` telemetry archives | Borehole, fluvial, sewer, highway gully, and rain gauge series | Sensor quality and sampling coverage require separate checks per archive |

**Timestamp blocker:** The README says raw device timestamps are generally UTC-offset RFC 3339 values (for example, `2025-06-30 16:42:43+00:00`), **except that Highway gully raw telemetry timestamps omit the timezone offset** (for example, `2025-06-30 16:42:43`). Its separately calculated QC-label CSVs *do* use UTC-offset timestamps. Until the source establishes what clock and DST rule governs gully measurements, do **not** automatically assume UTC, Europe/London, a fixed +01:00 offset, or a unique UTC event instant. A naive timestamp must not be directly joined to a timezone-aware weather/storm sequence as if its timezone were known.

**Quality flags:** The README defines numeric classes `1` = good, `2` = suspect, `3` = bad/not physically plausible, with optional failure suffix labels `A` = above range, `B` = below range, `C` = low signal-to-noise, `D` = high rate of change, `E` = persistent constant. It gives `3BE` as an example. Preserve original combined code and class; do not treat missing flags as `1`, drop all `2` rows without reporting the impact, or infer a flood event from an isolated QC label.

## Upstream example loader: explicitly documented UTC-localisation assumption

The original Blue Heart authors publish [the example scripts](https://github.com/csweetapple/blue-heart-dataset-scripts) as the versioned Zenodo software record [`10.5281/zenodo.21390824`](https://zenodo.org/records/21390824) (`v1.0.0`), linked to the concept DOI `10.5281/zenodo.21390823`. The official Zenodo API reports `cc-by-4.0` for the software record and a publisher-reported 261,380-byte source ZIP; no code ZIP bytes were fetched in this review. The public GitHub `blue_heart_data_handling.py` was inspected directly.

**Author implementation, not physical clock verification:** `_convert_to_tz_aware_index` parses a raw `timestamp` column with Pandas, checks whether it has an existing timezone, then applies `tz_localize('UTC')` *when timestamps are naive*. This is a reproducible **software convention**, but the repository does not demonstrate that every highway-gully device recorded in UTC or what happened across British summer-time transitions. We therefore preserve the stricter OpenCatastrophe rule: source-naive times remain unaligned until the logger's physical timezone and DST interpretation are substantiated; no silent `UTC` imputation or false event identity.

The author loader also offers a `Quality1` mode filtering to only QC flag `1`. That is a user-selected analysis filter, not a guarantee that discarded `2`/suspect data are invalid; report missingness and selection bias separately in future calibration. The project does not copy or vendor the example loader.


## Original highway-gully ZIP directory receipt — bounded tail (2026-11-10)

Zenodo record-v1.0 API lists `6_highway_gully_telemetry_data.zip` as **4,229,095 bytes**, with provider-advertised MD5 `64ebe2a3fe9d9cb09f820802d134b8fb`. A read-only intermediary retrieved one exact **12,095-byte suffix** from the original source content URL `https://zenodo.org/api/records/20699635/files/6_highway_gully_telemetry_data.zip/content`, requesting byte range **4,217,000–4,229,094**. The tail contained a classic ZIP end-of-central-directory and complete central directory; the latter starts at **4,225,122**, occupies **3,951 bytes** and is linked to the end-of-central-directory. This is **not** a full ZIP download or full-ZIP digest/CRC receipt.

The directory independently enumerates **31 entries**: **one root directory marker**, **15 measurement CSVs** and **15 corresponding quality-label CSVs**. All 15 stems pair one-to-one; no unmatched files, duplicate paths, unexpected extensions, encrypted entries, unsupported compression methods or unsafe parent traversal were observed in this original directory. The 30 CSV members use DEFLATE, and source-declared total uncompressed member length is **26,739,280 bytes** (largest single CSV **1,038,972 bytes**, maximum observed compression ratio about 6.71). Member payloads, individual data timestamps, CRCs, field values and actual on-device UTC configuration remain **unread** and **unverified**.

To turn this receipt into a reproducible full-object integrity gate once authorized local download exists, this PR adds `research_runners/blue_heart_gully_zip_inventory_v0.py` and `tests/test_blue_heart_gully_zip_inventory_v0.py`. The offline tool accepts only the original exact filename, size and publisher MD5; it computes the original full-byte SHA-256 on local files and validates safe 15/15 pairing, case-insensitive uniqueness, one root folder, no encryption/symlink/path traversal, supported compression, and capped expansion. It **does not open or extract any CSV member** or emit member names; tests use only independently generated synthetic ZIPs. It cannot claim its full-object checks have executed on the original until that exact ZIP is safely available locally.

**Next experimental boundary:** the directory receipt makes a source archive technically inspectable, but it does *not* resolve the 15 highway-gully raw timestamp timezone. Do not force event/time calibration from the matching index, the published README's naive timestamps or the upstream author's UTC-localization convention.

## Cross-file publisher index-to-archive path reconciliation

A second read-only metadata check reconstructed **two distinct original Zenodo v1.0 products** via finite HTTP Range windows: the 117,300-byte `index_telemetry_data.csv` (original full-source SHA-256 `44d53fe95e70cd3665678aec469666c1b22b3323c52424d9838ee5a6d24c4f40` as recorded above) and the original highway-gully ZIP's last 12,095 bytes (central-directory metadata only). The 497-row global index identifies exactly **15 Highway gully** rows, each with a `dataPath` and `dataQualityFlagsPath`.

Compared the original relative paths **in memory** against the 30 CSV filenames from the ZIP central directory:

- **15/15** highway-gully measurement paths resolve to a ZIP CSV member;
- **15/15** corresponding quality-file paths resolve to a ZIP CSV member;
- **0** index-referenced highway-gully paths are missing from the ZIP central directory;
- **0** ZIP CSV members are unreferenced by those 15 index rows.

This is an original **cross-file metadata linkage** between the published gauge index and the published archive inventory; it improves on merely matching 15 filename stems. **No individual source path, row, location name or coordinate was printed, stored in the public repository, or imported into Neon.** Metadata linkage does not prove original CSV payload CRC/integrity, quality scores, device timezone or a scientifically admissible storm-to-loss calibration.

## Offline two-file temporal reconciliation gate (added 2026-11-10)

New `research_runners/blue_heart_timestamp_pair_preflight_v0.py` and `tests/test_blue_heart_timestamp_pair_preflight_v0.py` exercise a **locally supplied**, bounded measurement CSV and its matching quality-label CSV, using synthetic data in repository tests. This additional preflight checks only the `timestamp` headers and rows. It does **not** fetch, embed or publish source telemetry or declare the gauge record fit for insured flood modelling.

The gate rejects missing/non-unique timestamp headers, missing or malformed time cells, naïve timestamps, duplicate **UTC-equivalent** instants (even across different declared offsets), empty datasets, malformed CSV rows and counts over the configured cap. Offset-bearing instants are normalized to UTC for matching; it reports only aggregate matched/missing timestamp counts. Equal timestamp sets are a *necessary technical shape condition* but do **not** approve the physical logger clock; `physical_clock_provenance_verified`, `timestamp_alignment_approved` and `source_bytes_admitted` all remain `false`.

Provider application-script behaviour still differs: author example code localizes offset-naive timestamps to UTC, but this is a coding convention rather than an instrument's verified UTC/DST provenance. Accordingly this preflight **fails closed** for the highway-gully raw-file timestamps documented as offset-naive in the source README. It is not appropriate to force UTC merely to produce matched joins. When upstream instrument timing has been verified, any specialized, documented alignment transform should be implemented separately and tested for ambiguous and repeated local DST hours, not silently enabled in the generic preflight.

The upstream paper [ESSD-2026-569](https://doi.org/10.5194/essd-2026-569) remains a **preprint under review** at the time of this source research; it is scientific methodology evidence, not a peer-reviewed acceptance claim or raw logger UTC certification.

**Not performed:** No individual sensor time series or QC ZIP archives were inspected during this new check, no original time pairing statistics asserted, no author correction or time-zone source evidence obtained, and no downstream model input admitted.

## Legal, privacy and independence limits

The rendered Zenodo page's **Rights / License display was blank** in the accessible view; however, the **official Zenodo REST API** for the exact version `https://zenodo.org/api/records/20699635` returned `metadata.access_right=open` and `metadata.license.id=cc-by-4.0`. The API also listed nine source files, including `README.md` (`size=6995`, advertised MD5 `dd4805e631f9519e1bf19472df82a13b`) and `index_telemetry_data.csv` (`size=117300`, advertised MD5 `aa2d98d36ea6837f35b8ced1c2141767`). This is version-bound **record-level licence and publisher checksum evidence**, not a downloaded index, signed response, or a complete audit of all embedded source rights. The README credits Southern Water for permitting **public sharing** of its sewer-monitoring data. Neither that acknowledgement nor Zenodo's generic default licence proves permission for commercial insurer model calibration, re-publishing telemetry, publishing individual sewer locations, or derivative distribution. Rights and privacy remain **not reviewed** and source admission **not admitted**.

Blue Heart water-level sensors, UK Environment Agency rainfall / river products, and modeled pluvial inundation surfaces can share input events and cannot automatically serve as independent ground truth for one another.

## Original index CSV receipt — bounded read-only inspection (2026-11-10)

This is a separate original provider-byte inspection from the 6,995-byte README review. We read the exact Zenodo record-v1.0 public resource `https://zenodo.org/api/records/20699635/files/index_telemetry_data.csv/content` using four finite, non-overlapping HTTP Range byte windows: `0-29999`, `30000-59999`, `60000-89999` and `90000-117299`. Each returned the expected number of response bytes. The four windows were reconstructed **in memory**, parsed as RFC-4180-style CSV and hashed with a SHA-256 routine checked against the `abc` test vector.

- Observed complete source length: **117,300 bytes** (equal to the official Zenodo record API's file size).
- Observed complete-source SHA-256: `44d53fe95e70cd3665678aec469666c1b22b3323c52424d9838ee5a6d24c4f40`.
- Zenodo API **advertised** MD5: `aa2d98d36ea6837f35b8ced1c2141767` (this MD5 was not independently recomputed).
- Strict structural scope: **497 nonempty CSV records**, **12 distinct field names**, **497 distinct telemetry paths**, **497 distinct QC paths**. All 497 rows had the required field values (except the three scientifically optional level/threshold attributes).
- Gauge classes: **398 Sewer**, **58 Fluvial**, **15 Rain**, **15 Highway gully**, **11 Borehole**. Parameter count distribution: **417 one-parameter**, **21 two-parameter**, **59 three-parameter** rows.
- Scientific optional dimensions: `floodThreshold_mm` populated in **15/15 highway gully** rows (482 blanks across the full index); `bedLevelEstimate_mAOD` and `bankLevelEstimate_mAOD` each populated in only **39/58 fluvial** rows (458 blanks per field across the full index). The other **19 fluvial rows** have no published bed/bank estimates in these index columns. Their absence is *missing*, not a value of zero or sea level.
- Structural checks observed **zero** duplicate data paths, duplicate QC paths, malformed `.csv` path extensions, missing required param/unit mappings, non-finite/out-of-range lat/lon, unexpected gauge-type placement for optional dimensions, non-numeric optional dimensions, and unpaired bed/bank population in this exact index snapshot.

**Evidence limit:** A read-only intermediary retrieved the source in four windows; this is not a publisher-signed attestation or a separate provider MD5 verification. Reproducibility requires the SHA-256, exact record DOI/version, content URI and the byte-window procedure; the source bytes are not present in Git. The number of sensors is not their **temporal** coverage, QC pass rate, a count of genuine observed flood events, a licence approval for individual sewer coordinates, or a validated pluvial loss model. No telemetry ZIP, gauge-level series, original index rows or sensitive coordinates were committed or loaded into Neon.

The offline Python preflight `research_runners/blue_heart_index_preflight_v0.py` now checks the optional columns for finite values and compatible gauge classes without requiring that all fluvial sensors have bed/bank estimates. This preserves source missingness and reports only aggregate optional-field counts. Its reproducible synthetic tests remain separate from the in-memory original-source inspection.

## Smallest causal next preflight

1. The official versioned Zenodo record now explicitly declares CC BY 4.0; verify whether the complete set of third-party telemetry, precise sewer assets and derivatives can be used for insurer model calibration and redistribution, especially Southern Water's reuse scope and privacy.
2. **Completed technical metadata inspection:** the exact 117,300-byte original CSV index was read in memory and hashed; 497 gauge rows and optional-field coverage are documented above. This neither authorizes publication of the source rows nor resolves third-party sewer-network reuse.
3. Confirm the Highway gully raw-device timezone and DST handling, including an explicit crosswalk to offset-bearing QC timestamps. The upstream example loader **assumes UTC for offset-naive values**, but this software convention alone does not resolve physical clock provenance. Do not silently impute UTC.
4. After source-specific rights and time-zone clearance, choose one bounded sensor and weather-event period, freeze the exact ZIP identity, preserve QC class and unit mapping, and run a deterministic synthetic/held-out challenge. Do not generalise to flood depth, urban sewer property damage or insured losses without separate physical evidence.

**Explicitly not done:** Original telemetry ZIP retrieval, independently signed provider-byte attestation, full time-series coverage/QC rate analysis, source-wide rights/admission approval, event overlay, AEP/OEP loss computation or Neon ingest.
