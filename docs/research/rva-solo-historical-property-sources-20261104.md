<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V Allgemeine: solo HGB property history and synthetic CAT portfolio source register (2026-11-04)

## Why this exists

This is public issuer and third-party research for a **fictional R+V-like** portfolio, **not** discovery of R+V's actual insured buildings, sums insured, per-location coverage, actual inward or outward treaties, or catastrophe PML. Target legal entity: **R+V Allgemeine Versicherung AG**. The colloquial requests "RNV"/"ENV" are provisionally mapped to this legal entity; the issuer identity must stay explicit. Separate the R+V *group*, parent R+V Versicherung AG, R+V Direktversicherung AG before its merger, and third-party national statistics.

**Canonical machine-readable issuer numbers:** [rva_solo_hgb_property_2019_2025_v0.toml](../../research/observations/rva_solo_hgb_property_2019_2025_v0.toml). It records annual **HGB booked gross written premium (TEUR)** for the **self-written/direct insurance** Fire and Property lines: Fire, Connected Household Contents, Connected Buildings, Other Property, and exact issuer report or later report comparative provenance for every year **2019–2025**. It also reports whole-company direct, accepted reinsurance and total premiums, whose small printed rounding differences are preserved. Not customer data. Unit conversion: 1,000 TEUR = EUR 1 million. Reproduce checks:

    python -m unittest discover -s tests -p 'test_rva_solo_hgb_property_history_v0.py' -v

## Original annual reports: issuer links and coverage

These entries are original primary documents at the publisher, not downloaded PDF copies. 2019–2025 figures in the canonical source were checked against their cited current/prior report tables; 2017/2018 are **indexed sources awaiting tabular extraction**.

