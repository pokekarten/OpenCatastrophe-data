<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V 53 NRW Kreis pilot: 2022 real physical buildings × 2026 reported PV-unit geography

**2026-11-05: Research-only public physical context.** This connects two distinct already reviewed and merged research source families. It is a **new spatial evidence bridge**, not an R+V Allgemeine company policy count.

## Original data sources and integrity

1. Official [Destatis Zensus 2022 Regionaltabelle Gebäude und Wohnungen](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html), publisher full original XLSX SHA-256 `82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551`. Already re-extracted and verified under merged #1326; stored only public **400 Kreis aggregates**, not original raw XLSX, with 2022 residential-use building counts, mixed-use and ten construction-age bands. Existing official 2022 NRW Kreis source count exactly **53**; their published count of buildings with living space sums to **4,042,220** (the separate 16-state original public observation reports **4,042,229**, a nine-building Cell-Key nonadditivity, not insurer coverage).
2. Verified previously under merged [#1338](https://github.com/pokekarten/OpenCatastrophe-data/pull/1338): [secondary municipal PV dataset solarzahlen-daten, 2026-10-02](https://github.com/mwhitex/solarzahlen-daten/blob/4208eeb39ce49eb2d12c60b0d7f3f51a7dacd9ef/data/photovoltaik-gemeinden-deutschland-2026-10-02.csv), sourced from Bundesnetzagentur MaStR and **subsequently transformed by solarzahlen.de**. Exact 2,258,397 bytes, Git blob SHA-1 `38d2427b792eb7418e214da18281973bcbe9f897`, full SHA-256 `32678e605fb6cc9c80e6b9dbce01b8ba2fcfc2f88fea4fcde8ddf97e1478b7dd`. Contains 10,759 Germany municipalities and exactly **396 NRW municipality IDs**.
3. Original [OpenGeodata NRW rooftop PV technical potential Excel](https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/photovoltaik/) March 2026, original 1,506,519 bytes and full SHA `a9730f844159781c0747a4eb816f88382924239d0cc1874ea69d7a70ce912071`, all 396 NRW municipality IDs verified. Its potential 84.309 GW is not the same statistic as 2026 installed all-type PV capacity **15.865 GWp**.

The two geographical products were **not drawn on the same date**. The county bridge uses the 8-digit municipal AGS **first five digits** to match the source 2022 Kreis `_RS` code. It must fail on an unknown/new Kreis, municipality not in the original official 396 code set, wrong original file hash, duplicate, incomplete county coverage, unexpected publication date, source time mismatch falsely attributed to same year, unexplained Cell-Key age residual above bound or any missing category. No individual PV operator, site address, municipal row or insured company position is loaded into persistent data here.

## What the read-only source run produces

- **53** public Kreis rows: 2022 physical buildings with residential use, 2022 narrow residential/mixed-use counts, sums of published pre-1950 and post-1999 building construction-era cells (construction year ≠ roof renewal/vulnerability), and 2026 registered **PV generating-unit counts** by plant class (building, balcony, ground, other) plus overall installed PV nameplate kWp from the secondary MaStR-derived dataset.
- Fixed original nationwide company **2025** legal-entity controls from merged R+V observations: **1,060,546** residential connected-building insurance *contracts* and **997,710 TEUR booked gross premium**. These are NOT allocated here; real R+V county shares, insured building locations, PV endorsement take-up/amounts, claim histories, actual treaty participation and 2025 regional TIV remain unknown.
- An **ecological density indicator**: 2026 registered *building PV generating units* per 1,000 public **2022** buildings with living space. **Not** percentage of rooftops equipped, since source populations have different vintages and multiple PV generating units may be registered per roof; it cannot directly determine company insurance penetration. A company-free structural rural/urban/hail exposure prior may later use it only as explicitly uncertain sensitivity.

All original data source attribution, DL-DE/BY2.0 rights for the Zensus and secondary MaStR-derived database and CC/DL-DE Zero NRW technical potential, must accompany any downstream use. Raw 2.3MB secondary CSV and original XLSX not committed. Per-Kreis rows are public official / source-derived **aggregate** statistics, not personal data or proprietary insurer values.

## Live original-source receipt and 53 public county observations

The exact-head [original-source GitHub workflow in PR #1340](https://github.com/pokekarten/OpenCatastrophe-data/pull/1340) has **passed its live 11-test synthetic gate and 53-Kreis source crosswalk** after a bounded source network retry (a first attempt had an upstream read timeout, not an invalid data source). The parsed source uses the already-verified exact governmental Zensus 2022 county files and original date-pinned MaStR-derived CSV, and obtains the following source totals:

| Verified NRW public county-data aggregate | Total |
| --- | ---: |
| Official Zensus Kreis keys | **53 / 53** |
| Original 2026 registry municipality rows matched to those Kreis codes | **396 / 396** |
| Public 2022 `Gebäude mit Wohnraum` county total | **4,042,220** |
| Secondary 2026 active registered PV generating units | **1,180,822** |
| Of these, registered building PV generating units | **876,684** |
| Reported balcony PV generating units | **302,851** |
| Other and ground-mounted PV generating units | **28 and 1,259** |

A complete **53-Kreis public source research table** is checked into [`rva_nrw_53_kreis_census2022_pv2026_source_bridge_v0.toml`](../../research/observations/rva_nrw_53_kreis_census2022_pv2026_source_bridge_v0.toml), containing only county-level aggregate measures and identifiers (5 digits), building counts by major class, the original pre-1950 and from-2000-plus *building age* counts, and year-differing registered PV unit/overall kWp context. It contains **no original municipality identifier row, no unit operator, individual roof, insurance contracts, insured sum or insurer location data**.

The source runner independently recomputes all 53 rows from the pinned source inputs on each run, compares the whole county table against the stored source dataset and fails if an underlying publication changes. Checks guard false claims that the **secondary transformed MaStR file is a primary official Bundesnetzagentur XML** or that the county ratio means insurance exposure. A 'building PV units per 1,000 buildings' indicator is explicitly labelled *ecological, source-vintage-mismatched*, and NOT fraction of insured roofs, percent actually equipped, or a R+V tariff/location variable.

The original source workbook's national 2022 county sum nonadditivity is published by Destatis Cell-Key; these 53 county source rows sum to **4,042,220** compared with published 16-Länder state-level **4,042,229**, retained as a reported difference of nine, not data loss. The ten published building-age class cells per Kreis can differ by up to 20 from the county total; they are not force-normalized.

**No CAT hazard, PV fragility, RI terms, insured PV contract shares or OEP/AEP calculations are provided by these sources.** A separate fictional country-wide R+V insurer layer must preserve published 2025 national contracts and premiums and vary county PV/roof uptake assumptions independently; a back-inferred true local R+V policy count from this source would be scientifically false.

## Source and model gate

Current status until successful PR run: `NEEDS_ORIGINAL_SOURCE_RUN`. In `research_runners/rva_nrw_53kreis_pv_zensus_physical_source_bridge_v0.py`, an exact-head read-only GitHub Actions workflow downloads the two pinned PV source bytes, uses the canonical 400-Kreis official Zensus research datasets already merged, checks 396-to-53 AGS conservation and source totals, and may emit only county-level public aggregates. Offline tests validate age/source/status invariants.

After successful source and license checks, the next controlled integration should be **three distinct hypothetical R+V 2025 insurer policy weights** (published building-stock, age/ownership sensitivities, and optionally PV risk-factor sensitivity), preserving exact issuer aggregate count and premium **without asserting any actual insurer PV installation or real geographical insurance market share**. Only after valid German hail/wind catalogue, actual building fragility, policy PV extension assumptions, fictional TIV and RI may native GUL/IL/RI/OEP/AEP be calculated. None is produced here.

The source count and original 2022 county buildings are real published statistics; every 2025 company county policy is unobserved.
