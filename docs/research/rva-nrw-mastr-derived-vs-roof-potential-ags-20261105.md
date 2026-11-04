<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V NRW municipal PV crosswalk: distinguish actually registered units from technical rooftop potential

**Reviewed 2026-11-05. Exact two-primary-source? NO.** This experiment combines (1) the **original, SHA-pinned** public NRW photovoltaic municipal rooftop-potential Excel from the state publisher, and (2) a *third-party, publicly Git-versioned and MaStR-derived* 2026-10-02 German municipality CSV from solarzahlen.de. It **does NOT fetch, reproduce, or cryptographically verify the Bundesnetzagentur full original XML export**. Until a separate independent official MaStR XML reconciliation, this is an officially sourced *secondary municipal indicator*, not independently attested counts from the federal original.

## Exact byte/snapshot/rights and boundaries

| Role | Source and fixed identity | Rights and technical boundary |
| --- | --- | --- |
| State spatial opportunity (NRW) | [Official OpenGeodata NRW March 2026 rooftop PV XLSX](https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/photovoltaik/); 1,506,519 original bytes; SHA-256 `a9730f844159781c0747a4eb816f88382924239d0cc1874ea69d7a70ce912071`; 396 matched 8-digit municipality AGS keys | Publisher lists DL-DE/Zero-2.0; **technical rooftop opportunity** by residential, commerce, agriculture, etc., NOT already installed/insured units |
| Registered-unit source **secondary transformed** | [solarzahlen-daten municipality CSV fixed 2026-10-02](https://github.com/mwhitex/solarzahlen-daten/blob/4208eeb39ce49eb2d12c60b0d7f3f51a7dacd9ef/data/photovoltaik-gemeinden-deutschland-2026-10-02.csv) on commit `4208eeb39ce49eb2d12c60b0d7f3f51a7dacd9ef`, Git blob `38d2427b792eb7418e214da18281973bcbe9f897`. Dataset README states **10,759 German municipalities, 31 columns** and MaStR primary export `Gesamtdatenexport_20261002_26.2.zip`. | Project's [README and LICENSE](https://github.com/mwhitex/solarzahlen-daten) cite **Datenlizenz Deutschland — Namensnennung 2.0** and mandatory derived-data note, attribution: **solarzahlen.de. Quelle: Marktstammdatenregister, Bundesnetzagentur (dl-de/by-2-0), Daten geändert**. Source includes corrected historic municipalities; 2026 geography may not exactly match NRW dataset's March boundary. Its reported `gebaeudesolaranlagen` means PV generating **units by plant type**, not insured buildings, roofs or physically individual premises. |
| Federal original and source method independent check (not acquired) | [Bundesnetzagentur MaStR complete public download](https://www.marktstammdatenregister.de/MaStR/Datendownload), published daily, historical snapshots; [official data export and service guide](https://www.marktstammdatenregister.de/mastrhilfe/subpages/datenexport.html) | Current full export ~3.2 GB compressed; **not** downloaded this PR. Official documentation says some recently registered units can be unverified, duplicated or late-reported. The 2025-10-01 export schema changed. Public address/person fields must not be copied into open insurance research. Official 2025-12-31 historical snapshot may need 2026-01-01 archive plus commissioning dates/status and delayed-reporting caveat to align with insurer 2025. |

## Exactly what is tested

`research_runners/rva_nrw_mastr_derived_municipal_crosswalk_v0.py` downloads only the exact commit-pinned `raw.githubusercontent.com` CSV, with an absolute **16 MiB** cap. It computes Git's **SHA-1 blob digest including `blob NUL` metadata** and compares it with the GitHub-declared blob SHA. On Git SHA mismatch, source byte size mismatch, duplicate/invalid AGS, missing required source fields, negative / NaN / malformed counts, unexpected reported timestamp or missing municipality set, the source check **fails** and does not print any municipal data. SHA-256 of the downloaded source is separately recorded as observed evidence after the real run.

The official NRW original XLSX is downloaded with the **existing exact full-source SHA-256 / byte / worksheet-structure checks** (merged #1321, #1331). The original 396 AGS are inspected in memory from `Potenzial Leistung` under the original shared-string parser. The secondary CSV supplies its NRW municipality AGS set, also only in process memory. A strict **396-for-396 exact key-set comparison** rejects unexplained missing or surplus keys. Nothing asserts that matching AGS on two editions means identical object geography or matched individual buildings.

Source-specific GitHub workflow `.github/workflows/rva-nrw-mastr-derived-ags-crosswalk.yml` uses SHA-pinned Actions, read-only permissions and 13 synthetic error-path tests. Raw CSV, original XLSX, municipality identifiers, individual power records, operator addresses and `R+V` site identifiers are **not** committed or uploaded as Actions artifacts. The workflow prints only: verified original source byte hashes and counts, source date, NRW **statewide aggregate of public reporting categories** (in-service PV units, `gebaeudesolaranlagen`, `balkonkraftwerke`, ground-mounted, other, and **overall installed PV kWp**), the number of full AGS matches and category count-discrepancy indicators.

### Data meaning / no premature numerical ratio

- The secondary `gebaeudesolaranlagen` is a **registered unit count**, not a building count. One physical roof can have multiple PV units; a unit might not correspond to an insured house; municipality key codes are **not** actual insurer risk addresses.
- The secondary `kwp` describes **reported overall PV nameplate capacity**, not necessarily roof-only PV capacity; it may include ground PV. Thus do **not** divide it directly by the state technical rooftop potential of **84.309 GW** and call the result **roof saturation** or insured PV share.
- The NRW `Potenzial Leistung` is **modeled physical future capability**, whereas `Bestand Leistung [kW] 2025` field’s **annual year-tag semantics have not been verified**. Do **not** subtract secondary 2026 overall PV installed capacity from an incompatible technical rooftop potential or infer the 2025 insurer’s policy attachment rate.
- The secondary data are for **2026-10-02**, while NRW potential is listed **2026-03-12** and issuer solo HGB contracts are **2025-12-31**. Any 2025 insurer regional distribution remains a hypothetical hypothesis, not an estimate measured by solar capacity.

## Real original 10,759-municipality secondary CSV + official 396 NRW crosswalk result

Actual original-source read-only GitHub workflow [PR #1338](https://github.com/pokekarten/OpenCatastrophe-data/pull/1338) **succeeded** after source-specific synthetic tests. The exact secondary file as downloaded from GitHub at the pinned commit was **2,258,397 bytes**, full-source **SHA-256 `32678e605fb6cc9c80e6b9dbce01b8ba2fcfc2f88fea4fcde8ddf97e1478b7dd`**, and independently verified Git **blob SHA-1 `38d2427b792eb7418e214da18281973bcbe9f897`**. It contained 10,759 German municipalities; exactly the **same 396 8-digit AGS in NRW** as the original official statewide `Potenzial Leistung` XLSX. There were **zero missing and zero additional NRW keys** in the crosswalk. No city identifiers, municipally disaggregated PV counts, exact installation coordinates or user/owner names were printed or committed.

For the secondary **MaStR-derived snapshot 2026-10-02**, the NRW sum of publicly reported **in-operation generating units** is:

| Reported secondary category | Units, NRW 396 municipalities |
| --- | ---: |
| Gebäude-Solaranlagen | **876,684** |
| Balkonkraftwerke | **302,851** |
| Freiflächenanlagen | **1,259** |
| Sonstige PV units | **28** |
| **In Betrieb, total** | **1,180,822** |

All 396 municipal category-unit counts add to their published `einheiten_in_betrieb` row count; category non-additive municipality count **zero**. This is a real check of the **secondary file** only, not an independent raw federal original verification.

Secondary **reported all-type installed PV generator nameplate power**: **15,864,876.7 kWp (15.865 GWp)**. This is **not roof-only kWp**, and there is no installed-power-by-building-category within the narrow secondary table. The independently original-verified **NRW potential model** says **84,309,002.198 kW** technical total rooftop PV opportunity, and the source includes a separate year-labelled 2025 `Bestand` field. **No ratio** of the 15.865 GWp secondary installed all-PV value to 84.309 GW technical roof potential may be represented as actual roof saturation, penetration of rooftop units or 2025 R+V covered PV.

These aggregate observations are now independently preserved with both source IDs, original bytes, 396/396 join, **zero unpaired keys, attribution, scope and negative flags** in [typed state research receipt](../../research/observations/rva_nrw_pv_mastr_derived_20261002_original_checksum_v0.toml). Every source-run now rereads that receipt and fails on unexpected company/source identity, PV category unit sums, Git blob or full SHA-256, all-company-loss/nonadmission flag changes, or fabricated licensed model intake. The original secondary whole CSV and state XLSX raw bytes remain out of Git.

**Scientific caveats:** (i) 2026 October secondary updated registry is not March 2026 publisher roof model and not 2025 insurer contract year; (ii) any generating unit could be small balcony/freefield/multiple units per roof, and no actual insurance contract or installed insured site is identified; (iii) MaStR public self-registered units are subject to late reporting, status changes and data quality issues; (iv) secondary municipality-key harmonization is a third-party transformation, not a primary BNetzA XML audit; (v) the older original NRW technical modeled building categories cannot be assumed independent of other NRW LoD2 or rooftop-potential source families.

## Product decision table

| Question | Current supported state |
| --- | --- |
| Could there be municipality-level PV registries to stratify a fictional NRW portfolio? | **Yes, source candidate.** Exact two-source AGS pairing required and checked in workflow |
| Are 2026 registered rooftop unit counts the insurer's covered rooftop count? | **No.** |
| Is the secondary source the Bundesnetzagentur raw signed XML? | **No.** Third-party transformation; independent original follow-on required |
| Can building-category PV potential be combined as if it were installed observed roof installations? | **No.** Different physical and statistical universes |
| Do R+V 2025 policies (1,060,546 national) and annual booked gross premium (997,710 TEUR) provide actual 396 NRW municipality insurer counts? | **No.** National legal-entity controls only |
| Have catastrophe hazard/vulnerability, outward net XL treaty terms, company TIV and native OEP/AEP run been established? | **No.** All must remain blocked |

## Insurer-specific PV coverage is optional and policy-family dependent (R+V original publisher)

This source match is particularly relevant only after establishing which 2025 contracts could have covered PV equipment. We additionally verified first-party R+V **public tariff/product descriptions**:

- [Private R+V photovoltaic insurance](https://www.ruv.de/erneuerbare-energien/photovoltaikversicherung): states that residential PV equipment **up to 30 kWp** may be insured within the residential-building insurance **after disclosure and at additional premium** if installed fixed on a building or garage; insured triggers include storm, hail, fire, lightning (product-detail and wording dependent); optional loss of PV feed-in revenue is separately mentioned. **Up to 30 kWp is product eligibility, not observed insurer contracted kWp or a model policy upper bound across the entire company.** In the [residential R+V building product](https://www.ruv.de/wohngebaeudeversicherung) additional private PV cover is separately selectable for classic and comfort. Do **not** assign every MaStR `gebaeudesolaranlagen` to a covered R+V ancillary item and do not assume all large commercial solar facilities use this private 30 kWp class.
- [R+V agricultural-building offer](https://www.ruv.de/firmenkunden/landwirtschaftliche-versicherungen/agrarpolice/gebaeudeversicherung): PV/solar can be **additionally** insured on farms with individually selected perils (fire, storm/hail, elemental etc.). A registered farm PV unit ≠ a R+V Allgemeine covered stable roof or an agricultural building sum insured.
- [R+V commercial solar EnergiePolice](https://www.ruv.de/erneuerbare-energien/photovoltaikversicherung?zg=fk): a **different commercial technical-insurance product**, not automatically the residential-building policy. The public Basis/Premium price/coverage description includes storm/hail and energy loss features; quoted loss-of-income cap **up to €2.50/kWp/day** with 180/360 days according to selected variant is a product maximum, **not** observed premium, claim, actual insured downtime or typical loss.
- Balcony solar generators, especially the **302,851 NRW secondary units**, must **not** automatically be mapped into a residential **building**-cover PV endorsement. Insuring small plug-in units can involve different property/contents wording and an unobserved issuer/product distribution.

**2026 web product descriptions cannot be retroactively presumed to describe every 2025 individual policy or contract inception year.** The issuer's exact product mix, optional PV uptake rate, insured panel cost, number of covered solar units per physical roof, and PV peril limits/deductibles remain unobserved. Therefore the correct optional R+V synthetic asset pipeline needs *two distinct stochastic gates*: (i) from regional published generation-unit population to a fictional **physical building asset/PV installation** population; then (ii) from a hypothetical R+V building or commercial policy to **potentially covered PV additions** with disclosed unobserved take-up and conditions. An installed generating unit is not a residential contract.

## Follow-on original verification

1. Run the current exact-Git-blob and official NRW original crosswalk in clean read-only GitHub Actions, save only SHA, state-level counts and mismatch statistics.
2. Validate exact CSV source data dictionary / 2026 commissioning and status flags independently against [federal MaStR description of export](https://www.marktstammdatenregister.de/MaStR/Datendownload) and official **public filtered exports**; only original source byte count and rights reviewed qualify for source admission.
3. Next independent release candidate: original 2026-01-01 federal XML snapshot, privacy-safe NRW **county-level aggregate only**, no individual unit owner address. Compare 2025-12-31 insurer year separately from publication/registration lag.
4. Combine **a scenario of residential/commercial/agriculture rooftop PV auxiliary equipment per fictional building archetype** (conditional on policy coverage) with independently licensed German hail/wind hazard/vulnerability. Keep object identity, content/material and policy endorsement assumptions transparent. Maintain separate group/solo legal entity and independent 2021 loss holdout.

**Research source status remains** `SOURCE_CANDIDATE_NO_MASTR_PRIMARY_XML`; portfolio, insured TIV and model-input admission **NO-GO**.
