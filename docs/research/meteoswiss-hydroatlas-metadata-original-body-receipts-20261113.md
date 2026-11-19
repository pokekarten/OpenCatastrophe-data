<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Two bounded public metadata checks: MeteoSwiss hail STAC and HydroATLAS v1 (2026-11-13)

**Research receipt only.** Neither request was executed through the repository's
strict `source-api-readiness.yml` `reviewed_18` job. Both were read-only
requests through an external web-content intermediary that returned a base64
representation of the response body. The body SHA-256 was computed over the
decoded bytes in isolated CAT research Neon SQL. The intermediary does not
provide an independently validated raw provider HTTP status/redirect chain or
the same trust guarantees as the reviewed GitHub runner. No API credentials,
provider dataset bytes, downloaded assets, or original response bodies were
persisted in Git or Neon. All model admission decisions remain **false**.

## MeteoSwiss national hail climatology

- Reviewed exact access contract:
  `access/meteoswiss.national-hail-climatology.json`.
- Exact metadata request:
  `GET https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-radar-derived-grid`.
- Body content-type observed: `application/json`; decoded response: **2,790 bytes**.
- Intermediary-returned body SHA-256:
  `7b43f4a885a379d8227e9c006cdcf7631e689a8222d54656ab7b7bf5ddd50a3e`.
- Parsed and independently compared: exact collection ID,
  `stac_version=1.0.0`, `type=Collection`,
  `title=Spatial climate analyses - Hail`, `license=CC-BY`,
  official MeteoSwiss producer/licensor and canonical self-link.
- Research Neon `research.source_sample_v0`: **#69**, stored
  `2026-11-13T09:11:09Z` (metadata summary and distinct sample JSONB digest).
- Provider terms: [MeteoSwiss Open Data](https://opendatadocs.meteoswiss.ch/general/terms-of-use)
  and [FSDI service terms](https://www.geo.admin.ch/en/general-terms-of-use-fsdi).
  CC BY 4.0 attribution applies to the reviewed product scope; the STAC
  metadata label alone cannot license arbitrary linked third-party assets.
- **Not tested:** STAC item iteration, hail observation grids, NetCDF data,
  annual exceedance maps, return-level calibration, model use or redistribution
  of underlying numerical source rasters. Climatology is season-limited
  (April–September), not proof of zero hail in other months.

## HydroATLAS version 1.0 public Figshare article

- Reviewed exact access contract: `access/hydrosheds.hydroatlas.v1.json`.
- Exact metadata request: `GET https://api.figshare.com/v2/articles/9890531`.
- Body content-type observed: `application/json`; decoded response:
  **7,212 bytes**.
- Intermediary-returned body SHA-256:
  `87ed43e0dd02e6fba1228566878b17e1ad35d9a903f1ef4d26eb9dc2a9a45e38`.
- Parsed publisher identity `HydroATLAS version 1.0`,
  DOI `10.6084/m9.figshare.9890531.v1`, public article version 1,
  aggregate article licence CC BY 4.0 and **seven** published file records:
  four separate BasinATLAS/RiverATLAS Shapefile/FileGDB ZIP archives,
  three technical/catalogue PDFs, declared total **12,027,317,200 bytes**.
  The seven provider-reported supplied/computed MD5 labels matched each
  other; **no archive MD5 was independently recomputed**.
- Research Neon `research.source_sample_v0`: **#70**, stored
  `2026-11-13T09:12:17Z`; only a bounded metadata summary and source
  receipt were persisted.
- The collective Figshare CC BY 4.0 label does **not** erase individual
  HydroATLAS attribute-level CC BY/ODbL obligations. Per-column rights,
  source vintage and catchment/river scientific semantics must be reviewed
  before storing actual attribute rows or assigning a CAT-model role.
- **Not tested:** the four GIS ZIPs, PDF bytes, archive SHA-256, hydrologic
  polygons, attribute values, topology or CAT model readiness.

## Separate Berlin ALKIS WFS transport limit

An exact read-only metadata request to
`https://gdi.berlin.de/services/wfs/alkis_gebaeude?request=GetCapabilities&service=WFS`
returned `application/xml` through the intermediary, but the intermediary
**truncated** its base64 content representation before the full document could
be reconstructed. This is **not** an original-body SHA-256, completed WFS
2.0.0 schema validation, feature query, or Neon sample. The next safe test is
the already reviewed fixed `GetCapabilities` runner in
`source-api-readiness.yml`; no `GetFeature`/cadastral fields should be
requested to overcome the transport limit.

## Verification boundary and next action

The JSONB digest checks for both recorded research samples passed:

```sql
SELECT sample_id, source_id, sample_kind,
       sample_sha256 =
         encode(sha256(convert_to(sample_json::text, 'UTF8')), 'hex')
         AS canonical_sample_hash_ok,
       model_input_approved, source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id IN (69, 70)
ORDER BY sample_id;
```

Both rows have `canonical_sample_hash_ok=true`,
`model_input_approved=false`, and
`source_byte_persistence_authorized=false`. The SHA-256 attached to
`provider_response_sha256` covers only the exact intermediary-returned
metadata body, **not** any linked source asset.

On an authorized manual workflow dispatch, choose `reviewed_18` and capture
the runner's **separate** PASS/BLOCKED results and fixed-source digests; do not
count this external observation as passing that strict workflow. Any later
asset sample needs an independently reviewed product-specific request,
rights, bytes, scientific semantics and exact source SHA-256.
