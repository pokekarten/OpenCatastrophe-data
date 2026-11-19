<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V Allgemeine 2025: source-gated synthetic German CAT portfolio bridge v0

**Research-only, 2026-11-04.** "RNV" is provisionally understood as **R+V Allgemeine Versicherung AG** (German solo direct-insurance entity). The term "EMV" has no independently established target model here. This study does **not** recover real insured sites, policy counts, TIV, reinsurance treaties, CAT claims or an approved German Oasis stochastic model.

## Issuer observations and accounting scope

- Official issuer [R+V Allgemeine 2025 SFCR](https://www.ruv.de/dam/jcr%3A9c8441a7-28dd-4d98-9b79-3eb3c8b4afa5/2025-SFCR-Allgemeine.pdf), solo 2025 underwriting premium table: **EUR 5,992.306m gross written premium** across the legal entity; **EUR 2,223.182m Fire and Other Property GWP**. These are insurance **premiums**, not insured asset value, natural catastrophe premiums, risk locations or losses. The 12 nonzero line-item values total EUR 5,992.305m; retain its EUR 0.001m publisher rounding residual.
- This repository's independently verified public source snapshot is `research/observations/rva_solo_2025_public_sfcr_v0.toml`. It carries the **issuer URL, 2025 solo legal entity, basis and 12 dated accounting lines** and is a transparent typed research receipt, **not an ingest of actual customer or exposure information**.
- Distinct R+V **group** [2025 HGB result press release](https://www.ruv.de/newsroom/pressemitteilungen/2026-04-13-bilanzpressekonferenz) contains EUR 7,983m 2025 group property/casualty contributions and 2025 EUR 150m versus 2024 EUR 442m group reported elemental claims. **Do not treat the group figures as the solo entity's observed CAT loss or peril loss frequency.**
- Independent official solo SFCR C.1 stress recorded in `research/observations/rva_solo_2025_natcat_stress_v0.toml`: illustrative two severe storms drive solo solvency coverage **241.2% -> 221.4%**, SCR **+EUR 121.899m**, eligible own funds **-EUR 314.118m**. It is **not** event gross/net insured loss, calibrated 1-in-200 PML, annual model return period, or a company-specific damage curve.

## Executable research bridge

`research_runners/rva_property_bridge_v0.py` reads **two local TOML files**, requiring the exact solo-source entity/year/measure/GWP reconciliation and independent explicit assumptions. `research/scenarios/rva_property_geography_hypotheses_v0.toml` invents **100,000 fictional sites** and **EUR 500bn wholly fictional TIV**, allocated over four arbitrary `DE_*` buckets using separate location and TIV weights. The original 500bn example is only a numerical sensitivity scale. It is **not** a conversion from published 2.223bn premiums or an estimate of R+V's real TIV.

The bridge conserves the integer site count and total fictional TIV. All results retain `company_site_geography_observed=false`, `company_tiv_observed=false`, `oed_location_ready=false`, `hazard_calibrated=false`, `risk_transfer_contract_observed=false` and `oasis_production_run_allowed=false`. It does not touch Neon or emit `location.csv`, hazard footprints, losses or RI treaties. Change the weights to expose risk-concentration uncertainty **without modifying observed GWP**.

Run using Python 3.11+:

```bash
python research_runners/rva_property_bridge_v0.py \
  research/observations/rva_solo_2025_public_sfcr_v0.toml \
  research/scenarios/rva_property_geography_hypotheses_v0.toml
python -m unittest discover -s tests -p 'test_rva_property_bridge_v0.py' -v
```

The printed `public_sfcr_input_sha256` and `scenario_sha256` pin the two parsed study inputs, **not** source PDF bytes. The separate source receipt's issuer URL and verification scope remain explicit.

## Original data to acquire and validate, in order

| Need | Public source or existing project asset | Boundary |
| --- | --- | --- |
| Exact legal entity, premiums and peril scope | Official 2025 solo SFCR and BaFin entity/risk-count statistics | Company identity, year, solo/group, direct vs accepted, reporting units; risk counts != buildings |
| German building geography and exposure opportunity | [Destatis Zensus 2022 Kreis building/dwelling tables](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html); Overture buildings; ALKIS | 2022 physical building stock != 2025 insured R+V addresses; inspect data licensing, vintage, nested geographic levels |
| Location replacement value and class | German structural cost index, public building/area/floors, occupancy/construction, consumer price and residential/commercial priors | Physical rebuilding cost != insured TIV; BI/contents separate; no fictitious company precision |
| German storm/hail and rain frequency/footprints | [DWD Climate Data Center](https://opendata.dwd.de/climate_environment/CDC/), radar and gust/extreme rain; physically reconstructed events | Station/grid historical observations not automatically Oasis stochastic event probabilities |
| Industry loss/vulnerability independent challenge | [GDV Naturgefahrenreport](https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport) | Industry peril-region insured claims != target carrier CAT loss; usage/automation rights must be reviewed before collection |
| Flood/earthquake hazard alternatives | Existing Copernicus, EFAS/GloFAS, ESHM20/ESRM20, EFEHR, OpenQuake studies | Return-period maps and GMPE hazard curves do not themselves form annual event/financial-loss simulations |
| First actual native Oasis OED/ORD Germany run | Validated geocoded synthetic `location/account/policy`, model-specific peril/vulnerability taxonomy, compatible hazard and native OASIS engine | Existing OpenCatastrophe [#23](https://github.com/pokekarten/OpenCatastrophe/pull/23) UK PiWind toy numeric strict audit still red; [#24](https://github.com/pokekarten/OpenCatastrophe/pull/24) original OEP/AEP artefact replay pending |
| Net and capital | Explicit **fictional** outward QS / catastrophe XL terms, independent native GUL/IL/RI/YLT/OEP/AEP checks | Do not attribute invented terms or model net PML to real R+V; capital solvency stress is not an event loss |

## Acceptance sequence

1. Build multiple geographically and compositionally distinct **synthetic** German property exposure hypotheses. Keep market building stock, insurer take-up, premium, replacement cost and covered value orthogonal.
2. Select a first Germany-supported peril (**windstorm preferred**) with version-pinned original hazard event catalogue and vulnerable building classes. Admit reuse rights and quality before generating loss.
3. Form correct geocoded Oasis OED `location.csv`, `account.csv` and optional policy/coverage inputs; reject unmatched area-peril and vulnerability mapping rather than defaulting to quiet events.
4. Execute native ground-up GUL -> insured gross IL -> optional **fictional** outward RI/net on shared event and period/sample IDs, produce `ORD`, annual ledgers, AAL, OEP and AEP.
5. Resolve native strict numeric audit in #23 and verify #24 against the original native artifact, and challenge model loss independently against appropriate external German peril/claims frequencies. Report scenario uncertainty separately from sampling error.
6. Only after observed company-scale and independently evidenced hazard/vulnerability/financial validation describe output as externally calibrated. An actual company-specific insurer CAT loss distribution is **not identifiable** from solo premium alone.

No production database write, external provider data row import, real company exposure claim or Germany model admission is proposed in this PR.
