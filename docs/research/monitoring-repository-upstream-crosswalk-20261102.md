<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Monitoring-repository upstream source crosswalk — 2026-11-02

**Scope:** Source discovery for catastrophe event intelligence, post-event impact validation and exposure context. Repository README/docs and identified provider pages were inspected on 2026-11-02. This is a **discovery and provenance map, not a data admission, executable API proof, licence clearance, production-readiness claim or permission to persist third-party data**. Source-level original rights and model fitness remain independent gates.

For the follow-up **code-level source sweep across all twelve shortlisted repositories**, see [monitoring-repositories-code-source-sweep-20261102.md](monitoring-repositories-code-source-sweep-20261102.md). The canonical registry now has **23** candidates: 12 first-pass entries and 11 additional code/provider-discovery entries.

## Registry link and anti-duplication rule

Canonical **new provider candidates**: [`landscape/sources-monitoring-repo-upstreams-20261102.json`](../landscape/sources-monitoring-repo-upstreams-20261102.json), with deterministic Markdown view. Existing World Monitor discovery: [`landscape/sources-worldmonitor-upstream-20261102.json`](../landscape/sources-worldmonitor-upstream-20261102.json). Existing provider candidates in `landscape/sources*.json`, including GDACS, NASA EONET, UNDRR DELTA, USGS ComCat and NOAA NHC, **must not be duplicated**. A dashboard/tool source can suggest a feed but does not make that third-party feed rights-cleared or scientifically independent.

## Upstream inventory from the reviewed repositories

