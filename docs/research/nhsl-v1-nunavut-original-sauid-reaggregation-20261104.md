<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original NHSL v1.0 Nunavut SAUID reaggregation: archetypes ↔ settled areas

**Date:** 2026-11-04. **Status:** cross-layer **numeric conservation demonstrated on original files** in a bounded read-only, in-memory independent SQLite B-tree audit; Python reproduction script and synthetic tests added. **Source not admitted.** This is not an insured exposure portfolio, an OED file or a native CAT model run.

## Original provider data and reproducibility identity

The source is [OpenDRR/NHSL v1.0, Natural Resources Canada](https://github.com/OpenDRR/national-human-settlement/releases/tag/v1.0). **Exact original ZIPs** (published assets, downloaded byte-for-byte via read-only bounded HTTP ranges; their source bytes were **not committed**) were separately pinned in [our original binary audit](nhsl-v1-original-dictionary-and-nunavut-zip-byte-proof-20261104.md):

| Source asset | Source ZIP length | SHA-256 |
| --- | ---: | --- |
| [Nunavut settled areas `s_nu.zip`](https://github.com/OpenDRR/national-human-settlement/releases/download/v1.0/nhsl_physical_exposure_indicators_s_nu.zip) | 73,663 B | `8da41815457b3a163de09be24691ffaf972c4b34ced69dfacabc00723275032b` |
| [Nunavut building archetypes `b_nu.zip`](https://github.com/OpenDRR/national-human-settlement/releases/download/v1.0/nhsl_physical_exposure_indicators_b_nu.zip) | 113,156 B | `c5b3e15bf1050712aba4d6b627f1a40bf616d4cfde8cf28f77967c9973ea0bdb` |

Both original ZIPs were reassembled from bounded source ranges, decompressed **in memory** using a byte-oriented DEFLATE reader, read as SQLite files with a bounded independent B-tree and record decoder, including the actual feature table data pages. No original `Sauid` values, raw rows, geospatial geometries, policy/customer identities or ZIP contents were stored in the GitHub repository. The original numeric proof below was calculated from those actual GPKG source rows, **not invented synthetic test fixtures**.

## Primary original cross-layer findings

The original **polygon table** `nhsl_physical_exposure_indicators_s_nu` has 103 settled-area features. The original **archetype table** `nhsl_physical_exposure_indicators_b_nu` has 2,087 archetype features, grouped into exactly 103 distinct `Sauid` groups.

- **103/103 polygon SAUIDs matched** to at least one building-archetype row.
- **0** polygon groups without an archetype group and **0** archetype SAUID groups lacking a polygon.
- **All seven comparable stock/value variables** agree per SAUID at a 0.02 CAD value tolerance and 0.000001 building/ft² count/area tolerance.
- **0/103 SAUIDs** exceeded the tolerance for **any** of these seven variables. This covers 103 independent *groups*, not individual roof geolocations.

| Original field pair, polygon ↔ archetype | Polygon aggregate over Nunavut | Archetype aggregate over Nunavut | Max absolute SAUID discrepancy |
| --- | ---: | ---: | ---: |
| `Et_BldgNum` ↔ `E_BldgNum` | 6,307 estimated buildings | 6,307 | 0 |
| `Et_BldgArea` ↔ `E_BldgArea` | 32,616,779 ft² | 32,616,779 ft² | 0 |
| `Et_StrValue` ↔ `E_StrValue` | ~1,413,830,627.38 CAD | ~1,413,830,627.38 CAD | 0.000001001 CAD |
| `Et_NStrValue` ↔ `E_NStrValue` | ~4,558,687,374.28 CAD | ~4,558,687,374.28 CAD | 0.000001014 CAD |
| `Et_BldgValue` ↔ `E_BldgValue` | ~5,972,518,001.67 CAD | ~5,972,518,001.67 CAD | 0.000001014 CAD |
| `Et_ContValue` ↔ `E_ContValue` | 1,058,566,591 CAD | 1,058,566,591 CAD | 0 |
| `Et_AssetValue` ↔ `E_AssetValue` | ~7,031,084,592.67 CAD | ~7,031,084,592.67 CAD | 0.000001014 CAD |

The tiny residuals are from SQLite binary floating-point representation and summation ordering; they are not observed differences in roof locations or policy cover. The exact source field values may have sub-cent precision; **the tolerance is a QC test threshold, not permission to round/modify the original records**.

**Provenance qualification:** The original run used an independent in-memory SQLite binary-table reader during research. The *new Python executable* below has passed/will be checked under repository CI on fully **synthetic** fixtures; this research run has **not yet claimed** that exact Python implementation ran on the original provider ZIPs. The original binary reader walked the SQLite table records; a separate native SQLite `PRAGMA integrity_check` for the provider ZIPs remains to be independently recorded.

## Python native-SQLite reproduction (source ZIPs never enter Git)

New [`scripts/nhsl_v1_original_sauid_reconcile_v0.py`](../../scripts/nhsl_v1_original_sauid_reconcile_v0.py) uses our [pinned release binary preflight](../../scripts/nhsl_v1_original_binary_preflight_v0.py) to require original provider byte lengths, exact SHA-256, ZIP CRC/member IDs and native read-only SQLite `integrity_check`. It then groups the actual archetype fields `E_*` by `Sauid` and compares each of seven fields to the corresponding polygon `Et_*` at the same `Sauid`, with explicit mismatch counts, group completeness and residuals. Its JSON receipt **never includes individual SAUID IDs, locations or source rows**, and `admission_status` stays `not_admitted` even when all values reconcile.

```bash
# Download only from the two official original v1.0 release URLs outside Git,
# e.g. to /tmp using curl --fail --location --max-filesize 1000000.
python scripts/nhsl_v1_original_sauid_reconcile_v0.py \
  --polygon-zip /tmp/nhsl_physical_exposure_indicators_s_nu.zip \
  --archetype-zip /tmp/nhsl_physical_exposure_indicators_b_nu.zip

python -m unittest discover -s tests \
  -p 'test_nhsl_v1_original_sauid_reconcile_v0.py' -v
```

Tests include invented multi-archetype group matching, deliberate 0.04 CAD mismatch, count mismatches, orphan/duplicate SAUIDs, swapped assignments, NULL/NaN/negative/text values, and empty inputs. The script **fails closed** on original byte identity failure or reconciliation errors; for a real conservation mismatch it emits a JSON failure receipt and exits nonzero.

## Why this matters for OpenCatastrophe / NextGen

This establishes a dependable **aggregate-preserving exposure taxonomy**: we can move among NHSL's settlement-area inventory and its *distribution of building archetypes* without unintentionally creating/destroying replacement-cost totals. The archetype classes can later be joined to documented earthquake/flood vulnerability functions, whereas the settlement-area polygons can be used for uncertainty-aware hazard support. The original source defines `BldgLon`/`BldgLat` as settled-area centroids, **not individual address/risk locations**. Estimated replacement values in **2019 CAD** are **not insured BuildingTIV or ContentsTIV**.

**Still missing before portfolio/model use:** (1) original native SQLite provider-file integrity check with CLI receipt, (2) centroid-versus-polygon geometry uncertainty assessment, (3) vulnerability/engineering-taxonomy mappings with references, (4) scenario-specific **synthetic insurance terms and insuring fraction** with an explicit methodology, (5) an original-licence/third-party and modeling-fitness review. Do not move this candidate's model-admission flag or infer actual insurer policy cover from the above consistency results.


## Trusted-main replay of exact provider bytes

A narrowly scoped [GitHub Actions original-source proof](../../.github/workflows/nhsl-nunavut-original-sauid-conservation.yml) follows the existing repository's reviewed-main download pattern. PR review runs **only synthetic unit tests**, without original provider egress. **On the first reviewed merge to `main`** changing the workflow itself (or a later manual `workflow_dispatch` on main), it:

1. Uses SHA-pinned read-only GitHub Actions and Python setup, and stores downloaded original ZIPs only in the runner's temporary directory with cleanup.
2. Downloads **only the exact two fixed original provider v1.0 Nunavut archive URLs** (no user-selectable URL/ref/source), subject to a 1 MB per-file and 90-second per-request cap.
3. Calls the new Python validator, which independently checks **exact SHA-256, ZIP metadata/CRC, native `PRAGMA integrity_check` and seven cross-layer quantities**, all with a no-go admission receipt.
4. **Fails closed** if any actual source value, SAUID count, grouping, ZIP identity or scientific tolerance changes; prints *only aggregate* values and exact source hashes, no GPKG/CSV/SAUID/site rows or source artifacts. `contents: read`, checkout credentials not persisted.

The **original native SQLite run is not yet confirmed here**. CI success on PR-head is *not* equivalent to a successful trusted-main original-source run: after merging, inspect the exact GitHub Actions workflow result and retain the run URL/log-reported receipt before claiming native SQLite source proof. A source-side 403/429, zip drift or 0.02-CAD mismatch is a scientific/access blocker to report, **not** a reason to weaken the gate.
