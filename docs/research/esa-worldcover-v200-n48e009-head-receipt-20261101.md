<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ESA WorldCover 2021 v200: fixed N48E009 map tile HTTP metadata check

**Date:** 2026-11-01. **Status:** T1 exact-object HEAD availability validated.
**Not:** source-pixel acquisition, COG layout verification, insurance exposure,
building matching, or production CAT model admission.

## Authoritative producer identity and rights

- Source/product: ESA WorldCover 2021 v200 land-cover Map, 10 m, 11 classes,
  [official access](https://esa-worldcover.org/en/data-access), release
  DOI [10.5281/zenodo.7254221](https://zenodo.org/records/7254221).
- ESA documents a public anonymous AWS object store and 3×3-degree GeoTIFF
  tiling. Original source attribution remains required under CC BY 4.0.
- The fixed candidate `N48E009` is the 48°–51° N, 9°–12° E nominal
  southern German tile derived from the official WorldCover grid/naming
  specification. It is not a claim that one tile covers all of Germany.
- The **exact object** is
  `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N48E009_Map.tif`.
- Neither S3 accessibility nor product-level rights grants authority to
  publish source bytes in this repository without artifact-specific admission.

## First actual HEAD execution and MIME clarification

The initial source workflow [41317355722](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41317355722)
correctly blocked the response because the S3 object had a generic
`binary/octet-stream` HTTP type, not the predeclared TIFF/octet MIME.
An independent rerun [41317425996](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41317425996)
identified that exact media type in bounded, sanitized error output.
After narrowing the approved HTTP MIME contract to include precisely this
observed *transport* type, the actual fixed HEAD succeeded:

- [GitHub Actions run 41317530204](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41317530204).
- UTC `2026-11-01T14:43:00.222814+00:00`.
- HTTP **200**; `Content-Type: binary/octet-stream`.
- Original provider-declared object size: **94,851,935 bytes**.
- ETag header *hash* (not original source SHA-256):
  `5efd0385095c7ae454d6f2a05dba47c80fc0c4cbba7685afe3056ff971129655`.
- Frozen HEAD request identity SHA-256:
  `9c85706b3b72c2f80bb153eb67ff43740f56f63597901e76e65e5f1e96937b39`.
- Reviewed source-access contract SHA-256:
  `ac33f21903b5b2c2a89a1f87a256286eb4b5b9f40dd3b785634a08c7f1ea1f6c`.
- Full raster bytes downloaded: **0**.
- `original_object_sha256_verified=false`,
  `cog_structure_validated=false`, `model_input_approved=false`.

A 94.85 MB S3 object **exists** for the one fixed WorldCover map tile
path. No HTTP response body was read, and no raster/pixel value was inspected.
The S3 ETag is transport/version metadata only; do not label its value as an
independent checksum for original GeoTIFF content. Likewise, a generic
`binary/octet-stream` header alone cannot verify the actual geospatial
raster format.

## Next separately reviewed T3 scope

1. Freeze an independently reviewed, bounded exact-byte acquisition or
   small fixed Range request against this **same versioned tile**. Distinguish
   a 4 KiB header sample hash from a full 94,851,935-byte source SHA-256.
2. Decode TIFF/COG metadata without trusting MIME: raster band datatype,
   CRS EPSG:4326, published 3° geographic tile extent, pixel size,
   no-data and the 11 classified Map codes, subject to source-bounded limits.
3. Read only a tiny predeclared fixed spatial window in approved local
   temporary storage for preliminary exposure-context research; report
   code occurrence counts rather than individual landowner/insurance data.
4. Calibrate false positives/limitations against independent official land
   cover and building observations, preserving the 2021 observation year
   and documented v100/v200 algorithm discontinuity.
5. Store large authorised rasters only in distinct CAT object storage with
   full original-byte provenance and rights; never in the lightweight Git
   registry or an unreviewed insurer exposure table.

The automated `HEAD` check is an operational availability receipt,
not authorisation for a follow-on GET/Range/sync, and not scientific or
commercial deployment approval for any insurer CAT model.
