<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Peer catastrophe, disaster-impact and insurance repository audit — 2026-11-02

**Purpose:** distinguish real external data-source candidates from useful but non-authoritative reference software. Source registry of **11 independent provider/product families**: [canonical JSON](../../landscape/sources-peer-cat-repositories-20261102.json) and its [generated view](../../landscape/sources-peer-cat-repositories-20261102.md). This research **does not admit any dataset, approve a provider's commercial use, download source bytes, or prove end-to-end model readiness**.

## Evidence and collision check

- Read current public GitHub repository metadata and relevant README / original documentation for the 20 selected repositories listed below. This is **repository-level suitability review, not a line-by-line code audit or dependency/security audit**.
- Cross-checked **48** canonical `landscape/sources*.json` shards with **327** prior entries on `pokekarten/OpenCatastrophe-data` main at `4b77c33f7d3b607adc7960b04307f10a57810991`. Existing `gem.geid.2026`, `worldbank.gfdrr.risk-data-library`, Oasis OED references and upstream USGS/GDACS/WMO/etc. are not re-added.
- The original provider is the source authority; a repo's code licence is **never** the licence of linked satellite imagery, reported disaster losses, proprietary portfolio data or commercial use of derivatives.
- A repository with no independent transferable dataset is documented here as a **method/adapter**, not inserted into the source dataset register.
- There were no identified direct open-PR changes to this new landscape shard during preparation; fresh GitHub state and CI still govern merge.

## All 20 reviewed repositories — classification and actual next use

