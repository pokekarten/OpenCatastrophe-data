<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BKG Berlin WMS: independent KOSTRA depth-layer metadata inquiry v0

**Research-only. This is not a raw-TIFF-to-centimetre conversion, insurance
exposure, property flood status or CAT model input.**

## Original-source result — verified 2026-11-01

The [reviewed main workflow #41354445114](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354445114)
executed the exact bounded WMS code on main SHA
`a1a342ac8e41e9129928674d5c5e81cb7e5820ca`:

- Actual original capabilities XML: **480,596 bytes**, SHA-256
  `1f5050be9a560c4a2e2bce3f5e17c74ed4ff8973c62e63b975da5c5e5d07f75f`.
- The exact Berlin `be_tiefe_agw` **KOSTRA depth layer existed and was
  queryable**. The original provider advertised **application/json**
  for the GetFeatureInfo response.
- One fixed small original GetFeatureInfo was successful: **205 bytes**,
  SHA-256 `6f6429b2def52bb12f9bdcd5f8092e88761e6d38e50023222bd26761c4a4f038`.
  It yielded **no recognized explicit unit-field candidate** (m/cm/mm).
- The original GDAL Int16 direct-download TIFF remains **physically
  uncalibrated**, and no insurer or property-depth modelling is approved.

The immutable **metadata-only** [original WMS receipt](bkg-berlin-original-wms-featureinfo-receipt-20261101.toml)
stores the two hashes and source/run identity. It stores **no provider
GetFeatureInfo JSON, raw code, individual building or source location**.
The offline
`tests.test_bkg_berlin_original_wms_featureinfo_receipt_v0` challenges
unit fabrication, source drift and insurance CAT nonadmission.

**Important:** the absence of an explicit unit in a single WMS feature-info
response does **not** prove the service lacks any documented map-depth
unit elsewhere. It does confirm that *this exact original request* did
not supply a valid raw TIFF scaling rule. The BKG technical clarification
is still required.

## Why this is a different original-source route

The independently checked BKG original Berlin KOSTRA GeoTIFF file
(47,280,200 bytes, SHA-256
`7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f`)
has one Int16 raster band, NoData -9999, **no explicit unit metadata**
and **no explicit scale/offset tags**. The source GDAL runtime reports
scale 1 and offset 0, but these may be implicit defaults. This was
verified on [source workflow 41353177132](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41353177132)
and admitted only into the read-only [native unit research receipt](bkg-berlin-original-native-tiff-unit-receipt-20261101.toml).

The official BKG [WMS product page](https://gdz.bkg.bund.de/index.php/default/wms-hinweiskarte-starkregengefahren-wms-starkregen.html)
publishes `https://sgx.geodatenzentrum.de/wms_starkregen` as a separate
**visual map service**. The [WMS GetCapabilities public catalogue as
rendered by Geoportal Brandenburg](https://geoportal.brandenburg.de/detailansichtdienst/render?url=https%3A%2F%2Fgeoportal.brandenburg.de%2Fgs-json%2Fxml%3Ffileid%3D8CFE8DEE-CDB7-44E2-BF54-4049F8464789&view=gdibb)
names layer `be_tiefe_agw` as Berlin's exceptional-event
maximum inundation depth. The WMS advertises `GetFeatureInfo` with
JSON/plaintext output among other formats **at service level**.
Queryable status of this *specific* layer must still be read from
the **actual** current GetCapabilities XML. An absent or unqueryable
layer is a source-access outcome, not permission to query a different
layer, city or scenario.

## Bounded original query design

The pure-stdlib original-source runner
`research_runners/probe_bkg_berlin_wms_depth_featureinfo_v0.py`
makes at most **two** HTTPS requests to the one official BKG service:

1. One exact WMS 1.3.0 `GetCapabilities`, XML only, 4-MiB absolute cap,
   DTD/entities prohibited; validates uniquely named Berlin KOSTRA layer.
2. **Only if queryable** and if the *original* service advertises JSON
   or plaintext `GetFeatureInfo`, one fixed `GetFeatureInfo` query
   for that same layer, EPSG:25832, a 64-by-64-m area in the already
   verified 200m Berlin pilot window, one central query pixel and a
   **16-KiB response cap**.

No caller-defined URL, source-original image, ad-hoc location,
per-building WFS identity, original pixel array, GeoTIFF, signed
raw depth, source query value, metadata text payload or user address
is logged or persisted. The output reports only original response
SHA-256/byte count, whether the exact target layer is present and
queryable, the advertised format, and whether an **explicit**
`unit`, `units` or `unittype` metadata field advertises a
recognized candidate (m/cm/mm). A free-text legend, arbitrary
`value`, `GRAY_INDEX`, RGB color, hazard class or water-depth
number is **not** silently accepted as the unit of the original
Int16 file.

The official WMS is a visualization service; its data preparation,
resampling, classing, potential unit transforms and NoData treatment
are **not established to match the downloadable Int16 GeoTIFF**.
Even a recognized WMS unit field only creates a follow-up question
for BKG and is **not** a calibration. Both explicit gate fields
`WMS_unit_implies_original_TIFF_Int16_scale` and
`insurance_cat_model_input_admitted` always remain false.

## Reproducibility and original evidence

```bash
python -m unittest tests.test_probe_bkg_berlin_wms_depth_featureinfo_v0 -v
# Only in a reviewed source-network environment:
python -m research_runners.probe_bkg_berlin_wms_depth_featureinfo_v0
```

On a pull request the GitHub workflow runs **eight offline synthetic
adversarial tests only**. After merging the workflow to main (or a
separately reviewed manual dispatch), it queries the original provider
and records **metadata only** in its short Actions output. A non-200
response, surprising redirect, unknown content type, invalid or
oversized document, changed scenario layer, contradictory unit label,
or unsupported WMS response is **blocked**, never interpolated.

The BKG [product description](https://www.bkg.bund.de/DE/Themen/Umwelt-und-Klimawandel/Starkregen/starkregen_cont.html)
warns that this is a countrywide *simulated* hazard overview,
not property-engineering evidence. KOSTRA exceptional rainfall is
not equivalent to a calibrated property-loss return period.
The BKG WMS and source data require DL-DE/BY 2.0 BKG plus
original provider attribution. This research logs no map derivative.

## Next external, independent proof needed

Send a targeted technical clarification to the BKG service/product
team (`starkregen@bkg.bund.de`, also `dlz@bkg.bund.de` on the
official public documentation), identifying the **exact**
Berlin original direct-file path and full SHA-256, asking for:

- The signed Int16 maximum-depth TIFF raw-code **physical units**,
  any unit/scale/offset metadata stored *outside* the TIFF, and
  representative raw-code → measured depth examples including
  `0`, `108`, and `-9999`.
- Whether the exact `be_tiefe_agw` WMS layer is generated from the
  *same* direct GeoTIFF and original KOSTRA model revision, without
  classing/resampling/numeric changes; if not, request the proper
  exact source-style specification.
- Whether `-9999` denotes physically unmodelled buildings,
  excluded areas, missing source data or a combination, with the
  stated mask treatment relevant to entrances and basements.
- Release/version coverage and provenance for the 2024 simulation
  inputs (especially 2021 nationwide house outlines and
  11/2022 Berlin ALKIS, as listed in the provider's
  [data source catalogue](https://sgx.geodatenzentrum.de/web_public/gdz/datenquellen/datenquellen_hwk_srg.pdf))
  against our separate, mutable 2026 WFS building footprints.

No email has been sent; this is a source-request protocol for
technical clarification, not an assertion that BKG endorsed
our reconstruction. Explicit publisher evidence and independent
numeric test vectors are mandatory before opening a new
physical-depth CAT-admission stage.