| Report year | Direct original issuer HGB source | Extraction state |
| --- | --- | --- |
| 2025 | [R+V Allgemeine 2025 HGB](https://www.ruv.de/dam/jcr:e0e32e31-09ff-4b0f-b693-2c6c9bee9bb5/01_GB%202025_R+V%20Allgemeine%20Versicherung%20AG_final.pdf) | 2025 row typed; 2024 comparison checked |
| 2024 | [R+V Allgemeine 2024 HGB](https://www.ruv.de/dam/jcr:71a5e2d0-4f86-4e5f-a716-f3f3f6aa5102/Allgemeine-2024.pdf) | 2024 row typed; 2023 comparison checked |
| 2023 | [R+V Allgemeine 2023 HGB](https://www.ruv.de/dam/jcr:781b9b4f-3574-44c3-8183-24d4dde18195/2023-allgemeine.pdf) | 2023 row typed; 2022 comparison checked |
| 2022 | [R+V Allgemeine 2022 HGB](https://www.ruv.de/dam/jcr:55c81597-b4fe-4df2-a3e0-65aedb9ba15a/2022-allgemeine.pdf) | 2022 row typed; 2021 comparative typed |
| 2021 | [R+V Allgemeine 2021 HGB](https://www.ruv.de/dam/jcr:ecf3969a-7a87-4a22-955a-81b52ac33bb9/2021-allgemeine.pdf) | original located; comparative covered by 2022 |
| 2020 | [R+V Allgemeine 2020 HGB](https://www.ruv.de/dam/jcr:3119d518-15fc-4926-a1b7-9f748af99a85/2020-allgemeine-pdf) | 2020 row typed; 2019 comparative typed |
| 2019 | [R+V Allgemeine 2019 HGB](https://www.ruv.de/dam/jcr:a8ab37fe-ce34-4ff7-9062-489ea252cdb7/2019-geschaeftsbericht-allgemeine.pdf) | original located; comparative covered by 2020 |
| 2018 | [R+V Allgemeine 2018 HGB](https://www.ruv.de/dam/jcr:f0db63f2-2299-4629-a4df-d189096f54d0/2018-geschaeftsbericht-allgemeine.pdf) | source indexed; no observation typed yet |
| 2017 | [R+V Allgemeine 2017 HGB](https://www.ruv.de/dam/jcr:f6a9965e-140f-49fa-b2d2-ae30af1c5c77/2017-ruv-allgemeine-geschaeftsbericht.pdf) | source indexed; no observation typed yet |
| 2004–2016 | [Publisher historical HGB archive](https://www.ruv.de/ueber-uns/unternehmen/geschaeftsberichte/archiv-geschaeftsberichte) | Archive available; year/entity specific source table extraction pending |

Separate but essential: [R+V SFCR and QRT archive](https://www.ruv.de/ueber-uns/unternehmen/geschaeftsberichte/archiv-sfcr-und-qrt), [SFCR 2025 solo](https://www.ruv.de/dam/jcr:9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf), [SFCR 2024 solo](https://www.ruv.de/dam/jcr:18372fd4-b07e-4c29-b83b-c01e08a30ac7/2024-SFCR-Allgemeine.pdf), [SFCR 2023 solo](https://www.ruv.de/dam/jcr:2b110fa6-0ae0-49f9-899c-1541227c99a6/2023-SFCR-Allgemeine.pdf); [R+V latest annual-report collection](https://www.ruv.de/ueber-uns/unternehmen/geschaeftsberichte). The repository's earlier canonical SFCR 2025 receipt is at [rva_solo_2025_public_sfcr_v0.toml](../../research/observations/rva_solo_2025_public_sfcr_v0.toml).

## Quantitative scope and newly useful exposure constraints

* The HGB **self-written** 2025 Fire and Property total is **EUR 2,125.473m**, composed of Fire **EUR 305.990m**, Connected Household Contents **EUR 164.585m**, Connected Buildings **EUR 997.710m** and Other Property **EUR 657.188m**. Technical insurance is an important sub-segment of Other Property (reported circa **EUR 315.3m**). These are **premiums**, not TIV. The separate 2025 **Solvency II** Fire and Other Property reported premium is **EUR 2,223.182m**: it is **not** the same HGB direct-sales subline, and a formal accounting reconciliation has **not** been established. Do not force the two measures to agree.
* The 2025 HGB describes approximately **1.1 million contracts** in Connected Buildings, falling circa **1.2%** despite premium growth (attributable in part to repricing). That is a valuable **contract-volume scale indicator**, **not** 1.1 million distinct building coordinates, not fully insured TIV and not all-risk flood penetration.
* The 2025 SFCR whole-company geography reports German GWP **5,932,143 TEUR**, Austria **55,540 TEUR** and Italy **4,622 TEUR**, versus whole-company reported **5,992,306 TEUR** (1 TEUR rounding). These are **all lines**: **not** geographic premiums for the property book.
* **Corporate perimeter breaks**: Condor Allgemeine Versicherung AG merged into R+V Allgemeine effective from the start of **2024**; R+V Direktversicherung AG merged into R+V Allgemeine effective from the start of **2025**. Prior-year comparisons and policy growth can reflect these scope changes. Price changes and building-cost inflation additionally decouple premium growth from actual exposure volume. Disaggregate on available disclosures rather than mechanically extrapolating premium.
* The 2025 SFCR two-storm solvency shock belongs to capital adequacy/available own funds, **not** insurer gross/net event losses, OEP/AEP, AAL, or an observed peril frequency. See [existing research bridge](rva-oasis-portfolio-bridge-v0.md).

## Further discoverable public sources, source utility and boundaries

| Source | Target field / modelling use | Status / rights and scientific limitation |
| --- | --- | --- |
| [Destatis Zensus 2022 original OpenData grid](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) | 100m / 1km / 10km public grid building-count, build-age, types; first spatial exposure *opportunity* | Publisher explicitly advertises open data with attribution; validate exact downloaded dataset license, suppression and CRS before any ingestion |
| [Destatis Zensus 2022 regional tables](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html) | Municipal/district counts, uses, tenure, dwelling types | 2022 physical universe, not R+V policies in 2025; district and grid sums must not be double-counted |
| [Destatis Zensus research microdata documentation](https://www.forschungsdatenzentrum.de/de/haushalte/zensus-2022) | Age, building and housing type, floor area, dwelling size, ownership | Controlled-access research records are NOT automatically open/reusable |
| [Deutschlandatlas open data](https://deutschlandatlas.bund.de/) | Regional household income, density, detached vs multifamily and building land prices as high-level scenario priors | Qualitative proxy only; individual insurer shares and replacement cost are unknown |
| [GDV Naturgefahrenreport data service](https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport) | German industry losses by peril, year, state/district where available | Industry != R+V. Read source terms and permissions before automated mining/redistribution |
| [GDV Elementar penetration by district](https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-elementar/versicherungsdichte-bei-elementarschadenversicherung-regional-sehr-unterschiedlich-183592) | Spatial **conditional flood cover take-up**, scenario challenge | Coverage is industry-wide; not R+V flood endorsement rate, does not imply full model-eligible insured buildings |
| [GDV ZÜRS Geo description](https://www.gdv.de/gdv/themen/klima/-zuers-geo-zonierungssystem-fuer-ueberschwemmungsrisiko-und-einschaetzung-von-umweltrisiken-11656) | Flood hazard zoning method / model interpretation | No assumption of open bulk access to proprietary address-level zones |
| [DWD Climate Data Center](https://opendata.dwd.de/climate_environment/CDC/) | Historic wind-gust observations, meteorology, event validation | Check station coverage, CRS and model reuse terms; measurements do not specify event-set frequency |
| [DWD KOSTRA 2020 original landing page and DOI](https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_KOSTRA_DWD_2020-de.html) | Rainfall-return-period regional baseline for pluvial intensity | Fixed point return values are not event footprints, spatial dependence, portfolio losses, or annual YLT |
| [R+V group 2024 press release](https://www.ruv.de/newsroom/pressemitteilungen/2025-03-31-bilanzpressekonferenz) | Group 2024 EUR 442m vs 2023 EUR 391m elementary claims context | **Group** only, not solo-cat per-peril claim or exposure; can't fit R+V Allgemeine damage functions directly |
| [R+V group 2025 press release](https://www.ruv.de/newsroom/pressemitteilungen/2026-04-13-bilanzpressekonferenz) | Group 2025 EUR 150m vs 2024 EUR 442m elementary claims context | **Group**, no attribution to solo buildings/insured loss; preserve group and year |
| [R+V cooperative financial group and channels](https://www.ruv.de/ueber-uns/unternehmen/konzernstruktur) | Distributed nationwide Volksbanken Raiffeisenbanken and direct channels as scenario market-access prior | Bank/branch distribution is not geocoded insured-risk distribution; needs regional partner business weights |
| [BaFin company entity/risk statistics](https://www.bafin.de/DE/PublikationenDaten/Statistiken/Erstversicherung/erstversicherung_node.html) | Historical solo licensed entity scope, risk counts/insurance branches, supervision cross-check | BaFin 'risks' can count policies and cover components; must match reporting population and vintage |
| [Overture Maps buildings](https://overturemaps.org/) | Synthetic physical building footprints after zoning/centroid quality checks | Open dataset license and ODbL/attribution details must be checked per release; buildings are not insured premises |
| [Copernicus Emergency Management Service](https://rapidmapping.emergency.copernicus.eu/) | Event post-disaster flood/fire footprints for historical challenge | Damage extent and detected polygons not themselves financial insurance paid claims |
| [Copernicus CEMS EFAS](https://www.efas.eu/) and [GloFAS](https://global-flood.emergency.copernicus.eu/) | Hydrological forecast/return period and transboundary validation | Forecast exceedance/river flow must not be equated to geocoded flood depth, or building flood loss |
| [BKG federal geoportal](https://www.geoportal.de/) | Administrative boundaries, settlement layers and GIS joins | Each underlying product has distinct reuse rights; do not assume whole portal open |
| [European Seismic Hazard Model ESHM20](https://www.efehr.org/) | Secondary German earthquake/hazard scenario validation | PGA hazard is not earthquake ground-up insured loss, and portfolio mix requires masonry/vulnerability classes |

The previous [German source inventory and model roadmap](rva-oasis-portfolio-bridge-v0.md) provides additional quality gates and country-peril options. This register lists **linkable source candidates**, not proof that their underlying bytes have been admitted or run.

## Reconstructing *hypotheses* without asserting a secret insurer book

Model separate latent quantities and validate only what source truly measures:

1. **Building opportunity / insured contract count:** first generate geographic census-based physical dwelling/building population. For connected-building insurance, use issuer ~1.1 million policies as an **aggregate, approximate contract calibration constraint**, allowing one policy to map to multiple buildings or vice versa; infer uncertain company share/penetration without presenting it as observed. Freeze merger-year normalisation separately. Keep commercial engineering, household contents and fire industrial separate. Never scale all 2.125bn property premium as residential TIV.
2. **Value at risk:** use independent rebuilding cost per m², building footprint/height/age and occupancy by geography, include inflation index and uncertain policy coverage limits; sample multiple competing insurer sum-insured distributions. Do **not** transform annual GWP into observed TIV.
3. **Peril insurance conditions:** basic storm/hail and optional Elementarschaden for flood are different covers. Implement a district-level flood-endorsement hypothesis, with official industry GDV reference as **external sanity challenge** when legally usable; never label it company-specific.
4. **Hazard/vulnerability:** windstorm first via documented DWD original observations and independently validated event catalogue, appropriate vulnerability curves by occupancy/age; later flood and hail with independent GUL and correlated annual year events as needed. Preserve event and stochastic period identities.
5. **Financial and statistical output:** produce Germany-compatible OED `location/account/policy`, then on same event/period/sample series native Oasis GUL -> IL -> **fictional** outward RI/net -> AAL/OEP/AEP, robust tests and deterministic receipts. Report gross and net curves with uncertainty bands across plausible alternative portfolios, avoiding invented treaty details.

## Next concrete acquisition and calibration work

* Parse historical 2017/2018 and earlier issuer reports, and dated solo **QRT S.05 and S.19** records for gross/net premium, claims development and ceded program scale, **after checking per-year reporting changes**. Extract separately and reconcile with HGB; do not mix SFCR accounting without a bridge.
* Add independently validated census grid downloads/CSV headers and admission (source license, exact data vintage, spatial constraints), then build a reproducible **synthetic** municipal exposure sampler calibrated to independently published ~1.1m connected-building contracts *as a range*. Decompose 2024–2025 merger and price drift.
* Use GDV county hazard/claims data **only after exact publisher permission**; initially isolate already open-license DWD and census sources, and build executable wind/gust to physical building damage calibration rather than equating storms' insurer aggregate loss to any single company's claim.
* Use the existing synthetic bridge as a *non-real* sensitivity harness; a source-gated published accounting dataset cannot alone authorize a Germany native Oasis production loss engine.
