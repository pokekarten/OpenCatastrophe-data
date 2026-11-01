<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Solar cadastre 2025 — original SHP/DBF headers, not original building records

**Date:** 2026-11-01. **State:** read-only, non-admission research metadata.

## Official producer and exact source version

- Producer: Klima-Agence G.I.E., Luxembourg; underlying product documents attribute `hid` and separate roof facet/WMS tables.
- Original provider catalogue: <https://data.public.lu/en/datasets/potentiel-solaire-au-luxembourg/> updated 2025-10-03.
- Original 2025-09-02 export: `20250902-0721-st-luxemburg-25-buildings-export` with separate SHP (listed 58.8 MB), DBF (212.2 MB), SHX (1.8 MB), PRJ (671 B) and CPG (5 B). Each component is a separate resource; **never assume a single source file includes all geometry and roof facets**.
- Product-specific IDs `hid` are NOT common ACT2023v2 `buildingid` or EUBUCCO `id`.
- Publisher licence label: **Other (Open)**, not a confirmed unambiguous open-commercial licence. Product-level reuse and derived-database rights remain to be reviewed.
- Source documentation: <https://data.public.lu/en/datasets/r/f57a9792-1598-4136-becf-21f2a9ac2bf1>. Reported EPSG:2169, with possible as-stored XY axis caveat; `hid` links the supplier's own building/roof products. `tilt/aspect/area3d/flat` may be supplied in **different roof facet WMS layers**, not in SHP building attributes.

## What this PR actually checks

- `research_runners/lu_solar_shapefile_header_v0.py` receives only official original **byte prefixes**: 100 bytes each of `shp` and `shx`, and up to 8192 bytes of `dbf`. It never parses or fetches any original DBF records, SHP polygon coordinates or address values.
- Checks original SHP/SHX magic, 1000 version, polygon geometry type, native bounding-box sanity, original source file length, DBF header field names/types/widths, DBF physical row length and equal original DBF-vs-SHX record count. Emits exact field-name evidence and whether `tilt`, `aspect`, `flat`, `area3d`, `hid` actually occur in the downloadable **building table**.
- `.github/workflows/luxembourg-solar-2025-header-receipt.yml` uses three fixed HTTPS source URLs, tight curl 206 HTTP Range validation, only ~8KB of source header data in temporary runner disk and no uploaded artifacts. Reject if provider refuses byte ranges, reports an inconsistent length or returns incomplete prefixes.
- Pure-standard-library synthetic tests cover original file consistency and malformed input. No dependencies added.
- Record counts from SHX/DBF **header assertions** are not full-file validated or proven complete. Observed bbox may be in native/unverified axis order; don't use it for source crosswalk without ground-control.

## What still needs proving

The actual building SHP column inventory and number of `hid` items must be measured. If the source returns a non-range HTTP 200 response, this research will explicitly fail rather than downloading 200MB under ambiguous rights. A successful header read does **not** certify legal reuse, future source changes, true building-level rooftop tilt or third-party independence, and does not permit a source-to-source building match.

Next path: independently legal-review rights, inspect separate accessible roof-facet WMS schemas and source lineage, then reconcile source segmentation with verified ACT and EUBUCCO tile (250m city area, alongside rural control sample). Never convert modelled solar **potential** into insured installed PV assets.
