<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EIA-860 annual 2025: generator nameplate MW, equipment and source ownership codes

**Evidence-labeled research only; no named insurer, replacement cost, asset TIV, building footprint, operating status in 2026, legal UBO, paid claim or CAT event loss.** This extends the [real 15-plant / 35-generator / 11-Utility-IDs source proof](eia860-2025-original-generator-utility-schema-20261104.md).

## Native source and what is actually measured

- Fixed official [EIA-860 annual 2025 detailed archive](https://www.eia.gov/electricity/data/eia860/), original ZIP SHA-256 `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba`. Inner original `3_1_Generator_Y2025.xlsx` SHA-256 `931e1ed0be2c6706794c196f158f779b5c8a32d08c61d748a823dfc25a3201a8`, `4___Owner_Y2025.xlsx` SHA-256 `f0600c57b24f065017983e50a8a6561c8aa563382bb8862ad216448ca32d9383`. The source remains in memory and is never committed or logged.
- The native worksheet's `Nameplate Capacity (MW)` is reported **rated generating capacity in MW**, not the replacement cost of a turbine, insured physical assets, one wind turbine per reporting generator, or a whole power-plant property sum insured. Solar nameplate is reported in AC; MW cannot be converted to USD without separate unit/vintage/cost and site evidence. [Official 2025 EIA annual source documentation](https://www.eia.gov/electricity/data/eia860/) and [EIA 2025 annual capacity table](https://www.eia.gov/electricity/annual/html/epa_04_04.html) explicitly distinguish capacity MW, generator counts and prime movers.
- Official [Form EIA-860 respondent instructions](https://www.reginfo.gov/public/do/DownloadDocument?objectID=126698201) give `Ownership` **S** = single ownership by respondent, **J** = joint ownership with another entity, and **W** = wholly owned by someone other than respondent. These are generator reporting codes, **not** parent-company proof, UBO, operating legal entity or insurer. The separately reported Schedule 4 `Owner` rows are keyed to (plant, generator), **not** the whole plant or insured buildings.
- The published generator workbook has **three incompatible population slices**: `Operable` (includes operational and standby units), `Proposed` (not yet operating), and `Retired and Canceled` (only the relevant recent reported subset). They cannot all be counted as insured active generator risk. The annual 2025 report is not the latest 2026 operating census.

## Bounded runnable source methodology

The [native capacity/ownership reader](../../research_runners/eia860_2025_generator_capacity_ownership_v0.py) takes only the original pinned EIA ZIP and native member hashes. Within the **15** independently EPA↔EIA-confirmed Delaware plant IDs, it aggregates by actual source tab and status:
- exact distinct `(Plant Code, Generator ID)` conservation and status `OP`, `SB`, `RE` and other recognized 2025 codes;
- `Nameplate Capacity (MW)` summed in **MW** separately for Operable, Proposed, and Retired and Canceled; decimals parsed without silent imputation, invalid values flagged, high/negative source values blocked;
- native S/J/W `Ownership` counts, explicit Schedule 4 keys and exceptions: J/W without Schedule 4, or S with special Owner row, require review and cannot be silently fixed;
- *limited exact source prime mover codes* classified into equipment categories for coarse risk prioritization; other/unrecognized codes are counted and quarantined **without printing unknown source field text**.

The code accepts **one bounded publisher HTTPS download** or local approved original ZIP, performs no web scraping at arbitrary URLs, keeps original source data in memory and emits **aggregate-only metrics**. Synthetic negative tests cover mixed ownership codes, retired vs operable status, type confusion, missing capacity, non-numeric MW, source hash rejection, and accidental source ID/name leakage. This is **not a calibration of insured replacement cost or portfolio losses**.

```bash
python -m unittest tests.test_eia860_2025_generator_capacity_ownership_v0 -v
python research_runners/eia860_2025_generator_capacity_ownership_v0.py --live
```

**Original-source run still required:** Do not claim the MW sums or actual S/J/W distribution until GitHub Action source job returns the exact original body/member hashes and the original EIA worksheet values are inspected. A scientific review flag is a **research finding to investigate**, not a reason to force original data to 100% or redefine codebook semantics.

## Next model steps once the original source is verified

Resolve ownership S/J/W against true respondent EIA reporting operator ID and Schedule 4 exception records; reject retired generators as current operable exposures. With original equipment capacity, prime mover, technology and vintage, estimate **scenario-dependent** replacement-cost ranges using independently sourced equipment and civil works unit costs. Then resolve GEM facility/unit legal and commercial source rights, physical coordinates and building/asset aggregation. Only with independent named-carrier premium/exposure regional and product-line disclosures could one synthesize actual **hypothesized** insurance allocation, never a factual insurer portfolio. Original `Nameplate Capacity (MW)` alone establishes no gross or net catastrophe claims, outward treaties or OEP/AEP curves.

Maintain [issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251) open for original GEM, legal company attribution and physical exposure gates.
