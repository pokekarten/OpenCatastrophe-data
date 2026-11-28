<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V-like OED research six-scenario original-source comparison (2026-11-05)

## Status and identity

**Full synthetic company allocation, not actual R+V insured locations, company distribution, exposure TIV or insurer loss experience.** All the base inputs come from source-pinned official Zensus 2022 county/age counts and separate 2025 R+V Allgemeine Versicherung AG solo national HGB controls. The cross-population association is an explicitly **fictitious** model.

- Source-authenticated official ODS Tools 5.0.8 CI successful: [GitHub Actions 42077035364](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42077035364).
- [Exact-source six-scenario OED 5.0 source artifact 13438192830](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42077035364/artifacts/13438192830), 14-day retention until 2026-11-19. ZIP archive 895,075 bytes; 26 files, no geocodes; separate license and SHA-256 receipt.
- Independent archive inspection: each scenario has 10,000 one-account/one-location **fictional** OED rows and all 4,000 county-age cells. Exact complete synthetic population conservation **1,060,546 hypothetical contracts** across 400 real AGS-2022 Kreis codes. Every coordinate field is empty. Summed cell TIV matches exported location TIV and SHA-256 receipts.
- Historical data sources: https://www.destatis.de/static/DE/zensus/gitterdaten/Regionaltabelle_Gebaeude_Wohnungen.xlsx (2022; Germany attribution licence DL-DE-BY 2.0) and original annual R+V solo issuer HGB records (2025). These do not supply actual company site or building-level insured records.

## Comparison from the **full 1,060,546-contract synthetic allocation**

This section compares the **entire hypothetical national county-age allocation in `cohort_receipt.csv`**, rather than extrapolating 10,000 losses.

| Hypothetical scenario | Pre-1950 contract allocation | Pre-1950 share | 2000+ allocation | 2000+ share | Top ten counties share | County HHI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PHYSICAL_BUILDINGS_UNIFORM_AGE_AFFINITY | 263,170 | 24.815% | 175,510 | 16.549% | 9.200% | 0.003660607 |
| HISTORIC_PRE1950_AFFINITY_1_5X | 351,196 | 33.115% | 156,121 | 14.721% | 9.153% | 0.003657619 |
| MODERN_POST2000_AFFINITY_1_5X | 243,090 | 22.921% | 243,123 | 22.924% | 9.186% | 0.003661586 |

Changing insurer-affinity assumptions affects **hypothetical building ages far more visibly than aggregate Landkreis concentration**. This matters for subsequent roof/construction-related loss vulnerability experiments, but **2022 age-band weights do not establish 2025 insurance contracts, roof materials or vulnerability**. County HHI alone cannot establish *within-county* spatial hazard concentration.

- From uniform to hypothetical pre-1950 affinity: **21,502 contracts** would need to shift between counties to reproduce the changed full county allocation: **2.0274%** of the fictional total by total variation. Biggest absolute county shift is **AGS 11000, +1,193 hypothetical contracts** (source/target share not actual).
- From uniform to hypothetical post-2000 affinity: **9,420 contracts** would shift: **0.8882%** of the fictional total. Biggest observed change within the fictional allocation is **AGS 03454, +310**.
- At Land level the pre-1950 variant shifts **Bayern 09: −6,785**, **Sachsen 14: +5,447**, **Sachsen-Anhalt 15: +3,749**, **Thüringen 16: +3,347** hypothetical contracts versus uniform. None is measured carrier distribution or empirical premium share.

## Independent **10,000-location output** TIV comparison, not full insurer TIV

All monetary figures below are **invented replacement-cost sensitivities**, in EUR, including optional stable hash-selected archetype and age multipliers. They are not obtained from premium divided by rate, not sum insured, not actual 2025 insured value.

| Source-aligned fictional geography | Flat 450k-per-building scenario | Age+archetype scenario |
| --- | ---: | ---: |
| Uniform 400-Kreis physical opportunity | 4,500,000,000 | 4,860,046,125 |
| 1.5x pre-1950 hypothetical affinity | 4,500,000,000 | 4,973,368,500 |
| 1.5x 2000+ hypothetical affinity | 4,500,000,000 | 4,891,378,500 |

**Interpretation:** geography allocation and TIV valuation create materially different severity assumptions even before peril hazard. Precisely because the synthetic location geocodes are absent, this comparison CANNOT substantiate regional CAT loss, tail risk or OEP/AEP, and the 10,000 pilot values cannot be scaled naively through nonlinear gross-to-net contracts.

## Follow-up tasks with greatest model value

1. **Spatial concentration in NRW pilot, not only Kreis shares:** link appropriately licensed, source-pinned real candidate *physical building footprints* to BKG district polygons at exact vintages. Preserve polygon identity, footprint vs building-part semantics and ODbL/other rights; don't claim selected buildings are actually R+V insured.
2. **Building form and cost assumptions**: move from invented four-class frequencies to independently documented building occupancy (EFH/MFH/mixed), surface area, floors and regional rebuilding costs, with source-specific missingness. Keep any unknowns as ranges and independently test calibration; do NOT assume Overture height/roof attributes exist everywhere.
3. **Insurer selection**: constrain only national 2025 solo totals; put separate learned/assumed regional propensity on banking agency networks and independently reported named commercial clients, with multiple plausible posterior/prior hypotheses. Avoid interpreting local cooperative banking presence as observed individual insurance.
4. **Model compatibility and financial terms**: select a source/licence-checked Germany Oasis Wind model, produce model-valid construction/occupancy/vulnerability mappings, then run common event/period/sample GUL→insured gross IL→explicit fictional RI/net OEP/AEP. The OED format CI does not establish a German peril engine.

**Research status:** OED schema/provenance gate PASS; third-party physical footprint source admission, rights, model taxonomy, geocoding and actual modeled gross/net OEP/AEP still BLOCKED.
