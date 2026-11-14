<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GHSL BUILT-S / BUILT-V R2023A — original native E2020 block proof gate

**2026-11-12 execution and original-source research receipt.** The first
main source run was blocked by an overly strict TIFF tag parser; a corrected
second main source run succeeded and is independently documented below.
These are limited original-source research values, not CAT model admission.

## Successful original provider-byte and Neon research staging — 2026-11-12

**Verified main-source run:**
[GitHub Actions #43309743505](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43309743505),
exact main merge commit
`c6c2dff480dc72ef77b7f141ba1a8dd2d12c6249`, all source-specific
synthetic/offline tests and **both live original-source probe steps
completed successfully**. This followed the fail-closed first run and
narrow original TIFF SHORT-tag fix in
[PR #1512](https://github.com/pokekarten/OpenCatastrophe-data/pull/1512).
No original source bytes, full TIFF, individual raw cells, feature IDs
or actual building coordinates were saved to Git or Neon.

The runner fetched the exact fixed 32 KiB TIFF original header per product,
reverified its SHA-256, checked **HTTP 206**, Content-Range/full file size,
expected Deflate uint32 encoding, EPSG:4326 and original native offset
tables. It then fetched exactly **one** immutable indexed original TIFF
block per product, and decoded exactly **262,144 original uint32 raster
cells (1,048,576 bytes)** transiently. One previously chosen
**32×32 (1,024 cell)** native source window was aggregated, with no
original pixel row or array logged, committed or imported.

| Actual original result | BUILT-S surface | BUILT-V volume |
| --- | ---: | ---: |
| Original source UTC | 2026-11-12 21:23:21 | 2026-11-12 21:23:22 |
| Original compressed block bytes | **523,373** | **570,557** |
| Original compressed source block SHA-256 | `eae39538ec234c80d43f135e7022e1c2ad4be3e10d72dcdc2e82534431a276d9` | `578a62b6164f30ab82479e37cbfbf4353af2db18ff2eef65552aff5dce12e53c` |
| Independently decoded native block SHA-256 | `1d961e2c951e4db8df6e22776903aa06ea943a9f49728ef4a8fa8178506c8923` | `e91e026954d2f37d19c48ea87b3e33207e8c67e0efdda0d5c66589a3e751b5f5` |
| Exact 32×32 original window uint32 LE SHA-256 | `2f1a3322b2081e70e8e7b08339dc14b61d5286605208f063fd57539e80121106` | `2929b3c7e33e00948ca6589bec268eb80ff59bafe13d9463e8440ee7bf298ec9` |
| Positive original source cells | **937** | **937** |
| Zero source cells | **87** | **87** |
| Potential uint32-max sentinel cells in window | **0** | **0** |
| Sum of positive source values in window | **74,802,406 m²** built-up surface | **520,775,503 m³** modelled built-up volume |
| Minimum/maximum positive cell values | 1 / 321,677 | 1 / 3,168,579 |
| Insurance Neon `sample_id` | **49** | **50** |
| Canonical Neon JSONB SHA-256 | `9b3e183d113c10f0fa1a1142ce9041813043874980eac67f038ef39802fd0ed5` | `a9bf86d9fbbe6c84fbd81ad6050a2d8774171af38953b7976e6dd48eabc01876` |

The original provider **block response SHA-256** is stored as
`provider_response_sha256` in Neon, *not* a claimed whole-object hash.
The signed-off source `rights_scope` is limited to the documented
CC BY 4.0 research sample. Both candidates were advanced from
`actual_sample_state=metadata_only` to
`collected_rights_cleared` **only for that single reviewed original
window**, retaining `commercial_reuse_verdict=allowed_verified`,
`admission_status=not_admitted` and all
`model_input_approved=false` flags. The original 32KiB prefix-only
samples **#43/#44** remain historical provenance alongside the actual
aggregate **#49/#50**.

Read-only replay inside the designated insurance Neon research database:

```sql
SELECT sample_id, source_id, sample_kind, provider_response_sha256,
       sample_sha256=encode(sha256(convert_to(sample_json::text,'UTF8')), 'hex')
         AS canonical_sample_hash_ok,
       sample_json->>'original_source_decoded_block_sha256' AS decoded_block_sha,
       sample_json->>'fixed_window_positive_non_sentinel_cells' AS positive_cells,
       sample_json->>'fixed_window_zero_cells' AS zero_cells,
       sample_json->>'fixed_window_positive_sum_raw_source_units' AS raw_unit_sum,
       model_input_approved, source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id IN (49, 50);
```

**Scientific interpretation remains explicitly limited:** built-up
surface per cell (m²) and modelled building volume per cell (m³)
are dependent GHSL estimates, not two independent building censuses.
The identical spatial nonzero mask does not prove roof/structure
identity, independent height, occupancy or TIV. At 30 arcseconds in
EPSG:4326, source raster grid pitch is angular and cannot itself be
treated as constant metric cell area. Full original TIFF SHA-256,
source-wide coverage, NoData semantics beyond the fixed observed
window, systematic spatial/temporal uncertainty, independent reference
building footprints and CAT model fitness are **not validated**.
Do not infer average height, unique buildings, insured TIV or event losses
from a ratio of these source sums. No source-model admission occurred.

## First original execution diagnosis and exact schema correction — 2026-11-12

The first trusted-main source workflow
[run 43308918239](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43308918239)
**failed closed** after the source-specific synthetic tests passed. It
reported `BLOCKED: original TIFF prefix verification rejected` before any
original compressed block was requested. **No original pixel values were
decoded, stored or admitted from that run.**

A separate fixed 4,096-byte original source-prefix inspection for **both**
unchanged JRC assets showed that TIFF tags `256` (width), `257`
(height), `322` (tile width), `323` (tile height) are all declared
**TIFF SHORT type 3**, as is valid for their numeric sizes. The first
offline parser incorrectly expected TIFF LONG type 4 for these four tags.
This is a code/schema mismatch, not evidence that the provider TIFF had
changed. The original 32 KiB and 4 KiB source SHA-256 pins remain unchanged,
and `BitsPerSample=32` plus `SampleFormat=1` remain the source
**UINT32 scientific raster value type**, independent of TIFF tag encoding.

The scoped correction requires **exact** original SHORT fields and adds
synthetic regression tests rejecting a LONG substitution. It does not
weaken or bypass the original SHA-256, HTTP Range, CRS, compression,
source byte ceiling or CAT model-admission checks. A corrected main
source run and actual successful original-byte logs are needed before
claiming original numeric cell samples.

## Original source and exact bounded retrieval contract

Source: European Commission JRC
[GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php)
(square metres built surface per gridded source cell) and
[GHS-BUILT-V R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buV2023.php)
(cubic metres modelled built volume per source cell). These are two
different derived products, not two independent observations of the same
quantity. Their original JRC
[surface licence notice](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/copyright.txt)
and [volume licence notice](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_V_GLOBE_R2023A/copyright.txt)
require CC BY 4.0 attribution and modification disclosure. No raw
original raster bytes or source location values are redistributed.

The [original 32 KiB source receipts](ghsl-built-s-v-original-native-32k-header-20261112.md)
are already pinned with SHA-256, true little-endian UINT32/Deflate
TIFF coding, EPSG:4326, 512×512 native block geometry, 2020 epoch
and 30-arcsecond angular pixel pitch. Two fixed, directly reviewed
S3 objects are accessed anonymously, with **exactly two sequential
HTTP Range GETs per product**, no retries, redirects, pagination or
bulk sweep:

| | BUILT-S surface | BUILT-V volume |
| --- | ---: | ---: |
| Reviewed original total TIFF bytes | 173,085,842 | 187,376,914 |
| Exact required header Range | `0–32767` (32,768 B) | `0–32767` (32,768 B) |
| Original 32 KiB SHA-256 | `002c21c644073b889df87135a95c902eecf8859b572458a021341ae5c90b35ea` | `7e61b8056273ea0f2fa84913c3458da6d5c38f52f41881af20a42b0d966e76bd` |
| Native block index | 809 | 809 |
| Native compressed block Range | `73699060–74222432` (523,373 B) | `80549811–81120367` (570,557 B) |
| Maximum decoded block bytes | 1,048,576 | 1,048,576 |
| Max original bytes permitted per request | 600,000 | 600,000 |

Each request must have HTTP **206**, the exact Content-Range
`bytes start-end/full-object-size`, exact Content-Length and a
reviewed TIFF/octet-stream MIME; any changed host, path, byte count,
compression, original header hash or full object length blocks the run.

## Independent scientific sample method

`scripts/probe_ghsl_built_native_original_block_v0.py` first invokes
the SHA-pinned original TIFF/CRS/table verifier. Only on success does
it request the preselected original compressed block, decode it
in memory via Python's bounded TIFF Deflate algorithm to exactly
`512*512*4` unsigned 32-bit bytes and inspect the **same fixed
32×32 native raster cell window** in the central Germany source-block
region. No other tiles, source dates, locations or caller-selected
areas are allowed. The output is limited to source-byte SHA-256s,
the decoded-block SHA-256, the fixed-window uint32 SHA-256 and
aggregate counts/sums/min/max values.

**No individual pixel array is output, saved in Neon, logged in
Actions or added to the public repository.** Any value equal to
`2^32−1` is reported separately as a *candidate* NoData sentinel:
the code intentionally sets
`uint32_max_nodata_semantics_approved=false`. Native raster
units are interpreted only according to the publisher's
product-specific definitions, not as individual buildings,
ground surface square metres, TIV, hazard depth or flood/wind damage.

The main-only source workflow is
`.github/workflows/ghsl-built-native-original-block.yml`.
On untrusted pull requests it performs **synthetic/offline
tests only**; on the reviewed main branch, a source-specific
push or explicit manually dispatched run tests each fixed original
product once in a transient GitHub runner. No credentials or signed
URLs are required. No original artifacts are uploaded.

## Interpretations and next gate

The exact full source TIFF file SHA-256 is not obtained; the original
source block SHA-256 will be measured during the first successful
live run, not guessed. The pixel values are **not** yet independently
checked against ground truth, and one historical 2020 epoch is not
a current building survey. Source spatial reference degrees,
uncertainty, source scale and NoData meanings must be reviewed
before use in a scientific CAT exposure model.

After **actual verified main-run success**, stage the aggregates into
the *separate* insurance research Neon source-sample table as
`sample_kind=observed_values`, with the literal original compressed
block digest from the completed run. Verify the canonical JSONB
sample hash and change only the strictly reviewed
`actual_sample_state` to `collected_rights_cleared`.
All model-admission and source-file/raw-byte persistence flags remain
false. If either original read is unavailable or mismatched, document
**BLOCKED** and do not stage fabricated or synthetic values as original.
