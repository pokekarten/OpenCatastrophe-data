<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Executed source findings: Storm Events and observed IBTrACS

Reviewed against repository main `b5d155e` on 2026-11-03. This integrates
previously issue-only experiments into executable repository behavior. It is
not a new source admission, acquisition entitlement or scientific validation.
External raw/derived records remain outside Git; tests contain synthetic data.

## What was missing, and what changes

| Existing repository knowledge | Additional executed evidence | Resulting change |
| --- | --- | --- |
| NOAA Storm Events is a candidate, and SPC/Storm Events share lineage | Three actual 2024 tables have per-event count contradictions; joining child tables multiplies parent records | Offline hash-bound relational auditor and regression tests; candidate note points here |
| Observed IBTrACS access documents one global NetCDF object | A distinct global CSV snapshot was downloaded and tested; longitude conventions, averaging periods and selection affect use | Candidate note expanded; CSV experiment remains separate from NetCDF contract |
| A research note claimed an admitted observed-IBTrACS manifest | The admitted STORM manifest describes synthetic tracks derived from historical IBTrACS | Existing research statement corrected; no admission widened |
| Engine demonstrations were reported in model issue comments | Numerical success, export behavior and scientific fitness are separate results | Bounded model evidence and unresolved limits linked below; no model-ready flag inferred |

Canonical source identities remain in [the landscape](../../landscape/sources.json).
The [observed IBTrACS access contract](../../access/noaa.ncei.ibtracs.v04r01.json)
is `documented_only` and specifies NetCDF, not CSV. The
[STORM admission](../../manifests/storm.ibtracs.present-climate.v4.json) is a
separate synthetic product. Neither CSV acquisition nor a successful model run
changes rights, redistribution scope or scientific admission.

## NOAA Storm Events: reproducible contradiction and join audit

Provider: [official bulk directory](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/).
The [bulk-format documentation](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/Storm-Data-Bulk-csv-Format.pdf)
defines EVENT_ID linkage, reported damage estimates, local-standard-time fields,
and measured/estimated gust/sustained wind types. Retrieval was 2026-11-03 UTC;
the following files all carry creation label `c20260728`.

| Original gzip CSV | Compressed bytes | SHA256 |
| --- | ---: | --- |
| `StormEvents_details-ftp_v1.0_d2024_c20260728.csv.gz` | 12,693,243 | `2070b83eccab041b36360ab73645b9a249c3eefc5b92b5b3fc0cbba4d9fcc09c` |
| `StormEvents_fatalities-ftp_v1.0_d2024_c20260728.csv.gz` | 13,057 | `7113ce3232c98056867cf8d144df770e9e6b140cce40dff3ef46ff805ba17fdb` |
| `StormEvents_locations-ftp_v1.0_d2024_c20260728.csv.gz` | 983,723 | `8847a6336e1af94000f7ecfb4a80c06bf0d5c1ac122fe39da5b2e379dc62c1b4` |

The [repository auditor](../../research_runners/noaa_storm_events_relational_audit_v0.py)
was rerun on these exact external files, independently of the earlier
exploratory script. Results:

- 69,801 detail rows, 41,574 location rows, 1,141 fatality rows.
- No duplicate tested keys, orphan child references or location/parent episode
  disagreement. All three compressed streams pass complete gzip/CRC iteration.
- Direct deaths: **773** in parent counts versus **772** matched child rows;
  one mismatched event. Indirect: **367** versus **369**, two mismatched events.
  Maximum absolute per-event residual is one. None was corrected automatically.
- Naive left joins to both children yield **86,556** rows, with 5,903 duplicated
  parents and maximum multiplicity **72**. Aggregate children to one record per
  EVENT_ID, or keep them separate, before any parent-level sum. This calculation
  demonstrates row duplication; it does not assert a universal loss multiplier.
- Property damage: 15,046 missing, 40,495 reported zero, 14,260 positive. Crop
  damage: 15,413 missing, 53,236 reported zero, 1,152 positive. Unknowns are never
  zero-filled. No reported damage is relabelled as insured loss.
- Thunderstorm Wind records separate 3,884 MG, 16,055 EG and one ES report.
  MG means measured gust; EG estimated gust; ES estimated sustained wind.

### Run the audit without network access

Set `STORM_EVENTS_DIR` to an external directory containing the three files.
Hashes must be pinned independently; computing them from an untrusted download
and passing them back proves only self-consistency, not provider authenticity.

```sh
python research_runners/noaa_storm_events_relational_audit_v0.py \
  --details "$STORM_EVENTS_DIR/StormEvents_details-ftp_v1.0_d2024_c20260728.csv.gz" \
  --details-sha256 2070b83eccab041b36360ab73645b9a249c3eefc5b92b5b3fc0cbba4d9fcc09c \
  --fatalities "$STORM_EVENTS_DIR/StormEvents_fatalities-ftp_v1.0_d2024_c20260728.csv.gz" \
  --fatalities-sha256 7113ce3232c98056867cf8d144df770e9e6b140cce40dff3ef46ff805ba17fdb \
  --locations "$STORM_EVENTS_DIR/StormEvents_locations-ftp_v1.0_d2024_c20260728.csv.gz" \
  --locations-sha256 8847a6336e1af94000f7ecfb4a80c06bf0d5c1ac122fe39da5b2e379dc62c1b4
```

