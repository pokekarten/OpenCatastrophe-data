<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V 2025 issuer-anchored regional non-identifiability and verified BVR regional association input

**2026-11-04 research milestone:** We now have a **reproducible, exact nationally constrained synthetic book sensitivity**, not an observed real R+V portfolio. The target is **R+V Allgemeine Versicherung AG solo HGB**; never merge group, other legal entities or public insurance-group press events.

## What was checked and what is original

The original [R+V Allgemeine 2025 HGB](https://www.ruv.de/dam/jcr:e0e32e31-09ff-4b0f-b693-2c6c9bee9bb5/01_GB%202025_R+V%20Allgemeine%20Versicherung%20AG_final.2026-04-21-14-59-23.pdf) provides **1,060,546 year-end contracts** in the self-written connected-buildings line; its premium by LoB is **997,710 TEUR booked direct gross premiums for 2025**. The input is read from the already-merged [source-pinned solo HGB observations](../../research/observations/rva_solo_hgb_property_2019_2025_v0.toml), not inferred from an offer form, phone book, financial model or 2022 housing counts. The annual HGB rounded-to-TEUR amount is therefore **EUR 997,710,000** in this accounting scenario. Dividing by the *year-end* count does **not** yield the average earned premium or a tariff.

The official, **original public publisher HTML** [BVR Jahresbericht 2025, regionale Statistik](https://berichte.bvr.de/jahresbericht-2025/ergebnisse/regionale-statistik/) was inspected. The issuer shows:

| Reporting group / unit | 2025 banks | 2025 branch offices | 2025 members |
| --- | ---: | ---: | ---: |
| Baden-Württemberg association | 115 | 1,126 | 3,555,260 |
| Bayern association | 175 | 1,443 | 2,557,974 |
| Genoverband | 277 | 3,020 | 7,364,367 |
| Weser-Ems | 47 | 244 | 574,466 |
| Regional **subtotal** | **614** | **5,833** | **14,052,067** |
| Sparda, PSD and other cooperative institutions | 32 | 334 | 3,490,126 |
| **Overall BVR reporting total** | **646** | **6,167** | **17,542,193** |

The typed [BVR 2024/2025 observation register](../../research/observations/bvr_regional_association_counts_2024_2025_v0.toml) includes **seven disjoint category rows**, both source years, and positive/negative guard flags. 2024 overall BVR total: **672 banks**, **6,311 branch offices**, **17,643,092 members**. From 2024 to 2025, bank **branches** declined by **144**, although this is **not** an observed decline in R+V branches, contracts, property TIV or sites. BVR `Zweigstellen` are not the same published population as `Bankstellen` including main offices. The first four observations are **associations**, some spanning multiple states. The Sparda/PSD/other categories are **national categories**, not Land equivalents. The stock is a sales-channel *opportunity proxy*, **not insurer-book policy geography**. Source contents have been narrowed to the separately audited aggregate numerical observations; no bulk unlicensed PDFs, personal data or customer lists were copied, and original BVR HTML bytes were **not** cryptographically pinned.

R+V sales mix is additionally supported by [R+V issuer recruitment channel overview](https://www.ruv.de/karriere/vertrieb/unser-ruv-vertrieb), its [2025 solo company HGB](https://www.ruv.de/dam/jcr:e0e32e31-09ff-4b0f-b693-2c6c9bee9bb5/01_GB%202025_R+V%20Allgemeine%20Versicherung%20AG_final.2026-04-21-14-59-23.pdf), regional sales territory [Koblenz](https://www.ruv.de/newsroom/pressemitteilungen/2023-06-23-100-jahre-koblenz), and previous [company group reports](rva-group-claims-tariff-territory-triangulation-20261104.md). None of these disclose sales weights for each German county, underwriting location, insurance amount or natural-perils endorsement.

## What the new executable actually demonstrates

```bash
python research_runners/rva_company_anchored_macro_prior_sensitivity_v0.py
python -m unittest discover -s tests -p 'test_rva_company_anchored_macro_prior_sensitivity_v0.py' -v
```

The source-linked runner reads three small original/independently-declared **TOML records** and hashes their exact bytes. It plugs issuer-published **national 2025** count and GWP into the previously tested [exact integer and cent conserved synthetic allocator](../../research_runners/synthetic_regional_property_book_v0.py). In **three deliberately invented alternative distributions**—uniform, south/west concentrated, and north/east concentrated—it keeps exactly **1,060,546 contracts and 99,771,000,000 euro-cents of 2025 booked premiums**. Every region/contract capacity, regional weight and price relativity remains a **hypothetical scenario parameter**. All are marked invented and cannot be converted into R+V location or TIV observations.

The runner computes the *half-L1* number of contracts moved relative to the uniform case and the corresponding total-variation share while holding national count, legal-entity accounting basis and total national written premium **constant**. This is an operational scientific demonstration of **nonidentification**: company totals alone do not establish the geographical book or model loss curve. BVR observed associations are **explicitly not used** as weights: no validated BVR-association-to-2022-Kreis bridge, partner-matched insurance sales or policy conversion rates were found. A parameter labelled `DE_NORTH` etc is an **abstract fictional macro bucket**, not a real geocoded Kreis/county, building-centroid or Census population.

The allocator has no verified optional flood cover. Its `hypothetical_elemental_cover_contract_equivalents=0` means **not estimated in this demonstration**, **NOT that R+V has zero elemental policies**. A loss model built on this must not report calibrated flood or storm net/OEP/AEP.

## What changed beyond the preceding research

- **First exact 2025 solo company aggregate controlled geographic sensitivity** (not a 100k-site/500bn EUR toy with unrelated company scale).
- Original numeric **2024/2025 BVR regional-association statistics** typed, subtotal- and grand-total-validated. Scope ambiguity (regional bank associations ≠ administrative Bundesländer) is automatically tested.
- Three hypotheses **deterministically compared on the same issuer national anchors** and exact cent precision, with no invented coverage or regional company attribution.
- Fail-closed tests reject shifted insurer identity or national GWP, BVR source tampering, bank branches being misrepresented as actual insurer sites, invented flood take-up being treated as observed, and attempts to label fictitious macro cases as real insurer exposure.

## Evidence admission requirements for actual geographic portfolio estimation

1. **Independent physical building population by district:** [Destatis original Zensus 2022 regional tables](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html) offer 2022 administrative Bund/Land/Kreis/Gemeinde CSV and XLSX; [Zensus Atlas grid OpenData](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html) offers 100m/1km/10km building classification. These do **not** give 2025 R+V sites, and the official CSV data must have exact asset hash, correct 2022 geographic code, count-not-dwelling validation, suppression/missing symbol treatment and reuse permission before replacing fictional weights. The existing [Zensus original workbook receipt](../../research_runners/zensus_regional_original_receipt_v0.py) confirms origin/package of a workbook in past workflow, **not numeric cells**. No new original Zensus numeric rows have been acquired or admitted in this commit.
2. **Independent industry and risk propensity:** GDV **district** storms/flood hazard, market elemental penetration and insured claim frequency only with documented original [GDV data-use conditions](https://www.gdv.de/gdv/statistik/nutzungsbedingungen-fuer-statistikdaten-und-deren-visualisierung-188704); automatic text/data mining is restricted without consent. For insurer-specific R+V region conversion, BVR bank associations alone are insufficient. Geography must be checked at the same land/district vintage; OSM or Overture buildings are opportunity footprint, never insurer sites.
3. **Peril-specific building archetypes, valuation, event losses:** [R+V public residential form](https://online.ruv.de/ruvdownloads/makler/vertriebsdownloads/ruv-privatpolice-analysebogen-wohngebaeude-summenmodell?action=download) gives construction, roof, area, floor and building type *variables* but not their frequencies. [Agrar policy](https://www.ruv.de/firmenkunden/landwirtschaftliche-versicherungen/agrarpolice/gebaeudeversicherung) and [SME building insurance](https://www.ruv.de/static-files/ruvde/downloads/firmenkunden/kundeninfoblatt-gebaeudeversicherung.pdf) require separate lines. DWD wind and flood catalogues need reproducible event frequency/footprints and building fragility; company all-cause HGB claims or R+V group press cannot supply geocoded frequency.
4. **Outward treaty and actual Oasis model:** Existing [R+V solo 2021–25 external RI sources](../../research/observations/rva_solo_public_natcat_ri_2021_2025_v0.toml) report public treaty *families* (XL, quota, parent NatCat cover) but **not exact real attachment, limit, cession, inuring order, reinstatements or incurred event ceded loss**. Use declared fictional contract terms to compute IL/RI/net and disclose every structural uncertainty. Only after independent German event/vulnerability and synthetic location/TIV intake can native Oasis OEP/AEP be called a calibrated run.

**Scientific result:** mathematically exact (counts and EUR cents), nationally issuer-anchored **fictional spatial scenarios**. Not yet a *statistically estimated* R+V geographic exposure portfolio, not real or synthetic geocoded OED, and not a Germany hazard-calibrated Oasis output.


## Major improvement: **real 2022 state-level building opportunity data**, not only fictional macro weights

Original **Thüringer Landesamt für Statistik**, *Statistisches Monatsheft Mai 2025*, article *Ergebnisse der Gebäude- und Wohnungszählung des Zensus 2022 zu Gebäuden mit Wohnraum in Thüringen*, **figure 5, printed p.29** (all 16 Länder plus Germany), direct official-archive link:
https://www.statistischebibliothek.de/mir/servlets/MCRFileNodeServlet/THMonografie_derivate_00000684/Aufsatz-05a-2025.pdf

A narrow, attributed and machine-readable transcription of the actual national/state **2022 Gebäude mit Wohnraum** totals and four ownership classes lives in [zensus2022_16_state_residential_use_buildings_v0.toml](../../research/observations/zensus2022_16_state_residential_use_buildings_v0.toml), the **first actual 16-state German physical opportunity numeric matrix** for the R+V exercise. Publisher print: Germany **19,957,268 buildings with residential use**. The **16 published individual Länder rows sum to 19,957,266**, i.e. **2 fewer**. Ownership subtotals likewise differ in small amounts, up to 6 within a state and up to 10 when comparing the sum of states to publisher national ownership categories. The pipeline **reports this original non-additivity instead of silently inventing 2 buildings or forcing statistical counts to agree**. Underlying original office PDF bytes were not downloaded or SHA256 authenticated in this step; only small cited aggregates were manually transcribed. Never treat this article as a licensed individual-building location file.

The published statistic **Gebäude mit Wohnraum** also includes *other buildings with some dwelling use*, so it is **not exactly** `Wohngebäude` and is **not equivalent** to R+V insured connected-building contract counts. It represents an independent **2022 physical-building opportunity denominator** only. Ownership classes are *physical building owner types*, **not** the insurer's policyholder / insured category shares.

### Executable 16-state hypothesis comparison, first truly external geographic distribution

```bash
python research_runners/rva_census_16state_company_prior_v0.py
python -m unittest discover -s tests -p 'test_rva_census_16state_company_prior_v0.py' -v
```

The executable reads the attributed **2022 public census state counts** plus the already source-pinned **2025 R+V Allgemeine solo HGB national policy count 1,060,546 and booked GWP EUR 997.710m**. It produces **three alternative hypothetical, exactly mass-conserving 2025 state allocations** based on different factual **2022 opportunity** categories:

1. all 2022 buildings with residential use (uniform hypothetical contract affinity per published physical building);
2. 2022 privately owned buildings (hypothetical bias towards individual owners);
3. 2022 apartment-owner association + housing-company buildings (alternative hypothetical bias towards professionally/collectively managed holdings).

The first case illustrates the raw 2022 physical opportunity benchmark. Its company-book distribution is a **simulation**, not a measured geographic share. Example approximate 2025 allocations under this **uniform hypothetical**: North Rhine-Westphalia **~214,807**, Bavaria **~171,503**, Baden-Württemberg **~136,411**, Berlin **~17,997** *hypothetical contracts*. They are not reported actual R+V sales! All 16 state predictions sum to exactly **1,060,546** and the allocated book GWP to exactly **EUR 997.710m**, after deterministic integer/cent rounding. The actual state share could differ substantially, as demonstrated by the other two scenarios.

No BVR association statistics enter these computed state weights: no validated BVR association->Land crosswalk or issuer bank partner conversion has been obtained. The earlier four invented macro-region stress script stays useful as a *separate structural sensitivity*, while this 16-state proof finally uses **genuine public physical-building evidence** for one dimension of the estimated portfolio. No real 2025 insurer locations, endorsements, TIV, county exposures or perils are inferred.

### Critical data gaps before production insurance/GIS modelling

The next technical evidence step is to acquire the **original Zensus 2022 Kreis-level** CSV at the same 15 May 2022 geography, with original byte SHA, column semantics and suppression treatment. The **national 2022** to **insurer 2025** population shift is not corrected by the currently source-backed record, and the model must explicitly calculate sensitivity to 2022–25 growth, insurance policy multiplicity, urban multi-unit cover and the issuer's own regional market shares. Once district-level data and genuine building footprints are admitted with correct rights, one can generate location-level *synthetic* OED. German DWD peril hazard, vulnerability, actual model execution and gross/net OEP/AEP are subsequent independent scientific gates, not outcomes of the present BVR/census research.

**Source state:** First audited public **16-state opportunity input and three company-anchored inferred spatial distributions**, still NOT actual R+V exposures, CAT losses, underwriting location or a calibrated Oasis model.
