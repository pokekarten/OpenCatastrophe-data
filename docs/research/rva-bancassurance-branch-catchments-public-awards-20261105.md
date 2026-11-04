<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V insurer portfolio discovery: bank catchments, agents, named public property awards, and non-obvious market priors

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
