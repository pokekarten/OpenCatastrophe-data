<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V Allgemeine 2025 -> synthetic German CAT portfolio research bridge v0

**Status 2026-11-04: offline executable, non-admitted research.** The spoken "RNV" target is provisionally interpreted as **R+V Allgemeine Versicherung AG**, a **solo direct insurer**. "EMV" is not identified as a verified separate model or entity. No insurer's actual site-level portfolio, TIV, policy coverage, outward treaty, calibrated Oasis loss or Solvency II capital is inferred.

## Existing canonical sources, not duplicate registers

- Single machine source: [FFBK 2025 solo SFCR profiles](https://github.com/pokekarten/FFBK/blob/main/research/reinsurance/solo_sfcr_de_fr_profiles_2025_v0.json), profile `RVA_DE_2025`. Original official [R+V Allgemeine 2025 SFCR](https://www.ruv.de/dam/jcr%3A9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf), A.2: **EUR 5,992.306m** reported solo gross written premiums (GWP); **EUR 2,223.182m** Fire and Other Property GWP. The latter is **not** NatCat-only, household-building premium, real-site TIV or loss. The FFBK 12 nonzero premium rows total EUR 5,992.305m: the EUR 0.001m rounding gap is acceptable, not silently corrected.
- [FFBK premium/CAT non-identification counterexample](https://github.com/pokekarten/FFBK/blob/main/research/reinsurance/portfolio-premium-cat-nonidentification-v0.md) proves that the **same** premium and **same fictional** EUR 500bn TIV can produce very different physical loss tails under different hypothetical geographic concentration. This example's EUR 500bn is **a fictional sensitivity scale only**.
- [R+V Group 2025 results](https://www.ruv.de/newsroom/pressemitteilungen/2026-04-13-bilanzpressekonferenz) include **2025 EUR 150m vs 2024 EUR 442m** group elemental claims and **EUR 7,983m** 2025 group HGB P&C GWP. Those are a **different group/coverage/accounting perimeter**, not R+V Allgemeine solo CAT event loss, company AAL or the basis of a hazard frequency fit.
- Existing OpenCat-data `synthetic_regional_property_book_v0.py`, `synthetic_insurer_premium_marginals_v0.py` and `export_synthetic_oed_v0.py` already implement distinct fictional allocation/projection experiments; do not silently merge their separate contracts. [OpenCatastrophe #23](https://github.com/pokekarten/OpenCatastrophe/pull/23) executes native Oasis PiWind toy calculations with an open strict float32-gross/net audit; [#24](https://github.com/pokekarten/OpenCatastrophe/pull/24) adds independent OEP/AEP period/sample gates. PiWind is a **UK demo toy**, not a calibrated German peril model.

## What is implemented

`research_runners/rva_property_bridge_v0.py` loads the exact FFBK canonical JSON file provided by an adjacent checkout (it never downloads and does not keep a second copy). It validates entity identity, date, accounting measure, property premium and the published rounding tolerance. It separately reads `research/scenarios/rva_property_geography_hypotheses_v0.json` and deterministically allocates **independent assumed site counts and imaginary TIV** across arbitrary region bins using exact decimal weights and integer-conserving largest-remainder allocation.

The example invents **100,000 risk sites** and **EUR 500bn total TIV** in four broad `DE_*` scenario bins. They are NOT observed R+V counts/TIV, real districts, real building geometries, CRESTA zones, geocoded points, actual properties or insurer policies. Changing regional TIV weights changes the synthetic allocation while leaving observed SFCR property premium unchanged. No premium/TIV conversion is performed.

Run from a checkout of OpenCatastrophe-data next to a checkout of FFBK:

```bash
python research_runners/rva_property_bridge_v0.py \
  ../FFBK/research/reinsurance/solo_sfcr_de_fr_profiles_2025_v0.json \
  research/scenarios/rva_property_geography_hypotheses_v0.json
python -m unittest discover -s tests -p 'test_rva_property_bridge_v0.py' -v
```

The bridge emits input SHA-256 receipts and explicit `oasis_production_run_allowed=false`, `company_tiv_observed=false`, `oed_location_ready=false`, `hazard_calibrated=false`, and `risk_transfer_contract_observed=false`. Positive and negative tests check conservation and block group/solo, year, accounting, false authority and value mixing. **It does not create a `location.csv` or execute Oasis.**

## Data acquisition priorities for a defensible German R+V-like CAT model

| Priority | Data source / existing registry | Needed evidence; key failure to avoid |
| --- | --- | --- |
| P0 | [R+V solo SFCR/QRT 2025](https://www.ruv.de/ueber-uns/unternehmen/geschaeftsberichte), FFBK `RVA_DE_2025` | Entity/LoB/accounting constraints; no insurer TIV or geography inferred from GWP |
| P0 | [Destatis Zensus 2022 regional building/dwelling tables](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html), indexed in OpenCat-data | 2022 building stock by *proper* Kreis codes, metadata and suppression handling; not a 2025 R+V risk-site count |
| P0 | OpenCat-data `sources-german-carrier-exposure-priors-20261103.json`: BaFin insurer-count candidate | Company-specific insurance/risk-count denominator when applicable; complaint-population selection and insurance counts not equal buildings |
| P0 | Overture buildings, ALKIS building footprints, Zensus demographics, construction and floor-count inputs | Physical building opportunity and replacement-value priors; original data rights/quality/vintage, insurer take-up and policy-to-site assignments still missing |
| P0 | [DWD Climate Data Center](https://opendata.dwd.de/climate_environment/CDC/), historical gust/radar and extreme precipitation | Observed wind/hail/precipitation hazard validation, missingness and spatial/temporal support before fitting Germany event frequency |
| P0 | [GDV Naturgefahrenreport 2026](https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport) | Regional **industry**, not R+V-only, storm/hail/flood insured losses/penetration benchmarks. **Do not bulk mine without provider rights review.** |
| P1 | OpenCat-data EFAS/GloFAS/Copernicus EMS and national flood hazards | Distinguish return periods/scenario maps from stochastic insured **event catalogues** and calibrated loss events |
| P1 | ESHM20/ESRM20 / GEM/OpenQuake/ EFEHR sources already studied | Earthquake hazard and fragility/taxonomy crosswalk; an OpenQuake result is not a native Oasis model without a proven adapter |
| P1 | OED per-site currency, construction, occupancy, latitude/longitude, building/contents/BI TIV, peril cover and deductibles | Create separate explicitly synthetic **locations, policies and coverage** with documented scenario uncertainty |
| P1 | Actual R+V outward reinsurance terms, if ever sourced | Net results require order, per-occurrence/aggregate limit, attachment, inuring order, reinstatements and scope. Otherwise label **fictional treaty**, never R+V actual net |

## Ordered technical acceptance path

1. Build **multiple** physical-exposure scenarios (residential-heavy, commercial-heavy, concentrated), rather than a unique book from premiums. Keep location, policy, covered TIV and premium units separate.
2. Choose first **German** peril (wind or flood), then acquire/licence-check and version original intensity grids, event/frequency catalogues and vulnerability functions. Physical event IDs and dependence across periods/perils must be explicit. A flood return-period layer is not a random-year event simulation.
3. Construct geocoded **synthetic** OED location/account/policy/coverage files with correct model-specific valid lookup taxonomies and total TIV reconciliation. Use actual model release, pinned ODS/Oasis versions; block unmatched hazard area-peril IDs, not default them to zero.
4. Run native GUL -> insured gross IL -> **fictional** outward RI -> net, then AAL, OEP, AEP on identical stochastic worlds. Verify 0-event years, shared physical events, frequency and sample/period identities.
5. Resolve OpenCatastrophe #23 native strict numerical differences and #24 original-artifact validation; compare native ORD/YLT to an independent event/annual oracle. Repeat across exposure and treaty scenarios to quantify non-identifiability **separately** from MC noise.
6. Only after independent observed catastrophe-loss and company-perimeter benchmarking may the result be described as *calibrated*. Current deliverable is a validated source-to-assumption boundary, **not** a real R+V Oasis risk model, net PML or SCR.

**No production Neon writes, no original provider rows in Git, and no company exposure or model admission are part of this PR.**
