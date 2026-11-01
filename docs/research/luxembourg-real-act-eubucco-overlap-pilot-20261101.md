<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg: first bounded ACT rooftop vs EUBUCCO original-building spatial diagnostic

**Date:** 2026-11-01. **Status:** research-only, no scientific match
acceptance, no external-data persistence and no insurer CAT model input.

## Original source receipts

| Provider source | Original product evidence |
| --- | --- |
| ACT2023v2 official CC0 roof-derived 2D MultiPolygon | 238,189 records, GeoPackage SHA-256 `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`, EPSG:2169, summer-2023 aerial survey |
| EUBUCCO v0.2 NUTS2 `LU00` | 186,171 records, Parquet SHA-256 `d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c`, documented EPSG:3035 |

Both original source file hashes are independently frozen from separate
successful real provider retrievals in earlier GitHub Actions. Those receipts
do not establish that the original datasets are scientifically independent or
that ODbL combined-database sharing obligations have been satisfied.

ACT's rooftop extent is **not** EUBUCCO's footprint concept; differences in
roof eaves, building segmentation, sources and dates are expected. The
existing source axis screen in merged PR #918 found ACT's **as-stored XY**
projection plausible at the aggregate country envelope scale and swapped
XY implausible. However this is **not ground-control certification**.
The bounded pilot intentionally labels as-stored as a **hypothesis** and
forbids approval of the derived matches for production use.

## Real, tightly bounded experiment

`research_runners/luxembourg_act_eubucco_bounded_overlap_v0.py` uses the
two original local, pinned files. The new
`.github/workflows/luxembourg-act-eubucco-bounded-original-overlap.yml`
fetches only those two exact official HTTPS URLs and immediately removes
the original bytes after the test. Both SHA-256 source receipts are
verified before any comparison.

- Fixed research centre: public Luxembourg city at approximately
  **6.1319°E, 49.6116°N**.
- Fixed equal-area ROI: **250 m × 250 m** (125 m half-width, EPSG:3035).
- ACT: use the official indexed GeoPackage layer
  `ACT2023v2_Buildings3d_Footprints`, true `buildingid` and
  bounded native EPSG:2169 RTree query, with the as-stored axis hypothesis.
- EUBUCCO: source Parquet `LU00`, read only `id`,
  `region_id`, and WKB `geometry`; filter to the same bounded
  EPSG:3035 area.
- Both inputs are capped at **500 polygons**, with no automatic second
  window, adaptive exploration, personal addresses, owner data, or raw
  source persistence. Abort if the window is empty/too large or if source
  data are corrupt or mutated.
- Two temporary GeoJSON FeatureCollections are created **only** in
  an auto-removed local temporary directory. The existing
  `scripts/building_footprint_overlap_v0.py` runs at illustrative
  **IoU 0.60** with a 0.20 substantial-overlap threshold. It reports
  only aggregate matches/weak matches/nonmatches and unresolved 1:n/n:1
  groups plus intersection-over-union distribution. No IDs, geometry
  coordinates, crosswalks or raw features leave the runner.
- Exact original source checks and 4 synthetic test cases
  run under pinned PyArrow 20.0.0, Shapely 2.1.2 and PyProj 3.7.2.
- The script explicitly outputs **false** for ACT ground-controlled
  source axis, original-source scientific independence, manual match
  precision/recall, model-input admission and insurer exposure import.

## What a successful run does and does not establish

If the original research window is nonempty and the original source
hashes match, a successful run establishes a **real aggregate spatial
overlap experiment**, i.e. an exploratory count of where rooftop
geometries from the two raw providers align. It does **not**
establish the number of missing buildings nationally. A roof structure
can appear as multiple polygons, EUBUCCO source boundaries can be
different ages, and thousands of EUBUCCO government-label geometries
could derive from **the same Luxembourg government input**. Thus
independence and identity remain explicitly unproven.

Next acceptance requirements:
- independent coordinate control points to verify the EPSG:2169 axis;
- review and pin `input-datasets-metadata.xlsx` EUBUCCO upstream
  Luxembourg geometry lineage/licence/survey date;
- manually label urban/rural, roof overhang, industrial and split/merge
  building samples; measure precision/recall against adjudicated truth;
- only then propose verified candidate crosswalks into an authorised
  staging/exposure schema with separate rights and scientific admission.
