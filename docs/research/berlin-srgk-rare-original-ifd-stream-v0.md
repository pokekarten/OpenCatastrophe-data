<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin SRGK rare scenario: ephemeral ZIP, complete TIFF tail metadata

**Research-only. Pending original source run after review.** This source
access is a deliberately reviewed, *larger* transfer than earlier
metadata-only 206 Range stages. Do not silently turn it into a
continuous archive or source database ingestion process.

## Scientific reason for a controlled single-source escalation

After [#1112](https://github.com/pokekarten/OpenCatastrophe-data/pull/1112)
proved the exact GeoTIFF member name and immutable source ZIP
central-index hash, [#1118 original run
41415860814](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41415860814)
proved **classic little-endian TIFF** but found its first
image-file-directory at an uncompressed TIFF offset of **167112958 B**
in the rare `wasserstand_T50_1.tif`, only **185895 B from the
uncompressed end**. Similar at-end IFD placement occurred in the
T100 and extreme GeoTIFFs. Ordinary ZIP DEFLATE cannot seek directly
to an uncompressed offset without decoding all earlier compressed
blocks or a verified independent DEFLATE checkpoint index. A
compressed ZIP tail Range cannot reliably replace source decoding.

## Exactly one original 132.7 MB product

`research_runners/berlin_srgk_rare_original_ifd_stream_v0.py`
is source-locked to
`https://gdi.berlin.de/data/ua_srgk/atom/wasserstand_seltenes_ereignis.zip`.
Its pinned source facts are:

- Provider HEAD / original ZIP size **132689382 bytes**;
- Original central-directory SHA-256
  `9a593d9d3e39c21ee99c34d13550c16ae9c0d8c3390c653dfb566f49f00be7b3`;
- Exactly one original member, name `wasserstand_T50_1.tif`,
  DEFLATE-compressed **132689170 bytes**, uncompressed
  **167298853 bytes**, first IFD at **167112958**.

Only after a reviewed workflow merge to `main` or explicit
reviewed dispatch does the job make **one** provider URL GET,
HTTP 200 with **exact pinned Content-Length**, no redirect, proxy,
gzip transport or unexpected media type. It streams in 1 MiB
chunks into a uniquely created mode-0600 file inside an isolated
temporary directory (deleted before the command returns). The full
source ZIP SHA-256 becomes a local reproducibility receipt, not a
provider-signed checksum. It then independently verifies exact ZIP
central digest and one member, streams all uncompressed TIFF bytes
through `zipfile.ZipExtFile` to verify CRC and uncompressed size,
**discards image bytes** and retains at most 256 KiB in memory from
the end to parse only TIFF first-IFD metadata and relevant
georeferencing tag payloads.

The report emits source full ZIP SHA-256, derived full TIFF SHA-256,
TIFF dimensions, bounded GeoTIFF numeric key IDs, horizontal pixel
scale **candidate**, GDAL-NoData text **candidate**, source UTC
and false data/insurance admission flags. No original ZIP, TIFF,
pixels, crop, building footprints, policy/insurer data or source
geometry is committed, uploaded, persisted in Neon or passed to
NextGen.

The TIFF GeoKey `ProjectedCSTypeGeoKey=3072`, if present, may
independently support a raster projection identity; it does NOT
establish the physical **vertical water-depth unit**. A NoData
ASCII text value is a source-typed metadata candidate, not a
certified wet/dry observation. A TIFF horizontal cell size does
not establish centimetres/metres of inundation depth.

## Safety and model admission

The verified **second** detailed Berlin SRGK *model area* pilot
`[391860,5816840,392060,5817040]` EPSG:25833
([source run 41363537076](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41363537076))
has **not** been joined to the actual raster pixels in this PR.
The extreme scenario is not available for all study areas;
T50/T100 filenames alone are not a stochastic annual event
catalogue or hazard frequency proof.

The original catalogue's licences are geographically mixed:
Germany Data Licence Zero 2.0 with CC BY 4.0 attribution for
Moabit and Flughafensee. Downloading source for ephemeral metadata
inspection is not automatic permission to redistribute every
area/product or to integrate into an insurer portfolio.

**This PR does not resolve** the separate nationwide BKG KOSTRA
signed-Int16 physical-scale blocker
[issue #1086](https://github.com/pokekarten/OpenCatastrophe-data/issues/1086).

After *original* metadata verification, the next separately
reviewed stage needs a source-version-pinned TIFF affine transform,
exact raster-vs-pilot coverage and NoData/pixel physical-depth
semantics, then vulnerability, event occurrence/frequency,
insured exposure and terms. **No automatic CAT admission.**
