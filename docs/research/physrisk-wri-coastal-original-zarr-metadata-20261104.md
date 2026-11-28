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

**Initially unresolved metadata-only cross-format gap (see later paired-cell result):** Physrisk's separately fetched derived Zarr `.zarray` declares `fill_value=0.0`.
The raster grid dimensions and georeferencing *appear consistent*. At this earlier stage, **`-9999` versus `0.0` was not yet an established mapping**. The later paired original-byte comparison validates `-9999 → NaN` for **183 sampled pixels**, but **unverified regions or missing chunks still must not automatically be interpreted as zero inundation depth or used in building losses**. This paragraph describes the earlier metadata-only stage. A later **1,000-cell paired comparison** below now decodes one TIFF row and one aligned Blosc block. Even that proof does **not** grant a licence or scientific model approval.

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

This is **positive evidence that the published derivative's original build revision cannot be inferred just from current upstream code**. The source code explains an *intended* `-9999 -> NaN` transformation, but the exact producing commit is still not pinned. A later original-byte pair comparison confirms NaNs in 183 sampled cells without proving the global construction history. Treat this as a **source/code-vintage conflict**, not a confirmed scientific error. Do not equate producer `NaN`, TIFF `-9999` and Zarr fill `0.0`; keep scientific and rights/model-input admission blocked until broader pixel comparisons and original derivative-version lineage are established. If the provider has a versioned build receipt, acquire that rather than guessing from `main`.

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

## Executed independent second WRI/Physrisk paired-pixel challenge: Bay of Bengal, 100 years (2026-11-04)

**New source-backed result, independently positioned from the previous US Gulf Coast sample:** original WRI Aqueduct Floods v2 historical **coastal, no subsidence, 100-year** return-period GeoTIFF matched its corresponding Physrisk derived Zarr for **1,000** paired cells in a one-row Bay of Bengal transect. The return period is **100 years**, not the first sample's 2 years. The world grid row is **8100** (~22.4958333°N) and global columns are **32000–32999** (~86.6708333°E to 94.9958333°E). It spans parts of eastern India/Bangladesh and the surrounding area. This is NOT a stratified or global accuracy measure.

### Exact source identities and byte-range receipts

