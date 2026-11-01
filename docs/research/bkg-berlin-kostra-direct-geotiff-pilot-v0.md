<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# BKG Berlin KOSTRA original max-depth GeoTIFF — bounded pilot v0

**Research-only. No insurer exposure, admitted CAT hazard or damage estimate.**

## Official source separate from Berlin GDI ZIPs

The [BKG product page](https://gdz.bkg.bund.de/index.php/default/wms-hinweiskarte-starkregengefahren-wms-starkregen.html)
provides the 1-m maximum-depth dataset, a single-tile direct download,
and the explicit DL-DE/BY-2.0 attribution requirement.

The [official Berlin download index](https://daten.gdz.bkg.bund.de/produkte/sonstige/starkregen/aktuell/be/)
has directories maxdepth_kostra and maxdepth_100mm.
This research selects ONE original KOSTRA event tile (about 45 MB):

https://daten.gdz.bkg.bund.de/produkte/sonstige/starkregen/aktuell/be/maxdepth_kostra/s32790/starkregen_maxdepth_kostra_32790_5820_10_be.tif

**This is not the 619-MB/563-MB Deflate ZIP pair named 2022 from gdi.berlin.de.**
No pixel equivalence, shared vintage, identical scenario, or cross-source
calibration is assumed. The BKG tile is dated August 2025 in the
official directory and the broader product metadata call it 2024.

## Pilot area and mandatory source gates

The original BLD4 200-by-200 m research bbox is
(391700, 5819950, 391900, 5820150) in EPSG:25833.
The centre transforms to approximately (798835.3, 5827979.5)
in EPSG:25832, which only *suggests* the indexed BKG tile.
The exact **original TIFF** must confirm actual EPSG:25832,
north-up 1m grid, extent containing the pilot, and one supported
numeric band. The parser densifies the pilot boundary before
transforming CRS. It never assumes that the two UTM zones are equal.

The source reader permits one fixed host and exact URL, refuses
redirects and unexpected HTTP media/encodings, limits total bytes
to **70 MiB**, computes original full-TIFF SHA-256 locally and deletes
the file after inspection. It cannot fetch an arbitrary region or
additional tiles. The original-byte transfer executes only in
reviewed main or manual GitHub workflow; PR checks are synthetic.

Only an actual source window of at most **512 by 512 cells**
can be decoded. The output separates source mask/NoData,
finite unmasked numeric zeros, positive/negative raw values,
and aggregate raw min/max. No source bytes, building positions,
building IDs or individual raw arrays are persisted. Source
missing-unit evidence is never silently upgraded to metres.

Tests: python -m unittest tests.test_probe_bkg_berlin_kostra_direct_tiff_v0 -v

The dedicated workflow pins rasterio and pyproj; it must not skip
spatial tests due to missing packages.

## Scientific and rights limits

BKG's HWK_SRG is a modelled potential hazard. The BKG cautions
against treating the overview as metre-exact engineering evidence,
and the regional modelling omits explicit sewer/infiltration effects.
The exceptional KOSTRA scenario is a rainfall design description,
not a fitted annual loss occurrence process.

The original BKG input vintages are not the current ALKIS footprints.
DL-DE/BY 2.0 source attribution and the required BKG third-party
source list must be preserved in later publications. Research
evidence does not automatically grant commercial insurer-model
suitability, policy TIV, building-level depth, damage or rights
admission. Before any CAT use, verify units and scaling, exact
source mask semantics, scenario alignment, exposure-vintage
differences and spatial joins with current/historical geometry.

**Do not translate raw numeric positives into insured flooding.**


## First real original BKG TIFF pixel receipt — 2026-11-01

A single BKG original TIFF of the **KOSTRA design rainfall scenario**
was independently fetched and examined **after** reviewed PR #1072
merged. The reviewed first-party
[GitHub Actions run 41348217549](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41348217549)
completed successfully on source revision
\`4ce081f8a6427d7ff674c9c8d3e1b6676f61b55d\`.
The fixed provider URI remains the sole original byte source listed
above. The original TIFF bytes were held only in a disposable temporary
directory, read through rasterio and deleted when the run finished.
They were not committed or copied to an insurer/TCG database.

| Independently verified fact from original source | Result |
| --- | --- |
| Exact source TIFF size | **47,280,200 bytes** |
| Entire source TIFF SHA-256 | \`7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f\` |
| Original read at UTC | **2026-11-01 20:42:43** |
| Source CRS | **EPSG:25832**, *different* from the older Berlin ZIP TIFFs (25833) |
| Original full TIFF pixel dimensions | **10,000 × 10,000** |
| Source pixel size | **1 × 1 metre** |
| Source raster-band type | **signed 16-bit integer** |
| Original band count | **1** |
| Declared NoData | **−9999** |
| Independently reprojected fixed pilot envelope | (798727.2708227294, 5827871.458055575, 798943.3961922952, 5828087.583425137) in EPSG:25832 |
| Actual bounded raster read | **217 × 217 = 47,089** raw pixels |
| **Actual NoData/masked pixels** | **4,746** |
| Finite unmasked pixels | **42,343** |
| **Actual valid zero-valued raw pixels** | **4,503** |
| **Actual positive raw integer pixels** | **37,840** |
| Valid negative raw integer pixels | **0** |
| Raw valid minimum/maximum | **0 / 108** |
| Physical band depth units/scaling independently established | **No** |
| Individual building exposure or insured losses | **Not performed** |

The categories have a conservative, exact conservation check:
**4,746 + 4,503 + 37,840 = 47,089**. None of the 4,746 masked
pixels are silently counted as dry; 4,503 observed unmasked
zero-valued pixels are a separate raw source category.
The **maximum raw integer 108 is not 108 m water depth**:
the actual physical depth unit and any publisher encoding
must be explicitly reviewed before interpretation or conversion.

This 47,089-cell result is an actual **raster-pilot-envelope**
sample, not a claim that 47,089 m² are five building footprints
or that any building has 37,840 positive cells under it.
The source EPSG:25832 pilot envelope conservatively encloses
a reprojection of the EPSG:25833 200 × 200 m research bbox,
which can include pixels *outside* the exact reprojected pilot.
No source pixel or building data are joined here.

### Separate products and rights

The BKG KOSTRA 2024/2025 original direct TIFF and the
GDI Berlin source ZIPs labelled 2022 are **different model
products**. The BKG source's 1 m UTM32 grid should not be
silently joined to the other provider's 1 m UTM33 grid,
and the observations above cannot establish pixel equivalence,
scenario equivalence, building-vintage equivalence or
independent validation of one source against the other.
BKG's public
[product page](https://gdz.bkg.bund.de/index.php/default/wms-hinweiskarte-starkregengefahren-wms-starkregen.html)
states that the 2D simulations omit sewer drainage and infiltration,
and requires [DL-DE-BY 2.0](https://www.govdata.de/dl-de/by-2-0)
attribution plus the official
[upstream source attribution](https://sgx.geodatenzentrum.de/web_public/gdz/datenquellen/datenquellen_hwk_srg.pdf).
The simulated KOSTRA scenario is not an actual observed insurance
claim or a Monte Carlo loss event.

**Next defensible source/model gate:** verify the raw signed-integer
water-depth encoding against authoritative original format/source
documentation (including any scale/units), then use original-derived
BLD4 building polygons only for a bounded spatial support
comparison with explicit CRS transform and NoData/uncertain-time
handling. No vulnerability/TIV/loss estimate or commercial CAT
model admission follows from this source-pixel QA receipt alone.
