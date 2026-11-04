<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Physrisk original S3 Zarr metadata: WRI Aqueduct Floods v2 (2026-11-04)

**Outcome:** A bounded, anonymous, real-source metadata inspection succeeded for
the Physrisk-hosted WRI Aqueduct Floods v2 historical *coastal* flood, *no
subsidence* return-period depth raster. An offline fail-closed preflight and five
synthetic regression tests were executed locally, including an original-response
metadata receipt. **No array chunks, raw hazard cells, insurer portfolios or
third-party bytes are committed to Git. No scientific or rights approval is granted.**

## Original provider identity and cross-source lineage

- WRI primary source: https://www.wri.org/data/aqueduct-floods-hazard-maps
- WRI detailed Version 2 file documentation: https://aqueduct.wridata.org/AqueductFloods20/index.html
- WRI current data catalogue: https://datasets.wri.org/datasets/aqueduct-floods-hazard-maps
- Physrisk public S3 collection: https://registry.opendata.aws/os-climate-physrisk/
- OS-Climate source inventory: https://github.com/os-climate/hazard/blob/main/src/inventories/hazard/inventory.json
- Canonical pre-existing WRI discovery ID: wri.aqueduct-flood-hazard.v2.2020.
- New Physrisk collection discovery ID on this PR: osclimate.physrisk.hazard-indicator-public-bucket.

The Physrisk representation is a **derived/repackaged hazard indicator**, not
an independent observation or a second WRI original. WRI cautions that Aqueduct
v2 flood surfaces are *modelled without flood protection*. WRI v2 was updated
on 2020-10-20, with a bias-correction revision affecting *riverine* maps.
A Physrisk transformation and a WRI GeoTIFF have not yet been reconciled
pixel by pixel, by source vintage, or by licence.

## Exact anonymous read-only source receipts

Original S3 array directory:

https://os-climate-physical-risk.s3.amazonaws.com/hazard-indicators/hazard.zarr/inundation/wri/v2/inuncoast_historical_nosub_hist_0/

2026-11-04 HTTP original-body fetches and local SHA-256:

| File | Original bytes | SHA-256 |
| --- | ---: | --- |
| .zarray | 369 | 1bfbe634ad340babd209a023f9b710da843fd7766994e9dcb4976370edf08e45 |
| .zattrs | 486 | b8135f52fa34025180c625ce65bb3b8b730bef8ef6796c98fb7ae6e296631305 |

Observed array: Zarr v2, Float32 little endian, shape 9 x 21,600 x 43,200,
chunks 9 x 1,000 x 1,000, Blosc/LZ4, value 0.0 for the fill field. Observed
metadata names three dimensions (index, latitude, longitude), calls the first
**return period (years)** and gives the indices 2, 5, 10, 25, 50, 100, 250,
500, 1,000. CRS is source-native +init=epsg:4326, transform has longitude
step +1/120 degree, latitude step -1/120 degree, nominal upper-left origin
(-180, 90). The original WRI provider documents depth units as **meters**;
the inspected Zarr .zattrs did not itself explicitly state meters.

These metadata establish a **30-arc-second modelled depth grid per return
period**, NOT an observation sequence, yearly event occurrence record, named
storm event, insurance loss or 9 independently occurring Poisson events.
Even if a downstream model uses return-period levels to fit a marginal hazard
severity distribution, dependence, event generation, coastal defences,
vulnerability and policy terms require separate modelling/validation.

A complete uncompressed array would contain 8,398,080,000 Float32 cells
(33,592,320,000 bytes). Do not download the full cube merely to test access.
The observed fill field does not by itself prove whether zero means dry,
masked, missing or an admissible depth. Use source-native masks/NoData and
upstream publisher documentation before physical sampling.

## Offline fail-closed executable gate

research_runners/physrisk_wri_aqueduct_coastal_zarr_preflight_v0.py reads two
independently SHA-pinned source-response byte files and emits only aggregate
metadata plus explicit **model_input_admitted=false** and
**annual_event_catalogue_present=false**. It never connects to S3 or reads
array chunks. The source bytes stay in an external local directory.

