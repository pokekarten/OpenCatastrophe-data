<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V insurer portfolio discovery: bank catchments, agents, named public property awards, and non-obvious market priors

## Breakthrough: **primary government document directly identifies 2025 R+V Allgemeine insured corporate property books**

**Much stronger than indirect bank/agency footprint or a secondary procurement index.** Original 6-page **Berlin Senate answer, April 1, 2025, Abgeordnetenhaus Drucksache 19/22033**, [full official public document](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf), specifically **question 2 on PDF page 3**. This is a written official response based on disclosures of the six state-owned housing companies themselves, **not a statistical prediction**.

The Senate confirms as of April 1, 2025:

| Named corporate housing property account | Official building insurer relationship | Status for hypothetical R+V exposure |
| --- | --- | --- |
| **GESOBAU AG** | **R+V Allgemeine Versicherung AG** building insurance contract | Confirmed **named property account**, not building/site list |
| **WBM Wohnungsbaugesellschaft Berlin-Mitte mbH** | **R+V Allgemeine Versicherung AG** building insurance contract | Confirmed **named property account**, not site list |
| **degewo AG** | **Allianz AG + R+V Allgemeine Versicherung AG in insurer consortium** | Confirmed **shared co-insurance relationship**, **R+V allocation unknown** |
| Gewobag | ERGO and Generali | **Other insurer comparator** for the named Berlin state-owned property book |
| HOWOGE | Westfälische Provinzial Versicherung AG | **Other insurer comparator** |
| STADT UND LAND | Allianz AG | **Other insurer comparator** |

Machine-readable primary evidence with these explicit positive and negative relationship checks: [`rva_berlin_senate_housing_insurer_relations_2025_v0.toml`](../../research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml); 13 tests. Government publication identifies the **legal insurer**, corporate account and general property cover, with significantly stronger direct evidence than bank office density.

**Contract / scientific semantics, Senate questions 3 and 4:** The corporate buildings are insured **under each company's broad/master building-insurance contract**, NOT one individually sold residential house policy per dwelling. WBM's **purely commercial properties use a separate master policy**; the Senate question 2 does not establish the carrier/2025 coverage for that separate commercial contract. Across the state-owned companies the Senate reports the following insurance peril categories: **fire, tap water, wind/hail, elemental and vandalism**, **NOT** granular peril endorsements for every property or a calibrated insured peril take-up. WBM commercial insurance has higher deductibles and price indexation provisions than the residential master. We do not know WBM commercial insured-site details or 2025 solo R+V share. More generally, no R+V insurer TIV, asset-by-asset schedule, amount of coverage, claims, or coinsurance percentage for degewo is disclosed.

**Senate Q1**: Examples across *unspecified* Berlin municipal housing company portfolios put annual net premiums per **residential dwelling** under EUR 100 in 2019, above EUR 200 in 2024, with yearly variation ~1–57%. **This is not actual R+V 2025 policy premium, insured property TIV, an insurer's annual GWP, or proof of the building insured.** A company named as insurer of a large housing corporate book cannot be naively injected as tens of thousands of residential insurance contracts into the R+V Allgemeine solo **1,060,546** year-end *connected residential building* policy anchor. The source reports typical EU-wide re-tendering of corporate building master agreements every **four years**, which helps monitoring past/future awards but does not guarantee 2026 continuation.

Supporting typed source for WBM/GESOBAU/degewo 2025 stock numbers plus the Berlin government WFS metadata and **no corporate-entity GIS join**: [`rva_berlin_named_housing_public_stock_geography_2025_v0.toml`](../../research/observations/rva_berlin_named_housing_public_stock_geography_2025_v0.toml). This source contains **only aggregated corporate counts and official WFS metadata**, no polygons, personal addresses or individual covered insurance risks. Tested with 12 source-gated negative controls.

### **New original 2025 Berlin district-by-corporation data: real geography for these named insurance-client corporates**

