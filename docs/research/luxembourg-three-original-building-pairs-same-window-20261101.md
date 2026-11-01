<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg: strict three-source, single-window aggregate building comparison

Date: 2026-11-01. Scientific research only, no model source admission.

## Causal problem

The real-source ACT2023-roof / EUBUCCO pilot (#924) used a **250×250m** area and counted 149 ACT roofs / 45 EUBUCCO footprints, whereas ACT2023 roof / GeoBase2026 (#936) and GeoBase2026 / EUBUCCO (#942) used a **100×100m** area. Comparing those pair results directly to assess source completeness or a three-way identity was invalid. The entire original national source counts (238,189 / 230,353 / 186,171) likewise cannot be subtracted to infer construction or demolition.

This change runs **all three** already verified spatial matchers against the SAME fixed **100×100m** square around the same public 6.1319°E,49.6116°N centre (EPSG:3035 half-width 50m), in one ephemeral GitHub Actions original-source execution. This makes the *aggregate diagnostic sample populations* directly comparable, but not transitive building identities. The same original ACT/GeoBase publisher family and EUBUCCO's ACT2013 government source mean no independent physical ground truth is claimed.

## Pinned original inputs (no source rows in Git)

- ACT2023v2 roof original ZIP SHA256 `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a`, GPKG SHA256 `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`.
- ACT BD-L-GeoBase2026 Buildings original ZIP SHA256 `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`, GPKG SHA256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`.
- EUBUCCO v0.2 LU00 original Parquet SHA256 `d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c`.

All sources have been independently accessed via fixed publisher URLs and SHA-verified in earlier merged PRs #914, #919, #926. This workflow repeats these checks, extracts original files only inside `RUNNER_TEMP`, runs three preexisting original spatial comparisons, and removes provider bytes and three pairwise intermediate JSONs before exit. Only one aggregate count+metadata report is printed, with no original per-building identifiers, matches, coordinates or source WKB, and no persistence to Neon.

## New independent aggregate consistency test

`research_runners/luxembourg_three_pair_same_window_v0.py` requires:

1. Exact three known output schema versions, source version SHA-256s and previously observed **full national counts**.
2. The same **50m halfwidth** and canonical city research reference for all pairwise reports. The workflow's source commands use the public fixed centre defaults; the reports themselves are **not** proof of coordinate control.
3. All three independent run-level source counts must agree: 2023 roofs counted in pairs AB and AC, 2026 GeoBase polygons in AC and BC, EUBUCCO footprints in AB and BC.
4. Every left/first-source count must be conserved exactly across unique high-IoU candidate, split/merge ambiguity, weak unique and no-overlap categories.
5. Fail closed on stale/replaced original files, wrong window dimensions, duplicate JSON keys, non-finite values, negative/boolean/beyond-budget counts, missing or true model-admission flags.

Ten synthetic tests in `tests/test_luxembourg_three_source_same_window_v0.py` exercise those boundaries. No sample sensitivity precision/recall, honest one-to-one crosswalk or partial building-stock change is calculated.

## Actual three-original-pair execution

The authoritative result must come from the newly scoped special GitHub Action `.github/workflows/luxembourg-three-source-same-window.yml`. Before that hosted exact-head run succeeds, **there is no measured 100m ACT2023-versus-EUBUCCO result**. Do not substitute the prior 250m result as if it were same-window proof.

Original source lineage caveats remain:

- ACT2023 roof extent vs ACT GeoBase2026 building object vs EUBUCCO's mixed 2013 ACT/OSM/Microsoft footprints use incompatible geometry/segmentation and observation dates.
- True EPSG2169 field axis order needs independent geodetic control point; current measurements are as-stored coordinate hypothesis.
- A high pairwise IoU, or even three high IoUs, cannot prove the same physical building without a reviewed 1:1 / 1:n / n:1 adjudicated match record. The aggregate output does NOT contain the individual building relationships required to test transitivity.
- All source redistribution/commercial rights, building asset survey dates, hazard intensity, occupancy, repair/replacement value, insurer coverage and CAT model approvals remain separate proof gates.

## Executed original-source result: three pairs, same 100m window

**Verified GitHub Actions run:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41313575476 . This passed all **ten synthetic consistency/privacy regression tests**, then downloaded all three previously SHA-pinned original sources, verified exact national source byte hashes, executed all three original polygon comparison scripts in the **same** 100m square, and passed the deterministic aggregate source reconciliation. No provider record, original matched building ID, raw WKB, geometry pair, source file or individual result was published as an artifact.

| Same source population in all corresponding pairs | Actual count |
| --- | ---: |
| ACT2023 roof polygons | **55** |
| GeoBase2026 building polygons | **107** |
| EUBUCCO v0.2 footprints | **11** |

| Observed pair in same 100m window | First-source polygons | Second-source polygons | Unique candidate IoU≥0.60 | Ambiguous first-source polygons | Weak unique | No substantial overlap | Spatial bbox pairs examined |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ACT2023 ↔ EUBUCCO | 55 | 11 | **1** | **54** | 0 | 0 | 73 |
| ACT2023 ↔ GeoBase2026 | 55 | 107 | **12** | **39** | 4 | 0 | 322 |
| GeoBase2026 ↔ EUBUCCO | 107 | 11 | **1** | **104** | 0 | 2 | 139 |

Each row's first-source classification conserves its first-source polygon count. This is the first *same-area* published aggregate three-pair comparison, but it **does not prove transitivity**: the single ACT–EUBUCCO match need not involve the same EUBUCCO polygon as the single GeoBase–EUBUCCO match. Inferring one triple-match, unique building count, independent validation, new/demolished buildings, or property-level insured exposure from the table is prohibited. Most EUBUCCO data in this sample cannot simply be mapped 1:1 to the more granular 2026 polygons. Segment definitions and source vintages remain under review.

The **old 250m ACT2023/EUBUCCO result (149 vs 45)** remains a separate historical experiment and is not overwritten. The newly observed 100m ACT2023/EUBUCCO result is **55 vs 11**, with **1** high-IoU unique candidate and **54** ambiguous ACT roofs. No changes to Neon model-input admission, insurer risk values or source redistribution rights.
