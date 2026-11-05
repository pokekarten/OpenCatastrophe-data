<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original 2024 USFS FPA FOD state × size × MTBS_ID statistics (2026-11-05)

**Original ArcGIS REST grouped counts actually queried, not only a proposed source.** This is a linkage-field availability diagnostic, not a cross-agency fire join, historical hazard event feed, CAT loss calibration, or permission to publish original source bytes.

## Reproducible official source and filter semantics

The [USFS FPA FOD Seventh Edition ArcGIS service](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer) described edition **FPA_FOD_20260615**, covering 1992–2024. The [2024 layer query](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/2024/query) was read three times, using identical query parameters apart from the WHERE filter:

- groupByFieldsForStatistics = state,fire_size_class
- outStatistics = [{"statisticType":"count","onStatisticField":"fod_id","outStatisticFieldName":"n"}]
- returnGeometry = false; f = pjson
- orderByFields = state ASC,fire_size_class ASC
- resultRecordCount = 2000
- WHERE #1: fire_year = 2024
- WHERE #2: fire_year = 2024 AND mtbs_id IS NOT NULL
- WHERE #3: fire_year = 2024 AND mtbs_id IS NULL

The original response native field types were state: esriFieldTypeString; fire_size_class: esriFieldTypeString; n: esriFieldTypeBigInteger. The full original raw JSON bodies were hashed at the point of the read-only research query. They have **not** been committed to the public repository, digitally signed by the provider, or copied into versioned archival storage. The current service can be revised under the same URL. For stable archive provenance, use [USFS RDS-2013-0009.7](https://doi.org/10.2737/RDS-2013-0009.7), **not** an assumption that CurrentEdition is immutable.

| Response | Original body bytes | Distinct original state × size groups | Source event rows | Raw body SHA-256 |
| --- | ---: | ---: | ---: | --- |
| All 2024 FPA | 28,006 | 299 | 87,708 | c8d596dea8685b7ed4e363c68f857c5f3af76d8eec880a9d5db4a8b1f7275c23 |
| Non-null MTBS_ID | 6,656 | 68 | 415 | d2b9a8a6c66dfa51f5abc78ea813924d3310888df70e848407786d32a7bc8551 |
| Null MTBS_ID | 26,450 | 282 | 87,293 | b86b6cb98cca23087a6de6ee91d779592643ac9fac56f082e7341bfe7e6d1cbc |

All 299 nonempty denominator cells can be reconstructed by summing MTBS_ID-present + MTBS_ID-null for the **same state and size class**. The totals also match previously checked [independent marginal A–G aggregates](us-wildfire-size-conditioned-mtbs-linkage-20261104.md). There are **53 original FPA state/territory codes**, not 53 US states. Only 35 codes contained a non-null MTBS_ID somewhere in the 2024 FPA data.

## Quantified effect of fire-size composition

The all-size national linked ratio is 415/87,708 = **0.47%**. The size class F+G denominator is **623** reported FPA records (1,000 acres or greater) and the source-link count is **377**, or **60.51%**. That gap shows why a link-present-only sample cannot calibrate all-fire frequency.

Selected state-conditioned F+G examples from the original three provider responses (not wildfire risk rankings):

| FPA state code | All size records | Linked across all sizes | F+G records | Linked in F+G | F+G ID ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| OR | 1,748 | 57 | 86 | 57 | 66.28% |
| ID | 1,555 | 48 | 76 | 45 | 59.21% |
| CA | 8,182 | 24 | 53 | 22 | 41.51% |
| AK | 379 | 22 | 51 | 22 | 43.14% |
| AZ | 2,260 | 44 | 51 | 44 | 86.27% |
| OK | 3,010 | 33 | 44 | 33 | 75.00% |
| WY | 1,343 | 25 | 41 | 25 | 60.98% |
| WA | 1,624 | 16 | 23 | 14 | 60.87% |
| MT | 2,435 | 12 | 22 | 12 | 54.55% |
| TX | 722 | 17 | 22 | 17 | 77.27% |
| CO | 8,223 | 12 | 16 | 12 | 75.00% |
| FL | 2,322 | 15 | 15 | 9 | 60.00% |

The single anomalous MTBS_ID in NWCG class **A** is in the **CA** cohort and requires **source event ID and incident complex identity** review, not a false 0.25-acre MTBS polygon conclusion. MO has 5 class F+G FPA records, none with an MTBS_ID, but 5 linked D/E rows. Note that [MTBS official mapping thresholds](https://www.mtbs.gov/faq/fire-mapping) target **500+ acres in the eastern US and 1,000+ acres in the western US**. Accordingly, F+G-only linkage rates remain regionally affected by inclusion thresholds, reporting systems, mapped-severity imagery, and multiple-source identity; they are *not* causal effects, fire frequency, or country coverage estimates. FPA MTBS_ID merely names a potential source key and does not guarantee a matching original 2024 MTBS FIRE_ID, physical-event join, even whether the MTBS target class is wildfire vs prescribed burn.

## Offline, original-raw-body-SHA-gated check

Use exact saved private original bytes of the three ArcGIS grouped-statistics JSON responses, not copied response numbers.

    python -m research_runners.us_wildfire_2024_state_size_linkage_v0 \
      --all-statistics /private/fpa-all-state-size-2024.json \
      --all-sha256 c8d596dea8685b7ed4e363c68f857c5f3af76d8eec880a9d5db4a8b1f7275c23 \
      --linked-statistics /private/fpa-linked-state-size-2024.json \
      --linked-sha256 d2b9a8a6c66dfa51f5abc78ea813924d3310888df70e848407786d32a7bc8551 \
      --unlinked-statistics /private/fpa-null-state-size-2024.json \
      --unlinked-sha256 b86b6cb98cca23087a6de6ee91d779592643ac9fac56f082e7341bfe7e6d1cbc \
      --fpa-release FPA_FOD_20260615

    python -m unittest tests.test_us_wildfire_2024_state_size_linkage_v0 -v
    python scripts/check_all.py

The runner is **offline** and proves the **exact three-way state×size arithmetic**, original raw-response hash identity, expected native ArcGIS fields, size-class A–G marginals, all 53 original state codes, and that no grouped response declares a transfer limit. It outputs only aggregate counts and conditional descriptive ratios for states with F+G denominator at least ten. A changed A–G marginal on the mutable service is a **fail-closed review signal**, not an automatic substitute source release.

## Next scientific step

Acquire a separately archived **version-pinned FPA original source asset**, and independently reconcile source MTBS_ID to original MTBS FIRE_ID with wildfire/prescribed classes and the east/west size-thresholds. Then validate incident match multiplicity, source wildfire footprints and original rasters/CRS, before overlaying synthetic building exposure. **Nothing here approves source reuse or insurer CAT simulations.**