Example (using files acquired separately from the exact above URLs):

    python research_runners/physrisk_wri_aqueduct_coastal_zarr_preflight_v0.py \
      /private/source/.zarray /private/source/.zattrs \
      --expected-zarray-sha256 1bfbe634ad340babd209a023f9b710da843fd7766994e9dcb4976370edf08e45 \
      --expected-zattrs-sha256 b8135f52fa34025180c625ce65bb3b8b730bef8ef6796c98fb7ae6e296631305 \
      --out /tmp/physrisk-wri-coastal-metadata-receipt.json

    python -m unittest discover -s tests -p test_physrisk_wri_aqueduct_coastal_zarr_preflight_v0.py
    python scripts/check_all.py

The hashes pin **the inspected responses only**, not a claim of permanent
publisher immutability. Re-fetch only with authorised bounded probes and
re-pin any changed source edition following review.

## Separate critical exclusion: Jupiter source entries

The same OS-Climate inventory lists Jupiter hazard layers, including the
previously probed days-above-35C example. The individual inventory marks
Jupiter's licence as **Commercial** and expressly says its data should not
be used for emergency management, public safety, physical safety or property
endangerment. The public AWS bucket notice of no restrictions and anonymous
technical access **must not** be treated as broader rights for Jupiter
upstream-derived assets. We therefore do not sample Jupiter chunks, use them
for CAT model calibration, or admit them for NextGen.

## Next scientific and legal gates

1. Confirm the specific WRI-to-Physrisk version lineage, transformation and
   legal scope, including the primary provider and publisher attribution.
2. Compare a tiny permitted sample of Physrisk transformed depth values
   against corresponding exact-release WRI GeoTIFF pixels, using the source
   geospatial transform, depth units, nodata and coastal-defence semantics.
3. Only then consider a **hazard marginal** benchmark, with independently
   validated treatment of return periods. An event frequency catalogue/YLT,
   exposure, vulnerability, insured losses and reinsurer response are **not
   supplied** by these surfaces.
4. Keep source review and model-input admission blocked until all relevant
   gates and exact original-asset identities are satisfied.

## Original WRI GeoTIFF catalogue-to-Physrisk coverage gate (4 November 2026)