| GitHub repository | Classification | Practical fit / limitation | Priority |
| --- | --- | --- | --- |
| [IFRCGo/GCDB](https://github.com/IFRCGo/GCDB) | **Real multi-source ETL + Montandon API lead** | Global disaster event/hazard/impact harmonisation and original-source crosswalk; upstream sources and API token restrictions. Register Montandon **once** as a source family. | P0 |
| [IFRCGo/monty-stac-extension](https://github.com/IFRCGo/monty-stac-extension) | **Interoperability standard, not source bytes** | Explicit STAC event–hazard–impact and relation types, per-source documentation and schema. Study before inventing our own semantic event interface. | P0 |
| [IFRCGo/pystac-monty](https://github.com/IFRCGo/pystac-monty) | **Adapter software, not an independent dataset** | Python STAC conversion, GDACS source transformers, correlation IDs. Evaluate no-loss vs bounded-loss joins and issuer/published times. | P0 |
| [gem/geid](https://github.com/gem/geid) | **Real historical earthquake impact data, already registered** | Contains an exact case folder for `us6000jllz`, including impact, rupture, station and OpenQuake inputs. Its `LICENSE.txt` states **CC BY-NC-SA 4.0**. Case impacts may cover a whole earthquake sequence; not independently assigned to one mainshock. **Do not duplicate existing `gem.geid.2026`.** | P0 |
| [microsoft/building-damage-assessment](https://github.com/microsoft/building-damage-assessment) | **Damage workflow software plus satellite-data leads** | Pre/post imagery workflow and SAR damage-proxy methods, including 2023 Türkiye/Syria. The toolkit is **MIT**, but linked Maxar imagery/xBD/ARIA assets have independent rights and uncertainty. Register those underlying products separately, not the toolkit as raw data. | P0 |
| [CLIMADA-project/climada_python](https://github.com/CLIMADA-project/climada_python) | **Scientific model engine + real data API lead** | Hazard, exposure, probabilistic impact, forecast and uncertainty. Software GPL-3.0; API data described as CC BY 4.0 with data-specific metadata. Register **CLIMADA Data API v2**, not `climada_python` as one raw data source. | P0 |
| [CLIMADA-project/climada_petals](https://github.com/CLIMADA-project/climada_petals) | **Specialised hazard model extensions** | Wind, surge, wildfire and other hazards. Dependent on CLIMADA core; catalogue models and original forcing data separately to avoid misleading independence. | P1 |
| [Deltares/Delft-FIAT](https://github.com/Deltares/Delft-FIAT) | **Open raster/vector impact calculation code** | MIT-licensed method reference for asset-damage overlays, especially flood. Model input imagery/maps and damage functions require separate source-specific admission; already listed in prior repo gap audit, so no duplicate source entry. | P1 |
| [gem/oq-engine](https://github.com/gem/oq-engine) | **Seismic hazard/risk engine** | OpenQuake physical scenario, vulnerability and event-loss benchmark, existing OpenCatastrophe programme relationship. Software AGPL-3.0; tool is not source-event data. | P0 |
| [OasisLMF/OasisLMF](https://github.com/OasisLMF/OasisLMF) | **Insurance CAT engine** | OED exposure -> GUL -> insured -> reinsured loss. BSD-3-Clause code; do not duplicate Oasis model assets or reinterpret model run as validated CAT catastrophe loss. | P0 |
| [OasisLMF/ktools](https://github.com/OasisLMF/ktools) | **CAT simulation/financial kernel** | Event loss calculations, aggregation, financial module semantics and efficient streaming. Useful as a comparator, not an independent event catalogue. | P1 |
| [OasisLMF/ODS_OpenExposureData](https://github.com/OasisLMF/ODS_OpenExposureData) | **OED/ORD interoperability specification** | Format semantics for location, accounts, reinsurance and result perspectives, NOT a catalogue of insured locations. ODS specifications and code have separate CC0/BSD licensing where applicable. | P0 |
| [GFDRR/rdl-standard](https://github.com/GFDRR/rdl-standard) | **Metadata standard** | Hazard/exposure/vulnerability/loss semantics, useful to crosswalk our canonical source registry. The GFDRR Risk Data Library itself is already registered. | P1 |
| [GFDRR/thinkhazard](https://github.com/GFDRR/thinkhazard) | **Risk screening data + reference implementation** | The official API/downloads provide multi-peril hazard classes by administrative unit. Register **ThinkHazard scores** only; underlying hazard layers have their own rights. | P1 |
| [GNS-Science/riskscape](https://github.com/GNS-Science/riskscape) | **RiskScape shared project/configuration examples** | Reusable multi-hazard risk-method design and configuration, not proof that the risk engine itself or external source data are bundled under the same licence. Do not register as direct data. | P2 |
| [AsMagiic/hurricane-cat-model](https://github.com/AsMagiic/hurricane-cat-model) | **Synthetic educational implementation** | Useful small Python chain: HURDAT2 calibration, illustrative synthetic OED locations, storms, damage, per-occurrence XoL, YLT, AEP and OEP. No insurer exposure or calibrated true commercial portfolio. HURDAT2 itself is an upstream source, not original data from this repo. | P1 |
| [GeoNode/geonode](https://github.com/GeoNode/geonode) | **Geospatial data portal platform** | Layer publishing, permissions, metadata and discovery; not an individual source dataset. Register specific GeoNode layers only when authoritative and rights-qualified. | P2 |
| [inasafe/inasafe](https://github.com/inasafe/inasafe) | **QGIS impact estimation plugin** | Conceptual benchmark for spatial hazard–population/building overlays; not authoritative building locations or ground truth. Code GPL-3.0. | P2 |
| [mapaction/disaster-impact](https://github.com/mapaction/disaster-impact) | **Multi-provider ETL/benchmark research** | Code brings together GDACS, GLIDE, CERF, EM-DAT, IDMC, IFRC DREF and Charter and matches events conservatively by peril/country/date. Repo says notebook-oriented and partially manual; do not assume its harmonised file exists as approved/licensed redistribution dataset. Register distinct original providers, not a duplicate synthetic `MapAction event`. GPL-3.0 software. | P0 |
| [koala73/worldmonitor](https://github.com/koala73/worldmonitor) | **OSINT/real-time source discovery and monitoring** | Alert/status/cache architecture only. Its NASA EONET, Canada, NOAA, etc. upstream feeds are already covered by [World Monitor discovery](../../landscape/sources-worldmonitor-upstream-20261102.json). Do not duplicate; AGPL-3.0 code. | P1 |

## Why these eleven *new* provider products matter

| Newly registered original provider/product | Data layer | Hard boundary |
| --- | --- | --- |
| Montandon Global Crisis Data Bank | Event IDs, source correlation, hazard and humanitarian impact | Authenticated IFRC token; mixed upstream provider rights; duplicates reports from primary sources |
| CLIMADA Data API v2 | Multi-hazard event/footprint/model data | Product/scenario precision and upstream dependencies; 4 km is not building-scale exposure |
| ThinkHazard scores | ADM-level hazard priority and source-layer lookup | Categories are **not** ground motion, wind, damage or insured loss |
| Maxar Open Data disaster imagery | Pre/post optical event scenes | CC BY-NC 4.0; imagery provenance and event coverage not universal |
| xBD / xView2 | Labelled building damage / imagery pairs | Non-commercial dataset rights; damage labels are not cash or insured losses |
| NASA JPL ARIA damage proxy maps | Case-specific SAR event-change maps | Product and JAXA/partners rights; not confirmed building-level damage |
| IFRC GO event and reports API | Humanitarian event timeline / response | Visibility and third-party attachments; overlaps Montandon |
| UN OCHA CERF API | Humanitarian response allocations | Funding is not economic or insured loss |
| UNDRR DesInventar Sendai | National/local historical damage and disaster impacts | Country-specific licensing and reporting changes; successor DELTA |
| ADRC GLIDE identifiers | Stable link keys between event catalogues | ADRC discourages statistical secondary analysis; never equate ID with treaty occurrence |
| International Charter activations | Satellite activation/derived map discovery | Maps and raw image rights differ by provider and activation |

The 11 entries all have `candidate_status=evidence_checked`, `rights_review_status=not_reviewed`, `scientific_review_status=not_reviewed`, and `admission_status=not_admitted`; this means documentary discovery, **not** accepted source/model data. No data transfer, API rights, external bytes, database writes or scientific calibration are claimed.

## High-signal joint pilot: 2023 Türkiye/Syria earthquake sequence

The existing GEM GEID [event folder](https://github.com/gem/geid/tree/main/Europe/Turkey/20230206_M7.8_KahramanmarasGaziantep) specifically identifies `us6000jllz` and contains station, rupture, OpenQuake ground-motion and reported-damage materials. Its country impact CSV includes multiple source rows and **observation/access dates**, some following 6 February 2023 by weeks. A single GEID impact total may include the broader sequence; this cannot be assigned automatically to the M7.8 initial shock. The already-reviewed USGS origins `us6000jllz`, `us6000jlm1`, `us6000jlqa` are **three distinct earthquake catalogue events**, with unknown financial occurrence grouping.

Microsoft's [building damage tool](https://github.com/microsoft/building-damage-assessment) also documents 2023 Türkiye/Syria applications, with [NASA ARIA post-event SAR damage proxy](https://www.jpl.nasa.gov/images/pia25564-satellites-assess-earthquake-damage-in-turkey/) and Maxar/xBD type data as separate validation possibilities. **Caveat:** shared Maxar/ground-truth imagery, reporting agencies or statistical processing can make two apparent products non-independent. A later damage benchmark can assess physical plausibility, never retrospectively turn an old `updateTime` into an authenticated T0 forecast.

Next concrete scientific experiment: rights-review ONE GEID event sample and ONE genuinely independent damage observation at a frozen product vintage, report the support/mask and split training versus holdout, and compare to a bounded OpenQuake-based synthetic scenario. Do not claim actual insurer ground-up / post-event ultimate loss or regulatory capital.

## Source links and explicit licence evidence

- [Montandon authenticated API instructions](https://montandondata.org/get-started.html) and [Monty source inventory](https://ifrcgo.org/monty-stac-extension/model/sources/).
- [CLIMADA data licensing and suitability](https://climada.ethz.ch/climada-api/) and [Data API v2 docs](https://climada.ethz.ch/data-api/v2/docs).
- [ThinkHazard official licences and administrative hazard data](https://gfdrr.github.io/thinkhazardmethods/) and [API](https://gfdrr.github.io/thinkhazard/api).
- [Maxar on AWS registry with CC BY-NC 4.0 notice](https://registry.opendata.aws/maxar-open-data/) and [xBD original](https://xview2.org/dataset).
- [NASA JPL ARIA 2023 earthquake DPM](https://www.jpl.nasa.gov/images/pia25564-satellites-assess-earthquake-damage-in-turkey/).
- [IFRC GO situation-report metadata](https://go-wiki.ifrc.org/en/go-api/Data_dictionary_situation_report) and [Monty IFRC-DREF mapping](https://ifrcgo.org/monty-stac-extension/model/sources/IFRC-DREF/).
- [CERF API](https://cerfgms-webapi.unocha.org/), [UNDRR data](https://www.undrr.org/building-risk-knowledge/data), [DesInventar](https://desinventar-api.undrr.org/), [GLIDE disclaimer](https://glidenumber.net/glide/public/disclaimer.jsp), [Charter activations](https://disasterscharter.org/activations).
- [GEID explicit NC-SA licence](https://github.com/gem/geid/blob/main/LICENSE.txt), [event data and sources](https://github.com/gem/geid/tree/main/Europe/Turkey/20230206_M7.8_KahramanmarasGaziantep/1_Impact).
