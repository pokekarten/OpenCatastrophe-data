<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ciara/Sabine 2020: event-matched wind source path for EIOPA validation

**6 November 2026. Source discovery ONLY — no ERA5 original
meteorology bytes, EIOPA original XLSX sheets or insurer claims
were obtained or imported. No CAT model, loss calibration,
GUL/IL/RI, annual frequency or gross/net OEP/AEP admitted.**

## Why Daria 1990 must stay separate

The independent 1990 XWS Daria wind footprint, combined with 10,000
2022 NRW physical building *candidates* and a wholly fictional
2025-like R&V exposure, is a useful implementation
proof but **not** an event-matched observed-insured-loss validation.

The officially published
[EIOPA Catastrophe Data Hub](https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en)
and [technical note EIOPA-BoS-22/505, especially pages 8–11](https://www.eiopa.europa.eu/system/files/2023-12/Technical%20description%20-%20Catastrophe%20Data%20Hub.pdf)
supply reported insured wind claims for **Ciara/Sabine in
February 2020**, not Daria January 1990. The other two events
are a June 2013 central European flood and a June 2017 Portuguese
wildfire.

Public insured exposure is year-end **2020**, shown at
**NUTS2** for anonymity, with at least **three individual submitting
companies per displayed data point**, potentially
residential/commercial combined. It is not R&V insured-household
geocoding or the actual NRW 53-Kreis insured property TIV.

## Source-verified compatible hazard candidates, NOT executed

1. [Copernicus CDS ERA5 hourly single-levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download),
   DOI **10.24381/cds.adbb2d47**; original provider model
   reanalysis from 1940, including February 2020, global grid
   ~**0.25°**. The dataset requires CDS login and **explicit
   acceptance of CC BY terms** before API requests. No account
   token or licence acceptance was assumed.
2. The ECMWF [ERA5 10-metre gust since previous
   post-processing](https://confluence.ecmwf.int/pages/viewpage.action?pageId=228862799)
   is the specific `10m_wind_gust_since_previous_post_processing`
   variable, short name **10fg**, GRIB parameter **49**,
   unit **m/s**. [ECMWF parameter definition](https://codes.ecmwf.int/grib/param-db/49)
   specifies a **3-second maximum at 10 m**, separately
   representing the gust maximum in each processing interval.
   This should **not** be replaced with `u10`, `v10`,
   instantaneous wind speed or 100 m wind.
3. The [ECMWF Ciara forecast case study](https://confluence.ecmwf.int/spaces/FCST/pages/173381258/202002%2B-%2BWindstorm%2B-%2BCiara)
   documents the **9–10 February 2020** peak wind system and
   its 8–11 February meteorological evolution, while the
   [Copernicus February 2020 record](https://surfobs.climate.copernicus.eu/stateoftheclimate/february2020.php)
   identifies German name **Sabine** and broader 9–11
   February cross-European impacts. The event-window
   candidate is therefore **2020-02-08 through 2020-02-11 UTC**;
   use a later event/track/claims-specific window verification
   before computing loss or max gust.
4. The existing original XWS Daria footprint is maximum
   **3-second 10 m gust over 72 hours**, with three alternate
   modelled *same-event* gust uncertainty views. An ERA5
   hourly original `10fg` field is a different temporal
   aggregation and grid process. Even though both have
   nominal 3-second/10 m gust definitions, they are **not**
   automatically interchangeable; require a complete hourly
   interval audit, maxima within scientifically matched
   storm events, geographical reprojection, source-model
   bias/representation uncertainty and observed DWD gust
   station holdout.
5. Original **2020** EIOPA insured values cannot be scaled to
   2022 public building candidates or arbitrary 2025 fictional
   TIV without separate source-vintage, location-level and
   partial-market denominator evidence. A public NUTS2
   policy-loss aggregate may support **regional plausibility
   checking** after data rights and event matching, but is
   insufficient to uniquely fit per-building PAA/MDD or
   derive an R&V treaty financial contract.

## Source-rights and reproducibility gates before any original fetch

- Record ERA5 dataset product/version/doi, selected 10fg variable,
  source period/region, CDS licence acceptance, full downloaded
  original byte SHA256, original geographic projection, cell count
  and time-step completeness **before** aggregating multi-hour gusts.
- Obtain/verify the original EIOPA XLSX workbook bytes and
  workbook-specific reuse constraints. The original loss workbook
  was listed at 27.55 KB and the exposure workbook at 5.33 MB,
  but their direct retrieval was not successful on this
  review; zero workbook sheets, rows or hashes were inspected.
- Preserve actual EIOPA observed **incurred insured building
  claims** separate from other claims, residential/commercial
  combined values, EIOPA partial sample GWP shares, economic
  losses, modeled CLIMADA direct damage and historical
  provider Daria original source.
- Pre-register the event join keyed by the original *Ciara*
  storm identity, region/NUTS2, source observed-residential
  loss category, year and coverage/amount definitions;
  reject Daria ↔ Ciara and fabricated insurer sites.
- Do not call any rate/annual probability of event from
  the single observed 2020 Ciara storm. Independent annual
  catalogues, many historical storm years including explicit
  zeroes, and loss ordering are required for gross/net OEP/AEP.

Machine-readable original EIOPA publication/no-admission receipt:
`research/observations/eiopa_catastrophe_hub_2023_original_dossier_v0.toml`
with strict negative gates in
`research_runners/eiopa_catastrophe_hub_2023_original_dossier_gate_v0.py`.

**Current conclusion:** Ciara 2020 ERA5 `10fg` has a *source
discovery and data download specification*, not a completed
open-data acquisition or EIOPA-based vulnerability calibration.
Keep the German/R&V model scientifically **NOT ADMITTED**.