The authoritative [WRI Aqueduct Floods v2 file listing](https://aqueduct.wridata.org/AqueductFloods20/index.html) was fetched as an exact UTF-8 HTML original response via a bounded read-only HTTP request. At the observed 2026-11-04 retrieval, the original response was **59,487 bytes**, SHA-256
`04157a7069d172a0e10f85db7b3e5db33007265ec33c0ec5720a6a346404b4ad`.
This is the *HTML index response*, **not** a TIFF, tile, provider version/edition digest or confirmation that every linked large TIFF is accessible.

The original WRI catalogue lists **ten** separate historical *coastal / no subsidence* single-band Float32 GeoTIFFs for return periods
`[1.5, 2, 5, 10, 25, 50, 100, 250, 500, 1000]` years. Its file naming pattern is
`inuncoast_historical_nosub_hist_rpXXXX_Y.tif`. In contrast, the exact Physrisk-derived `.zattrs` index lists **nine** return periods:
`[2, 5, 10, 25, 50, 100, 250, 500, 1000]` years. The **1.5-year** original is missing from that specific Zarr array. This may be a deliberate producer subset; it is **not** assumed to be corruption, a missing site, an intensity-zero period, or a new independent event. Exclusion must be explicit when comparing marginal hazard distributions.

The new executable, `research_runners/wri_physrisk_coastal_return_period_crosswalk_v0.py`, binds the exact original WRI index HTML and exact Physrisk `.zattrs` to separately provided SHA-256 receipts, checks all ten WRI hrefs and all nine Physrisk index values, refuses duplicates/missing periods or mixed subsidence/scenario names, and emits only the **nine potential WRI original GeoTIFF URLs corresponding to Physrisk** plus the one unmatched WRI 1.5-year file identity. It **does not** claim any original TIFF was fetched or pixel values matched.

```bash
python research_runners/wri_physrisk_coastal_return_period_crosswalk_v0.py \\
  /private/original/wri-v2-index.html \\
  /private/original/physrisk-wri-coastal.zattrs \\
  --expected-wri-sha256 04157a7069d172a0e10f85db7b3e5db33007265ec33c0ec5720a6a346404b4ad \\
  --expected-zattrs-sha256 b8135f52fa34025180c625ce65bb3b8b730bef8ef6796c98fb7ae6e296631305 \\
  --out /tmp/wri-physrisk-coastal-crosswalk.json

python -m unittest discover -s tests -p 'test_wri_physrisk_coastal_return_period_crosswalk_v0.py'
```

For original data comparison, choose **a bounded single return period and small window**, pin the WRI TIFF original asset revision, inspect and preserve both GeoTIFF and Zarr geotransforms/nodata conventions, and then compare paired pixel values against a tolerance informed by producer conversion. Do **not** construct annual independent events from these nine quantile/return-period surfaces. Full random-event chronology, inter-site peril correlation, defended depth, insured exposure and loss distribution are all additional missing layers.

## Original WRI 2-year GeoTIFF byte-range geometry / NoData preflight (2026-11-04)

**Actual provider original, not a filename-only check:** read-only HTTP `Range` requests to the provider's exact
[`inuncoast_historical_nosub_hist_rp0002_0.tif`](https://aqueduct.wridata.org/AqueductFloods20/inuncoast_historical_nosub_hist_rp0002_0.tif).
The three independently bounded response bodies (no complete TIFF) are:

| Absolute original HTTP byte range | Returned bytes | SHA-256 |
| --- | ---: | --- |
| `0-1023` (classic TIFF header) | 1,024 | `a715eac20b82b4f9fe377e69a279d5445f46b3a58e0818d56be207af7c58f1ee` |
| `44820220-44822267` (first IFD) | 2,048 | `c722b9ba36751d0331fe961730c5865024dc183b58233e33e02a5c47194c638e` |
| `44993200-44993711` (GeoTIFF auxiliary data, through provider EOF) | 208 | `1d7f0b4f46c6d2f97979794ba8858b954a445dcfa218e15ab04bcf4e73c84a3e` |

Decoded, exact original TIFF header/IFD evidence:
- little-endian classic TIFF, IFD pointer at **44,820,220**; 18 IFD entries;
- image width **43,200**, height **21,600**, single-band **Float32**, compression **LZW**, one raster row per strip;
- `ModelPixelScaleTag` = 1/120 by 1/120 degree, `ModelTiepointTag` = grid (0, 0) at longitude -180, latitude +90;
- GeoKey confirms EPSG:**4326** (WGS84); **original WRI TIFF NoData = `-9999`**, identified in GDAL NoData ASCII tag 42113.

**Material cross-format gap:** Physrisk's separately fetched derived Zarr `.zarray` declares `fill_value=0.0`.
The raster grid dimensions and georeferencing *appear consistent*, but **`-9999` versus `0.0` is not an established mapping**. It may reflect legitimate transformation, masking or source conventions, and must **not** be converted into zero inundation depth, filled into building losses or treated as resolved without original paired cell comparison. The original TIFF band has not been decoded and the transformed Zarr has not been sampled. An open-file HTTP byte-range probe does **not** grant a licence or scientific approval.

New offline validator `research_runners/wri_aqueduct_original_tiff_range_preflight_v0.py` accepts only these exact, independently SHA-pinned original range responses, validates TIFF width, height, data type, original GeoTIFF tiepoints/CRS and original NoData, and emits only a fail-closed metadata receipt, including
`nodata_to_zarr_fill_transformation_verified=false`, `pixel_values_read=false` and `model_input_admitted=false`. Its tests are purely synthetic and preserve rejection of changed source offsets, EPSG, georeference, NoData, broken range lengths and wrong SHA.

```bash
python research_runners/wri_aqueduct_original_tiff_range_preflight_v0.py \
  /private/original/tiff-header.range \
  /private/original/tiff-first-ifd.range \
  /private/original/tiff-geodata.range \
  --expected-header-sha256 a715eac20b82b4f9fe377e69a279d5445f46b3a58e0818d56be207af7c58f1ee \
  --expected-ifd-sha256 c722b9ba36751d0331fe961730c5865024dc183b58233e33e02a5c47194c638e \
  --expected-geo-sha256 1d7f0b4f46c6d2f97979794ba8858b954a445dcfa218e15ab04bcf4e73c84a3e \
  --out /tmp/wri-original-geo-metadata-receipt.json

python -m unittest discover -s tests -p 'test_wri_aqueduct_original_tiff_range_preflight_v0.py'
```

A scientifically meaningful next stage needs **a separately permitted, bounded original TIFF strip and corresponding Physrisk Zarr chunk**, preserving `-9999` nodata, `0.0` fill, compression and exact cell/return-period axes. No pixel equivalence claim, loss curve, simulated YLT or original-source admission yet.

## OS-Climate importer source code vs currently published Zarr: vintage mismatch

Original upstream code inspection at OS-Climate GitHub (2026-11-04):

- [`src/hazard/onboard/wri_aqueduct_flood.py`](https://github.com/os-climate/hazard/blob/main/src/hazard/onboard/wri_aqueduct_flood.py), exact Git blob SHA `c9599366ba5e0f3f825d50a70caa6e987ec770b5`. `WRIAqueductFlood.__init__` hard-codes return periods `[2,5,10,25,50,100,250,500,1000]`; `onboard()` reads original WRI TIFF bands and explicitly executes `values[values == -9999.0] = float("nan")` before writing `z[i,:,:]`. `generate_tiles_single()` separately calls `create_tile_set(..., nodata=-9999.0, nodata_as_zero=True)` for visualization tiles; a map display rule is **not** a license to convert raw flood depth NoData to zero.
- [`src/hazard/sources/osc_zarr.py`](https://github.com/os-climate/hazard/blob/main/src/hazard/sources/osc_zarr.py), exact Git blob SHA `24e269b3d3307aa55a477aacf51041387ba70b0d`, has `_zarr_create()` using `fill_value=float("nan")` and `write_empty_chunks=False`.
- **In contrast**, the real distributed OS-Climate WRI Zarr `.zarray` fetched in this research has `fill_value=0.0` (see pinned original 369-byte response above).

This is **positive evidence that the published derivative's actual binary encoding/producer revision cannot be inferred just from the current upstream code**. The source code explains an *intended* `-9999 -> NaN` transformation, but there is still no pinned provenance proving that the public Zarr object was built from these exact blobs or preserving NaNs at the chosen pixels. Treat this as a **source/code-vintage conflict**, not a confirmed scientific error. Do not equate producer `NaN`, TIFF `-9999` and Zarr fill `0.0`; keep importer and scientific model gates blocked until exact derived-object lineage and cellwise comparisons resolve which interpretation is correct. If the provider has a versioned build receipt, acquire that rather than guessing from `main`.

## Executed paired original GeoTIFF / derived Zarr **cell values** — 4 November 2026

**Outcome:** A real, bounded 1,000-cell **Float32** comparison was executed on the *same WRI historical coastal/no-subsidence 2-year depth surface* in its original GeoTIFF and a public OS-Climate Physrisk transformed Zarr. Original TIFF LZW and derived Zarr Blosc/LZ4 byte-shuffle were independently decoded in-memory. No raster array/chunk/strip bytes are added to Git.

### Exact geographic and array selection

- Global grid row **7206**, centre latitude `29.9458333333° N`; global columns **10000–10999**, centre longitudes approximately **-96.6625° to -88.3375°**, covering a narrow, one-row US Gulf Coast transect, **not a representative global sample**.
- WRI original: [historical/no-subsidence/rp0002_0.tif](https://aqueduct.wridata.org/AqueductFloods20/inuncoast_historical_nosub_hist_rp0002_0.tif); first IFD identifies Float32, LZW and **one row per strip**.
- Derived Physrisk: [Zarr `0.7.10` chunk](https://os-climate-physical-risk.s3.amazonaws.com/hazard-indicators/hazard.zarr/inundation/wri/v2/inuncoast_historical_nosub_hist_0/0.7.10), with *Zarr index 0 = 2-year return period*, 1,000 × 1,000 spatial chunk; Blosc **block index 1**, offset **37004** of a **1,162,420-byte compressed object**.
- The chosen partial Blosc block covers **131,072 Float32 cells** of the 9 × 1,000 × 1,000 chunk; its four independently LZ4-compressed byte-shuffle streams were decoded to 131,072 bytes each.

### Minimal exact read-only source-byte receipts

| Source | Absolute byte range | Bytes | SHA-256 of *that returned range* |
| --- | --- | ---: | --- |
| WRI TIFF row-offset table entry (row 7206) | `44935666–44935669` | 4 | `3b68c20cb1b4c84524ca3ff529add0a4a8301a65e89737010d66add57e0f6085` |
| WRI TIFF row-bytecount table entry (row 7206) | `44849266–44849269` | 4 | `73127703586268c82467f1ee6461b3377cf3ecb535acc8cd3bd0c55eb9c2e768` |
| WRI compressed original LZW row | `15020376–15022920` | 2,545 | `9e1003f381fc224621d88ea901f40a12daadcfa7112b1fe8fc942c68cd8bca5d` |
| Physrisk Zarr chunk Blosc header and block-offset table | `0–4095` | 4,096 | `ae3cfe008420624c637d489d4f6faaaf496ddc906a4430f512c7580619540120` |
| Physrisk compressed Blosc block 1 | `37004–60269` | 23,266 | `cc8272a08fc242b33123d099a76abec19d6e64f9668b3d3931cc34485a494c0b` |

The TIFF row-offset bytes decode to **15,020,376**, and its row-bytecount decodes to **2,545**. The Blosc header reports 36,000,000 logical uncompressed bytes, 524,288-byte blocks, Float32 (4-byte type), compressed object size 1,162,420, and the block-offset table independently pins block 1 to 37,004. **Only these bounded ranges, not either entire raster asset, were retrieved.**

### Independent paired comparison result

| Category on 1,000 selected cells | WRI original Float32 | Physrisk Float32 | Pairing |
| --- | ---: | ---: | --- |
| Numeric zero | 813 | 813 | **813 exact Float32 byte matches** |
| Positive depths | 4 | 4 | **4 exact Float32 byte matches** |
| Original NoData | 183 at `-9999` | 183 as IEEE `NaN` | **183 / 183 category matches** |
| Unexplained discrepancy | — | — | **0** |

Example positive matched original and derived cells at columns 10889, 10939, 10940 and 10941:
**0.2220311165 m, 0.8582940698 m, 0.7227445841 m, 0.4280654192 m**, respectively. The 817 non-NoData cells match *exact Float32 byte values*, not a rounded visual or approximate tolerance. The 183 NoData cells match in category (`-9999 → NaN`), **not in numeric value**.

**Key conclusion:** For this one sampled region and 2-year return period, the on-disk published Zarr data preserve **NaN** for the original TIFF `-9999` cells even though that Zarr array metadata declares a default `fill_value=0.0`. The fill metadata and the actual compressed blocks describe different concepts. This is consistent with the current OS-Climate WRI source code converting `-9999 → NaN`, but cannot prove the historical production commit or any unsampled/unwritten chunk semantics.

### Reproducible offline source-byte gate

`research_runners/wri_physrisk_coastal_paired_strip_preflight_v0.py` accepts the **five independently acquired, exact original HTTP response byte files** above, pins their SHA-256 and lengths, decodes TIFF LZW + Blosc/LZ4 with only Python standard library, verifies pairing and class counts, and produces a small receipt with
`published_build_revision_proven=false`, `all_return_periods_verified=false`, `model_input_admitted=false`. The paired geographic cells are not released as a raster product or copied into Git. Synthetic-only unit tests cover codecs, malformed input, Float32 exact match, missing-value conversion and incorrect alignment.

The offline gate deliberately refuses any changed source bytes, re-ordered/index-drift original artefacts, unsafe decoded sizes or changed sample-class counts. To re-run it, save **only the five allowed original byte-range responses** outside Git, use the exact original URLs and byte ranges above and then run:

```bash
python research_runners/wri_physrisk_coastal_paired_strip_preflight_v0.py \
  --tiff-offset /private/original/tiff-row-offset-4b.bin \
  --tiff-bytecount /private/original/tiff-row-bytecount-4b.bin \
  --tiff-strip /private/original/tiff-row-2545b.bin \
  --zarr-header /private/original/zarr-chunk-header-4096b.bin \
  --zarr-block /private/original/zarr-block1-23266b.bin \
  --out /tmp/wri-physrisk-paired-1000-cell-receipt.json

python -m unittest discover -s tests -p 'test_wri_physrisk_coastal_paired_strip_preflight_v0.py'
python scripts/check_all.py
```

### Scientific and legal remaining blockers

- **One row/one period is not a global validation:** Other regions, 8 other Physrisk return-period surfaces, 1.5-year upstream-only original, geospatial boundary cases, unsampled chunks and year/scenario variants remain unchecked.
- Publisher original TIFF and derived Zarr **full-asset immutable versions and exact build commit remain unproven**. The listed hashes refer only to exact HTTP response ranges.
- Source/product-specific rights and derivative redistribution require final review before a production, proprietary or public data build; no model input is admitted from this analysis.
- Return-period maps give marginal exceedance-depth levels, not stochastic storm event IDs, spatial hazard dependence, financial insured losses, ELTs, YLTs or CAT treaty results.
