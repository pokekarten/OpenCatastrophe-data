<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# US wildfire 2024: FPA FOD fire-size-conditioned MTBS_ID availability (2026-11-04)

**Research-only, observed current USFS REST service counts. No original archive download, release SHA, admission or CAT frequency/loss estimate.** This improves on the already-merged [bounded original-response audit](us-wildfire-native-arcgis-query-pair-v0.md) by testing **all reported 2024 fire-size classes** and reconciling missing ID population through three source-controlled grouped counts rather than biased selected records.

## Observed provider-original aggregate readings

The [official USFS FPA FOD Seventh Edition current service](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer) describes layer 0 as the complete point database and layer **2024** as its year-filtered view. Its *current-edition service URL may later point to a different release*. Edition as advertised when reviewed: `FPA_FOD_20260615`.

Grouped statistics from the [2024 layer query service](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/2024/query) were read with `groupByFieldsForStatistics=fire_size_class` and `outStatistics=[{"statisticType":"count","onStatisticField":"fod_id","outStatisticFieldName":"n"}]`, `returnGeometry=false`, `f=pjson`. Exactly three `where` clauses were used: `fire_year = 2024`, `fire_year = 2024 AND mtbs_id IS NOT NULL`, `fire_year = 2024 AND mtbs_id IS NULL`. The latter two together reconcile to the former **for every class**, not only globally.

| Fire size class, NWCG reported final size | All FPA 2024 | MTBS_ID non-null | MTBS_ID null |
| --- | ---: | ---: | ---: |
| A: 0–0.25 acres | 43,445 | 1 | 43,444 |
| B: >0.25–<10 acres | 34,441 | 0 | 34,441 |
| C: 10–<100 acres | 7,296 | 0 | 7,296 |
| D: 100–<300 acres | 1,263 | 6 | 1,257 |
| E: 300–<1,000 acres | 640 | 31 | 609 |
| F: 1,000–<5,000 acres | 388 | 224 | 164 |
| G: >=5,000 acres | 235 | 153 | 82 |
| **Total** | **87,708** | **415** | **87,293** |

All figures are **counts of reported FPA wildfire records**, not MTBS mapped events, burn areas, exposure units or insurer occurrences. The grouped provider response listed original `fire_size_class` as `esriFieldTypeString` and `n` as `esriFieldTypeBigInteger`. Link completeness is **0.4732% of FPA 2024 records**, but strongly varies by *reported FPA final-fire size*: F and G combined contain **623** records, **377** with MTBS IDs (~60.5%), and **246** without them. A-C combined contain **85,182 records but only one MTBS reference**, an identity-review exception. Thus an ID-present-only selection is scientifically unsuitable as an all-fire-frequency calibration sample.

The classes correspond to the [NWCG fire-size glossary](https://www.nwcg.gov/publications/pms205/nwcg-glossary-of-wildland-fire-pms-205/size-class-of-fire-723). MTBS itself generally maps reported fires >=1,000 acres in western U.S. and >=500 acres in eastern U.S. (see [original MTBS project scope](https://www.mtbs.gov/)); FPA classifications, multiagency incident records, prescribed-fire inclusion, historical satellite-image availability and geographies do not have a 1:1 event relation. **FPA missing MTBS_ID does not imply the same incident is absent from MTBS** (the linking key may be absent). The single A-class linked row must not be interpreted as a one-quarter-acre MTBS perimeter: association could involve a complex/mapping/reporting discrepancy and requires identity review. Differences in estimated acres or geometry are a separate study.

The separate [2024 MTBS boundary layer 82](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/82) returned **1,051 polygon features**, grouped as **411 Wildfire**, **638 Prescribed Fire** and **2 Other** in independent count-only / grouped statistics queries. This is a *different product population*; its totals are not conservation denominators for FPA FOD rows. The term **MTBS_ID present is not equivalent to the MTBS source `FIRE_ID` actually matched**, independently verified or model-ready.

## Reproducible offline grouped-statistics gate

After separately saving each of the three original **small aggregate JSON responses** to private files, record original bytes and SHA-256. This repo contains **no provider response bytes** and the research notes do not claim captured original HTTP headers, metadata timestamps or provider SHA receipts. Run:

```sh
python -m research_runners.us_wildfire_2024_size_linkage_stats_v0 \
  --all-statistics /private/fpa_2024_all_size_stats.json \
  --all-sha256 64_CHARACTER_LOWERCASE_SHA256 \
  --linked-statistics /private/fpa_2024_mtbs_present_size_stats.json \
  --linked-sha256 64_CHARACTER_LOWERCASE_SHA256 \
  --unlinked-statistics /private/fpa_2024_mtbs_absent_size_stats.json \
  --unlinked-sha256 64_CHARACTER_LOWERCASE_SHA256 \
  --fpa-release FPA_FOD_20260615
```

The tool parses strict ArcGIS statistics output with bounded size, typed original fields and A–G class codes. It rejects duplicate/nonfinite JSON keys, bad hashes, malformed geometry/fields, transferred group truncation, unknown classes, negative counts and *compensating cross-class inconsistencies*. It produces aggregate counts and **class-specific ratios with explicit denominators**, plus non-admission flags. Only the **first input of each class** is needed: this is a descriptive linkage-availability diagnostic, not a platform to retrieve source event IDs.

**Evidence and next steps:** The live provider counts remain unversioned observational readings until an operator freezes original response bytes together with endpoint/query, retrieval timestamp, status, headers, SHA, service version and archived `FPA_FOD_20260615` asset receipt. Required next scientific analyses: genuinely matched events by fire size and geography, coverage by MTBS mapped-area thresholds, FPA fire reporting source systems, precise event-year versions, discrepancies between incident final size and MTBS map area, and pre/post source reprocessing effects. Do not extrapolate a size-adjusted national CAT loss/frequency model from this linkage table without those gates.

## Checks

```sh
python -m unittest tests.test_us_wildfire_2024_size_linkage_stats_v0 -v
python scripts/check_all.py
```
