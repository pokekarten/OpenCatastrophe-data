<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Ontario historical events: bounded original layer metadata contract (2026-11-03)

Research-only supplement to OpenCatastrophe-data PR #1153. No source bytes, external geometry, personal records, claimant/insurer data or raw feature attributes are committed. The official [Government of Canada dataset listing](https://open.canada.ca/data/en/dataset/3ddd1967-a5a1-47b2-b3b9-554495581ea2) names Ontario as publisher, links the [Ontario Open Government Licence](https://www.ontario.ca/page/open-government-licence-ontario) and provides the authoritative ArcGIS REST layer. These statements do not constitute an OpenCatastrophe admission decision or authorize any particular public redistribution of original layer records.

## Original source identity and exact scope

- Fixed public ArcGIS metadata document: `https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open05/MapServer/20?f=pjson`.
- Original metadata inspected by Exa on 2026-11-03. It advertises layer id `20`, display name `Emergency Management Historical Event`, type `Feature Layer`, source WKID `4269` (NAD83) and **`esriGeometryMultipoint`**, not flood, fire, damage or loss polygons.
- Provider fields include `OGF_ID` (double, indexed unique in original metadata), `EVENT_TYPE`, `EVENT_YEAR` (small integer), `EVENT_NUMBER`, `LOCATION_ACCURACY`, `EVENT_DESCR` and date fields. A unique OGF_ID index does not prove globally stable historical disaster identifiers, let alone insurer event-to-claim attribution.
- Service metadata advertised `Map,Query,Data`, `maxRecordCount=2000`. These are machine capabilities, **not** authorization to fetch feature rows, bulk-copy original records, or reuse them commercially in the absence of a specific review.
- The Canadian federated catalogue currently reports modification 2026-10-07, while the Ontario provincial catalogue shows an older dataset update/vintage; neither date proves the timestamp or completeness of each event feature. The catalogue also admits selection effects: events are those involving Ontario MNR emergency response or a request for assistance, not a population-wide hazard/event census.
- No quantitative loss field is asserted from the published schema. `EVENT_DESCR` and `EVENT_DATA_REFERENCE` are free-text/data-reference attributes and are not harvested, echoed, or used by this preflight.

## Offline source-byte verification

`research_runners/ontario_historical_events_metadata_receipt_v0.py` accepts only an operator-supplied original metadata JSON file and a precomputed SHA-256. It never makes HTTP calls, follows redirects, downloads source geometry, or writes the response. It reads at most 131,073 bytes, requires exact byte SHA-256, strictly parses JSON and rejects duplicated keys, NaN, wrong layer ID/name, multipoint-to-polygon drift, incorrect CRS, changed key field types, and feature-row payloads. It emits only a safe JSON receipt with a fixed source identity, size, hash and explicit negative admission/geometry/loss claims.

Example, only after independently retrieving the **metadata response** through an authorized provider interface:

```bash
python research_runners/ontario_historical_events_metadata_receipt_v0.py \
  --original-json /path/outside/git/ontario-layer-20-original.json \
  --expected-sha256 <verified_64_character_lowercase_sha256>
```

The path is illustrative and not a repository dependency. The verifier does not establish that the original HTTP response came from Ontario: transport provenance (actual request URL/status/UTC and retrieval environment) must be attested separately, and a copied or synthetic body is never authoritative. No exact original-byte SHA-256 has been recorded in this PR.

## Scientific acceptance boundaries

Ontario's multipoints are **event-referencing locations**, not actual event hazard intensity, inundation footprints, affected property geometry, insured exposure, loss payments or financial event definitions. A realistic historical loss model still needs independent footprints, event identity crosswalks, contemporaneous exposure and validated damage/insurance observations. Before source admission, review the exact Ontario product's current licensing/attribution, personal-data risk of feature attributes, upstream event selection, coordinate uncertainty, temporal and cross-border completeness, and how event IDs map to independent perils. No Neon import or model simulation is authorized by this document.

The CHIRPS v3 source in this PR is independently documented at https://www.chc.ucsb.edu/data/chirps3 and its original README at https://data.chc.ucsb.edu/products/CHIRPS/v3.0/README-CHIRPSv3.0.txt: the preliminary and final products are distinct vintages; daily `rnl` is ERA5-disaggregated and daily `sat` is IMERG Late V07-disaggregated. Consequently, comparing daily CHIRPS3 to ERA5/IMERG is not independent validation. Global CHIRPS3 is restricted to land at 60°N–60°S, not literally all globe latitudes. Its provider cites CC BY 4.0, but dataset/asset reuse and OpenCatastrophe model admissions remain separate reviews.
