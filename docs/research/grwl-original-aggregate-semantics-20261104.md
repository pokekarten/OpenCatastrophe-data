<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GRWL 2018 vs 2026: attribute-value and XY-sequence aggregate source test

Research target: primary Zenodo originals [2018 / GRWL_summaryStats_V01.01.zip](https://zenodo.org/records/1297434) and [2026 / GRWL_summaryStats_V01.02.zip](https://zenodo.org/records/18624542). Both original ZIPs were downloaded, source SHA-256/MD5 verified and original SHP/SHX/DBF members compared in [successful trusted-main run 41822336297](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41822336297); the original ZIP SHA-256 are pinned in `docs/research/grwl-original-byte-receipt-2018-vs-2026-20261104.md`.

That prior byte analysis proved SHP/DBF/SHX differ. **It did not prove any change to the same named river feature.**

## New, falsifiable semantic questions

1. **DBF field descriptors:** Are the original schemas the same, including field names, type and allocated width?
2. **Width histogram:** Is the **multiset** of normalized `width_mean` values identical, independent of record order? If not, what minimum number of numeric values cannot be matched between releases? Normalize numeric DBF values using exact Python `Decimal` (different zero padding and precision representation do not count as different measurements).
3. **Every DBF field:** Compare each source-native typed field value multiset and all whole-record value multisets without ever emitting raw third-party records, local paths, user data or individual values.
4. **Original SHP polyline XY streams:** Compute SHA-256 per record on the geometry part offsets and WGS84 coordinate payload; compare the **multiset** of streams, not only record index. Report total vertices and the number of unmatched XY payloads independent of feature order. A reversed polyline, precision/serialization change or changed part layout may still cause a different byte fingerprint: this is **not** proof of hydraulic geometry change.
5. **Ordering:** If per-ordinal sequences differ but source record multisets are identical, the data could merely be reordered. No record index is assumed to be a stable river identifier.

These are separate from source-file integrity, which remains mandatory: the executable accepts only the two source ZIPs whose current original SHA-256 hashes exactly match:
- 2018: `16830e5444d47d6ba74790613533b6a81b4036a15f3ad7a7066241da28f95306`
- 2026: `78aa43a7104d24b1696e9b1547347eec13ba5d660aa990c1e7cea98e7ae70e4a`

The downloaded original ZIPs remain in runner-local temporary storage; ZIP archive safety and length/MD5 verification are inherited from the already merged trusted source-download and source-preflight modules. The two original source downloads are **disabled for pull-request heads**.

## Exact workflow

`.github/workflows/grwl-original-aggregate-semantics.yml` executes offline synthetic unit tests on pull requests and permits one original source semantic aggregate comparison on a **reviewed main push** or explicit main manual dispatch.

```bash
# Offline synthetic tests:
python -m unittest tests.test_grwl_original_aggregate_semantic_diff_v0 -v

# Only when reviewed and run on trusted main with source access:
python -m research_runners.grwl_original_aggregate_semantic_diff_v0 --live
```

It reports exact source ZIP SHA-256, source DBF field names/descriptor types, field-level counts of distinct values and minimum unmatched value counts, holistic row multiset comparison, and SHP XY-stream multiset comparison. Output is bounded aggregate metadata; **no original source ZIPs or raw DBF/geometry rows are published**.

## Actual original-source aggregate result (2026-11-04)

The first trusted-main original attempt failed closed with a source-network timeout. **The single controlled retry succeeded**: [GitHub Actions run 41850217184](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41850217184), rerun attempt 2, original source checkout `f385eac72de228cd3372b23f476c952d41218800`. Both source ZIP SHA-256 pins matched exactly. Original ZIPs were read ephemerally without publication of source feature records.

Observed on **both original releases**:
- `record_count=42,077`, `total_xy_points=3,129,821`.
- Identical DBF field schema for `OBJECTID`, `ID`, `WIDTH_MIN_`, `WIDTH_MED_`, `WIDTH_MEAN`, `WIDTH_MAX_`, `WIDTH_SD_M`, `LAKEFLAG`, `NSEGPX`, `SHAPE_LENG`.
- The **entire value multisets** of the first nine fields are identical, including all five width measures. `WIDTH_MEAN` has 32 distinct normalized numeric values in each release.
- `SHAPE_LENG` differs in all 42,077 normalized numeric value assignments at **multiset** level; unique numeric lengths: 42,076 in 2018, 42,077 in 2026.
- `semantic_row_multiset_equal=false` because full DBF rows include `SHAPE_LENG`; do not interpret this as every *other* field changing.
- `minimum_unmatched_xy_sequences_each_release=37,355` from 42,077 original SHP polyline XY-sequence hashes. Equal total coordinate point counts do **not** establish identical geometry.
- `OBJECTID` has exactly **42,077 distinct numeric values** in each original, and its **value multiset is identical**. Unlike `ID` (383 distinct values), `OBJECTID` can serve as a testable unique export-row join candidate, but **is not thereby validated as a permanent real-world river identifier**.

This is original, observed aggregate evidence, not a synthetic example. It establishes preserved aggregate width distributions, while leaving per-river widths and per-feature geometry changes **unattributed**.

### Original export-`OBJECTID` keyed result — observed, not inferred

**Successful trusted-main original-data run:** [GitHub Actions #41852020214](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41852020214), checkout `22fef9e93458d241244c4bc10d29a54b5502b3a5`, completed 2026-11-04 ~14:54:29 UTC. The run reacquired the exact source files and verified the same 2018/2026 original ZIP SHA-256 pins. It compared typed DBF field-value digests and original polyline XY-sequence digests after requiring the `OBJECTID` to be numeric, unique in each original, with identical key sets. Each original has 42,077 unique `OBJECTID` values, and **the original `OBJECTID` record order is also identical** across the two releases.

| Exact field or WGS84 XY stream, joined at the same export `OBJECTID` candidate | Number of differing values |
| --- | ---: |
| `OBJECTID` | 0 |
| `ID` | 0 |
| `WIDTH_MIN_` | **0** |
| `WIDTH_MED_` | **0** |
| `WIDTH_MEAN` | **0** |
| `WIDTH_MAX_` | **0** |
| `WIDTH_SD_M` | **0** |
| `LAKEFLAG` | 0 |
| `NSEGPX` | 0 |
| `SHAPE_LENG` | **42,077** |
| Original polyline XY coordinate/part-order **byte sequences** | **37,355** |

The updated keyed comparison is strictly stronger than equality of aggregate width histograms: **all five width fields are numerically identical at the same verified-unique export `OBJECTID`**. The difference between 42,077 original geometries and 37,355 differing XY sequences means **4,722 export-`OBJECTID` matches retain byte-identical XY sequences**, *even though* their `SHAPE_LENG` DBF values still differ. Therefore the `SHAPE_LENG` re-computation cannot be explained solely by changed XY coordinates. It could involve how length was calculated, serialized or reprojected; the original upstream processing history has not yet been established.

**Identity limit:** `OBJECTID` is a dataset/export row ID. Uniqueness, equal value sets, equal order and matching non-length attributes make it a reproducible within-release crosswalk *candidate*, but **not** an independently certified river identifier. No original feature IDs, coordinates, widths, or raw rows are published. The code reports `objectid_is_approved_stable_river_identifier=false` and `per_river_change_attribution_verified=false`.

**Scientific next step:** distinguish polyline orientation reversals and coordinate serialization/precision differences from actual spatial relocation by comparing geometries at matching `OBJECTID` using direction-insensitive geometry checks and a documented geographic-to-metric transformation, then independently validate original river identity against GRWL documentation and regional base-map observations. Investigate the provenance/units of `SHAPE_LENG` separately; **do not** use it as a measured hydraulic river width.

## Scientific gate

If the numeric `width_mean` value distribution differs, a numeric value difference is supported without needing row alignment, but **the altered individual rivers are not yet identified**. If the width multiset is identical while SHP/DBF member bytes differ, the change could be reordering or another attribute. If the original XY multiset differs, the result still requires a future fully keyed, geometry-normalized spatial comparison to distinguish reversed coordinate sequences, precision shifts and true geometry changes.

No RiverATLAS crosswalk admission, flood-stage widths, return periods, insured losses, loss modeling or production Neon writes are authorized. Use-specific source licensing/attribution and independent scientific holdouts remain pending. All original individual row/coordinate data stay off public GitHub.

**Original source evidence:** both aggregate and export-OBJECTID-keyed trusted-main original checks have completed successfully (runs linked above). All numerical comparisons were performed on source bytes with the pinned original ZIP hashes. The semantic interpretation of physical river-geometry changes remains unvalidated.
