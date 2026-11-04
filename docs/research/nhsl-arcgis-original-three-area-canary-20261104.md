<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NHSL original ArcGIS layer + 3-row settlement canary — 2026-11-04

**Scope:** first source-observed (not only source-shaped) NHSL metadata and **three read-only records** from the original Natural Resources Canada ArcGIS MapServer. This is a geographically/temporally **bounded sample**, not a census national-exposure validation, original-v1.0 GeoPackage byte proof, scientific model calibration or permission to invent insured locations.

**Existing upstream work:** [NHSL v1.0 release metadata gate](../../scripts/nhsl_release_metadata_preflight_v0.py), [NHSL→OED aggregate staging gate](../../scripts/nhsl_oed_staging_preflight_v0.py) (PR #1246), and [full field-lineage report](nhsl-v1-oed-staging-crosswalk-v0.md).

## Original-provider, license and geometry provenance

- Original Canadian open-data dataset: [National Human Settlement — Physical Exposure](https://open.canada.ca/data/en/dataset/1818cf27-03ea-4ebb-bc43-fd371b42198b), publisher Natural Resources Canada. The data catalogue identifies **Open Government Licence — Canada** and modeled 2019-CAD replacement-cost estimates. [Official terms](https://open.canada.ca/open-government-licence-canada) permit commercial reuse with attribution and specific exclusions (including third-party rights); they do not warrant model fitness or imply governmental endorsement. This is **provider catalogue licence evidence**, not completed item-by-item model admission or an exception to repository data-byte policy.
- Original [NRCan MapServer](https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/physical_exposure_en/MapServer?f=pjson) currently exposes two non-interchangeable layers:
  - [Layer 0](https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/physical_exposure_en/MapServer/0?f=pjson), **Natural Hazards Building Exposure Model**, `esriGeometryMultipoint`, **43** fields. Building archetype fields include `BldgID`, `BldgLat`, `BldgLon`, `E_BldgNum`, `E_BldgValue`, `E_ContValue`. These are **archetype points co-located at settled-area centroids**, not independent individual rooftop or policy locations.
  - [Layer 1](https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/physical_exposure_en/MapServer/1?f=pjson), **Landuse**, `esriGeometryPolygon`, **64** fields, native map spatial reference `EPSG:3857`. Source numeric field names `Et_BldgNum`, `Et_BldgArea`, `Et_BldgValue`, `Et_StrValue`, `Et_NStrValue`, `Et_ContValue`, `Et_AssetValue` and `E_SauidLat`, `E_SauidLon`. This is the **correct aggregate layer** for [our existing NHSL staging proof](../../scripts/nhsl_oed_staging_preflight_v0.py).
- Original [documentation YAML](https://github.com/OpenDRR/national-human-settlement/blob/main/docs/_data/nhsl_physical_exposure_attributes.yml) documents **66 attribute names**. The current ArcGIS polygon layer reports **64 service fields**, including 10 required staging fields with matching ArcGIS types. **Do not assume 66 == 64 or infer all YAML keys exist**: many YAML-only virtual/computed descriptions and some service-only fields differ. The original [v1.0 XLSX data dictionary](https://github.com/OpenDRR/national-human-settlement/releases/download/v1.0/nhsl_physical_exposure_attributes_en.xlsx) has not been downloaded/parsed here. An exact v1.0 GPKG ↔ original XLSX ↔ current live service **release/version equivalence has not been demonstrated**.

## Bounded observed read-only evidence

One **deterministic, filtered, non-geometry three-feature query** ran against polygon `MapServer/1/query` on 2026-11-04:

- `where=1=1 AND pruid='24'` (Québec), `resultRecordCount=3`, `orderByFields=OBJECTID`, `returnGeometry=false`, projection of `Sauid`, `E_SauidLat`, `E_SauidLon`, `Et_BldgNum`, `Et_BldgArea`, `Et_StrValue`, `Et_NStrValue`, `Et_BldgValue`, `Et_ContValue`, `Et_AssetValue`, `OBJECTID`.
- **Observed return:** exactly 3 ordered source feature records, `exceededTransferLimit=true` (explicitly shows the result is truncated, not a national or regional census); no geometry transferred.
- Per-record arithmetic: **3/3** satisfy `Et_StrValue + Et_NStrValue = Et_BldgValue` and `Et_BldgValue + Et_ContValue = Et_AssetValue` with **zero** observed difference. Computed aggregate estimated building count = **54** and modeled 2019-CAD total replacement value = **17,495,502** across **only those three selected areas**. These are **not** insured TIV, true number of coordinate-identifiable buildings, a representative province estimate or statistically independent calibration data.
- Source row bytes, source SAUIDs, object IDs and archive/geometry payloads were **not committed**. Original sample and metadata body SHA-256 hashes were not carried across runtimes and **are not claimed**. The executable below computes SHA-256 over provided local JSON bytes when a downstream user replays the request and retains those responses outside Git.

**Executable:** [`scripts/nhsl_arcgis_polygon_canary_v0.py`](../../scripts/nhsl_arcgis_polygon_canary_v0.py), [synthetic regressions](../../tests/test_nhsl_arcgis_polygon_canary_v0.py). It pins *layer 1/64-field/Polygon/EPSG:3857 geometry* and the exact eleven projected field names/types, then delegates all value checks to the already-merged NHSL→OED staging preflight. It fails on a swapped archetype layer, wrong types, negative/contradictory estimated values, duplicate SAUID/OBJECTID, unbounded sample size, raw geometry, unexpected insured fields, invalid/missing source data, reversed result ordering, malformed JSON and file-size violations. It yields only aggregate sums, local-file hashes, no raw feature rows, and always reports `not_admitted` and `can_export_oed_loc_or_account=false`.

## Reproduction: local read-only source retrieval, offline inspection

Source access is a **bounded query only**; do not use the national ZIP or commit source JSON into the public research repo.

```bash
curl --fail --silent --show-error --max-time 30 --max-filesize 300000 \
  'https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/physical_exposure_en/MapServer/1?f=pjson' \
  -o /tmp/nhsl-arcgis-layer-1.json

curl --fail --silent --show-error --max-time 30 --max-filesize 50000 \
  'https://maps-cartes.services.geo.ca/server_serveur/rest/services/NRCan/physical_exposure_en/MapServer/1/query?where=1%3D1%20AND%20pruid%3D%2724%27&outFields=Sauid%2CE_SauidLat%2CE_SauidLon%2CEt_BldgNum%2CEt_BldgArea%2CEt_StrValue%2CEt_NStrValue%2CEt_BldgValue%2CEt_ContValue%2CEt_AssetValue%2COBJECTID&returnGeometry=false&resultRecordCount=3&orderByFields=OBJECTID&f=pjson' \
  -o /tmp/nhsl-quebec-three-areas.json

python scripts/nhsl_arcgis_polygon_canary_v0.py \
  --layer-json /tmp/nhsl-arcgis-layer-1.json \
  --sample-json /tmp/nhsl-quebec-three-areas.json

python -m unittest discover -s tests -p 'test_nhsl_arcgis_polygon_canary_v0.py' -v
```

The offline gate **does not cryptographically authenticate the source of supplied JSON files**. Confirm their original official URL and an authorised original request separately; content SHA-256 hashes establish local byte identity, not original-publisher signatures. A future service update may change field counts, IDs or stock values, in which case the strict canary should **fail closed**, get a new review and a new source version rather than accepting drift.

## Next independent scientific proof

1. Acquire only the original **17,888-byte** XLSX dictionary from the official pinned GitHub release and one **small regional GeoPackage ZIP** (e.g. Nunavut), outside Git, under the confirmed Canadian licence and archive safety constraints; compare actual `v1.0` layer names/CRS/field types to the live ArcGIS schema. Do not equate live service with the downloaded archive unless the evidence proves equivalence.
2. Run a bounded polygon-geometry integrity/area-centroid inspection, coordinate uncertainty review and source-field null/missing-data probe. Validate restoration-cost components and whether count fractions or edge cases exist in multiple provinces; only then think about a properly declared *synthetic policy-location allocation* with model uncertainty rather than making each SAUID an insured building.
3. Maintain clear lines between original modeled replacement-cost stock, OED's building/contents **insured** TIV, actual terms/deductibles/reinsurance, and downstream hazard/vulnerability calibration.

**Scientific/model state: not admitted. Source rights review for the exact downstream use: still pending.**
