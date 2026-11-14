<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ec-jrc.ghsl.ghs-built-s.r2023a.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ec-jrc.ghsl.ghs-built-s.r2023a.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ec-jrc.ghsl.ghs-built-s.r2023a

## Source ids

- ec-jrc.ghsl.ghs-built-s.r2023a

**Provider:** European Commission Joint Research Centre / Global Human Settlement Layer (JRC GHSL)

**Interface type:** object_store

**Status:** documented_only

**Documentation url:** <https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php>

**Service root:** <https://jrc-ghsl.s3.eu-central-1.amazonaws.com>

**Api version:** GHSL GHS-BUILT-S R2023A / E2020 / WGS84 30 arcseconds / V1_0 / DOI 10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- head_fixed_asset
- read_fixed_tiff_prefix
- read_fixed_native_block_809

### Path templates

- /ghs-built-s/r2023a/4326/30asec/2020/GHS_BUILT_S_E2020_GLOBE_R2023A_4326_30ss_V1_0.tif

**Parameter rules:** DOCUMENTATION-ONLY, zero requests authorized here. Exact one original GHS-BUILT-S E2020 4326 30ss V1_0 object at the single pinned path. Prior observed 4096- and 32768-byte Range prefixes are historical evidence, not approval of a new request. A future independently reviewed fixed source canary may request only bytes=0-32767 or the original compressed TIFF block 809 bytes=73699060-74222432 using strict Content-Range/total-byte checks, fixed host, no redirects, zero retries, no caller URLs, epoch variation, bulk listing, adjacent block downloads or pagination. Never treat the AWS multipart ETag as a whole-file SHA-256; no source bytes in Git or Neon.

## Response contract

### Expected media types

- image/tiff
- application/octet-stream

**Format:** One single original JRC GHSL R2023A 2020 EPSG:4326 30ss uint32 compressed GeoTIFF object; native 512x512 blocks, deflate compression. A Range read returns an incomplete TIFF prefix or a compressed native tile, not a stand-alone GeoTIFF; no raster values were retrieved under this contract.

**Scientific semantics:** Derived from Sentinel-2 and Landsat multi-temporal models; reported quantity is built-up surface m2 per cell, not footprint geometry or number of insured buildings. Temporal interpolation and 2025-2030 extrapolation are not observed. Product can be an exposure proxy only after careful validation. TIFF full object 173085842 bytes per independently observed public S3 listing; original 32KiB header indicated 43201x21384 cells, GeoTIFF EPSG:4326, PixelIsArea, 3570 tiles. Official NoData 4294967295 must not be zero-filled. Research-only; never infer asset TIV, insurer exposure, peril hazard, or loss from square metres of modelled built-up surface per cell.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `32768`

**Max sample bytes:** `590000`

**Retry policy:** none

**Rate limit notes:** Public anonymous JRC-managed AWS S3 bucket and CC BY 4.0 data licence do not by themselves establish a reviewed automated-service request entitlement, cost, acceptable rate, or JRC/AWS operational policy. Zero automated probes authorized by this documented_only contract. A separate reviewed bounded probe and explicit rights review are required before any new original Range request.

**Mutability notes:** Pinned R2023A/E2020/4326/30ss/V1_0 original object identity: listed size=173085842; native block 809 offset=73699060 bytes=523373; independently captured 4096-byte SHA-256=fe98c0a0057657f973b85bb4e3f96ab610a3d702b842c973c09135bbc2490e78 and 32768-byte SHA-256=002c21c644073b889df87135a95c902eecf8859b572458a021341ae5c90b35ea on 2026-11-12 (see research note). These are original-prefix hashes, NOT full-object SHA-256. Provider file/version or byte drift requires a new review; source full-object hash, decompressibility, value quality and any insurance model role are unproven.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** JRC product-specific original copyright notice covers the selected GHSL GHS-BUILT-S R2023A dataset under CC BY 4.0, including commercial reuse and raw-data redistribution in principle with attribution and modification disclosure. This is the source-rights ceiling, NOT repo permission to republish bytes; repository review remains non-admitted metadata-only. Separate AWS S3 service/automation/cost/fair-use terms have not been fully reviewed, hence no active probe. Licences of unrelated AWS or Earth Engine downstream services are NOT inherited; privacy/scientific input review remains separate.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-13

## Evidence urls

- <https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php>
- <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/copyright.txt>
- <https://registry.opendata.aws/ghs-built-s/>
- <https://github.com/pokekarten/OpenCatastrophe-data/blob/main/docs/research/ghsl-built-s-v-original-native-32k-header-20261112.md>

**Notes:** Narrow source access contract for previously observed original GHSL GHS-BUILT-S R2023A E2020 immutable canary. Historical 2026-11-12 original prefixes were SHA-pinned by scripts/verify_ghsl_built_r2023a_native_prefix_v0.py and metadata samples 43/44 in Neon; no new HTTP fetch, native block, decoded pixel, original raw-byte copy, Git publication, insurer exposure, or CAT input is created here. Keep candidate rights/scientific/admission = not_reviewed/not_reviewed/not_admitted in canonical landscape.
