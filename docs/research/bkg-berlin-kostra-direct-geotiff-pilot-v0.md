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
