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

## Legal, privacy and independence limits

The rendered Zenodo page's **Rights / License display was blank** in the accessible view; however, the **official Zenodo REST API** for the exact version `https://zenodo.org/api/records/20699635` returned `metadata.access_right=open` and `metadata.license.id=cc-by-4.0`. The API also listed nine source files, including `README.md` (`size=6995`, advertised MD5 `dd4805e631f9519e1bf19472df82a13b`) and `index_telemetry_data.csv` (`size=117300`, advertised MD5 `aa2d98d36ea6837f35b8ced1c2141767`). This is version-bound **record-level licence and publisher checksum evidence**, not a downloaded index, signed response, or a complete audit of all embedded source rights. The README credits Southern Water for permitting **public sharing** of its sewer-monitoring data. Neither that acknowledgement nor Zenodo's generic default licence proves permission for commercial insurer model calibration, re-publishing telemetry, publishing individual sewer locations, or derivative distribution. Rights and privacy remain **not reviewed** and source admission **not admitted**.

Blue Heart water-level sensors, UK Environment Agency rainfall / river products, and modeled pluvial inundation surfaces can share input events and cannot automatically serve as independent ground truth for one another.

## Smallest causal next preflight

1. The official versioned Zenodo record now explicitly declares CC BY 4.0; verify whether the complete set of third-party telemetry, precise sewer assets and derivatives can be used for insurer model calibration and redistribution, especially Southern Water's reuse scope and privacy.
2. Retrieve **metadata-only** the 117.3-kB original index CSV with its own byte count + SHA-256 outside Git (subject to rights). Validate field names, one-to-one paths, category distribution and units, without recording source coordinate rows or identities in the public repo.
3. Confirm the Highway gully source timezone and DST handling, including explicit crosswalk to offset-bearing QC timestamps. Do not synthesize it.
4. Only after clearance, choose one small, bounded sensor and weather-event period. Freeze the exact ZIP identity, preserve QC class and unit mapping, and run a deterministic synthetic/held-out challenge. Do not generalise to flood depth, urban sewer property damage or an insured loss without separate physically observed evidence.

**Explicitly not done:** Original telemetry or index data retrieval, licence approval, direct independent publisher-byte signature, full range/time coverage evaluation, event overlay, AEP/OEP loss computation, source admissibility or Neon ingest.
