<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GHSL BUILT-S / BUILT-V R2023A E2020: first original native 32 KiB TIFF source receipts

**Observed on 2026-11-12.** Research-only exact-source file-format and
geospatial prefix verification; **no original pixel values read**, no complete
TIFF download, no individual building or insured portfolio inference.

## Official publication and source/version identity

The European Commission JRC's official product pages describe
[GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php)
as **built-up surface per raster cell in square metres** and
[GHS-BUILT-V R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buV2023.php)
as **built-up volume per cell in cubic metres**, derived from surface and
height sources. Both provide multitemporal modelled grids for 1975–2030.
Later vintages may include projections and the products are not independent
building censuses. Both official product-specific JRC copyright notices,
[GHS-BUILT-S](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/copyright.txt)
and [GHS-BUILT-V](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_V_GLOBE_R2023A/copyright.txt),
state **CC BY 4.0** with source acknowledgement and modification disclosure.

The [JRC-managed public S3 data registry for surface](https://registry.opendata.aws/ghs-built-s/)
and [volume](https://registry.opendata.aws/ghs-built-v/) list unsigned
`jrc-ghsl` bucket access. One exact public AWS S3 ListObjectsV2 request
for each fixed `r2023a/4326/30asec/2020/` prefix returned exactly one
native TIFF source asset. Its S3 multipart ETag is **not** a source-file
SHA-256 (no full file hash was acquired).

| Source field | GHS-BUILT-S surface | GHS-BUILT-V volume |
| --- | --- | --- |
| Candidate ID | `ec-jrc.ghsl.ghs-built-s.r2023a` | `ec-jrc.ghsl.ghs-built-v.r2023a` |
| Product version | R2023A, epoch 2020, `4326/30asec` V1_0 | R2023A, epoch 2020, `4326/30asec` V1_0 |
| Full object size from official S3 listing | **173,085,842 bytes** | **187,376,914 bytes** |
| First 4,096-byte exact-source digest (SHA-256) | `fe98c0a0057657f973b85bb4e3f96ab610a3d702b842c973c09135bbc2490e78` | `3be916bc8f2bf49cdcce38a73c44f70cca460384a6ff81dc42ca021d7c3c4038` |
| First **32,768** original bytes SHA-256 | `002c21c644073b889df87135a95c902eecf8859b572458a021341ae5c90b35ea` | `7e61b8056273ea0f2fa84913c3458da6d5c38f52f41881af20a42b0d966e76bd` |
| Native compressed TIFF block index **809** byte offset | **73,699,060** | **80,549,811** |
| Native compressed TIFF block size | **523,373 bytes** | **570,557 bytes** |
| Neon metadata-only record | `research.source_sample_v0.sample_id=43` | `research.source_sample_v0.sample_id=44` |
| Neon canonical JSONB SHA-256 | `eb1d04fffde91b0aa2d42414901c4ca0c40c63dc9ac7e5ae2d10b0cf9169544a` | `0834f8e9a7691e502633c6a6a4ab1a9057a80c9374c6c1a3cc90700c2cad83f3` |

Exact single fixed TIFF object URLs:

- Surface: `https://jrc-ghsl.s3.eu-central-1.amazonaws.com/ghs-built-s/r2023a/4326/30asec/2020/GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif`
- Volume: `https://jrc-ghsl.s3.eu-central-1.amazonaws.com/ghs-built-v/r2023a/4326/30asec/2020/GHS_BUILT_V_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif`

**Original-byte acquisition scope:** a single direct read-only public S3 object
request with `Range: bytes=0-4095` and a separate,
later `Range: bytes=0-32767` for each fixed file. The transport
returned exactly 4,096 and exactly 32,768 bytes per request; the
prefix SHA-256 of the latter independently matched the earlier 4 KiB
digest. The delegated transport did not expose authoritative HTTP status
and `Content-Range` headers to this run, so **do not claim that those
were independently checked**. The native TIFF source bytes were handled
transiently by the read-only research runner and **not committed to Git or
persisted in Neon**.

## Original TIFF metadata decoded from 32 KiB

For **both** independent original products, TIFF structural parsing found:

- Classic little-endian TIFF `II/42`, first IFD offset **192**, **19**
  native IFD tags; the exact same set of tag IDs in both assets.
- Raster dimensions **43,201 columns × 21,384 rows**; one unsigned
  **32-bit** sample per cell; TIFF Deflate compression code **8**,
  predictor **1**, 512×512 native tiles; **3,570** tile entries.
- GeoTIFF original GeoKeyDirectory indicates geographic EPSG:**4326**,
  `PixelIsArea`, angular unit degree. Declared pixel pitch ≈
  **0.0083333333 degrees** (30 arcseconds), not equal physical metres
  everywhere on Earth.
- Native tiepoint approximately **longitude −180.0012493°**,
  **latitude 89.0995832°**; table 324/325 hold 3,570 source byte
  offsets and compressed lengths respectively and are completely
  inside the 32 KiB prefix.
- One fixed, preselected central-Germany spatial research canary lies in
  native compressed **block 809** (row 9, column 44). The exact block
  offset/size in the preceding table have been captured in the table above.
  **These source compressed blocks were NOT fetched or decompressed.**
- The original NoData/pixel-class semantics were **not** established
  by the first 32 KiB, and neither complete COG/overview conformance,
  full file hash nor independent pixel-level ground truth was established.

## Safety-checked read-only replay

`scripts/verify_ghsl_built_r2023a_native_prefix_v0.py` independently
accepts only **one previously, lawfully acquired 32 KiB prefix** of the
exact reviewed product. It verifies two SHA-256 pins per source, original
TIFF schema and EPSG geokeys, finite geotransform, tile arrays and
source block identity. It has **zero network access, no provider URLs to
select, and no ability to create model inputs**. All unit tests use
synthetic TIFF headers with wrong-source, wrong-CRS, compression,
coordinate, block-index and other fail-closed negative cases.
No raw provider bytes are bundled as test fixtures.

```sh
python -m unittest tests.test_verify_ghsl_built_r2023a_native_prefix_v0 -v
python -m scripts.verify_ghsl_built_r2023a_native_prefix_v0 \
  --product surface --input /private/reviewed-built-s-32k-prefix.bin
```

Original-data replay requires the exact source bytes, obtained separately
under the source's current licence and operational constraints. The
sample's actual 32 KiB raw bytes are not in Git, public logs, this
document, or Neon.

Read-only insurance Neon QA:

```sql
SELECT sample_id,source_id,sample_kind,provider_response_sha256,
       sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')),'hex') AS valid_sample_hash,
       sample_json->>'original_tiff_first_32768_bytes_sha256' AS reviewed_prefix_digest,
       sample_json->>'original_native_pixel_values_inspected' AS original_pixels_inspected,
       model_input_approved,source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id IN (43,44);
```

## Remaining evidence/admission barriers

`actual_sample_state=metadata_only` remains for both source candidates,
because **neither sample contains actual native surface/volume values**.
The existing `commercial_reuse_verdict=allowed_verified` is
licence/attribution-scoped only and does not prove scientific suitability.

The next governed step is a **strictly source-scoped range probe**
for the **single fixed compressed original block** of each product.
First validate a source access contract with byte ceilings,
original 32 KiB prefix SHA, file size and NoData rules; then fetch the
single frozen range into an ephemeral process and independently decode
one small, fixed, aggregatable raster window. Reject any TIFF coding,
block size, source or value-unit mismatch. Do not silently assume
raster values represent individual roofs, unique building counts,
construction type, TIV or flood/wind damage. Any actual derived
summary must be staged separately as a research-only sample and
cross-checked against an independent source/vintage.
