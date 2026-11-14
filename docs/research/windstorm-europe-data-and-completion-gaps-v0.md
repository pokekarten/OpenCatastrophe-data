<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windstorm Europe: useful repository data and completion gaps

Repository review: 14 November 2026. Goal: a European extratropical windstorm
CAT model with common physical events, geographically consistent exposure,
country/building response, policy and reinsurance losses, and defensible
annual risk. Germany is the first validation region. This is a repository
evidence review; source catalogue entries alone do not prove downloads,
current availability, reusable rights or calibrated model inputs.

The [machine-readable source index](windstorm-europe-source-index-v0.toml)
records selected exact catalogue IDs, catalogue hashes and provider links.
It includes national building registers already discovered in the repository.
The source entries remain authoritative for their individual review status.

## What exists and what is missing

| Component | Existing evidence/data | Useful now | Still required |
|---|---|---|---|
| Historical footprints | Four original CLIMK files; XWS Kyrill raw/decontaminated; data-repo original source receipts | Conditional scenarios and source alternatives | Complete masks over the intended exposure domain, common event reconciliation and wider independent validation |
| Continuous weather | Source-verified Google ARCO ERA5 Ciara 96h; DWD original FX911 and event-era station histories | Hourly diagnostics and timing challenges | Multi-event, multi-country observations with compatible gust duration, height and time support |
| Annual event catalogue | C3S Enhanced Windstorm Service and WISC 22,980 synthetic footprints catalogued; C3S acquisition runner exists | Acquisition route and frequency-method prototype | Actual complete event/year records, occurrence weights, zero-event years, calendar coverage and dependence/seasonality checks |
| Building geography | Acquired NRW HU2022 original ZIP; existing 10k candidate study; EUBUCCO, Overture and national registers indexed | Regional point/geometry experiments and candidate enrichment | Versioned country extracts, deduplication, event-era alignment, occupancy/mixed-use mapping and documented coverage gaps |
| Building size/stock | GHSL BUILT-S/BUILT-V inspected/sample workflows; census dwelling-age and national registers | Aggregate stock checks and enrichment | Building-level validated area/height/age mapping; aggregate rasters do not identify individual insured assets |
| Values | Explicit fictional EUR values in runs; Eurostat construction cost indices indexed | Controlled valuation sensitivity experiments | Replacement cost per area/building class/country, price year, currency conversion and contents/BI values; sales prices are not replacement costs |
| Vulnerability | Acquired Schwierz/CLIMADA PAA/MDD reference with GPL source/notice; WISC implementation/paper inspected | External generic European reference and sensitivity | Country/resistance-class response, conditional severity variability, empirical calibration/holdout; WISC CURVES.csv remains absent |
| Damage evidence | Acquired EIOPA loss/exposure workbooks; GDV and other aggregate candidates in model review | Matched event/geographic aggregate challenges after cell validation | Verified worksheet semantics and denominators, wind-only separation, reporting completeness, claims and building damage with matching exposure |
| Financial layer | Native Oasis GUL/IL/RI demonstration and independent financial oracles in model repo | Engine/contract correctness experiments | Actual policy deductibles/limits/coverage, currencies, hours clauses and reinsurance contracts for insured results |
| GIS/model bridge | Native polygons, shared area-peril IDs, building lookup and executable scenario loss in PR #1586 | Source→map→point→expected physical building damage | Country profile/class mapping, broader portfolio conservation and native multi-cell Oasis export/reconciliation |

## Evidence that changes the completion assessment

The OpenCatastrophe model repository already reports a 7,998 fictional-interest
experiment with only three completely covered footprints and 47 incomplete
ones: see `docs/wind_annual_ep_gate_v14.md` and
`research/ruv_reference_evidence_v1/wind_mask_v12.json` there. Missing gusts
must stay unknown. The successful 50-scenario run on three fictional points
in this data repository proves only that example's coverage.

Four model-source views of Kyrill represent one physical storm. They cannot
be counted as four annual occurrences. The model repository's
`docs/wind_source_roster_v15.md` also records inconsistent stored CLIMK storm
ranks and unresolved event aliases. Join by checked identity/date evidence;
do not infer shared storm identity from rank or source-local row number.

`OpenCatastrophe/docs/germany_wind_data_to_model.md` records that the original
WISC code's German C2/C3/C4 mixture differs from supplementary Table S3 and
that its numeric curve asset is missing. Copying legacy class weights or
silently replacing missing responses with zero would create unsupported
loss estimates. Preserve the source disagreement until resolved.

## Geographic acquisition priorities

Use EUBUCCO/Overture as cross-border geometry candidates and national registers
for attribute validation and completeness checks. Already indexed routes
include Germany LoD2/ALKIS, Netherlands BAG/3DBAG, France RNB/BDNB/BD TOPO,
Poland BDOT10k, Czech RUIAN, Spain Catastro, Switzerland swissBUILDINGS3D,
Denmark BBR, Finland NLS, Norway FKB and Sweden Lantmateriet. UK EPC and
Estonia EHR appear in other source shards. Their respective access/rights,
spatial coverage, source date and attribute definitions must be checked before
combining them. Overlapping products need a source priority and deduplication
rule; adding their building counts would double count assets.

## Completion order and concrete acceptance evidence

1. Freeze the model domain, supported countries, building coverages and base
   valuation year. Retain common storm IDs across borders and distinguish
   physical event, alternative source view and financial hours-clause event.
2. Acquire the full C3S historical/event or justified synthetic occurrence
   product with source terms/account access where required. Demonstrate
   complete years and explicit weights before computing AAL/OEP/AEP.
3. Check hazard support at every intended asset for every selected event.
   Report excluded asset count/value and distinguish source masks from domain
   boundaries; resolve missing support before portfolio loss comparison.
4. Extract regional building samples from existing originals first; enrich
   country/occupancy/size/age and assign explicit replacement values. Keep
   physical stock and insured portfolio as distinct model use cases.
5. Evaluate reference vulnerability alternatives against compatible observed
   damage and held-out events. Preserve class uncertainty and PAA/MDD
   semantics; a mean response does not identify a severity distribution.
6. Run shared cross-border historical scenarios in the physical oracle and
   native Oasis with per-cell, item and portfolio conservation. Then apply
   explicitly supplied policy/reinsurance terms and compare financial outputs.
7. Produce annual loss tables from an admitted common occurrence catalogue,
   test joint-country losses and tail stability, and document frequency,
   hazard, exposure and vulnerability uncertainty separately.

## Repositories and evidence locations

- Data implementation and source reports: this repository, especially
  [executable scenarios](germany-wind-executable-scenarios-v0.md),
  [source inventory](model-scenario-vulnerability-catalog-v0.md),
  [C3S acquisition/frequency status](c3s_wind_historical_frequency_calibration_candidate_v0.md),
  and [Oasis/source follow-up](oasis-model-data-second-pass-20261105.md).
- Model/scientific experiments: `pokekarten/OpenCatastrophe`, particularly
  `docs/germany_wind_data_to_model.md`, `docs/wind_vulnerability_reference_v8.md`,
  `docs/wind_source_roster_v15.md`, and `docs/wind_annual_ep_gate_v14.md`.
- Local originals currently exist under `/tmp/pr-ci/germany-wind-data` in
  this execution environment; they are temporary storage, not a permanent
  project archive. Original acquisition receipts and licence notices must
  accompany a durable copy. No raw portfolio or licensed curve arrays are
  published by this review.

The German-language continuation entry point, including required access,
input fields, persistent storage and acceptance evidence, is now
[Windstorm Europe: Modellstand und Voraussetzungen](../WINDSTORM_EUROPE.md).
