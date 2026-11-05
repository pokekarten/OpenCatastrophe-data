<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Exact original CLIMK–WINDS v2 ERA5 → OasisLMF 2.5.8 run receipt

**Observed 5 November 2026.** Original provider scientific weather data
were obtained during an isolated GitHub Actions job, verified against
the existing repository's pinned byte identity and converted into
a new native Oasis hazard footprint. This is a **real data → native
footprint converter** proof, NOT a fully run CAT model.

## Actual independent source

- Original [Zenodo v2 record 15305753](https://zenodo.org/records/15305753)
  by Flynn et al., CC BY 4.0, acknowledged as **CLIMK-WINDS ERA5** and
  explicitly **not the synthetic Copernicus WISC event set**.
- Exact filename:
  `ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc`
- Original byte count: **6,792,278**.
- Publisher MD5: `887ae3218793c599862f115876c145f9`.
- Source byte SHA-256 independently re-verified in run:
  `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.
- Observed original storm label: **KYRILL**, date label
  `20070118`. The label is preserved as source-provided text,
  not silently interpreted as a complete source-year probability measure.
- Event: `storm_index_zero_based=0`, `local_experiment_event_id=1`.
- Native source grid: **181 × 269** latitude–longitude samples,
  physical gust measure `absolute_maxwindgusts`, units `m s**-1`.
- Original 2 × 3 tile: grid rows `90:92`, columns `130:133`,
  **6 valid, 0 unknown** weather cells. Tile was selected by native
  grid indices, **not claimed to be German insurer geography**.

## Independently observed GitHub workflow proof

[Successful original-source-and-native-Oasis workflow #42110693641](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42110693641),
job `127537140823`, branch commit
`b063ce09992067c3bbca318569754d717aa37d2f`.

The exact job completed every phase:
(1) install pinned `netCDF4==1.7.3` and `oasislmf==2.5.8`;
(2) **10/10 independent fictional unit tests PASS**;
(3) fetch exact original Zenodo scientific NetCDF and verify original
size/MD5/SHA-256; (4) parse original event index 0 and export four
bounded Oasis hazard CSVs; (5) accept `footprint.csv` with native
`csvtobin footprint -m 9` and produce nonempty
`footprint.bin` and `footprint.idx`;
(6) verify every output CSV checksum and size in the final job summary.

| Derived CSV output | Bytes | SHA-256 |
| --- | ---: | --- |
| `events.csv` | 11 | `8336d8801f75d65bbb33de833eeca48f8079e90ed50accde75b6641ad81e3486` |
| `footprint.csv` | 135 | `43c0585e8b9d528f46e5189f8b59ccc827aee0441631fba4a69837444cc6c96f` |
| `intensity_bin_dict.csv` | 174 | `a254ca8005a858954a22eb6facd8de48b5021a1a6cfdb09139eede7acb508d1b` |
| `areaperil_dict.csv` | 197 | `796d86b94f9a30f9b6436af0a72618f262eb2b61db8a17d6a8890db95c4d839a` |

These digests were obtained from the actual successful job receipt,
not guessed from synthetic tests. Provider original weather file,
windfield values and generated NetCDF-derived outputs remain
**outside Git**; only research code, documentation and
source-identity receipts are committed.

The earlier same-PR workflow #42110527337 failed to start the
new CLI because direct invocation did not resolve repository-root
imports. Commit `b063ce0` corrected the script's root search path;
the successful subsequent workflow proves that correction and
original source conversion, without relaxing provider hash checks.

## Explicit scientific and financial limits

- CLIMK's 50 **selected extreme** ERA5 storms are a **biased
  conditioned sample**, not a full independently weighted stochastic
  year catalogue, and not 50 annual observations of a real carrier.
- No frequency inference, source period universe, event clustering,
  independent physical-event matching across CLIMK's other
  weather models, complete hazard coverage or damage
  calibration is proved.
- `footprint.bin` is a **single conditional hazard event**.
  It is not a complete Oasis GUL/IL/RI simulation, a complete
  spatial areaperil lookup, an OED synthetic insured portfolio,
  an approved vulnerability model, a company gross/net
  OEP/AEP curve or a Solvency II capital result.
- The source's CC BY 4.0 licence and scientific citation are
  preserved. No license admission for other WISC/C3S datasets
  or unrelated vulnerability curves is inferred.
- Next engineering step: separately choose an **explicitly
  geolocated fictional building** whose support overlaps a
  verified original storm grid cell, use audited
  building-specific wind vulnerability, produce a complete
  single-scenario Oasis GUL, and only afterwards construct
  verified sample-year/loss financial curves with the proper
  source-year measure.

For the separate credential-gated **synthetic WISC**
original archive, retain
[issue #1391](https://github.com/pokekarten/OpenCatastrophe-data/issues/1391)
and the merged
[WISC native hazard adapter #1388](https://github.com/pokekarten/OpenCatastrophe-data/pull/1388).
