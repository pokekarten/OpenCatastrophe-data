<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin pluvial flood: independently scoped WFS metadata and original raster routes

**2026-11-01 — source-access research only.** This is the next scientific
source gate after the 5-building source-derived Berlin BLD4 staging and the
synthetic flood-depth polygon/grid overlay. It is NOT a real building/hazard
join, a simulation result, a complete source admission, a loss estimate or
proof of coverage of the sample building box.

## Two different official original products

1. **Berlin 2025 Starkregenhinweiskarte**: authoritative open-data
   [WFS catalogue](https://daten.berlin.de/datensaetze/starkregenhinweiskarte-wfs-882d18d8),
   service `https://gdi.berlin.de/services/wfs/ua_srhk`, official
   catalogue licence **Datenlizenz Deutschland Namensnennung 2.0
   (dl-de-by-2.0)**. The hazard indication includes 2025 BKG
   rainwater-surface modelling plus other original official information.
   Its WFS technical
   [source documentation](https://gdi.berlin.de/data/ua_srhk/docs/Datenformatbeschreibung_SRHK_2025.pdf)
   explicitly identifies **four separately downloadable Atom ZIP /
   GeoTIFF** raster layers in **EPSG:25832**: water levels and
   flow velocities for extraordinary and extreme rainfall scenarios.
   This *technical raster channel is separate from WFS polygon/point
   feature access*. Do not treat a WFS layer display or a WMS colour
   pixel as a metre-valued raster sample. BKG's extreme rainfall
   scenario is not automatically an observed historical event.
2. **Berlin detailed Starkregengefahrenkarte**: authoritative
   [WFS catalogue](https://daten.berlin.de/datensaetze/starkregengefahrenkarte-wfs-1aa4f1ef),
   service `https://gdi.berlin.de/services/wfs/ua_srgk`,
   catalogue licence **CC BY 4.0** (product-specific attribution
   details). The product uses coupled **1D sewer / 2D overland flow**
   calculations for rare/extraordinary/extreme scenarios. Unlike the
   indicative map, detailed calculated coverage is **only available in
   some parts of Berlin**, not necessarily around the frozen
   central-Berlin ALKIS BLD4 box `391700,5819950,391900,5820150`.

The two maps must be treated as different source families: scenario,
topography, model-resolution, geometry vintages and known data inputs
differ. They may share upstream BKG/ALKIS/source components; thus
neither can be assumed an independent validation ground truth for
the other or used as insured losses.

## Reviewed bounded live research step

`research_runners/berlin_starkregen_wfs_capabilities_v0.py` makes
**one exact, anonymous, HTTPS WFS 2.0 GetCapabilities request per
explicitly chosen source**. Requests have a fixed full URL and
read-only GET, TLS verification, no proxy or redirects, a 35s timeout,
2 MiB XML cap and no credentials. It checks WFS XML structure, duplicate
layers, CRS advertisements and invalid XML/DTD. Only public feature
type names, CRS declarations, response byte counts/SHA-256,
retrieval UTC and code SHA are reported.

`tests/test_berlin_starkregen_wfs_capabilities_v0.py` contains
synthetic XML/HTTP abuse and exact-URL tests, with no provider calls.
The one-shot workflow `.github/workflows/berlin-starkregen-wfs-metadata.yml`
runs the synthetic checks on PRs but issues source requests **only
on a reviewed workflow revision merged to main**, or a separate
explicit manual dispatch. Each source has an independent job so
one source's failure does not suppress the other's result.

### Decision boundary

- A successful WFS capabilities response only proves that *service
  metadata* can be fetched, not that a water-depth layer or a
  meter-valued hazard grid is downloadable by WFS.
- ZIP/Atom GeoTIFF discovery and downloading require a **separate
  source-specific bounded access review**, exact object identity,
  source licence/redistribution/derivative review, file/ZIP-size
  limit, full-object SHA-256, projection and pixel/mask semantics.
- The official hint-map GeoTIFF uses **EPSG:25832**; BLD4 building
  polygons are **EPSG:25833**. Any real join needs an explicit
  reproducible, non-ballpark transformation in a reviewed raster
  runtime. Non-overlap must remain missing support, never "dry".
- Product temporal mismatch is unresolved: current monthly mutable
  ALKIS buildings vs maps derived from multi-year public/nonpublic
  inputs. Event/scenario is not a loss event or a Monte-Carlo
  stochastic catalogue.
- No source feature, raster pixel, coordinates, provider XML,
  building geometry, customer/claim data or production DB rows
  are persisted by this metadata probe.

## First original-source receipts

Await exact source-specific main workflow execution after review.
No successful capabilities, layers, CRS or real hazard pixel values
are claimed before this original-run evidence is available.
