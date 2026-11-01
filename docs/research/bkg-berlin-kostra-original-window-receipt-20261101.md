<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First verified original BKG Berlin KOSTRA pixels (research only)

**Original main run:** [GitHub Actions 41348217549](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41348217549), 2026-11-01 20:42:43 UTC, main revision 4ce081f8a6427d7ff674c9c8d3e1b6676f61b55d.

The directly downloaded original BKG Berlin KOSTRA GeoTIFF has:
- Exactly **47,280,200 original TIFF bytes**, locally measured whole-source SHA-256 **7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f** (not an independently signed provider hash).
- An original 10,000 by 10,000 single-band **Int16** raster in **EPSG:25832**, with 1 by 1 m *spatial* pixels and source-declared **NoData −9999**.
- Frozen original research bbox in EPSG:25833 transformed into BKG source EPSG:25832, and a **217 by 217** cell original window within the real tile.
- Real original pixel-mask inventory: **4,746 masked/NoData**, **4,503 finite raw numeric zeros**, **37,840 finite raw positive values**, **zero finite raw negative values**. Unmasked valid source raw numbers range 0 to **108**. These sum to the exact 47,089 read cells.

Machine-readable **metadata-only** receipt:
[bkg-berlin-kostra-original-window-receipt-20261101.toml](bkg-berlin-kostra-original-window-receipt-20261101.toml).

This first 47-MB original data download was made within a reviewed one-URL, 70-MiB total-size gated temporary runner and deleted after the sample. **No original TIFF bytes, pixel matrix or per-building data** are preserved in Git, Neon or any production source catalogue.

## Interpret the data correctly

This source is the **BKG HWK_SRG KOSTRA exceptional scenario** and is **not** the Berlin GDI 2022-named extreme/extraordinary ZIP source previously tested by their TIFF metadata. The observed integer range **0…108 is not a verified centimetre or metre depth**. The NoData count is not evidence of dryness; numeric zeros are not automatically dry insured building locations. The centre of a 200-m bbox cannot substitute for exact building/raster overlay.

The BKG publishes this product under DL-DE/BY 2.0 with attribution and data-source requirements; external model use needs scientific suitability and rights review. The BKG advises against interpreting the overview as metre-exact property risk. No annual insured loss frequency, TIV, vulnerability or insurer risk has been established here.

## Next gates

1. Verify BKG-specific actual Int16 raster depth **unit and scale** against the exact original source specification or independently signed legend/data rules, not from a map rendering or the raw 108 maximum.
2. Determine source validity semantics for masked and numeric-zero cells and compare to the separate Berlin 2022-named product without merging vintages.
3. Only then inspect exact, licensed current/historical building polygons against valid pixels; record multi-pixel support, water depth uncertainty and asset vintage, without interpreting a design storm as a real annual loss.

Offline immutable receipt check:
python -m unittest tests.test_bkg_berlin_kostra_original_receipt_v0 -v

The successful original-source run itself is the primary evidence. The local TOML tests only check that the precise observed metadata and non-admission statements have not drifted.