**Expected exit: 1**, JSON `status=inconsistent`. Exit 0 means only the selected
checks agree; exit 2 means invalid identity/format/resource-bound input.
The auditor requires exact complete headers, CRC-valid gzip and independently
supplied compressed SHA256. Bounds are 30 MB compressed and 80 MB decoded per
table. It does not download anything, emit provider records, normalize dates or
coordinates, or infer rights/model readiness. Changed provider vintages require
new reviewed hashes; do not substitute a newer file for this snapshot silently.

[Synthetic regression tests](../../tests/test_noaa_storm_events_relational_audit_v0.py)
cover compensating per-event errors with equal global totals, orphan children,
duplicate keys, mismatched episodes, schema drift, byte corruption, decompression
bounds, missing/zero damage, empty parents, aggregate-only output and CLI failure.

Full acquisition receipts, earlier date/coordinate checks and the conditional
measured-gust experiment are in the
[data evidence](https://github.com/pokekarten/OpenCatastrophe-data/issues/1101#issuecomment-6598119707).
The original conditional Beta-Bernoulli diagnostic used 1,227 training and 156 test
episodes, with no shared episode IDs. Fitted probability of a selected measured
gust >=65 knots was 0.17386; test proportion 0.15385. This describes a reporting-
selected sample, not site hazard or annual catastrophe probability. Seasonality,
coverage and cross-episode dependence remain unresolved. No fatality discrepancy
was used as a model input.

## Observed IBTrACS: CSV findings must not widen NetCDF admission

The [official NOAA product page](https://www.ncei.noaa.gov/products/international-best-track-archive)
linked the separately tested `ibtracs.ALL.list.v04r01.csv`. Snapshot acquired
2026-11-02: 333,183,438 bytes, SHA256
`7a11978ceba2953754b75bcc99bf1cfc8f00046aa5054054573edc904240d820`.
[Acquisition/test evidence and code](https://github.com/pokekarten/OpenCatastrophe-data/issues/1101#issuecomment-6584210591)
record 730,416 rows, 174 columns, 13,631 storm IDs and the required units-row skip.

- 10,658 raw longitudes exceed 180 degrees east, reaching 266.9, in SP/EP.
  A declared derived view `(lon + 180) % 360 - 180` passes coordinate-domain and
  full-turn-equivalence checks. This is not evidence of physical track accuracy,
  and direct dateline polygon construction still requires review.
- WMO wind values retain different agency averaging periods. The column and
  technical documentation explicitly state there is no adjustment between them.
  US-family one-minute winds were selected for the NA experiment; measured gust,
  sustained wind and different averaging conventions are not interchangeable.
- Main/spur/provisional tracks must be distinguished. For the stated 1980–2024
  NA/main/USA_WIND>=34-knot selection, tropical-only stages give 597 SIDs;
  including subtropical stages gives 612. All-time versus synoptic-only selection
  did not change those counts in this snapshot. These are not automatically
  official named-storm totals, NA genesis counts or landfalls.
- A year-trend Poisson follow-up improved retrospective count MAE from 5.53 to
  3.51 in 2015–2024; the same test outcomes had already been inspected, so this
  is exploratory, not a fresh blind holdout or climate attribution.
- NHC/AOML HURDAT page attempts returned HTTP 403/503 on 2026-11-02.
  Cross-source annual-count reconciliation remains open. HURDAT is upstream of
  IBTrACS, so a later match would test extraction/definitions, not independent
  physical truth. The access failures are historical observations, not a claim
  that the provider is permanently unavailable.

[Trend, selection and failed-access evidence](https://github.com/pokekarten/OpenCatastrophe-data/issues/1101#issuecomment-6584338719)
contains the exact fit/evaluation splits, numerical warnings and reproduction
scripts. No CSV rights/admission inference is made from the NetCDF contract or
from repository-authored code licensing.

## Model-engine findings retained with their limits

[Median-spectrum evidence](https://github.com/pokekarten/OpenCatastrophe/issues/17#issuecomment-6583947636)
records an OpenQuake 3.26.2 derived **one-sampled-branch** numerical experiment:
40 -> 80 -> 160 intensity levels reduce maximum weight-sum deviation from
1.2953% -> 0.4482% -> 0.1254%, without changing the engine's 1% sanity tolerance.
The 160-level job completes, but this is not the original full epistemic mixture
or a physical calibration. An independent 80-level rupture reconstruction still
misses a tight comparison in one source group; numerical completion is not exact
cross-output reconciliation.

Raw HDF5 `median_spectra` has three components but four kind labels in that
installed version. Crucially, the official extractor supplies the correct three
labels and the tested CSV export succeeds. Do not repeat the stronger, unsupported
claim that the metadata mismatch blocks every export path. Raw positional
interpretation must still be checked against the exact installed version.

These are version-specific engine findings, not additions to a source admission.
A completed Oasis PiWind or OpenQuake demonstration does not validate the external
catalogue, exposure values, vulnerability calibration or insured-loss semantics.

## Boundaries and next causal work

No statement here means that all registered sources have been downloaded/tested.
The NOAA fatality contradictions, source-coverage biases and rights review remain
open. A useful next change is a version-bound resolution/quarantine rule for
mismatched EVENT_IDs and multi-year measured-gust evaluation, retaining parent
cardinality and episode-separated splits. The current auditor deliberately emits
only aggregates; no fatality demographics or narratives are added to Git.
