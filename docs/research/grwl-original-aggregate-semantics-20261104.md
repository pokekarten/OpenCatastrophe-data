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

## Scientific gate

If the numeric `width_mean` value distribution differs, a numeric value difference is supported without needing row alignment, but **the altered individual rivers are not yet identified**. If the width multiset is identical while SHP/DBF member bytes differ, the change could be reordering or another attribute. If the original XY multiset differs, the result still requires a future fully keyed, geometry-normalized spatial comparison to distinguish reversed coordinate sequences, precision shifts and true geometry changes.

No RiverATLAS crosswalk admission, flood-stage widths, return periods, insured losses, loss modeling or production Neon writes are authorized. Use-specific source licensing/attribution and independent scientific holdouts remain pending. All original individual row/coordinate data stay off public GitHub.

**Current PR evidence:** source semantic workflow has not executed the live step at PR creation. Its results must be read from the exact merge commit workflow logs rather than guessed.
