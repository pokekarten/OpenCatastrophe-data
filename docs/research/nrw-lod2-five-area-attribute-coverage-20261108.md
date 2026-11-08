<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NRW LoD2 — bounded five-area original CityJSON attribute diagnostic

**Observation:** 2026-11-08.  
**Scope:** Five small convenience windows across NRW, 5 first-returned `Building` objects per request, **not a probability sample**, insurer-specific exposure or a state-wide estimate.  
**Canonical source identity:** [NRW OGC API Features](../../landscape/sources-nrw-lod2-ogcapi-20261108.json). **Source status remains not_admitted; model_ready=false.**  
**Provider / licence evidence:** [Geobasis NRW / Bezirksregierung Köln](https://ogc-api.nrw.de/3dg/v1/collections/building); official [AdV metadata](https://www.distributions.informationgrid.eu/trefferanzeige?docuuid=bde30228-a718-45a8-9518-1e17e47c0187) and GovData identify `Datenlizenz Deutschland – Zero 2.0`. Product licensing is not proof of geometry/vintage validity, unrestricted bulk API rates, or insurer-model calibration suitability.

## Exact read-only original observations

Each provider request used exactly `f=cityjson&limit=5&bbox=<west,south,east,north>` and yielded `application/city+json`, CityJSON **1.1**, CRS **OGC CRS84h**. The service advertises EPSG:5555 as a **storage** CRS; it must not be substituted for the **output** CRS84h. No automatic pagination, city-wide bulk extraction, insurer addresses, original features, external asset bytes, or raw geometries entered Git.

| Study area | Four-ordinate bbox, lon/lat | Original bytes | Building roots | BuildingParts | Vertices | Root roofType | Root measuredHeight | Root missing with part-level roofType and height |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Köln | `6.9500,50.9300,6.9520,50.9320` | 9,038 | 5 | 3 | 72 | 4 | 4 | 1 |
| Münster | `7.6250,51.9600,7.6290,51.9640` | 18,941 | 5 | 10 | 197 | 2 | 2 | 3 |
| Dortmund | `7.4610,51.5120,7.4650,51.5160` | 14,009 | 5 | 4 | 152 | 3 | 3 | 2 |
| Schleiden (Eifel) | `6.4740,50.5290,6.4800,50.5340` | 6,634 | 5 | 0 | 60 | 5 | 5 | 0 |
| Meschede (Sauerland) | `8.2770,51.3480,8.2830,51.3530` | 13,264 | 5 | 7 | 123 | 3 | 3 | 2 |
| **Total observed** | Five predeclared area windows | **61,886** | **25** | **24** | **604** | **17** | **17** | **8** |

All **24/24** `BuildingPart` objects had their own `roofType` and `measuredHeight` fields populated. None of the **25/25** top-level `Building` objects had `storeysAboveGround` or `function` populated in these responses. All 25 root-associated transformed geometry envelopes **intersected** their requested bbox and all listed BuildingParts had a root parent. Intersection is not whole-building containment; provider geometry may extend beyond the requested window.

**Critical meaning:** 17/25 is **attribute presence in five convenience API samples**, *not* a NRW-wide completeness estimate or a scientifically calibrated roof-type prior. The eight other main buildings have values on associated building parts, but a building may have multiple roof types/heights. Neither a single roof classification nor a default value is inferred for those eight. Rooftop form is distinct from roofing material, roof integrity, code compliance and wind vulnerability.

The API returned one `Building` with any number of associated `BuildingPart` objects. **Do not sum 24 parts into 25 root buildings to claim 49 insurable buildings.** The root `creationDate` field is an object-record date and is **not demonstrated as construction year**. The selected 2025 building catalogue is not a 2021 historical event snapshot. This study has no R+V policy or insurer holding identification.

### Reproducible bounded QA

Source-free dry-run of five hardcoded URLs:

```sh
python scripts/assess_nrw_lod2_five_area_v0.py --plan
```

Offline synthetic tests, no provider access:

```sh
python -m unittest discover -s tests -p 'test_assess_nrw_lod2*py' -v
```

Optional deliberate original-data QA, **only if provider API conditions and execution policy permit**, with no raw provider data emitted:

```sh
python scripts/assess_nrw_lod2_five_area_v0.py --live
```

Original fixed-request bytes are processed in memory only. Result includes an independently calculated per-area SHA-256, byte length, bbox-intersection status, 3D object/part counts and attribute-presence counts. The five original HTTP responses above were fetched with an **external read-only web tool**, decoded and checked independently in memory; the Python `--live` command **has not yet been executed against those original sources**. Consequently the initial observations above have **no purported Python live receipts or SHA-256 values**, and the original source bytes are not archived in the public repo.

Validation is fail-closed on wrong CityJSON type/version, mixed-up CRS, malformed quantized 3D vertices, invalid roots/part links, root geometry outside the specific declared bbox, mismatched sample URL, too many source rows, missing observations or oversized responses. Five fixed non-overlapping investigation windows are **not** an independently drawn exposure sample; returned `limit=5` introduces server ordering/selection effects.

## Next scientifically causal tasks

1. Review the **official RoofTypeTypeAdV / BuildingFunctionTypeAdV code lists** and define an explicit per-asset versus per-part taxonomy. Preserve multi-roof, missing and conflicting cases rather than filling values opportunistically.
2. Derive a justified regional/urbanization-stratified **sampling frame** (and selection weights, if available) before estimating NRW-wide attribute completeness.
3. Version historical geometry separately for the **2021/2025 event vintage**, and compare independent official ALKIS / Census buildings before hazard/vulnerability joins.
4. Prove the spatial mapping to separate **synthetic** insurer locations, TIV assumptions and financial terms; only then produce bounded Oasis GUL, IL, RI and OEP/AEP runs with explicit full-year event/frequency process.

This is useful real-source evidence, not an actual insurer portfolio or an admitted CAT-model exposure dataset.
