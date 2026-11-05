<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLIMK–WINDS ERA5 native point gust → synthetic physical damage: strict conditional pilot

**Research draft (2026-11-05). Not an insurer's real exposure or loss data; no CAT annual frequency, AAL, OEP, AEP, premium, insured recovery, regulatory capital, observed claims calibration or vendor-model validation.**

## Existing original source and proven research route

The **existing** OpenCatastrophe-data source route must be reused rather than duplicated:

1. `scripts/inspect_climk_winds_era5_v0.py` retrieves and verifies the original [CLIMK–WINDS v2 ERA5 NetCDF](https://zenodo.org/records/15305753), a **top-50 extreme-winter-storm selection for 1995–2015**, not a complete representative multi-year event catalogue. Verified provider bytes: size **6,792,278**, publisher MD5 `887ae3218793c599862f115876c145f9`, pinned SHA256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`. Existing repository execution receipt reports an authentic provider download and NetCDF header check, with 50 storms × 181 latitudes × 269 longitudes; see `docs/CLIMK_WINDS_ERA5_PROVIDER_PROBE.md` and [GitHub Actions source receipt](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41227457898). This PR does **not** re-download or rerun the original NetCDF.
2. `scripts/climk_era5_synthetic_native_sample_v0.py` independently samples one source-specific storm index at synthetic lon/lat points on the native grid, preserving source names/date annotations and the original unit `m s**-1`. No claimed mapping to the distinct C3S EWS physical storm event IDs.
3. **New** `scripts/climk_era5_synthetic_damage_preview_v0.py` takes that strict original JSON *shape* and separately authored synthetic assets and wind-gust damage curves. It computes exact-rational per-asset *conditional expected ground-up loss* without pretending to be original policy-insured gross, inward reinsurance or net retained loss.

The scientific paper [Flynn et al., *Earth System Science Data* 17, 4431–4453 (2025)](https://doi.org/10.5194/essd-17-4431-2025) confirms each of the four meteorological input sources selects its own top 50 extreme storms. The source dates and storm IDs **cannot** be assumed to match across source models. The publisher README states **CC BY 4.0**; attribution, third-party licenses and a source-specific publication review remain mandatory. An original sample's embedded SHA256 is only a declared source binding. Without additional flags, the downstream adapter **cannot prove that forwarded JSON gust values still equal original NetCDF** and exports `source_sample_gust_values_independently_reverified=false`. With both optional `--original-netcdf` and `--original-sites`, it invokes the existing source-authentic native CLIMK sampler again against pinned original bytes and fails if **any** forwarded sample field differs; only this actual re-extraction produces the `true` flag. The 15 local unit tests mock this optional dependency to verify wiring and corruption detection; they do **not** independently rerun real publisher NetCDF bytes.

## Explicit new input contracts

Three independently pinned JSON files are supplied to the new CLI:

- `--source-sample`: exactly the existing sampler's `oc-climk-era5-synthetic-native-point-sample-v0` JSON. It must cite the pinned source SHA, retain one original `storm-index:0..49`, the original gust-unit/measure, location IDs and all `scientifically_admitted=false`, `source_event_frequency_inferred=false`, and `damage_or_insured_loss_computed=false` flags. Bad types, mismatched IDs or omitted sites fail closed.
- `--synthetic-assets`: `{"schema_version":"oc-climk-era5-synthetic-asset-roster-v0","synthetic_only":true,"currency":"EUR","insurer_label":"ZURICH_RESEARCH_PROXY","rows":[{"asset_id":"invented-1","site_id":"site-1","taxonomy":"COM","replacement_cost_eur":10000000}]}`. These are **invented buildings** and an inspiration-only insurer label, not a Zurich property schedule. Every source sampled site must map to at least one synthetic asset; every asset must have an explicit reviewed source sample site.
- `--vlt`: `{"schema_version":"oc-climk-era5-synthetic-conditional-gust-vlt-v0","physical_intensity_measure":"MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT","normalized_unit":"mm/s","model_evidence":"USER_AUTHORED_UNCALIBRATED_SYNTHETIC_ASSUMPTION","curves":[{"taxonomy":"COM","gust_knots_mm_s":[0,15000,25000,35000,200000],"damage_ratio_bps":[0,0,100,2000,10000]}]}`. Monotone, physically bounded piecewise-linear *assumed* ratio, not a fitted claim curve. No extrapolation allowed.

CLI (run on real pinned point-sample JSON prepared **separately**):

```bash
python scripts/climk_era5_synthetic_damage_preview_v0.py \
  --source-sample /tmp/climk-synthetic-source-native-sites.json \
  --synthetic-assets /tmp/climk-synthetic-assets.json \
  --vlt /tmp/climk-assumed-wind-vlt.json \
  --original-netcdf /tmp/ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc \
  --original-sites /tmp/synthetic-sites-as-used-to-create-source-sample.json \
  --out /tmp/climk-synthetic-conditional-damage-preview.json
python -m unittest discover -s tests -p test_climk_era5_synthetic_damage_preview_v0.py -v
```

### Exact physical-loss calculation

Gust in m/s is converted to **mm/s** with decimal half-up rounding. Damage ratio is interpolated *exactly* between user-supplied bps knots; per-asset conditional ground-up EUR is kept as exact rational numerator/denominator, without silently rounding cents, damaging source units or converting per-asset cost into a book-level TIV. With hypothetical gusts 20/30 m/s, per-asset cost EUR 10m, and the sample VLT above, loss ratios 50/1,050 bps give **EUR 50,000 / EUR 1,050,000**, or **EUR 1.1m** combined. **All these are invented test values.**

### Scientific and financial boundaries

- **Not the native C3S stochastic stage.** NextGen `research/c3s_wind_footprint_stage_v0.py` requires `MAX_3_SECOND_10M_GUST_OVER_72_HOURS` plus C3S-specific NetCDF/track/footprint semantics. CLIMK's `absolute_maxwindgusts` is published as its own storm footprint variable. This adapter **never relabels** CLIMK as C3S, nor treats C3S counts as CLIMK occurrence probabilities.
- **Not original-policy gross.** The existing NextGen `model_factory_portfolio_bridge_v0.py` applies limits/deductibles/shares to per-asset *sampled integer physical losses*; this adapter supplies only conditional rational means and **does not** generate `MUSE_SYNTHETIC_CAT_GROUND_UP_V0` or misrepresent original real hazard as `new_synthetic`.
- **Not EP.** The 50 preselected extremes are **not** 50 complete annual worlds, annual frequencies or a Poisson intensity. All reported `annual_AAL`, `annual_AEP`, `annual_OEP`, original insured gross, primary net, outside inward gross/net are explicitly `null`.
- **Not calibrated.** Actual empirical event-level impact observations, consistent buildings and taxonomy, spatial/temporal train/holdout and impact-function parameter bounds are needed before empirical vulnerability calibration. Even the source-aligned historical point gusts must be revalidated against original bytes at conversion time for an admitted physical loss stage.

## Local executed gates and next steps

- 2026-11-05: **15/15 local Python stdlib tests passed**, including a 2-asset exact hand-oracle, invalid source identity and event key, unsupported C3S gust substitution, duplicate assets, incomplete site mapping, nonmonotone VLT, unbounded gust, invalid JSON, CLI source-overwrite protection, optional original-reader wiring with mock re-extraction and tampered JSON challenge. Tests use **invented source-shaped JSON**, not original CLIMK event values. The mocked reader is **not** a live authentic NetCDF proof.
- [x] Implement optional original-byte-bound re-extraction and complete JSON equality check (tests via mock reader; no original binary fetched in this PR).
- [ ] Actually execute that real-source option against original SHA-pinned CLIMK NetCDF at the same event index and 24 invented coordinates, producing separate raw+point+damage SHA evidence.
- [ ] Obtain independent event-level historical *observed impact* samples for a real test/holdout damage-function calibration; do not fit to a published insurer net AEL/PML directly.
- [ ] Build scientifically admitted annual physical-event frequency/occurrence law and correlation, then **sample** physical damage with validated dependency and explicit positive integer EUR handling.
- [ ] Run producer-admitted event/asset physical losses through NextGen **original insured → outward/inward Cat XL → external retro**, preserving all zero-event years and physical event identities, then Gross/Net AAL/AEP/OEP with independently rebuilt curve receipts.

No original/provider raw data, derived grid values, person information, actual insurer contracts or production database rows are committed in this research PR.

## Live end-to-end ORIGINAL NetCDF → 24 fictional assets (2026-11-05 addition)

The added `scripts/climk_era5_conditional_damage_live_receipt_v0.py`
executes a bounded, **nonannual** single-event source test. It reuses the
original already-reviewed live source URL, hashes the 6,792,278 original bytes
against the pinned SHA256, extracts **storm index 0** at two original-source-
preflight synthetic coordinate pairs from `docs/CROSS_PERIL_PHYSICAL_EVENT_EVIDENCE_V0.md`,
and then rereads the *same original NetCDF* inside the new conditional damage
adapter to ensure the supplied gust sample JSON matches exactly. No raw source
file or raster is saved to this repo.

Precisely **24 invented commercial assets** at two fictional point markers
(12 each), each EUR 10m replacement cost, total invented EUR 240m, are
processed with the displayed **unfitted** monotone piecewise-linear wind/VLT
curve. Do not call these *Zurich* insured risks; the Zurich-labelled name is
a research tag only. The result keeps original source sha, source-specific
storm label, exactly two native grid point values, assumed VLT SHA and an
exact rational per-event conditional physical ground-up loss. It does not
produce a sampled occurrence loss, a primary insured loss, inward/retro claim,
or any AEP/OEP/annual AAL.

To run online from a complete repository checkout:

```sh
python -m pip install -r requirements-glofas-acquisition.txt
python -m unittest tests.test_climk_era5_synthetic_damage_preview_v0 tests.test_climk_era5_conditional_damage_live_receipt_v0 -v
python scripts/climk_era5_conditional_damage_live_receipt_v0.py --out /tmp/climk-original-24-fictional-buildings.json
```

The specifically triggered `CLIMK ERA5 Original Source Conditional Loss Research
Receipt` workflow (`.github/workflows/climk-era5-synthetic-conditional-loss-live.yml`)
runs these commands with **source-immutable digest and scientific negative
assertions** on GitHub Actions. Its output contains no confidential information.

The new **4/4 offline live-orchestration tests** challenge synthetic inventory,
mocked source-reader wiring (EUR 13.2m hand calculation from fake 20/30 m/s
gusts), original-byte SHA mismatch, and fabricated re-verification status.
These are *not* live-NetCDF tests. The real output's storm gusts and actual
conditional loss can only be quoted after the linked workflow succeeds.
The separate baseline adapter unit suite remains 15/15 locally green.


## Completed first original-source CI receipt (source commit `f4379d4`)

[GitHub Actions successful run 42012362586](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42012362586)
executed against the authentic Zenodo **6,792,278-byte** original ERA5 v2
NetCDF, pinned SHA256 `92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102`.
The workflow completed **20/20 Python tests** followed by an actual source
read and an independent *second* original-NetCDF point-sampling equality check.
An initial live run exposed the original source's previously unmodelled
`event_identity_cross_model_matched=false` field; the exact schema and
negative challenge were corrected before the successful rerun.

The source-selected historical storm index 0 is **KYRILL**, date label
`20070118` (not an independently parsed UTC timestamp). Both fictional
sites happen to choose **the same native ERA5 cell (x=112, y=78)**;
both observed native source gusts equal **35.21054044063598 m/s**. We make no
claim of geographic risk diversification. For 24 × EUR10m fictitious
buildings and the declared *unfitted* damage VLT, the conditional **physical**
expected loss is the exact rational **EUR530700800 / 11 = about EUR48.2455m**.
This is NOT a calibrated insurer loss, an annual AAL, or an AEP/OEP value.

The reviewable machine-readable JSON-in-Markdown *original successful run receipt* is committed at
`docs/research/evidence/climk-era5-kyrill-24-fictional-buildings-source-loss-20261105.md`,
including source, synthetic asset and VLT SHA-256, selected source storm/date,
exact wind samples, exact conditional loss and all non-admission disclaimers.
The CI workflow now independently compares current original-source output to
this pinned receipt rather than accepting only self-reported source labels. The repository prohibits tracked JSON/JSONL artifacts outside specifically registered projections; therefore the compact structured receipt is embedded in the single licensed Markdown evidence page.
All underlying native NetCDF files and grid arrays remain outside Git.

## Native-cell multiplicity / nonindependence guard (2026-11-05)

The original-source-to-conditional-loss wrapper now reports `distinct_native_hazard_grid_cells_sampled`, `source_sites_share_a_native_grid_cell`, and `max_fictional_assets_sharing_one_native_grid_cell`. The current fixed Kyrill receipt must show **2 synthetic site labels → 1 distinct native ERA5 cell → 24 invented assets associated with that same cell**. The existing source-locked live workflow checks these fields and the original evidence receipt; no additional provider observation is inferred by introducing more site or asset labels.

The conditional point adapter additionally rejects contradictory native gust, center or relative climatology values when two synthetic site labels refer to the *same* `(native_cell_x,native_cell_y)`. New synthetic-only tests challenge both consistent and inconsistent shared-cell scenarios and the distinct-cell case. This specifically blocks false geographic diversification and fabricated independent wind observations. It does not establish physical building location, insurance ownership, storm frequency, primary terms, reinsurance, vulnerability calibration or EP curves. The original CLIMK source file remains external, exact-SHA-pinned and re-read only by the special CI; do not claim scientific or production admission from this gate.


## Additional official wind-loss reference – WISC Tier 3 (research only, 2026-11-05)

A separate older [ECMWF/C3S WISC historical winter windstorm indicator dataset, DOI 10.24381/cds.9b4ea013](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-indicators) contains **Tier 3 modelled building-level loss and risk indicators** for **21 European countries**, including Germany, France, Luxembourg, Belgium and the UK. This is **not** the new all-year C3S EWS summary-count CSV, the CLIMK–ERA5 v2 grid, or real policy/claims data. Do not use the products interchangeably.

- Official [historical loss indicator guide](https://confluence.ecmwf.int/spaces/CKB/pages/253724006/Loss+indicators+Tier+3+Product+User+Guide): modelled per-historical-storm loss, OSM-derived building footprint/centroid and classifications, NUTS3 output; published period and historical winter-storm scope must be verified against exact original product bytes. These are **model outputs**, not observed paid insurance claims.
- Official [synthetic risk indicator guide](https://confluence.ecmwf.int/spaces/CKB/pages/253724009/Risk+indicators+Tier+3+Product+User+Guide): physically plausible synthetic storm-set *average annual damage* based on OSM building footprints, country construction fractions from PAGER and public fragility curves. This is not direct empirical damage calibration and must not replace a yearly cross-peril event calendar or historical observed claims.
- C3S [Windstorm Information Service overview](https://climate.copernicus.eu/windstorm-information-service) states that the historical WISC model was adapted to Oasis LMF-compatible exposure/vulnerability, while its separate physically plausible storm-set is a distinct product. The old WISC Tier 3 guidance expressly flags **ODbL obligations for derivative works of OpenStreetMap-based building data**, a different rights chain from the new C3S EWS service's CC BY licence. Product-level terms, attribution and permitted derivative uses need independent review before model/source admission.
- The [official WISC known-issues listing](https://cds.climate.copernicus.eu/datasets/sis-european-wind-storm-indicators?tab=documentation) identifies a historical Xynthia filename misdated **2009** rather than **2010**. Never merge storm identities by raw filename/year without checking event metadata.
- The separate [EIOPA Catastrophe Data Hub](https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en) provides samples of *insurer-reported* catastrophe exposure/loss aggregates (not a 100%-market view). It is **already catalogued** in this repository under docs/source-reviews/eiopa-catastrophe-data-hub-2023.md and manifests/eiopa.catastrophe-data-hub.*.2023-12-05.json; avoid duplicating that dataset. EIOPA aggregates are a potentially independent **market-scale economic challenge**, not policy/site-level damage observations.

**Scientific test proposal, not performed:** after rights/original-byte validation, join WISC source storms and geography to CLIMK only through *verified event, date, intensity-measure and spatial lineage* (not guessed same-name events); compare conditional synthetic VLT loss **against WISC's explicitly modelled** loss with clear common-model/circularity flags. For true vulnerability out-of-sample calibration independently prefer observed event-specific physical repair/claims sources; WISC model-on-model comparisons cannot establish absolute accuracy. Independently challenge regional insured totals against properly time-/perimeter-/currency-matched EIOPA source receipts. No source bytes, member hashes, joined records, rights admission, empirical fit or policy/Gross-Net CAT outputs are claimed from this section.


## 2026-11-05 – actual European historical loss observations: HANZE windstorm v1.0 and Norway claims methodology

Two *new* non-admission source candidates are now catalogued, separately from our existing HANZE **flood** catalogue and EIOPA aggregates, in `landscape/sources-windstorm-observed-loss-validation-20261105.json` with its rendered Markdown view.

**HANZE European Windstorm Impact Database**, https://doi.org/10.5281/zenodo.15266959 (23 April 2025, v1.0). The original Zenodo API record metadata advertises CC BY 4.0 and one downloadable **XLSX**, not the CSV/GIS files suggested by its narrative description. Its exact published filename is `HANZE European Windstorm Impact Database 1950-2020.xlsx`, size **292136 bytes**, with provider-supplied `md5:0a523543adf76003916186623812ab74` (not independently checked against local original bytes). A document parser accessed the provider's original spreadsheet endpoint and confirmed its 20-column header, including `ID`, `Code`, `Year`, `Country`, `Start`, `End`, `Source` (storm name), NUTS2/3 affected-region lists, nominal economic loss and currency, **2020 EUR millions**, `Notes`, `CDS` and `Sources`. Only a **truncated workbook view** and selected samples were inspected, not the entire underlying XLSX with a locally verified SHA256.

Selected preview rows sharing the *name* Kyrill and January 2007 date demonstrate **country-specific source IDs, not distinct physical storms**:

| Country | Publisher row ID | Original reported date interval | 2020 EUR millions (economic impact; not insured claim) | Source-circularity / origin |
| --- | ---: | --- | ---: | --- |
| Austria | 20034 | 2007-01-18 | 96.41 | Notes explicitly: **Modelled economic loss from CDS**; NOT independent CLIMK/C3S model calibration |
| Belgium | 20076 | 2007-01-18 | 400.38 | Compiled sources EM-DAT, Copernicus, Pinto; review primary source and overlap |
| Czechia | 20104 | 2007-01-18 | 154.3 | EM-DAT, Czech authorities, Pinto; original CZK estimates, converted to 2020 EUR |
| Denmark | 20128 | 2007-01-17 to 2007-01-19 | 87.94 | DKK-original estimate; overlaps the event period in other countries |
| France | 20250 | 2007-01-18 | 209.5 | EM-DAT and third-party sources; not certified independent paid claims |

These are **source-preview reference values**, not newly fetched, hash-proven original data rows, company insured losses, per-building repair costs, or empirical vulnerability calibrations. A same-name/storm-date crosswalk to CLIMK v2 `20070118` is only a **candidate**, not a verified common native event ID, matched physical path, exposure region, loss peril or time zone. Missing regional damages must remain unknown rather than zero. Even if the published record-level CC BY declaration is valid, HANZE's companion site says "research purposes only" and cites third-party sources: redistribution, upstream licence, and potential observational/modelled circularity require explicit review.

**Norwegian natural-perils claims study:** Jaison et al. (2024), https://doi.org/10.5194/nhess-24-1341-2024, compares **36 years (1985–2020)** of daily municipality-level insurance claim counts and amounts for **356 municipalities** with NORA3 wind fields. It documents geographic heterogeneity, many zero-claim days, and damage-function uncertainty. The paper is publicly accessible under CC BY 4.0, **but its data-availability statement expressly says the raw insurance claims are proprietary and cannot be shared**. The external NORA3 wind fields are available and some aggregated Norwegian NASK statistics may be public. Treat the original claims as **restricted**, never as an open training CSV or as an implied permission to ingest insurer policy-level records.

**Proposed independent out-of-sample validation, NOT run:** 1) fetch permitted unmodified original HANZE XLSX outside Git and compute actual SHA256; 2) pin NUTS geography/version, original input dates, nominal-vs-2020 EUR units, loss-type flags and original citations for each event/country; 3) hold out all rows with self-described modelled CDS impacts and all circular upstream source chains; 4) independently tie common physical storms to CLIMK/GIS by event dates and paths; 5) evaluate *country-level economic-loss scale only* under genuinely independent, explicitly labelled economic-loss observations. Separately seek legally authorized insurance claims data where available; neither source by itself determines a 24-building joint damage correlation, Zurich market penetration, Gross/Net treaty outcome, annual AAL or OEP/AEP.
