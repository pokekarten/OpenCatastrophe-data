<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windstorm Europe and Atlantic tropical-cyclone official source gap: 14 November 2026

This is a **non-admission source-access follow-up** to [Windstorm Europe data gaps](windstorm-europe-data-and-completion-gaps-v0.md) and the current model-side wind source/annual EP gate. The only canonical new candidate facts are in [the five-entry landscape shard](../../landscape/sources-windstorm-europe-tc-official-20261114.json); its Markdown view is generated. No source bytes, access credentials, actual insured exposure, policy rows or proprietary hazard files are committed.

## Concrete web-source checks in this turn

| Source | Provider page result | Original-data/API status | Commercial use boundary |
|---|---|---|---|
| Meteo-France hourly climate | Official data.gouv.fr dataset labels **Licence Ouverte / Open Licence 2.0**, hourly CSV.GZ by department and period. Public `https://www.data.gouv.fr/api/1/datasets/donnees-climatologiques-de-base-horaires/` returned JSON dataset metadata. | **Metadata API body read; zero hourly CSV resources downloaded or hashed.** Field dictionary and a bounded single-gust-resource proof next. | Open Licence label reviewed at catalogue level; per-file scope, attribution and sensor dictionary still require validation. |
| KNMI EDR validated hourly | Official EDR documentation lists `hourly-in-situ-meteorological-observations-validated`, a spatiotemporal API and mandatory registered EDR API key. | **Documentation verified, no authorized EDR request, no result or sample**. | KNMI describes free open data; inspect each dataset's licence and attribution before commercial modelling. No keys in Git. |
| CEDA MIDAS Open v202607 | Official citable July 2026 record, DOI 10.5285/d04207b551674c07801b7d4e6d883e50, BADC-CSV, wind speed/direction, UK OGL v3, 1875–2025. | **Public metadata inspected; registration and original file/variable needed.** Excludes METAR and commissioning trial sources. | Catalogue labels OGL v3 / permitted use Any, conditional on attribution and CEDA citation; not the restricted full MIDAS product. |
| ECA&D MeteoGate | ECA&D announced its 2026 MeteoGate RODEO endpoint for **non-blended** station observations. ECA&D also lists wind gust in its station element dictionary. | **Documentation only; no live MeteoGate API result.** Keep source-station blending and downloadable policy explicit. | **Research/education non-commercial** under published ECA&D/E-OBS data policy; no insurance-commercial admission without permission. |
| NOAA NHC Atlantic HURDAT2 | NHC archive advertises 1851–2025 Atlantic HURDAT2 and 2026 September historical revisions; six-hour track/intensity. | **Archive page verified; no original revision file, SHA-256 or parser output**. | Review dataset-specific reuse notice and revision before integration; overlapping IBTrACS NHC observations are not independent. |

The authoritative pages are the respective `authoritative_url` values in the shard. Catalogue availability does **not** imply admitted source bytes, licence clearance for every original resource, or a fully callable public API.

## Shortest reproducible acquisition queue

1. **France P0**: query the public data.gouv.fr dataset JSON, choose one official original CSV.GZ department/period covering a named storm, download to a temporary private path with byte and SHA-256 receipt, parse the provider field dictionary, check station IDs, wind units, recorded gust statistic, site height/time zone and QC before pairing with ERA5/C3S.
2. **UK P0**: with an authorized CEDA account obtain one exact v202607 BADC-CSV for a named storm. Preserve file path, version, citation, station moves, QC flags and missing measurements. Do not treat hourly mean wind as 3-second gust.
3. **Netherlands P0**: acquire an EDR key via the provider account (never as repository data); request collection metadata and a bounded historical station/time slice, preserving original CoverageJSON, units, timestamps and raw digest in a private evidence store. Fail closed when a gust parameter is absent.
4. **ECA&D P1**: document endpoint parameters and whether the non-blended station/variable is downloadable; **do not** request or use commercial calibration data until ECA&D permits that exact purpose. Keep non-downloadable stations excluded.
5. **Atlantic HURDAT2 P1**: fix exact archive revision, acquire and hash one public official text file, parse header/event rows strictly and independently compare a handful of Atlantic storm IDs with NOAA IBTrACS. Separate temporal/source overlap from true independent validation.

## Scientific integration barriers

- A true observed station gust with its height and averaging interval can independently challenge an ERA5/CLIMK footprint, but a station's `wind speed` measurement cannot be silently converted to 3-second gust.
- Historic HURDAT2 tropical systems are **not** European extratropical storm occurrences. Use as a separate peril/basin and for IBTrACS reconciliation, never to construct a cross-basin annual event rate by naïve summation.
- C3S Enhanced European Windstorm remains the high-value **complete annual event/footprint** acquisition dependency. WISC's retired/soon-removed dataset notice and missing simulated windows remain open; neither a new station source nor a HURDAT2 track solves European annual AAL/OEP/AEP.
- The model repository's `docs/wind_annual_ep_gate_v14.md` found 47/50 incomplete CLIMK footprint representations over 7,998 fictional interests. New sources should first increase valid storm support and independently test values, not fill missing cells with zeros or count four representations of Kyrill as four events.

## Reproducibility and admission state

No original data payload, live authenticated API result, station-observation sample, checksum, source-specific accepted manifest or automatic commercial rights clearance was produced by this task. The five new entries therefore remain `evidence_checked / not_reviewed / not_reviewed / not_admitted`. The paired landscape Markdown is a generated projection, not another authority. A full checkout can run `python scripts/render_public_views.py --check` and `python scripts/check_all.py` against the exact PR head.
