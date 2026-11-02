<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WFP ADAM OGC and JMA best-track original-source preflights (2026-11-02)

**Boundary:** provider documentation checked, bounded **offline validators** implemented, synthetic regression coverage added; **no live provider-response receipt, source-data download, dataset rights clearance, model admission, loss benchmark, or Neon import**. These are candidate research operations, not enabled source-access contracts.

## ADAM — exact 13-collection surface

The WFP ADAM [API reference](https://docs.adam.geospatial.wfp.org/developers/reference/api/) states its public read-only OGC API base is `https://api.adam.geospatial.wfp.org/api` (currently documented as `v1.0.0-alpha`), no account or key, GeoJSON and tiles. [Official collections reference](https://docs.adam.geospatial.wfp.org/developers/reference/collections/) describes thirteen named collections:

| Module | Collection names |
| --- | --- |
| Earthquake (1) | `adam.adam_eq_events` |
| Flood (4) | `adam.adam_fl_events`, `adam.adam_fl_alerts`, `adam.adam_fl_alerts_mom_forecast`, `adam.adam_fl_glofas_gauges_forecast` |
| Tropical cyclone (8) | `adam.adam_ts_events`, `adam.adam_ts_tracks`, `adam.adam_ts_buffers`, `adam.adam_ts_nodes`, `adam.adam_ts_disturbance_events`, `adam.adam_ts_disturbance_tracks`, `adam.adam_ts_disturbance_buffers`, `adam.adam_ts_disturbance_nodes` |

**Important upstream dependence:** See [WFP's authoritative original source listing](https://docs.adam.geospatial.wfp.org/developers/reference/data-sources/), [flood methodology](https://docs.adam.geospatial.wfp.org/users/hazards/floods/) and [cyclone methodology](https://docs.adam.geospatial.wfp.org/users/hazards/tropical-storms/).

- Earthquakes: GDACS + USGS, including ShakeMap. ADAM's population impact is an **estimate**, not independent observed insured damage.
- Floods: GloFAS/GeoGLOWS forecasts, ECMWF rainfall, NOAA VIIRS flood observations, NASA GPM IMERG rainfall, JRC Global Surface Water climatology, Copernicus EMS, FloodScan, CSDMS, and processing with GEE/GCS. Some products are predicted or model-derived while others are observed/classified. Distinguish **onset time, footprint acquisition, upstream sensor, model run, analysis version and event date**.
- Cyclones: JTWC/NHC bulletins, ECMWF precipitation, GDACS event crosswalk. Forecast track and wind buffer polygons **are not measured wind footprints**.
- Reference layers: LandScan population, global cropland, FAO GAUL boundary identifiers, OSM/OCHA infrastructure. **Do not assume building insurance values or exact exposure**.
- Already existing discovery sources include `ec-jrc.global-surface-water.1984-2024`, `nasa.gpm.imerg.v07b`, `noaa.ncei.ibtracs.v04r01` and source catalogue GDACS/GloFAS/USGS. Do not add duplicate identities for their reuse by WFP.

The `/api/collections` response can be captured **outside Git** after provider access/rights review with bounded query and audited tool. To check an independently captured catalogue file offline:

```bash
python research_runners/wfp_adam_collection_catalogue_preflight_v0.py \
  /secure/source-metadata/adam-collections.json \
  --expected-sha256 PINNED_SHA256_FROM_INDEPENDENT_RECEIPT \
  --out /tmp/adam-catalogue-profile.json
```

The offline preflight enforces strict JSON, exact documented names/count, metadata limits, complete pagination and SHA-256 source identity; only an aggregate profile is emitted. A failed match means **review changed upstream catalogue**, never silently drop or invent a collection. It does not make API requests, download features, assess individual event provenance or grant rights.

**Live status:** The local Linux runtime cannot resolve these provider hosts, but an external read-only retrieval successfully fetched the original provider responses. The source-byte details and catalogue drift are documented below. The documentation's "free" and public API status is **not** blanket third-party underlying data redistribution or commercial model permission. WFP source attributes and individual original-data terms need separate review.

## JMA — original best-track ASCII preflight

The official [RSMC Tokyo best-track page](https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/besttrack.html) provides a 1951–2026 ZIP, a current-year text file, a [field-by-field original format](https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/Besttracks/e_format_bst.html) and a revision-history CSV.

- Original format has `66666` header records with a count of subsequent analysis lines; observations are ASCII `YYMMDDHH`, grade, latitude/longitude in **0.1 degrees**, pressure in **hPa** and maximum sustained wind in **knots**. Geographic and temporal values need a basin-aware consumer.
- `research_runners/jma_besttrack_source_preflight_v0.py` takes an original text file whose SHA-256 was **pinned separately** and tests format, storm/header count, increasing analysis time, valid dates, units and nonnegative/geographic ranges. It emits **aggregate counts and a SHA**, not third-party storm IDs, positions or full track data.
- Zero or missing max-wind values are marked as missing/unknown, **not proof of no wind**. A best track is post-event agency analysis, not an observed wind swath, financial loss or independent cross-check of all tracks in IBTrACS, which may already incorporate JMA.

```bash
python research_runners/jma_besttrack_source_preflight_v0.py \
  /secure/original-provider/bst2026.txt \
  --expected-sha256 PINNED_SHA256_FROM_INDEPENDENT_RECEIPT \
  --out /tmp/jma-besttrack-profile.json
```

Do not use `sha256sum(original_file)` from the same unverified input as proof of **independently** pinned original identity. Retain exact provider URL, retrieval date, version, original bytes and revision-history identity outside this repository under approved retention policy. Do not commit raw downloaded JMA text/ZIP without rights clearance.

## Independently fetched live metadata/source-byte evidence — 2026-11-02

Public original-provider HTTP responses were read through an external read-only web retrieval service. **These results validate access and response shape at that instant only**; a separately pinned original-byte receipt is required for any future downstream reuse, and raw provider bytes were **not committed**.

| Direct original URL | Response evidence | Source-byte SHA-256 |
| --- | --- | --- |
| [WFP ADAM OGC collections](https://api.adam.geospatial.wfp.org/api/collections) | HTTP body as `application/json`; **18,704 bytes**, `numberMatched=12`, `numberReturned=12`, 12 collection objects, one `self` link, no `next` page | `dafb20f002df7af7ca3e97487416f7cc65be9c6da632eedbb4630eb6598e6ace` |
| [JMA RSMC Tokyo bst2026.txt](https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/Besttracks/bst2026.txt) | `text/plain` original CRLF ASCII, **44,034 bytes**; 537 lines, **13 header records and 524 analysis records**; 341 records with positive max-wind code; latest provider header revision `20261028` | `35c90ced9691fc9b4afffa09cb54ba3f2e0b0c786007a73e6b020acf6fca642f` |

The byte digests were calculated over the returned original body (not a copied Markdown/web display). JMA source lines were independently inspected for the documented 72-column header, counts, date order, grade, latitude/longitude and pressure/wind bounds: **no structural violations observed**. This is an independent read-only check of an original-source response, **not** an execution of the checked-in Python runner against captured provider bytes.

### Confirmed WFP ADAM documented-versus-live discrepancy

The [official WFP reference](https://docs.adam.geospatial.wfp.org/developers/reference/collections/) describes **13** collections, but the original public endpoint returned **12** with internally consistent result counters. All documented IDs except `adam.adam_ts_disturbance_events` were present. That is one missing **disturbance event collection**, not proof that the cyclone module itself is unavailable; forecast tracks/buffers/nodes still appear. This is **not** a pagination omission, since `numberMatched` and `numberReturned` are both 12 and there is no `next` link.

The offline strict validator remains fail-closed: `inspect_adam_catalogue_bytes` rejects this difference. The explicit `--diagnose-only` option records the 12/13 discrepancy and reports the absent ID, but exits with **status 3** and sets `source_admitted_for_model_use=false`. Do **not** silently change the reference to 12, invent a missing collection, or allow model use because a vendor API responds. Request provider clarification on intended retirement/visibility, retain both API and documentation identities, then consider a bounded catalogue-contract version.

```bash
python research_runners/wfp_adam_collection_catalogue_preflight_v0.py \
  /secure/source-metadata/original-adam-collections.json \
  --expected-sha256 dafb20f002df7af7ca3e97487416f7cc65be9c6da632eedbb4630eb6598e6ace \
  --out /tmp/adam-drift-diagnostic.json --diagnose-only
# Expected: nonzero (3) with explicit reference mismatch, if input matches receipt.
```

For JMA, the retrieved file is mutable; the provided source-byte digest identifies **only this particular 44,034-byte response**. Preserve source retrieval time, bytes, SHA and publisher revision metadata separately from the claim of current archive completeness. This research report must not serve as a dataset licence grant.

## Offline regression / next acceptance gates

```bash
python -m unittest discover -s tests -p 'test_jma_besttrack_source_preflight_v0.py'
python -m unittest discover -s tests -p 'test_wfp_adam_collection_catalogue_preflight_v0.py'
python scripts/check_all.py
```

**Next causal actions:** (1) reconcile actual CI results and fix all test errors; (2) complete WFP ADAM rights/terms and one safe bounded source collection discovery receipt with no source-data persistence; (3) capture version-pinned JMA original source SHA and revision history for a chosen release; (4) compare independent JMA/HKO/JTWC original track estimates with NOAA IBTrACS only after resolving common source lineage and intensity averaging conventions; (5) distinguish hazard footprint, exposure and impact estimate before any model input approval.