The **same government that directly confirmed insurer identities in April** later published a **complete 12-Berlin-Bezirk × seven land-owned property operators original dwelling count matrix**. Its independent official source is [Berlin Senate, 11 Nov 2025, Drucksache 19/24229](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24229.pdf), **question 2, PDF page 3**. This is **NOT postcode data**: the government explicitly says **no PLZ breakdown** is available. Six corporation totals are **as of June 30, 2025**; berlinovo total **as of Sept 30, 2025**. This is a genuine company-by-borough corporate **dwelling stock observation**, not a measured count of risk addresses or insurance contracts.

Canonical bounded public numeric transcription with source exact row totals: [`rva_berlin_senate_housing_borough_stock_2025_v0.toml`](../../research/observations/rva_berlin_senate_housing_borough_stock_2025_v0.toml). Executive original table:

| Borough (selected) | GESOBAU **dwellings** | WBM **dwellings** | degewo **dwellings** |
| --- | ---: | ---: | ---: |
| Pankow | 19,578 | 139 | 964 |
| Reinickendorf | 18,049 | 0 | 995 |
| Mitte | 6,625 | 12,455 | 8,055 |
| Friedrichshain-Kreuzberg | 0 | 16,531 | 1,662 |
| Marzahn-Hellersdorf | 2,878 | 0 | 19,566 |
| Treptow-Köpenick | 0 | 159 | 16,656 |
| **Published corporate TOTAL including non-borough stock** | **49,054** | **34,040** | **82,637** |

The full 12-district table also includes **Gewobag, HOWOGE, STADT UND LAND** as **competitor-insured controls** (per April Senate document) plus berlinovo (insurer not established by that report). The original **six companies' aggregate totals reconcile exactly to 376,278 housing units**, plus separate berlinovo **18,666**; a subset of corporate stock is explicitly classified `weitere Bestände` that can include property outside Berlin, student/MUF housing and holdings in affiliates/funds. Do **NOT** smear `weitere Bestände` over the twelve Berlin districts. The sum of the three named R+V-connected company totals is **165,731 dwellings** including the outside/other category, while the **12-Berlin-district subtotal** is **162,883 dwellings** (WBM + GESOBAU + degewo), and this still is **NOT insured buildings** or active insurance policies.

A deterministic [`rva_berlin_named_corporate_borough_opportunity_sensitivity_v0.py`](../../research_runners/rva_berlin_named_corporate_borough_opportunity_sensitivity_v0.py) computes **three declared what-if scenarios** for the degewo **share/coverage of its observed dwelling-based corporate opportunity**: 0%, 50%, 100%, added to the GESOBAU+WBM corporate dwelling opportunity baseline **for prioritizing geographic survey**. Total **hypothetical corporate dwelling-equivalents within the 12 Berlin boroughs** are respectively **82,787; 122,835; 162,883**. These are **scenario denominators**, NOT the company's actual insured dwelling count, insurers' legal co-share (especially degewo vs Allianz), R+V year-end contract count, property TIV, cat exposure or actual retention. No insurer participation share or assured cover of all owned corporation properties is known. The hypothetical scale *must not be added* to **1,060,546 R+V Allgemeine 2025 connected-building policies**, as buildings, unit counts and master contract structures are not equivalent.

**This is now a high-confidence *geographic named-corporate-opportunity* layer** directly anchored by two **separate official government publications** (corporate insurer names and corporate dwelling stock distribution). It is scientifically MUCH more informative for Berlin **large multifamily/corporate accounts** than universal bank-office proximity and establishes controls: WBM concentration Mitte and Friedrichshain-Kreuzberg; GESOBAU Pankow and Reinickendorf; degewo Marzahn-Hellersdorf/Treptow-Köpenick, among others. Still no identifiable insurer-covered building geometry or property-specific cover!

2025 owner-stock reporting dates differ from the 2025-12 company balance-sheet snapshot, and the **2023 WBM award ends Jan 2027 per secondary contract-index sources**; these do not prove cover unchanged in 2026. [Later Berlin Senate Nov 24 2025 answer, Drucksache 19/24336](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24336.pdf) specifically confirms no public fine-grained street + house-number + PLZ company housing table of this type was supplied in response, pointing researchers to the district-level parliamentary table. That is a useful **source disclosure limit**; public GIS polygons do not carry company identifiers as described above.

