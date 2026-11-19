<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Exact European wind/flood paired-event original byte proof (2026-11-03)

**Scope:** source-specific, bounded, read-only original public-data proof; **not** scientific/commercial admission or a catastrophe loss run.

## Original source identity

- Publisher: Claassen & Koks, European Multi-Hazard Dataset in Sparse Array Format (2026), https://zenodo.org/records/22080546
- Registered source candidate: nl.vu.european-multihazard-sparse-events.v1 (merged in PR #1152)
- Fixed original download: https://zenodo.org/api/records/22080546/files/fl_ws.csv/content
- Original file fl_ws.csv, precisely **801,138 bytes**
- Original Zenodo publisher MD5: **4b88bee853013fa40095b555620f0852**
- Independently recomputed SHA-256: **087a0db2f6cfde6e952f5944040019ec32f956297487b1f6e429f91c82b6225f**
- File read transiently by the GitHub Actions runner in memory only; no source rows committed, persisted to Neon, or emitted in logs.

## Reproducible original provider execution

- Successful exact workflow run: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41615098737
- CI workflow: .github/workflows/zenodo-eu-wind-flood-pairs.yml
- Runner: scripts/zenodo_eu_wind_flood_pairs_preflight_v0.py --fetch
- Regression command: python -m unittest tests.test_zenodo_eu_wind_flood_pairs_preflight_v0 -v
- **15 synthetic tests passed.** An initial direct provider request gave HTTP 406 with a narrow Accept header. A normal Accept */* solved the transport issue without reducing fixed byte size, original MD5, or strict original URL verification.

Original verified aggregate receipt:

| Evidence | Value |
| --- | ---: |
| Unique event-pair rows | **2,794** |
| Wind-flood cross-peril rows | **1,351** |
| Flood-flood within-peril rows | **1,360** |
| Wind-wind within-peril rows | **83** |
| Distinct referenced wind IDs | **231** |
| Distinct referenced flood IDs | **1,318** |
| Pair rows with no overlapping calendar interval | **0** |
| Pair rows with no overlapping event bounding boxes | **0** |
| Earliest source event start | **2014-12-29** |
| Latest source event end | **2025-01-06** |

**Scientific discovery:** Although named fl_ws.csv, this published file includes substantial **same-peril** event pairing. Treating all 2,794 rows as wind-flood events would overstate the cross-peril count by more than 100 percent. Never convert pair-row totals directly into annual event rates, event dependence parameters, insured claims or CAT XL payouts.

## Scientific and rights boundaries

- Publisher events preserve source IDs, start/end dates, event rectangles, *Mean wind speed (m/s)* and *Mean flood depth (cm)*. Mean wind speed is not maximum gust. The unit cm is not metres.
- Original source event time windows cross the nominal 2015-2024 coverage boundary. Preserve event IDs and actual 2014-2025 boundary dates; do not assign annual insurance losses without year semantics.
- Bounding-box overlap is **not** proof of overlapping hazard pixels, building exposure, physical causal interaction, or financial dependence. The six-gigabyte sparse NetCDF ZIP was not acquired or examined.
- The package derives its hazard layers from already known C3S wind, JRC flood depth, EFFIS burned areas, ERA5-Land heat and related sources; this derived data is not an independent holdout against its own input layers.
- Zenodo record access and its CC BY 4.0 field do not establish that all upstream rights allow commercial reuse, model calibration, or redistribution. Scientific review and model admission remain blocked.

## Next causal steps

1. Verify and crosswalk publisher event IDs with hazardinfows.csv and hazardinfofl.csv; preserve many-to-many relationships and original hashes.
2. Define a typed event-relation research consumer that links time-window and hazard IDs but cannot generate claims, loss correlation, AEP or OEP directly.
3. For a bounded licensed subset, test exact overlapping NetCDF **pixels** rather than event envelopes, then compare to independently sourced post-event observations.
4. Only after rights/science review, design a separate consumer for annual event clustering, reinsurance CAT-XL evaluation, and Oasis-compatible model input without overwriting source identities.

**Decision:** exact source-byte technical verification passed for the 801,138-byte original CSV. Commercial rights, scientific sufficiency, original NetCDF acquisition and operational CAT model admission **remain blocked**.
