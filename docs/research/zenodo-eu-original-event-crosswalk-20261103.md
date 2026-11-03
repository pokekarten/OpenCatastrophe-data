<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# European original hazard ID crosswalk — bounded three-file proof (2026-11-03)

**Scope:** technical validation only; no model/scientific/rights admission, and no insurance claims or financial loss calculation.

Published source: Claassen & Koks, European Multi-Hazard Dataset in Sparse Array Format (2026), https://zenodo.org/records/22080546. Earlier source-discovery and paired-event technical receipts are in merged PRs #1152 and #1162.

## Original source identity and complete file hashes

| Original file | Exact original bytes | Publisher MD5 independently matched | Independently computed SHA-256 |
| --- | ---: | --- | --- |
| hazardinfows.csv | 32,210 | e58a511d83da230931b57cb9822d8841 | 35f10da966ad8b6f0bc5fd9dba904bb8251ae11a9f52fe7e10f4f6ff9e2bf787 |
| hazardinfofl.csv | 477,845 | 01ee8e21e7844e1335767bd40ea3f836 | 0d4d24baf9839b43559a7c3a3abca781ad2626ee19dbdde6d741be2f5db5a431 |
| fl_ws.csv | 801,138 | 4b88bee853013fa40095b555620f0852 | 087a0db2f6cfde6e952f5944040019ec32f956297487b1f6e429f91c82b6225f |

Verified execution: [official-source original-byte GitHub run 41639535207](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41639535207), source runner scripts/zenodo_eu_original_event_crosswalk_v0.py. Three bounded official HTTPS reads verify full byte length and original MD5, compute SHA-256, parse native event schema and compare by source event ID. Temporary original bytes are **never committed, retained as artifacts, written into the insurance database, or logged as rows**. Synthetic offline safety tests validate negative cases independently.

## Verified publisher source/crosswalk results

| Metric | Original-source observation |
| --- | ---: |
| Distinct original wind events in wind index | **234** |
| Distinct original flood events in flood index | **3,280** |
| Original paired-event rows | **2,794** |
| Cross-peril wind/flood records | **1,351** |
| Within-peril flood/flood records | **1,360** |
| Within-peril wind/wind records | **83** |
| Referenced distinct wind event IDs | **231** |
| Referenced distinct flood event IDs | **1,318** |
| Total unique referenced source IDs | **1,549** |
| Missing original event IDs in the indexes | **0** |
| Discrepant event start/end dates | **0** |
| Discrepant original event bounding boxes | **0** |
| Discrepant event intensities | **0** |
| Discrepant event units | **0** |
| Event IDs with mutually conflicting pair rows | **0** |

The non-referenced source events are **3 wind events** and **1,962 flood events**. The pair file selects a subset, and not appearing in the pair file is **not evidence** that an event did not occur, had zero hazard or had no insurance damage. Derived source event-ID coverage in this single pair file: wind **98.718%**, flood **40.183%**. Follow-up source run rechecks these exact coverage metrics.

**Meaning:** every original event referenced in the published pair index resolves to its native peril catalogue with consistent date, bounding-box and mean-intensity information. The strength of this result is technical original-event identity, not independent observational validity.

## Strict model-interpretation limits

- Original wind intensity means **Mean wind speed (m/s)**, not peak gust; flood intensity means **Mean flood depth (cm)**, not metres or policy-site inundation.
- Pair event windows and coarse bounding rectangles overlap, but this does **not** prove same-cell hazard pixels, spatial causation, building-level exposure, claim loss, insurer financial correlation or stochastic annual rates. The ~6 GB sparse NetCDF archive was not acquired.
- The pair index unexpectedly contains significant within-peril matching, so counting all 2,794 as wind/flood compound events is invalid.
- Source event windows include boundary dates **2014-12-29** and **2025-01-06** despite a primary stated 2015–2024 study scope. Preserve true event windows and do not assign annual reinsurance payments from index-year alone.
- The compound dataset is derived from upstream C3S/JRC/EFFIS/ERA5 source families already tracked in the registry; it is not an independent blind validation reference.
- Public Zenodo metadata and dataset-level CC BY 4.0 do not automatically approve commercial reuse/redistribution of each underlying source component.

## Next non-loss scientific steps

First, define an event relation contract that keeps original event IDs, provenance, time windows and hazard-specific units, with **no loss amount or independent-event simulation**. Second, use a bounded rights-reviewed sparse NetCDF sample to verify actual coincident *cells*, CRS, and grids, rather than bounding boxes. Third, compare against independently sourced post-event observations. Only after licensed and scientific validation can a separate, controlled consumer be considered for later annual event clustering, Oasis/ORD model interchange and independent reinsurance/capital-modelling consumers.

**State: source original-byte and event-ID linkage verified; scientific model use, upstream commercial rights, data ingestion, insured loss, and CAT simulation admission remain blocked.**

## Repository integration verification (2026-11-03)

This research PR must pass a **new full exact-head CI run** against current `main` after integration changes to the global validation geometry dependency (merged PRs #1183 and #1185). Earlier branch CI failure on pinned Luxembourg AGE geometry tests is **not** evidence of an error or success in this EU event-ID crosswalk. Keep the separately successful Zenodo original-source workflow as a distinct receipt, not as proof of full repository compatibility. No multi-peril model input or insurance loss is admitted by either test.
