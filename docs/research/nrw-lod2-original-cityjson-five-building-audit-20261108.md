<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NRW LoD2 original CityJSON five-building access and attribute-coverage pilot

**Source observation:** 2026-11-08, read-only bounded original HTTP source response.  
**Canonical candidate:** [NRW LoD2 OGC API source](../../landscape/sources-nrw-lod2-ogcapi-20261108.json), still **not admitted** to CAT modeling.  
**Publisher:** Geobasis NRW / Bezirksregierung Köln.  
**Source license evidence:** [official AdV-MIS metadata](https://www.distributions.informationgrid.eu/trefferanzeige?docuuid=bde30228-a718-45a8-9518-1e17e47c0187) explicitly states **Datenlizenz Deutschland – Zero 2.0**, allowing unrestricted use; [GovData product card](https://data.gov.de/suche/daten/3d-gebaudemodell-nw-lod28b9df) separately identifies the OGC API Features delivery. A small public query is not a CAT scientific admission, whole-catalogue throughput authorization or proof of source currency.

## Original fixed request

The exact research sample was read once at the following URL; no unbounded pagination, authentication, bulk export or whole-NRW request was used:

```text
https://ogc-api.nrw.de/3dg/v1/collections/building/items?f=cityjson&limit=5&bbox=6.9500,50.9300,6.9520,50.9320
```

This is a fixed small *study area*, not an address linked to an insurer policy. The original HTTP representation was `application/city+json`, **9,038 response-body bytes**. Original source bytes and their building IDs, address attributes and geometry are **not checked into Git**. The fixed offline QA script computes a SHA-256 receipt when run on exact original bytes (the historical web-tool request did not execute that Python command).

### Verified original-response structural counts

| Field / property | Observation | Interpretation |
| --- | ---: | --- |
| CityJSON version | 1.1 | OGC 3D JSON document, not GeoJSON |
| Coordinate reference | OGC CRS84h | Source's *CityJSON output* reference, different from collection's storage CRS EPSG:5555 |
| Root `Building` objects | **5** | Provider sample, not population census |
| Associated `BuildingPart` objects | **3** | Do not double-count as distinct insured buildings |
| Quantized 3D vertices | **72** | No geometry published in repository |
| Root Building `measuredHeight` populated | **4/5** | Height difference; not storeys, insured value or vulnerability |
| Root Building `roofType` populated | **4/5** | Official roof-form code; **not** roof-covering material |
| Root Building `storeysAboveGround` populated | **0/5** | Not present in this tiny sample; no statewide inference |
| Root Building `function` populated | **0/5** | Not present in this tiny sample; not proof of complete absence |
| BuildingPart `measuredHeight` and `roofType` populated | **3/3 each** | Nested properties must not replace missing whole-building values without a declared aggregation rule |
| Geometry type observed | `Solid` | Additional formats must be reviewed separately |
| Spatial intersection with requested bbox | **5/5 Building roots**, including their associated parts | Bounds may cross the small AOI edge; whole-building containment was not required |

**Important:** The initial exploratory one-building access had an inconsistent apparent location in a preliminary inspection. The five-building original query was independently decoded and per-root checked; it intersects the requested AOI for all five roots. This does not prove that all possible bbox queries will be honored correctly. The executable gate below fails closed when a root violates the bbox.

No claims are made about representativeness, statistical precision or insurer exposure based on five convenience-selected urban buildings.

## Executable aggregate-only evidence gate

```sh
python -m unittest discover -s tests -p 'test_assess_nrw_lod2_cityjson_sample_v0.py' -v
# ONE exact source call if permitted by the executing environment:
python scripts/assess_nrw_lod2_cityjson_sample_v0.py --live
# Or offline, using an independently acquired provider file stored OUTSIDE Git:
python scripts/assess_nrw_lod2_cityjson_sample_v0.py --offline-json /private/original-nrw-cityjson-response.json
```

The checker enforces all of: fixed request URL; at most **5** root Buildings; HTTP response up to **65,536 bytes**; no redirects, credentials, arbitrary URLs or auto-pagination; CityJSON 1.1, OGC CRS84h and a finite 3D transform; valid referenced geometry vertices and associated building parts; every Building intersecting (not necessarily contained by) the selected query bbox; expected MIME and only aggregate evidence output. There is no automated download into Git or into an insurer database. Even if the checker succeeds, `model_ready=false`.

## Consumer boundaries and next step

1. Derive a **representative** stratified attribute-coverage sample across varied NRW settlement structures before inferring any NRW-wide missingness or building classes; record selected sampling mechanism rather than optimizing a small convenience AOI.
2. Decode official AdV roof form and building function code lists; make unknown and multiple BuildingPart values explicit instead of defaulting to a generic type.
3. Establish building/policy granularity and event-time vintage independent of 2025 contemporary footprint geometry. The R+V 2025 OED staging PR is *synthetic* and not geolocated.
4. Only after separate peril, value, event, vulnerability, policy and treaty source gates should any provider building features be combined with wind/hail/flood and native Oasis GUL/IL/RI/OEP/AEP.

This evidence is **one tiny real-world original-response structural test**, not an insurer portfolio and not a German production CAT calibration.