Reproducibility:

```bash
python research_runners/rva_berlin_named_corporate_borough_opportunity_sensitivity_v0.py
python -m unittest discover -s tests -p 'test_rva_berlin_named_corporate_borough_opportunity_2025_v0.py' -v
```

12 additional tests validate 12×7 source numeric entries, original six-company housing mass, named R+V/competitor legal-entity separation, no artificial geo assignment of `weitere Bestände`, no risk address/TIV assumption, and degewo alternate *hypotheses*.

### Independent corporate inventory opportunity and location data

Primary company **2025** inventory, **dwelling units / business units**, NOT insurance policies, TIV or single buildings:

- [WBM 2025 corporate annual presentation](https://gb.wbm.de/) identifies **34,498 dwellings**, **2,159,600 m² residential area** and **314,000 m² commercial area**; these are corporate **stock**, not a 2025 R+V covered asset schedule.
- [GESOBAU 2025 corporate numbers](https://www.gesobau.de/ueber-uns/gesobau-in-zahlen/) describe roughly **48,800 own dwellings** and **~800 commercial units** plus ~700 third-party-managed dwellings; distinguish owned from managed holdings and insurance liability.
- [degewo 2025 corporate news](https://www.degewo.de/wir-sind-degewo/presse) states **more than 83,000 apartments managed/supplied** (source UI sometimes differs by textual interpolation); 2025 company owned/managed legal group and degewo joint insurer co-share remain unverified.
- Very approximately those three corporations together have **more than 166,000 dwelling units**, but these figures have mixed owned/managed definitions; **never call them 166,000 buildings, R+V contracts or insured sites**.

**New highly useful 2025 public geospatial dataset:** [Berlin official Wohnungsbestand der landeseigenen Wohnungsunternehmen WFS](https://daten.berlin.de/datensaetze/wohnungsbestand-der-landeseigenen-wohnungsunternehmen-wfs-4c4e0115) with **DL-DE-Zero-2.0 licensing** and polygons of **cadastral parcels with at least 4 residential units per address**, derived from address-level corporate stock reports and subsequently geocoded by the Senate. Government source is a **2025 spatial opportunity mask** and much better than a bank office catchment for *possible* large multifamily housing locations. BUT critically: the [official source data format description](https://gdi.berlin.de/data/lwu/docs/Datenformatbeschreibung_LWU.pdf) lists only geometry, **`gisid` cadastral parcel ID and `typ` category**. **It does not expose WHICH of the six corporations owns/operates a parcel**. Source explicitly warns parcels can contain units owned by other landlords; so **one cannot join polygons to GESOBAU/WBM/degewo insured company** from this WFS. A parcel is not automatically a building, one dwelling, or one R+V-covered site. No raw WFS output or individual house coordinates were acquired in this PR. Its 2025 geography vintage is also different from the 2022 Zensus 400 Kreis building population.

Additional independently dated [Berlin Senate WMS metadata](https://daten.berlin.de/datensaetze/wohnungsbestand-der-landeseigenen-wohnungsunternehmen-wms-f97597ac) supports spatial coverage, not owner attribution. Individual company **legitimately published** portfolio mapping such as [WBM's self-published corporate stock map](https://www.wbm.de/neubau-berlin/bestandskarte/) or official reports may eventually help *corporate* site identification; those are still not the property schedule attached to the R+V policy. Inspect source rights before combining/distributing geometries.

**Model impact:** Most defensible new class is **confirmed corporate-property insurance relationship** with conditional public real-estate opportunity; prioritize Berlin WBM, GESOBAU and degewo *separately* from standard one-policy-per-building residential household book. Test influence of named public multi-building accounts in dedicated commercial/multifamily / large-risk modelling scenarios and alternative co-insurance fractions (0–100% intentionally hypothetical). Negative controls from Senate ensure other state-owned Berlin property accounts are **not automatically ascribed to R+V**.

---



**2026-11-05 research note.** Target **R+V Allgemeine Versicherung AG** (legal entity, SOLO), not all of R+V group and not an ENV company different from this identified target. Machine-readable inventory: [28 source candidates](../../research/observations/rva_distribution_bancassurance_public_awards_20261105_v0.toml), each with evidence grain, source scope, vintage, research priority and explicit **NO source asset/insurer site/TIV admission**.

## 1. What the stronger evidence actually shows

### Insurer itself: distribution architecture

[R+V publisher corporate network page](https://www.ruv.de/ueber-uns/unternehmen/konzernstruktur) describes **more than 640 cooperative partner banks and around 260 general agencies**, alongside transport cooperatives, industry groups and brokers. Another [R+V sales recruitment page](https://www.ruv.de/karriere/vertrieb/unser-ruv-vertrieb) refers to **about 700 partner banks, about 300 general agencies and over 5,000 field-sales colleagues**. These may be different populations/snapshot vintages. **Do not sum, resolve as a current stable denominator, or treat 5,000 individual staff as 5,000 distinct offices.** Both are R+V *group* distribution networks, not geographic observations of solo R+V Allgemeine insured properties.

The [R+V agent locator](https://www.ruv.de/vor-ort/shared/consent) links published offices; the **third-party** [generalagenten.de](https://www.generalagenten.de/) lists many agency offices grouped by Land; example self-reported directory category counts: [Bayern 70](https://www.generalagenten.de/Bayern), [Hessen 47](https://www.generalagenten.de/Hessen), [Nordrhein-Westfalen 28](https://www.generalagenten.de/Nordrhein-Westfalen). These are **not comparable** to BVR bank offices, may duplicate named agents serving multiple offices, may be outdated, and have unreviewed bulk-extraction and reuse conditions. Counts may be used as **alternative exposure-opportunity priors only after a full geographic and license audit**; no private agent personal contact fields are transferred.

[2025 BVR original regional statistics](https://berichte.bvr.de/jahresbericht-2025/ergebnisse/regionale-statistik/) publishes **646 cooperative institutions, 6,167 branches and 17,542,193 cooperative members**, including Sparda, PSD and other institutions. The regional associations **do not equate to Länder**, and **BVR institutions ≠ verified R+V bank partnership roster**. An existing typed [BVR source and checksum](../../research/observations/bvr_regional_association_counts_2024_2025_v0.toml) already reconcile 2024/25 data. [BVR original 2025 bank directory](https://www.bvr.de/Presse/Zahlen_Daten_Fakten) adds names, *bank headquarters*, aggregate assets, customer claims/loans by bank; **headquarters are not local branch geocodes, and customer loans do not imply insured properties**. [Bundesbank bank-branch series](https://www.bundesbank.de/de/statistiken/statistische-fachreihen/-/1-zahl-der-kreditinstitute-und-ihrer-zweigstellen-807844) can help identify different bank population definitions (banks, branches, offices and time), not insure any R+V house. There may be a major selection bias in bank head offices of big multi-county cooperative banks.

A concrete **R+V specialist named by local bank** on [Volksbank Berg's public bank adviser page](https://www.volksbank-berg.de/meine-bank/unsere-ansprechpartner/ansprechpartner-der-rv-versicherung.html) establishes local referral or coverage service, not a customer list. Do **not** scrape or retain personal staff data in the portfolio.

A [2026 Handelsblatt-reported statement](https://versicherungswirtschaft-heute.de/unternehmen-und-management/2026-04-20/rv-muss-schwaechelnden-geno-banken-vertrieb-kompensieren/) describes **fewer than 200,000 annual bank referrals**, compared with up to **320,000 formerly**. Source is **secondary news, group scope and referral flows, not stock or conversion rate**. Important consequence: **a bank-branch location has only an imperfect, time-varying relationship with geographic R+V acquisitions** because servicing now spans phone and digital channels.

### More insurer-specific than a bank: **named public awards / customers**

- **WBM Berlin, 2023:** [secondary original-public-procurement index](https://de.openprocurements.com/tender/verbundene-wohngebaude-versicherung/) attributes a **Verbundene Wohngebäude-Versicherung** award on the WBM housing portfolio to **R+V Allgemeine Versicherung AG**, referencing **EU TED OJS 783307-2023**. Direct primary [TED notice](https://ted.europa.eu/en/notice/-/detail/783307-2023) is confirmed to exist, but its complete contractual roles, schedules, terms and policy duration have **NOT** been independently parsed here. **This is a real-world named-customer award *candidate***, far stronger than bank office proximity, but NOT yet a complete verified list of insured addresses, actual 2025 claim exposures, coinsurance share or coverage period.
- **WBM Berlin, 2026:** [second public indexed award](https://auftragsatlas.de/ausschreibung/industrielle-sachversicherung-fuer-reine-gewerbeobjekte-1172391) references [EU TED 668506-2026](https://ted.europa.eu/en/notice/-/detail/668506-2026). It concerns **nine commercial buildings**, with **R+V Allgemeine, HDI Global and Helvetia** named among awardees. This demonstrates **multi-insurer participation**, not that R+V bears 100% of nine buildings' loss or TIV; the indexed scheduled start is **2027**, so it must **never** be counted as a 2025 existing R+V insurer exposure.
- [WBM corporate annual reports](https://www.wbm.de/presse/downloads/) and [public property map](https://www.wbm.de/neubau-berlin/bestandskarte/) are powerful follow-up sources for **named-account building opportunities** in central Berlin and potentially exact non-personal legal-entity property locations. WBM reports **many thousands of dwelling units**; **one dwelling ≠ one insured building ≠ one insurance contract**. A map showing the WBM inventory in 2025/26 cannot establish that all objects are in the 2023 R+V policy, especially where subsidiaries, excess cover, coinsurance or property disposal intervene. Dates, risk addresses, company subsidiaries and permission must be matched individually if legally available.
- **Additional procurement candidates** indexed under the legal entity include Kassenärztliche Vereinigung Baden-Württemberg industrial property/electronics and Baugesellschaft UMG Göttingen fire-construction cover; [award overview](https://auftragsatlas.de/auftragnehmer/r-v-allgemeine-versicherung-ag-23682) reportedly lists ~20 procedures, not 20 actual insured-property books. **Individually verify original TED notice, CPV/LoB, full awardee roles, contract start/end, covered objects and co-insurer shares.** Any **motor fleet** contract (for example [Landkreis Rosenheim](https://vergabehero.eu/ausschreibungen/kraftfahrzeug-und-flottenversicherung-fuer-den-landkreis-rosenheim--cmthw85c70o133msreyqqnume)) is an explicit **negative control**: legal-entity regional activity, **ZERO property-observation value**.

For a public **named account** with an authoritative insurance procurement notice and a publicly documented corporate property portfolio, capture *only lawful high-level corporate attributes* (corporate entity, date, asset type, geographic areas, public building stock counts, published cover family). Do NOT assert individual buildings insured by R+V until the underlying risk schedule permits it. Financial/insurance award price is NOT the building TIV or expected CAT loss.

### Agriculture: distribution not obvious from a bank branch

[R+V AgrarPolice building insurance](https://www.ruv.de/firmenkunden/landwirtschaftliche-versicherungen/agrarpolice/gebaeudeversicherung) covers separate farm **houses, stables, barns** and restoration-cost claims. The [Landesbauernverband Brandenburg](https://www.lbv-brandenburg.de/2-projekte/vvb/uncategorised/87-versicherungs-vermittlungsgesellschaft-mbh) publicly describes its VVB agricultural insurance brokerage as a **joint organisation of the farmers' association and R+V Versicherung AG**; the [Bundesverband Rind und Schwein](https://www.rind-schwein.de/brs-de/kooperations-rahmenvertragspartner.html) names **R+V Allgemeine Versicherung AG** among its insurer cooperation partners. This is a **strong agrarian brand/channel affinity signal**. It does not reveal penetration, insured sites, whether an individual farm selected the property line, or solo direct premium. Do not force barns, warehousing or farm business-interruption TIV into the **1,060,546 year-end self-written connected-residential-buildings** HGB observation.

### Industry market benchmark and product terms

[GDV original residential building market series](https://www.gdv.de/gdv/statistik/statistiken-zur-deutschen-versicherungswirtschaft-uebersicht/schaden-und-unfallversicherung/geschaeftsentwicklung-in-der-verbundenen-wohngebaeudeversicherung-137968) supplies historical nationwide market premium and policy counts. [V.E.R.S./Versicherungsjournal 2026 ranking](https://www.versicherungsjournal.de/markt-und-politik/die-groessten-wohngebaeudeversicherer-157000) quotes approximately **19.2m** German 2025 building insurance contracts and **EUR 14.35bn** market booked premiums, placing R+V in the leading premium group. This benchmark can constrain a *national* share with strict scope alignment; it cannot reveal Kreis market shares and is **not insured TIV**. The official [GDV county natural-perils cover rates](https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-elementar/versicherungsdichte-bei-elementarschadenversicherung-regional-sehr-unterschiedlich-183592) benchmark market take-up and have **independent reuse/mining restrictions**. They are not observed R+V add-on adoption.

[R+V Wohngebäude coverage](https://www.ruv.de/wohngebaeudeversicherung) has **classic/comfort** and optional natural-perils clauses; [commercial building cover](https://www.ruv.de/static-files/ruvde/downloads/firmenkunden/kundeninfoblatt-gebaeudeversicherung.pdf) and the agricultural product demand separate **risk classes** and catastrophe cover archetypes. R+V tariff language/requirements yield a **feature dictionary**, not loss rates, geographic premium maps, actual selection or endorsement counts.

## 2. How to test the user's bank/agent radius hypothesis rather than assume it

**Question:** Does the likelihood of a building being an R+V risk increase around Volksbank/Raiffeisenbank branches, insurance specialists, R+V agencies, agricultural cooperatives or known named-customer insured assets?

It is scientifically **plausible**, not proven. In particular, mere branch density mainly reflects **where people and businesses are**, so a naive correlation with insured buildings would arise even if the insurer had no local channel advantage. There are strong competing explanations: owner occupation, bank mortgage origination, local competitor relationships (regional public insurers), urban/rural distance, building mix/age, bank service districts and digital/broker sales.

A **falsifiable study** at 2022-Kreis (then 1km Zensus/2025 geocodes if rights and dates permit) should use:

1. **Observed opportunities:** The 400-Kreis public 2022 housing/building stock, original ten construction age columns, ownership original-coded counts (upstream research PR #1326). Treat official building **count** and home insurance **contracts** as different units; model missing cell confidentiality rather than zeros.
2. **Candidate banking footprint:** 2025 cooperative bank branch / customer service sites, geocoded from **bank-published public office directories** or [OSM bank POI schema](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dbank) if ODbL and completeness are acceptable. Do not apply BVR **headquarters** at all service locations. Validate the local office represents an R+V **actual partner**; Sparda, PSD and another banking type must not be assumed eligible simply for being in BVR.
3. **Agent and agri channel footprint:** Public *office entities*, not personal contact information, independently measured R+V agency sites and eligible agricultural intermediaries, with date, postcode, source URL and deduplication. Travel-time or urban/rural-adjusted catchment **sensitivities** rather than one fixed radius; agency office does not represent group insurer written contracts.
4. **Bank business relevance rather than raw ATMs:** BVR bank-specific original 2025 assets/loans and, where public, **local mortgages** (not the *whole* loan balance), bank service boundaries and actual explicitly named R+V advisers. Mortgage balance is still a bank statistic, not insurer cross-sell conversion. Avoid including ATMs as active insurance advisers.
5. **Named account overlay:** WBM/other independently verified property insurance procurement cases in a separately tagged **commercial or housing-association account layer**, NEVER automatically translating *dwellings* to R+V *residential policy counts* or including a 2027 commercial contract in the 2025 solo benchmark.
6. **Competitor and peril sensitivity:** Industry building-cover share by county and flood take-up as **GDV industry priors only**. Regional public insurers may dominate a county despite dense VR branches. Risk appetite/region constraints and insured commercial policy mix need independent evidence before estimating TIV.

For an expressly **hypothetical** model (not yet fitted or validated), county weight for segment `s` can be:

```text
raw_weight[k,s] =
    observed_2022_physical_building_opportunities[k,s]
  * hypothetical_relative_RV_bank_affinity[k,s]
  * hypothetical_relative_RV_agency_affinity[k,s]
  * hypothetical_relative_sector_partner_affinity[k,s]
  * hypothetical_relative_underwriting_selection[k,s]

hypothetical_contracts[k,s] =
    conserve_integer_counts(raw_weight[*,s], declared_national_segment_total[s])

hypothetical_booked_premium_cents[k,s] =
    conserve_euro_cents(segment_premium_weights, declared_national_HGB_GWP[s])
```

These **multipliers are not observed coefficients**. Avoid estimating any coefficients from just the national `1,060,546` building contract count: it is mathematically **unidentifiable** from one control and 400 unknown regional responses. For a first study, compare:
- `H0` **building-stock only** (bank / agency coefficients zero);
- `H1` **bank-only** with several *invented* effect sizes, explicit catchment kernel and false bank classification sensitivity;
- `H2` **agency-only**, adjusting for population density, branch service areas and clustering;
- `H3` **bank + agency + agriculture partners**, avoiding multiplication of highly correlated branch and agent counts without regularization;
- `H4` **verified public named-client case studies** held apart from broad statistical stock and never forced into a hypothetical Kreis allocation unless matched to validated unit count.

**Quality gates:** held-out public company/award validation, source asset hashes, copyright/rights, 2022/2025 vintages, duplicate branch/fusion handling, weighted population standardization, posterior/prior sensitivity, alternate agent radius and online-serviced zero-distance scenario, exact national mass conservation, excluded group and motor business, explicitly unknown insured TIV/natcat cover. Don't use *group catastrophe claim locations* for customer penetration inference: event losses are affected by event footprints and flood selection, so they provide biased exposure evidence.

## 3. Decision queue — which newly discovered sources to admit next

| Priority | Concrete original data-acquisition / validation work | Why |
| --- | --- | --- |
| P0 | Retrieve 2023 **TED 783307** and 2026 **TED 668506** full original award details, identify *leader / participation shares, corporate scope, asset schedule, effective dates*, plus WBM public portfolio reports | **First genuinely named property-buyer anchors**, vs opportunistic marketing |
| P0 | Reconcile original R+V agent offices (group vs solo) and **verify 2025 eligible partner-bank subpopulation**, instead of treating all BVR institutions as R+V partners | First meaningful spatial bancassurance proxy, direct response to radius hypothesis |
| P0 | Audit the BVR **2025 legal-bank list** and bank mortgage/service areas (publish a source signature/rights record), then compare to known **400 Kreis** physical building/age base | Correct denominator and service territory; no HQ-to-RV-site mistaken join |
| P0 | Document Brandenburg farmers' VVB/other sector partnerships and public farms / agricultural census counts; separate direct legal-entity LoB | Farm/SME buildings may have substantial CAT TIV and distinct peril/coverage |
| P1 | Check [GDV market natural-perils county map](https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-elementar/versicherungsdichte-bei-elementarschadenversicherung-regional-sehr-unterschiedlich-183592) access conditions and include only legally admissible stats | Flood insurance propensity benchmark, *not R+V* take-up |
| P1 | Scope regional German **public procurement** beyond TED by contracting entity and CPV, merge/deny duplicated awards | Commercial property named accounts may be discoverable in service authorities and hospital complexes |

**Admission status on this turn:** This is source **discovery and an executable source-integrity gate**; **no new original full 2025 branch/agency coordinate dataset, bank source PDF, exact TED award contract/risk schedule, or actual property insured location has been imported**. Until explicit licensing, original entity matching and contract terms are validated, all 28 candidates remain *research_only* in the source register. The upstream synthetic count/cent allocator and original 400 Kreis building/age/owner 2022 observations remain a separate data lineage.

Additional analytical caution: The related [BVR insurance-group financial reports](https://berichte.bvr.de/jahresbericht-2025/ergebnisse/verbundunternehmen/) may describe R+V group contributions and distribution, but not R+V Allgemeine solo risk positions. Historical bank closures and changes in referring flows after 2024 make proximity estimates time-varying.