- WRI original: [`inuncoast_historical_nosub_hist_rp0100_0.tif`](https://aqueduct.wridata.org/AqueductFloods20/inuncoast_historical_nosub_hist_rp0100_0.tif). Its classic TIFF first IFD is at original byte **46,209,472**; the IFD width/height and Float32 LZW scheme were inspected through a separate bounded source metadata request. Original strip pointer for row 8100 = **17,824,039**, compressed strip size = **4,291 bytes**.
- Physrisk-derived Zarr: [`0.8.32`](https://os-climate-physical-risk.s3.amazonaws.com/hazard-indicators/hazard.zarr/inundation/wri/v2/inuncoast_historical_nosub_hist_0/0.8.32), where the first chunk index is zero because the Zarr chunks all **nine** return periods in one physical chunk. Inside, 100 years corresponds to return-period **array index 5**. The selected Blosc compressed **block #38** starts at original object offset **1,380,254**, ends just before **1,466,009**, length **85,755** bytes. The S3 object was listed with compressed size **2,375,870 bytes**. The Blosc block consists of four compressed byte-shuffle streams; each expands to 131,072 bytes, allowing comparison of the exact selected source pixels.

Seven independently fetched bounded original HTTP response parts (no complete TIFF, no entire Zarr object):

| Original | Inclusive byte range | Bytes | SHA-256 of received original response |
| --- | --- | ---: | --- |
| WRI TIFF row-strip offset entry | `46328494–46328497` | 4 | `241a517ef24d0a4d13ecc1223a5e15673fd57de102e3b7e6e8414bce187b10e2` |
| WRI TIFF row-strip bytecount entry | `46242094–46242097` | 4 | `d4251ca6381f532ec18b0ba155f27737f25a8abfddde141cab0ac80f7a171bf0` |
| WRI original LZW strip | `17824039–17828329` | 4,291 | `272f3ca2ddb9c39e2218e96980c34d4ed60b04d651023a3e4da4e6ffa127b5fd` |
| Zarr object Blosc header and offsets | `0–4095` | 4,096 | `d0d1abe763ca50acc59706516a12d744d359d81c235d0ba1b9c0e1fa4b8dfad8` |
| Zarr Blosc block #38 — bounded segment 0 | `1380254–1410253` | 30,000 | `ea204ee2f7a0380e1ee0507c410690fded8173425a52aa933a3b54d7433464fd` |
| Zarr Blosc block #38 — bounded segment 1 | `1410254–1440253` | 30,000 | `3aa2077b06753066c10b9bc1ae127e1dd986407bfeaa1e40a457b5c897a71d55` |
| Zarr Blosc block #38 — bounded segment 2 | `1440254–1466008` | 25,755 | `0845dd587ce5d4ca91b718140de8e554cf12c47dadca0ded0b22c26796c68450` |

The **concatenation of the three contiguous Zarr source responses**, in sequence, has SHA-256 `9144355508425d0f703c309d28e919c019ca4c52841ec2e000e3c69849a5d8f5`. Each segment and the reconstructed compressed block are pinned independently. The blocks never leave the local inspection workspace or enter Git. Original HTTP range body sizes were verified; none of these SHA-256s is a whole-TIFF or whole-Zarr object hash.

### Actual paired source/derived pixel results

| Pair category | Number | Outcome |
| --- | ---: | --- |
| Both source and derivative finite zero | **594** | All bit-identical Float32 |
| Both finite positive coastal depth | **334** | All bit-identical Float32 |
| Original `-9999` NoData -> derived IEEE `NaN` | **72** | All match as missing-value category |
| Unexplained mismatches | **0** | None in this selected 1,000-cell section |

Selected **exact matching positive depths** include source/derived column **32140 = 0.8493490219 m**, **32144 = 1.1128225327 m**, **32146 = 5.9934983253 m** and **32147 = 4.3581857681 m**. All 928 finite values match *exact Float32 bytes*; NoData is compared by category, not falsely claimed numerically equal.

**Two independent locations and return periods now validated:** **2,000** cells total across the earlier US Gulf Coast 2-year transect and this East India/Bay of Bengal 100-year transect: **1,745 exact finite pairs** (1,407 zero and 338 positive), **255 original NoData correctly stored as `NaN`** and **zero observed discrepancies in these windows**. These counts are selected diagnostics, not an unbiased estimate of global CAT-model error.

### Reproducible offline code and fail-closed scope

The repository now includes `research_runners/wri_physrisk_coastal_second_window_preflight_v0.py` and accompanying **synthetic-only** regression tests `tests/test_wri_physrisk_coastal_second_window_preflight_v0.py`. The validator reads only the seven exact outside-Git original byte-range response files, checks each SHA/length and reassembled block SHA, verifies TIFF strip pointer/size, the Blosc 69-entry offset table and type/codec, decompresses the bounded LZW and four LZ4 streams, and challenges all 1,000 paired values/categories. It refuses invalid geometry, inconsistent lengths, unexpected positive/zero/NoData counts and any source drift. It reports `model_input_admitted=false`.

```bash
python research_runners/wri_physrisk_coastal_second_window_preflight_v0.py \
  --tiff-offset /private/wri100/row8100-offset-4b.bin \
  --tiff-bytecount /private/wri100/row8100-bytecount-4b.bin \
  --tiff-strip /private/wri100/row8100-lzw-4291b.bin \
  --zarr-header /private/physrisk100/chunk0.8.32-header-4096b.bin \
  --zarr-part0 /private/physrisk100/block38-part0-30000b.bin \
  --zarr-part1 /private/physrisk100/block38-part1-30000b.bin \
  --zarr-part2 /private/physrisk100/block38-part2-25755b.bin \
  --out /tmp/wri-physrisk-second-window-proof.json

python -m unittest discover -s tests -p 'test_wri_physrisk_coastal_second_window_preflight_v0.py'
python scripts/check_all.py
```

**No scientific or commercial admission:** The exact build/producer commit of public Zarr, the full TIFF and Zarr source-object fingerprints, original rights and derivative-use permissions, other coastal return periods/geographies, all riverine inputs, defence effects, vulnerability, exposure and risk dependence are still unverified. The 1.5-year WRI original return period remains absent in the nine-period Physrisk derived source. Neither return-period collection supplies event IDs, an annual occurrence/YLT generator, reinsurance losses nor insurers' actual insured TIV.

## Original Physrisk nine-return-period monotonicity / mask audit (4 November 2026)

**New executed real-source read-only test:** All **nine** historical coastal, *no subsidence* Physrisk/WRI return-period planes were checked on the **same 1,000 Bay of Bengal cells**: original world raster row 8100, global columns 32000–32999 (22.4958333°N, approximately 86.6708333–94.9958333°E). Source object:
https://os-climate-physical-risk.s3.amazonaws.com/hazard-indicators/hazard.zarr/inundation/wri/v2/inuncoast_historical_nosub_hist_0/0.8.32

Using the independent original Zarr array metadata source receipts, each return period maps to a different **Blosc compressed block** within the *same* 9×1,000×1,000 Zarr chunk. Original HTTP ranges were individually fetched in <=40,000-byte fragments and concatenated in source byte order; each reassembled **complete compressed block** is independently SHA-256-pinned. No complete Zarr object was downloaded, no third-party raster bytes entered Git and no actual input assets were uploaded to Neon.

| Return period (years) | Blosc block | Original compressed HTTP byte range (inclusive) | SHA-256 of reassembled block |
| ---: | ---: | --- | --- |
| 2 | 0 | 81215–127556 | 045b4f5a6d7967e66e0ae44d34f926f5ec2b1062bbdac0cbe0d92fee4fddca7e |
| 5 | 8 | 390129–499231 | 79ed33e93d9a2c7dcfbc49b152609bce9bddab2987c908f0691c12dda72b688a |
| 10 | 16 | 519441–632668 | 343c1dd325eed5af633a50638f7f7a272c0075381874fd9951f435ff0d63383f |
| 25 | 23 | 798336–912377 | 2c3a6eb4ddbea6c19da6f65b4d0037630bc7889c2903dd361f48f3bc14aecf7e |
| 50 | 31 | 1088543–1242359 | 71980e6dc36f4735d895be13e1ab8bb9e1fd89b8f7528a8ad98c16d2951ce7f0 |
| 100 | 38 | 1380254–1466008 | 9144355508425d0f703c309d28e919c019ca4c52841ec2e000e3c69849a5d8f5 |
| 250 | 46 | 1657387–1804362 | c8d36d83d2ba920a458e1e4cb54db46dfcde10c1b37a81c7e8d3869b4f9ced38 |
| 500 | 54 | 1950955–2110961 | 2ed7f66bb72a72d604ca6e9027c09ba69e536fddaa7d7b7507745e0c1bbe3f7f |
| 1000 | 61 | 2256526–2375869 | 7bf594f62bc4e9c7e26311869df19188a2e77f7a72f4487dda0a5c6c26837d0d |

Bounded original 4,096-byte chunk header SHA-256 = \`d0d1abe763ca50acc59706516a12d744d359d81c235d0ba1b9c0e1fa4b8dfad8\`; header states 69 Blosc blocks, byte-shuffled Float32 with 524,288 uncompressed bytes per ordinary block and original compressed object total 2,375,870 bytes. The exact nine block extents and offsets were independently checked against the original 69-entry header index. These hashes **only** prove the selected source responses, not an immutable globally versioned release.

### Actual 1,000 cells × nine return periods, no invented or synthetic depths

| RP years | Positive finite cells | Zero finite cells | NaN NoData cells | Selected positive example at global column 32146 (m) |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 110 | 818 | 72 | 0.000000000 |
| 5 | 213 | 715 | 72 | 3.797132969 |
| 10 | 252 | 676 | 72 | 4.274469852 |
| 25 | 288 | 640 | 72 | 4.991788387 |
| 50 | 312 | 616 | 72 | 5.516768932 |
| 100 | 334 | 594 | 72 | 5.993498325 |
| 250 | 357 | 571 | 72 | 6.621191025 |
| 500 | 368 | 560 | 72 | 7.095147610 |
| 1000 | 378 | 550 | 72 | 7.568761349 |

**Verified:** 928 locations have finite, nonnegative values in all nine periods; the exact same 72 locations are **NaN** throughout; no mixed-missing cell was observed. All eight adjacent return-period transitions at these 1,000 aligned locations yield **8,000 total comparisons: 7,424 finite pairs, 576 both-NaN pairs, 2,502 strictly increasing pairs, 4,922 equal pairs, zero decreases, zero valid↔missing transitions**. No negative, infinite or otherwise invalid Float32 value was observed.

The increasing depth at global column 32146 is one illustrative source cell only. This is not an empirical statement about water depth at a specific building; it is a modelled flood *return-period intensity surface*.

**New executable quality gate:** \`research_runners/wri_physrisk_coastal_nine_period_monotonicity_v0.py\` (stdlib only) binds the original 4,096-byte Blosc header plus the **nine exact original compressed block byte-range files**, checks full response lengths and SHA-256, compressed block offsets, Blosc/LZ4 codec and byte-shuffle, spatial/period indexing and per-cell finite/missing conditions. For this original-source evidence it **fails closed** if any of the pinned per-period populations or adjacent-pair monotonicity/mask categories changes. Its synthetic-only regressions are in \`tests/test_wri_physrisk_coastal_nine_period_monotonicity_v0.py\` and deliberately introduce decreasing depths, altered NoData masks, negative/infinite values and truncated/hijacked compressed inputs.

Example using the exact original response ranges from the table (for source files acquired and joined **outside** the Git repository):

\`\`\`bash
python research_runners/wri_physrisk_coastal_nine_period_monotonicity_v0.py \
  --zarr-header /private/physrisk-rp/zarr-header-4096b.bin \
  --rp-2 /private/physrisk-rp/2y-blosc.bin \
  --rp-5 /private/physrisk-rp/5y-blosc.bin \
  --rp-10 /private/physrisk-rp/10y-blosc.bin \
  --rp-25 /private/physrisk-rp/25y-blosc.bin \
  --rp-50 /private/physrisk-rp/50y-blosc.bin \
  --rp-100 /private/physrisk-rp/100y-blosc.bin \
  --rp-250 /private/physrisk-rp/250y-blosc.bin \
  --rp-500 /private/physrisk-rp/500y-blosc.bin \
  --rp-1000 /private/physrisk-rp/1000y-blosc.bin \
  --out /tmp/physrisk-wri-coastal-nine-rp-monotonicity.json

python -m unittest discover -s tests -p 'test_wri_physrisk_coastal_nine_period_monotonicity_v0.py'
python scripts/check_all.py
\`\`\`

### Strict conclusions and remaining blockers

This is **one** deliberately selected region and only the nine return-period bands of one Physrisk *derived* coastal Zarr object. It is neither a global/raster-wide nor an upstream original-WRI GeoTIFF monotonicity audit. The earlier original WRI vs Physrisk cellwise comparisons remain limited to *two return periods and two locations*. The WRI-only 1.5-year return period is missing here; source-defence protection, tidal and subsidence differences, regional uncertainty, full-object producer revision, upstream rights, other hazard types/regions and the possibility of independent events/correlated annual modelled losses have **not** been resolved. Consequently all admission flags must remain **false** and no CAT event/YLT, insurer TIV, OEP/IP gross/net or reinsurance output may be derived directly from this gate.

## Executed THIRD original WRI TIFF / Physrisk sample — European North Sea, RP 100 years (2026-11-04)

**Executed original-data comparison, independent geography from the prior USA Gulf Coast (RP2) and Bay of Bengal (RP100) samples.**

The original WRI Aqueduct Floods v2 **historical coastal, no subsidence** 100-year [GeoTIFF \`inuncoast_historical_nosub_hist_rp0100_0.tif\`](https://aqueduct.wridata.org/AqueductFloods20/inuncoast_historical_nosub_hist_rp0100_0.tif) was compared to a separate Physrisk distribution [Zarr chunk \`0.4.22\`](https://os-climate-physical-risk.s3.amazonaws.com/hazard-indicators/hazard.zarr/inundation/wri/v2/inuncoast_historical_nosub_hist_0/0.4.22). Original WRI TIFF's source IFD (first IFD at byte 46209472) was used to locate LZW row 4560 at original strip offset **9,532,356**, with **2,717** compressed bytes. The Zarr array's 100-year return period is *index 5*; global row **4560**, columns **22000–22999** correspond to array-local row 560 and all 1,000 columns of Zarr chunk \`0.4.22\`, with the selected original **Blosc block #42** from compressed byte offset **1,118,968** to **1,169,975** (51,008 bytes). Blosc original header verifies Float32 byte-shuffled LZ4, 69 blocks and full *compressed* Zarr object length **1,751,433 bytes**.

Geographic grid centres are approximately **51.995833°N, 3.3375–11.6625°E**, a one-row section crossing the Netherlands/North Sea coastal area and extending into Germany. This is only one highly selective latitude line, not a representative sample of all protected and unprotected European buildings.

### Original HTTP response byte receipts

**Six independent, bounded, anonymous read-only provider source HTTP Range responses; no complete TIFF/Zarr was fetched and no source bytes have been committed to Git:**

| Original object | Inclusive byte range | Bytes | SHA-256 of exact returned body |
| --- | --- | ---: | --- |
| WRI GeoTIFF row 4560 strip-offset table | \`46314334–46314337\` | 4 | \`e0566cbf3b0a881e353c75e0ac62b41d391941947f8aa85fd5b93f4814d9e01b\` |
| WRI GeoTIFF row 4560 strip-length table | \`46227934–46227937\` | 4 | \`4079d31186209119f8b7d75a5375b4db0991f7e149e621c6369ddc422f749f8f\` |
| WRI original compressed TIFF LZW row | \`9532356–9535072\` | 2,717 | \`aa32aef31052fadef112ab337c0c609f085965e8a7ad4eabdfd0e3e4e0e0f911\` |
| Physrisk Zarr chunk \`0.4.22\` Blosc header/offset table | \`0–4095\` | 4,096 | \`c1fa76465612674450949a993c2ce31ffcbfc3cb2ee8b5d3d9dc1d828f81432d\` |
| Physrisk compressed block #42, part 0 | \`1118968–1148967\` | 30,000 | \`cd154830e94a6a5bb6d96b35b55868fa6c2029635c3cbe589bceb2eb45793068\` |
| Physrisk compressed block #42, part 1 | \`1148968–1169975\` | 21,008 | \`6cfb0ea208674c0455faafe5a1f6b675ff8b59c1a9f39252ee13c66b46cf9609\` |

### Independent original-to-derived comparison

Real source **LZW strip** was decompressed to one Float32 row with 43,200 columns and real source **Blosc block** decoded from four LZ4 byte-shuffled streams, with exact return-period, row and column indexing. **1,000/1,000 paired cells agree on source category and depth:**

| Value category | Actual WRI TIFF | Actual derived Physrisk | Match |
| --- | ---: | ---: | --- |
| Finite zero | 819 | 819 | **819 exact Float32 byte matches** |
| Finite positive depth | 88 | 88 | **88 exact Float32 byte matches** |
| WRI original missing \`-9999\` | 93 | 93 actual \`NaN\` values | **93/93 missing-category matches** |
| Unexplained pair differences | — | — | **0** |

Positive matching examples include global columns **22093 (0.8273507953 m)**, **22096 (1.8572196960 m)**, **22097 (1.8661835194 m)** and **22115 (0.0180678368 m)**. Exact original-byte Float32 equality was checked for all 907 finite source pixels (no rounded numeric tolerance). The source NoData sentinel is *intentionally not numerically equal* to the resulting derived NaN.

**Three distinct geographically located original↔derived checks now total 3,000 source cells: 2,652 bitwise-identical finite pairs (2,226 zeros and 426 positive depths), 348 original NoData \`-9999\` → derived \`NaN\` category matches, and zero observed mismatches.** The first RP2 USA check, second RP100 Bangladesh/Bay of Bengal check and this third RP100 Europe/North Sea check together validate *sampled transformations*, not a global dataset or model. The separately executed nine-period monotonicity test is inside one derived Bay of Bengal Zarr chunk and is not additional original-WRI TIFF pairing.

### New bounded offline verifier and synthetic regression tests

- \`research_runners/wri_physrisk_coastal_europe_100yr_pair_v0.py\` is a **stdlib-only, fail-closed** reader for the six exact source byte-range response files saved **outside Git**. It checks fixed SHA-256/size, TIFF original table entries, Blosc original header/69-entry offset table, source LZW and derived LZ4 decompressors, return-period/coordinate alignment and all 1,000 paired cell categories. Emits **\`model_input_admitted=false\`**.
- \`tests/test_wri_physrisk_coastal_europe_100yr_pair_v0.py\` contains **synthetic-only** tests for exact finite and missing-category matching, mutated/invalid original files, unexpected depth, NoData erroneously converted to zero, block boundary changes and output-source overwrite protections.

\`\`\`bash
python research_runners/wri_physrisk_coastal_europe_100yr_pair_v0.py \
  --wri-row-offset /private/europe-original/wri-row4560-offset-4b.bin \
  --wri-row-length /private/europe-original/wri-row4560-bytecount-4b.bin \
  --wri-strip /private/europe-original/wri-row4560-lzw-2717b.bin \
  --zarr-header /private/europe-original/zarr0.4.22-header-4096b.bin \
  --zarr-part0 /private/europe-original/zarr0.4.22-blosc42-part0-30000b.bin \
  --zarr-part1 /private/europe-original/zarr0.4.22-blosc42-part1-21008b.bin \
  --out /tmp/wri-physrisk-100yr-europe-third-pair.json

python -m unittest discover -s tests -p 'test_wri_physrisk_coastal_europe_100yr_pair_v0.py'
\`\`\`

### What remains scientifically unresolved

This does **not** verify all European coasts, all WRI return periods, future scenarios, riverine flood, physical flood defences, vulnerability functions or exact published Zarr build/asset version. Full original TIFF and original derived Zarr whole-object immutable identifiers are still unpinned. Dataset- and usage-specific legal rights plus scientific model review remain unresolved. The source's missing 1.5-year original recurrence is not reconstructed. Return-period quantile depths do not yield actual stochastic event records, insurer exposure, dependence, ELTs/YLTs, gross/net OEP, AEP or IP; the source remains **not admitted** as a production CAT model input.

## Follow-up: flood-defence source access is not an automatic correction to WRI depth

The three independently proved original WRI GeoTIFF→Physrisk Zarr 1,000-pixel transects (USA, Bangladesh, Europe) and the nine-period Physrisk monotonicity sample validate **selected original value transformation and raster intensity ordering**. The original flood-depth maps are explicitly **undefended** by product design.

A separate research note, [WRI flood-defence source access and risk bridge](wri-flood-defence-source-access-and-risk-bridge-20261104.md), now documents **live original-source evidence** for Netherlands IHW NBPW formal primary dike trajectories and their legal norms, a working Rijkswaterstaat WFS route despite a broken older catalogue URL, native EPSG:28992 vs WRI EPSG:4326, and Bavaria LfU CC BY-SA 4.0 Shapefile downloads in EPSG:25832/4258 including complete 12-member ZIP central-directory checks. The access-focused Python gate and synthetic regressions are separately implemented in the current PR. Broadest FLOPROS, openDELvE, HELCOM and UK EA layers are documented as **not-yet-byte-verified candidates**.

**The source bridge does not establish protection side/topology, barrier crest elevation, achieved barrier performance, event-dependent breach or overtopping, legally valid transfer of a standard to a modelled hazard quantile, or a site-specific defended flood depth**. Preserve \`wri_original_depth_m\` and an eventual scientifically calibrated \`defended_scenario_depth_m\` as separate values. No approval of insured losses, YLT/ELT/OEP/AEP/IP gross/net, vulnerability or treaty processing follows from this evidence. **\`model_input_admitted=false\` remains unchanged**.
