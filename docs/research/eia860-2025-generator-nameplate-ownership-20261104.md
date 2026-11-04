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

**Original source has now been fetched, hashed and its actual generator MW / S-J-W counts examined in GitHub CI.** The independent live source job #41907253424 succeeded with 11 synthetic regressions and read the same pinned full annual 2025 ZIP. An independent first raw-source run #41907035951 also passed and reported matching totals. The findings below are actual source observations, not synthetic calculations. A later source-code/doc change still requires exact-head repository CI before merging.

## Next model steps once the original source is verified

Resolve ownership S/J/W against true respondent EIA reporting operator ID and Schedule 4 exception records; reject retired generators as current operable exposures. With original equipment capacity, prime mover, technology and vintage, estimate **scenario-dependent** replacement-cost ranges using independently sourced equipment and civil works unit costs. Then resolve GEM facility/unit legal and commercial source rights, physical coordinates and building/asset aggregation. Only with independent named-carrier premium/exposure regional and product-line disclosures could one synthesize actual **hypothesized** insurance allocation, never a factual insurer portfolio. Original `Nameplate Capacity (MW)` alone establishes no gross or net catastrophe claims, outward treaties or OEP/AEP curves.

Maintain [issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251) open for original GEM, legal company attribution and physical exposure gates.

## Direct 2025 EIA original-source audit: reproducible results

Source receipts: [original-capacity job #41907035951](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41907035951), followed by [exact source rerun #41907253424](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41907253424) after separating MW by EIA status and prime mover. Both read the original 23,622,347-byte official annual 2025 ZIP. Nested source SHA: Generator `931e1ed0be2c6706794c196f158f779b5c8a32d08c61d748a823dfc25a3201a8`; Owner `f0600c57b24f065017983e50a8a6561c8aa563382bb8862ad216448ca32d9383`.

The cohort is **15 exact source-recorded Delaware plant codes from three previously sampled FRS cities, *not* a complete census of Delaware generators or insurers**.

| EIA 2025 status/sheet | Unique generator keys | Original nameplate sum (MW) | Scientific interpretation |
| --- | ---: | ---: | --- |
| Operable / `OP` | **26** | **2,344.4** | Reported in operation in 2025; **not** proven active or insured in 2026 |
| Operable / `SB` | **4** | **83.7** | Standby equipment; not equal to normal business-interruption exposure |
| Operable subtotal | **30** | **2,428.1** | OP + SB; avoid counting SB as always-operating |
| Proposed | **0** | **0.0** | No generators in this cohort's 2025 proposed sheet |
| Retired and Canceled / `RE` | **5** | **152.0** | **Not current operable equipment**; 2025 retired inventory is non-exhaustive |
| 2025 native source total | **35** | **2,580.1** | **Historical mixture**; do **not** call this current insurable portfolio capacity |

| Native prime mover family in `Operable` sheet | Generator keys | EIA original nameplate MW |
| --- | ---: | ---: |
| Combined-cycle combustion turbine part (`CT`) | 8 | 981.2 |
| Steam turbine (`ST`) | 3 | 697.8 |
| Combined-cycle steam part (`CA`) | 4 | 546.0 |
| Combustion/gas turbine (`GT`) | 6 | 178.8 |
| Photovoltaic (`PV`) | 7 | 20.4 |
| Fuel cell (`FC`) | 2 | 3.9 |
| **Conservation, Operable** | **30** | **2,428.1** |

The retired subset has **3 steam-turbine generator keys with 151.2 MW** and **2 photovoltaic generator keys with 0.8 MW**. No original prime mover family was unknown in this bounded cohort. **Prime mover denotes the equipment configuration, not primary fuel or all distinct buildings**: `ST` is **not automatically coal**; combined-cycle turbine and steam-part keys can belong to one larger power unit. Before any capital-cost model, the EIA `Unit Code`, integrated physical site, and actual prime energy source require additional source-level association.

| 2025 source `Ownership` code | Operable | Retired |
| --- | ---: | ---: |
| `S` – single ownership by respondent | **27** | **2** |
| `J` – jointly owned | **0** | **0** |
| `W` – entirely owned by an entity other than reporting respondent | **3** | **3** |

All **6 `W` generator keys** are independently present in the original `4___Owner_Y2025.xlsx` special-schedule evidence; **0** reported `S` generator keys have an Owner special record, and **0** `J/W` generators lack a Schedule 4 record. No missing or negative/invalid source nameplate MW, zero-capacity values, unsupported prime-mover code, missing `Ownership` code or duplicate generator key occurred in this sample.

**Very important:** `S` means *single respondent ownership under the EIA survey*, **not** a verified ultimate legal holding company and never an insurance counterparty. All quantities are source-reported **nameplate MW, not EUR or USD TIV**, not replacement value, not estimated premiums, not flood/wind/hail fragility, not event losses. The source states and sizes are for **2025**.

### What this enables, and what it does not

An admissible *synthetic* risk exercise can now stratify hypothetical plant equipment by EIA source status and prime-mover class, and separately apply documented, licensed technology-specific **cost-per-MW scenarios**, construction year, source geometry and physical aggregation with uncertainty. That is a scenario *estimate* only: without verified asset granularity and costs it cannot be called replacement-cost insurance valuation. A named carrier's portfolio composition must independently derive from its geographic/line-of-business disclosures rather than assuming any of the 11 EIA reporting utilities is insured by that carrier.

Scientific acceptance remains distinct from passing parser tests. [Issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251) stays OPEN until separate original 2026 GEM licensing and exact location/unit ID evidence, physical site geometry, dated legal parent entities/LEIs and insurer allocation priors are independently validated.
