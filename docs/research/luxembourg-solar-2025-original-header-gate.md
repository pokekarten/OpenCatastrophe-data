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

## Measured original publisher header evidence — 2026-11-01

The **actual exact three original provider SHP/SHX/DBF prefix reads** all returned
HTTP `206 Partial Content` with verified range lengths, and the corresponding
full-file advertised sizes matched SHP/SHX's internal declared sizes.
GitHub source run: <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41313789822>.

| Header observation | Verified metadata |
| --- | --- |
| Published source prefix bytes fetched | SHP 100, SHX 100, DBF 8,192 — **no feature records** |
| DBF and SHX source record count | **238,433** each; actual row data not read |
| DBF column count | **12** |
| SHP original geometry code | **5 (Polygon)** |
| SHP declared full size | **61,634,180 bytes** |
| SHX declared full size | **1,907,564 bytes** |
| Native header bbox | `(49113.407,57196.2218,105258.2696,138729.7195)` — axis order not ground-controlled |
| Product-local key | `HID` numeric column (uniqueness not tested) |
| Column names | `HID, STREET, NUMBER, ADDITION, ZIPCODE, CITY, PV, ST, X_2169, Y_2169, X_4326, Y_4326` |
| Missing in this building DBF | `tilt, aspect, flat, area3d` (not present as fields) |

**Consequences for building models:** The 2025 supplier building export includes
polygon shape, product-local reference `HID`, georeferencing data and PV/ST
categorisation columns, **but does not itself contain physical roof pitch,
orientation, construction date, building material, actual photovoltaic
installation or roof facet area**. Those cannot be invented from the SHP
header. Any roof-facet WMS source needs its own original independent access
and field/schema evidence. `PV` and `ST` are source model classifications,
**not verified already installed systems**.

This is a **different source object than ACT2023v2**, which lists 238,189
roof extents. The difference in original published header counts is **244**
records but is *not evidence of 244 missing/new buildings*: segmentation,
dates, coverage, models and source families differ. No matches have been
computed.

The DBF *header* contains a nominal last-update value of
`1995-07-26`; this is **not trustworthy survey age evidence**, given the
publisher's September/October 2025 export dates. It appears to be a legacy
header field and must not enter a temporal model without supplier
confirmation.

The original complete files, record bodies, `STREET/NUMBER/ZIPCODE/CITY`
values and geometry were **never fetched** by this test. The source
licence remains labelled `Other (Open)`; exact commercial reuse rights,
underlying source independence and per-building matching remain blocked.

## What still needs proving

The actual building SHP column inventory and number of `hid` items must be measured. If the source returns a non-range HTTP 200 response, this research will explicitly fail rather than downloading 200MB under ambiguous rights. A successful header read does **not** certify legal reuse, future source changes, true building-level rooftop tilt or third-party independence, and does not permit a source-to-source building match.

Next path: independently legal-review rights, inspect separate accessible roof-facet WMS schemas and source lineage, then reconcile source segmentation with verified ACT and EUBUCCO tile (250m city area, alongside rural control sample). Never convert modelled solar **potential** into insured installed PV assets.
