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
