<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Environment Agency 3.3% AEP defended river/sea: original OGC metadata receipt (2026-11-10)

**Scope:** One *present-day, defended-only* England flood-depth product.
Technical metadata inspected from the original Environment Agency service:
`https://environment.data.gov.uk/spatialdata/rivers-and-sea-1in30-defended-flood-risk-depths-present-day/ogc/features/v1`.
This is NOT a geospatial dataset sample, building flood depth, damage/loss,
event set, or OEP/AEP curve. No provider feature item, geojson, spatial ZIP,
building record, local raw provider bytes, or GIS asset is committed.

This technical service resolves to dataset service UUID
`767c96e6-b149-4744-9d4d-34b32f6c0e1b`, linked to official
[data.gov.uk catalogue UUID `2b1dc7a4-ff9f-42fd-9971-11638eabf814`](https://www.data.gov.uk/dataset/2b1dc7a4-ff9f-42fd-9971-11638eabf814/rivers-and-sea-3-3-defended-flood-risk-depths-present-day).
The **two UUIDs identify different catalogue/service namespaces** and are
not interchangeable.

## Original provider JSON response-body evidence

Read via a bounded third-party HTTP transport, with uncached requests on
2026-11-10, and SHA-256 computation checked against standard empty/abc vectors.
`Content-Type: application/json; charset=utf-8`. Exact endpoints and expected
byte-length/digest pairs are frozen as `RECEIPTS` in
[`scripts/preflight_ea_1in30_ogc_metadata_v0.py`](../../scripts/preflight_ea_1in30_ogc_metadata_v0.py).

| Metadata endpoint suffix | Raw bytes | SHA-256 |
| --- | ---: | --- |
| `/ogc/features/v1` (landing) | 3863 | `84792937c27156e4fc6c79a0aad81abb985b414494c3cd94b7476d273ffe76a1` |
| `/ogc/features/v1/conformance` | 1910 | `89131744b55b74343dd3684d0381f3a024a1ce2b6c9d659752b2ef8ca8181284` |
| `/ogc/features/v1/collections` | 6448 | `633ee4f556b91b235860d0cd430e2a2e66fca37f41a3733bf080555080789349` |
| `/ogc/features/v1/collections/Rivers_1in30_Sea_1in30_defended_depths` | 5727 | `e3728a3c0f1a37a01c4fdcb80eb66f0b93dc98f8523cdc3c6c9fbed05649a384` |
| `/ogc/features/v1/collections/Rivers_1in30_Sea_1in30_defended_depths/queryables` | 1232 | `494963373e369d1cfc4e0ebe075d25c6b7424f03899e4eb8a80cc1fdb29e8b11` |

**Interpretation of receipt:** A hash can establish a byte-for-byte match to
the *one observed response body*; it does not authenticate arbitrary
caller-provided input, grant reuse rights, or prove geospatial values. Service
links returned in the metadata include alternate endpoints and external hosts;
no returned URL should be automatically followed by a downstream consumer.
The separate WFS GetCapabilities XML response exceeded the retrieval tool's
complete-byte output limit, so **no XML byte receipt or WFS feature schema was
claimed**. The JSON OGC API response bodies above were complete.

## Verified OGC API and spatial-contract facts

1. Landing JSON identifies `WFS` operated by the Environment Agency, has
   an OGC `data` link to the expected dataset-specific collections service.
   Conformance JSON includes OGC API Features core and Features CRS.
2. The collections JSON lists **exactly one** layer ID:
   `Rivers_1in30_Sea_1in30_defended_depths`.
3. Collection metadata advertises **storage CRS EPSG:27700** (British
   National Grid) alongside selectable CRS84, EPSG:4326, EPSG:4258,
   EPSG:3857 and EPSG:900913. Its published spatial bounding box is in
   **OGC CRS84** longitude/latitude order:
   `[-6.9869611877272115, 49.881385801260535, 2.0755019347798958, 55.810777963189906]`.
   That advertised rectangle is **not confirmed coverage of every location**
   within it, and not a source-published depth raster resolution.
4. Queryables JSON exposes **exactly these public field names**:
   `depth_band: string`, `flood_source: string`,
   `shape_length: number`, `shape_area: number`, and
   `shape` as a GeoJSON geometry reference.
   The metadata does **not** define a numeric depth in metres, a measured
   per-property water depth, explicit `Unavailable` value codes,
   or the units of `shape_length`/`shape_area`.
   A later feature-byte/sample and source product-description check are
   needed to map actual `depth_band` strings to millimetre intervals.
   Absence/unsupported areas must never become observed zero-depth values.

The [official EA dataset page](https://www.data.gov.uk/dataset/2b1dc7a4-ff9f-42fd-9971-11638eabf814/rivers-and-sea-3-3-defended-flood-risk-depths-present-day)
states this is a 3.3% annual-exceedance-probability *defended*
scenario and not a single-building flood-risk assessment. The
[Defra fair use policy](https://dsp.environment.data.gov.uk/support/faqs/275808874/1169555459)
permits legitimate uses of OGL data/API subject to conditions, but
third-party components, exact asset-specific terms and scientific review are
not cleared by this research metadata step.

## Offline executable regression gate

`scripts/preflight_ea_1in30_ogc_metadata_v0.py` accepts one **saved**
metadata JSON response, never fetches it itself. Example:

```sh
python scripts/preflight_ea_1in30_ogc_metadata_v0.py --document queryables --input /private/ea-queryables.json
```

The validator rejects mismatched fixed collection identity, changing
CRS metadata, incorrect CRS84 bounding box, changed queryable field names,
numeric-versus-string `depth_band` drift, malformed JSON or feature
payloads. It emits only metadata checks, byte count and SHA-256, with
negative rights/admission flags. Its Python unittest is synthetic-only.

**Not admitted:** Real OGC Feature items, WFS feature rows, flood polygons,
depth-value mapping, precise building inundation, annual loss frequencies,
hazard vulnerability and OEP/AEP curves. The current source-access JSON is
`documented_only` / `probe_contract.mode=none`: this receipt does NOT
promote it to an executable automated GIS connector.
