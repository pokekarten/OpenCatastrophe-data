<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Worldwide original source sweep: 2026-11-02

**Status: research only, no scientific/rights admission.** This audit cross-references 48 canonical `landscape/sources*.json` shards on public main, the separate open monitoring-source PR #1141, and public primary-provider catalogs. The new source identities are in [the canonical JSON discovery register](../../landscape/sources-global-deep-research-20261102.json), with [the generated Markdown projection](../../landscape/sources-global-deep-research-20261102.md). The new shard has **17 entries**, no external data bytes, claims or model inputs.

## Research execution / original directories

Search workstreams: Exa deep searches covering (1) original seismology/tsunami and impacts, (2) global flood extent, (3) building stock/critical infrastructure, (4) multi-peril drought/heat/fire, and (5) metadata catalogs. Independently queried original publishers and checked the current GitHub trees/source files of:

- [Climate Risk STAC](https://github.com/climate-risk-data/climate-risk-stac): `csv/hazard.csv` has original source/product/format/license/asset-link rows. The [peer-reviewed 2026 publication](https://doi.org/10.1016/j.envsoft.2026.106906) describes 214 metadata entries and multiple hazards/exposure/vulnerability categories, **not** 214 verified new sources. This meta-index is complementary to our global canonical source landscape.
- [UNICEF Global Child Hazard Database](https://github.com/unicef/GCHD): `hazard_data/README.md` and per-hazard notebooks map the 100 m age-specific population layer to observed and modeled hazard inputs. Assets live outside Git on Google Earth Engine under UNICEF namespace. JRC flood, GIRI, FAO ASIS, TerraClimate, ERA5, NASA FIRMS, ACAG PM2.5 and UNCCD sand/dust are the useful upstreams to evaluate. River/coastal flood, storms, heat, drought, wildfire and air quality are **not independent observed losses**.
- [ESIP Trusted Data Now](https://github.com/ESIPFed/disasters-trusted-data-now): `data.json` inventories provider links with `lastChecked` and `accessibilityStatus`. Accessibility checks **do not** establish data identity, historical coverage, scientific quality or reuse rights.
- [UNICEF GCHD Dashboard](https://github.com/unicef/GCHD-dashboard): technical documentation points to GEE-hosted outputs and country/age exposure methodology, not independently surveyed building loss.
- Previously checked 12 monitoring/response repos documented in [PR #1141](https://github.com/pokekarten/OpenCatastrophe-data/pull/1141): [World Monitor](https://github.com/koala73/worldmonitor), [GlobeWatch](https://github.com/lumixed/globewatch), [Terra Watch](https://github.com/cifertech/Terra-Watch), [WorldMirror](https://github.com/houalexdev/WorldMirror), [Crisis Compass](https://github.com/Muhit-1/Crisis-Compass), [MapAction disaster-impact](https://github.com/mapaction/disaster-impact), [UNDRR DELTA](https://github.com/unisdr/delta), [Ancoda Atlas](https://github.com/ancoda-labs/Ancoda-Atlas), [FIRESTORM](https://github.com/Deasus/firestorm-news-data), [Emergency Centre](https://github.com/Ninezel/emergency-centre), [Ushahidi](https://github.com/ushahidi/platform) and [Sahana Eden](https://github.com/sahana/eden).

The twelve monitoring repositories were reviewed at tree/source-adapter/documentation level in the preceding PR; this pass adds four additional trees/source registries and original provider verification. **Neither review constitutes exhaustive line-by-line code reading of every large repository**. Public search/crawl results are discovery evidence, not an operational API receipt.

## Source table: meaningful missing products

| Group | New distinct candidates | Why they matter | Conditions / risk |
| --- | --- | --- | --- |
| **Building vintage and economic exposure** | DLR **WSF Tracker** 2016–2026, DLR **WSF 3D Material Stock** | 10 m settlement growth and 90 m estimated material composition; improve vintage and replacement-cost assumptions | DLR states CC BY 4.0 per product; remote-sensing grids are not individual building records or insured replacement costs |
| **Independent historic flood observation** | JRC **GFDS v2** | Long 1997–present passive-microwave flood/water change over basins, different sensor/method from existing Sentinel-1 GFM | Coarse pixel scale; multi-sensor systematic half-pixel offsets; cannot be treated as inundation depth or observed building damage |
| **Agricultural drought and climate covariates** | FAO **ASIS** (1984+, approx 1 km) and **TerraClimate v1.1** (~4 km monthly) | Drought events, crop stress, antecedent precipitation/soil-moisture contexts, cross-peril hazard | FAO GEE access may require request; TerraClimate now depends on ERA5 anomalies; not independent of upstream reanalysis |
| **Regional earthquake source and impact** | INGV **CPTI15 v4** and **DISS v3.3.1** | Italian historical earthquakes and original seismogenic rupture-source parameters | Different from worldwide ComCat/GEM, but shared ESHM inputs and fault sources require lineage check; archive original release and uncertainty |
| **Coastal tsunami validation** | INGV **ITED v1**, NOAA NCEI **tsunami runup/gauge/survey point layers** | Quantitative/historical local tsunami effects and surveyed/gauge observation locations | Observation point ≠ inundation polygon; surveys may be located at nearby populated place, vary datum/precision, are biased by event |
| **Indonesia multi-hazard and events** | BNPB **InaRISK hazard/vulnerability maps** and **DIBI-labeled 2015–2024 hydrometeorological administrative wet/dry layer service** | High geographic value for river/flash floods, seismic, tsunami, volcano, drought, landslide and fire; DIBI-labeled map currently exposes provincial/district polygons, not proven event rows | ArcGIS MapServer/ImageServer service catalogs verified as public; DIBI service ?f=pjson verified layers 0 Provinsi_basah_kering and 1 Kabupaten_basah_kering as EPSG:4326 polygon maps, not event-level loss observations. Per-layer fields and licences remain unchecked |
| **Linked source indices and risk taxonomies** | **Climate Risk STAC v1**, **UNICEF GCHD**, **UNDRR Datum**, **UNEP/CDRI GIRI**, **ESIP Trusted Data Now**, **UNDRR PreventionWeb global risk collection** | Substantially broaden long-tail discovery and harmonize all-peril classifications | Source indexes, composite model outputs or 3rd-party portals are not direct asset/loss truth; do not count their referenced datasets twice |

### Explicit duplicate avoidance across main and open PRs

Original providers or products **already registered** on main: `gem.geid.2026` (GEM Global Earthquake Impact Database); `gem.global-exposure-model.v2026.0.0` (some tiers **CC BY-NC-SA**, commercial restricted); `copernicus.cems.gfm.v4.1.1`; `nasa.opera.dswx-hls.v1`; `nasa.opera.dswx-s1.v1`; `nasa.gpm.imerg.v07b`; `geoglows.rfs.v2.global-discharge`; `noaa.ncei.global-historical-tsunami` (events, not the new runup observation layers); `noaa.ncei.ibtracs.v04r01`; `dlr.wsf.2019`, `dlr.wsf.evolution.1985-2015`, `dlr.wsf.3d.v02` (but **not** the new Tracker or Material Stock). Existing wildfire/air-quality and natural-hazard products remain in their original shards.

PR #1141 contains 23 additional monitoring-derived candidates including WFP ADAM, JMA RSMC tracks, NOAA tsunami alerts, USGS volcano, Cloudflare, etc. This branch does **not** duplicate those identities. PR #1144 separately owns NASA GFWED fire-weather and Smithsonian GVP v5.4; PR #1132 owns GTSM ERA5-E and other coastal source families. Do not fork or alter those files for this source sweep.

### Immediate technical work after discovery

1. **Make one actual original source useful without jumping rights gates.** Probe DLR `WSF_TRACKER` STAC `/collections/WSF_TRACKER` for CRS/extent/temporal source identity, then one bounded item metadata operation; preserve timestamps and return only receipts, not COG bytes. Distinguish update cadence advertised biannually from STAC composite-type `P1Y`.
2. **JRC GFDS:** verify single-sensor vs merged product, exact grid/origin, resolution, missing-water masks, timestamp, rights. Scientific challenge against existing CEMS GFM must account for resolution, point spread function and provider shared ancestry.
3. **Italy:** create exact-source DISS v3.3.1 GeoJSON SHA/geometry receipt, and separately CPTI15 v4 FDSN temporal/parameter schema. ITED OGC point runup observations can be a powerful *independent observation* of tsunami arrival/runup in contrast to historical event catalogs.
4. **Indonesia:** inspect InaRISK metadata and DIBI layer **attribute fields** only; initial DIBI map-level metadata shows administrative wet/dry classification polygons rather than confirmed individual disaster events. Determine return-period semantics and per-layer rights before executing any spatial/event queries.
5. **Drought:** FAO ASIS imagery WMTS and TerraClimate original monthly netCDF access-contract reviews; keep FAO land-cover/season basis and TerraClimate ERA5 lineage.
6. **Index expansion:** use the Climate Risk STAC `csv/hazard.csv` as a *candidate discovery* document, crosswalk provider/product and dataset version, then hand-pick originals not represented in the 48 canonical landscape shards. Exclude unlicensed rehosts and models derived wholly from sources already registered.

## Outcome

The repository receives 17 carefully distinct candidate source families in the canonical landscape, plus evidence and action order. **No original data has been acquired here; no source was admitted into a CAT model, no insurer loss generated, no existing shared files overwritten and no Neon rows modified.** The canonical JSON governs this discovery; Markdown is a deterministic projection. A successful CI contract is necessary but not evidence of data licensing or hazard/loss science.