| Open-source code/research project | Upstream sources explicitly described by its documentation | Potential CAT use and caveat |
| --- | --- | --- |
| [World Monitor](https://github.com/koala73/worldmonitor) | See existing [World Monitor upstream discovery](../landscape/sources-worldmonitor-upstream-20261102.json): NASA EONET, Canadian wildfire and quake agencies, NOAA NHC, NWS, HKO, IMD, Environment Canada, WMO SWIC, ReliefWeb, IOM DTM, UNHCR, IMF PortWatch, Global Energy Monitor, ENTSO-E, OpenAQ, NSIDC and World Bank | Existing candidate provenance, do not register twice |
| [GlobeWatch](https://github.com/lumixed/globewatch) | USGS, BMKG, JMA, GDACS, NASA EONET, NOAA tsunami bulletins, US NWS weather alerts, OpenSky, Digitraffic ship AIS, FAA airport status, TfL/LTA cameras, CelesTrak TLE, Launch Library, ISS position, GDELT news; optional panel feeds CoinGecko, NOAA planetary K-index, BBC/Al Jazeera/NPR RSS, CISA KEV, US State Dept travel advisory | **High:** BMKG/JMA secondary quake cross-check and cross-agency dedup. **Lower:** transport, cameras, crypto, satellites, generic news. Geography and quotas limited. GDELT GEO described by project as retired/non-operational; do not assume geolocated article events |
| [Terra Watch](https://github.com/cifertech/Terra-Watch) | NASA EONET v3, USGS earthquakes, NOAA NHC, NASA GIBS satellite visualization, GDELT headlines, Wikipedia event context; Cesium/Esri imagery basemaps | **High:** satellite timeline as visual event context, but GIBS tiles are not numerical hazards or verified damage. Most event feeds overlap existing entries |
| [WorldMirror](https://github.com/houalexdev/WorldMirror) | GDELT, USGS, NASA EONET, NASA FIRMS, OpenSky, NOAA Alerts, ACLED, Polymarket, FAA, NetBlocks/IODA, USGS Volcano, 186 RSS feeds; monthly strategic layers include UCDP, UNHCR, nuclear facilities, ports, pipelines, submarine cables, mineral sites and AI data centers | **High to medium:** critical-infrastructure interruption hypotheses and hazard-event monitoring. Exact data provenance, freshness and licence of each of 15 strategic layers are **not proven** by umbrella repository claims. ACLED/other geopolitical feeds are not catastrophe loss data |
| [Crisis Compass](https://github.com/Muhit-1/Crisis-Compass) | Open-Meteo spatial weather tiles, point forecast and geocoding; NASA EONET, USGS, GDACS. Selectable DWD ICON, ECMWF IFS, Météo-France ARPEGE and CMA GRAPES forecast models; map basemap services | **High:** multi-model forecast comparison and archived run/lead-time studies. Forecast/interpolated fields are not observed hazard or independent from their upstream model inputs |
| [MapAction Disaster Impact](https://github.com/mapaction/disaster-impact) | GDACS REST, IDMC IDU REST, GLIDE scrape, CERF scrape, International Charter activations scrape, manual EM-DAT and IFRC-DREF. Source harmonisation and matching by hazard/country/time | **Very high:** historical event crosswalk and response/impact context. Event matching ±7 days may merge distinct concurrent events or miss slow-onset/multi-country events. The README explicitly reports some feeds manual and funding-stalled ETL |
| [DELTA Resilience](https://github.com/unisdr/delta) | National/local hazard and impact records entered/owned by participating countries; legacy DesInventar DIX importer, not a bundled universal live upstream feed | **Very high:** disaster loss and damage semantics; use only original national accepted records with country, time, quality and usage rights preserved. Already in operational disaster services shard |
| [Ancoda Atlas](https://github.com/ancoda-labs/Ancoda-Atlas) | USGS, Open-Meteo weather and air quality, NASA FIRMS, ReliefWeb with HDX fallback; Nepal BIPAD river gauges/events/notices; Nepal government and OPMCM operational pages; OWID CO2 and national news/RSS | **High:** Nepal BIPAD national hazard/impact registry and cross-peril flood–landslide context. Government reports and user/community information may include personal data and are excluded without privacy review. Ancoda code AGPL; not a data licence |
| [FIRESTORM news data](https://github.com/Deasus/firestorm-news-data) | GDELT DOC 2.0, GDELT GEO 2.0, GDELT Disasters/ReliefWeb, InciWeb RSS, Google News RSS, optional GDELT BigQuery | **Medium:** wildfire awareness and incident text. Headlines, geotagged mentions, reporter volumes, and automatic urgency are not independently confirmed hazard footprints. The GDELT GEO endpoint must be re-probed before implementation; GlobeWatch reports failures |
| [Emergency Centre](https://github.com/Ninezel/emergency-centre) | No mandatory built-in live feed; adapters for US NWS weather/alerts, UK Met Office forecasts and warnings RSS, England Environment Agency flood API and USGS seismic | **High:** UK warning + river telemetry feed adapters and source-health/staleness patterns. Polling a JSON briefing does not certify the upstream data |
| [Ushahidi Platform](https://github.com/ushahidi/platform) | User-configurable submitted SMS, social posts, RSS and email; no universal named open observation feed | **Medium:** volunteered, geocoded impact reports if explicit deployment/dataset, consent and rights exist. Severe sampling, privacy and verification bias |
| [Sahana Eden](https://github.com/sahana/eden) | Humanitarian/emergency application framework; deployments choose their own inventories and external systems | **Medium:** disaster reporting process and operational data models; not itself a globally reusable data source |

### Primary data families and registry decisions

**Already represented (do not re-add):** GDACS, EONET, NHC operational GIS, NWS CAP, ReliefWeb, UNHCR, IOM DTM, UNDRR DELTA, USGS ComCat, NASA FIRMS, Global Energy Monitor, IMF PortWatch, and other existing `landscape` identities. A candidate is not the same as admission.

**First-pass discovery entries (12 of 23):** GLIDE IDs, IDMC IDU, UN CERF project API, IFRC GO/DREF appeals, International Charter activations, Nepal BIPAD, England Environment Agency flood monitoring, UK Met Office severe warning API, Open-Meteo model/single-run API, BMKG Indonesia earthquake feeds, JMA earthquake/volcano XML, and NASA GIBS visualizations. They are recorded with `evidence_checked` and `not_admitted` and are **not** installed as pipelines.

**Investigate next:** BMKG operational versus fully reviewed historical catalogue, Japan and Indonesian original bulletin retention, NASA GIBS quantitative source-product mapping, InciWeb incident metadata, public national damage/impact datasets surfaced by Charter and DELTA, exact sources for WorldMirror's infrastructure features. Prioritise original sources over feed mirrors.

### Scientific and rights traps

1. **Events versus damage:** GLIDE and GDACS event identifiers, warning footprints, humanitarian funding, displacements and GDELT article volumes do not measure insured loss. Use typed roles and never train loss magnitudes on these as if they were claims.
2. **Independent validation:** USGS quoted by four dashboards is still one underlying source. Separate primary agency observations, model-derived forecast/nowcast, media references, curated operational catalogues, surveys and claims. Resolve time/geometry/version and provenance.
3. **Temporal integrity:** Preserve original event, issuance, ingestion and revision time separately. For alerts keep lifecycle; for model forecasts preserve run/lead time; for national reports pin survey/coverage window. Do not reinterpret a currently missing alert as a confirmed zero.
4. **Rights:** Open-source dashboard code licences (MIT/GPL/AGPL) never grant rights to source datasets, satellite imagery, news, casualty, beneficiary, phone, household or response records. No external bytes committed; unknown rights remain blocked.
5. **Source quality:** GlobeWatch describes GEO API failure; MapAction labels several source workflows manual and its matching experimental. Provider-side endpoint or API documentation is not a successful production probe.
6. **Geospatial meaning:** Forecast polygons, warning zones, active fire hotspots, reported incidents, event centroids and damage masks have different semantics. Never use an alert area as an observed physical footprint.

## Proposed OpenCatastrophe integration

`source -> provider event identity/version -> canonical event crosswalk -> authoritative hazard footprint/observation -> permitted exposure join -> modelled gross/net loss -> independent post-event comparison`.

First implement **source-access/documentation probes** for Environment Agency (warning/level schema), Nepal BIPAD (public non-personal flood/river endpoints), and BMKG/JMA; next resolve GLIDE/IDMC/Charter/IFRC/DELTA historical event identities. In downstream risk and loss models, compare **independent observed impact** and modelled loss with uncertainty and data-lineage flags, not an unverified auto-generated 'ground truth'.

### Inspection boundary

Verified repository README/provider documentation only; no bulk upstream downloads, no tokens, no sample data in Git and no direct rights/admission decision. Full live endpoint validation, exact field schema and licence review are future access/admission steps.
