<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Verified original Bavarian building footprints × DLR WSF2019: first real area overlap (2026-11-12)

**Evidence classification: preliminary two-source/two-vintage scientific research only.**
No real-world buildings, site/insured addresses, TIV, policy data, loss or CAT-model inputs are approved by this report.

## Primary-source provenance and contracts

| Dimension | Independently observed evidence |
| --- | --- |
| Authoritative source | `de.bayern.hausumringe`, Bavarian cadastral-derived public `091_Oberbayern_Hausumringe.zip` |
| Exact original ZIP | [BVV Oberbayern downloadable ZIP](https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip), listed in the [official BVV region KML](https://geodaten.bayern.de/odd/m/3/daten/hausumringe/bezirk/kml/HU_regierungsbezirk.kml) |
| Product-specific rights | LDBV [Gebühren- und Preisliste, §7.4 Hausumringe](https://www.ldbv.bayern.de/mam/ldbv/dateien/gebuehren_und_preisliste.pdf): CC BY 4.0, publicly downloadable; attribution/changes required. Does **not** grant protected ALKIS WFS or federal HU-DE rights |
| Official geometry CRS | Original SHP companion `hausumringe.prj`, independently identified by pyproj as **EPSG:25832 ETRS89/UTM zone 32N** |
| Original ZIP total | 174,299,765 bytes (original HTTP Content-Range) |
| Original SHP compressed | **166,172,236** bytes, SHA-256 `22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615` |
| Original SHP unpacked | **501,212,696** bytes, SHA-256 `977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c` |
| Original ZIP SHP member CRC32 | **55540a66**, recomputed over the complete source geometry stream |
| Original source records | **2,703,736** valid sequential Polygon type 5 binary records, independently matching the fully verified SHX index and original dBase table cardinality |
| Real source execution | [Actions run 43317649994](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317649994), actual original `source_shp` step **success** |
| Source script | [research_runners/by_hausumringe_oberbayern_shp_windows_v0.py](../../research_runners/by_hausumringe_oberbayern_shp_windows_v0.py), already merged via [PR #1516](https://github.com/pokekarten/OpenCatastrophe-data/pull/1516) |
| Original provider bytes persisted | **No**. Streaming decompression only, bounded source-specific 166 MB HTTP Range; output includes **no source polygon coordinates or feature IDs** |

**Important:** The original ZIP compressed Shape record count is an administrative
source file record count, *not* a count of distinct insurable or residential
buildings. A real 2026 observation-date-per-feature has not been verified;
the source DBF's header file update date was 2026-10-01. It is **not** a
survey-capture date. The independently verified DLR WSF raster refers to
2019; these sources are not a same-year ground-truth pair.

## Two original WSF 32×32 fixed Munich windows

Original DLR WSF2019 is `dlr.wsf.2019`, internal Neon research-only
`research.source_sample_v0.sample_id` **#28** and **#29**. The
provider's compressed native TIFF-block SHA-256 is
`8f06d03fcc3cc63930d216a834bca6c51275da6b436e1b2639a39952ddbf0503`.
The two 32×32 original masks were independently cross-decoded by native
LZW/GeoTIFF Python and independent GDAL 3.12.2 in
[Actions 43226483288](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43226483288).

- Window **#28**: bbox `[11.548022640413272,48.12858881962954,11.550897249322455,48.13146342853872]`; exact native-mask SHA-256 `ff08ea1f4b89475bb4bcf8d4a453e55058f21eba2de2daa1fb5943d1706293df`.
- Window **#29**: bbox `[11.549459944867865,48.12571421072036,11.552334553777047,48.12858881962954]`; exact native-mask SHA-256 `85aaf92c2b87fc7ea80359498680bca371aaa0e974d65476328bb70e314b3fce`.

The merged source runner selected only geometries intersecting the respective
**projected UTM32 envelope**, unioned cadastral polygons in memory and
projected those onto each original WSF pixel grid. For each of the
2,048 cells in total, it calculated fractional polygon-square coverage
using GEOS, quantized to unsigned **uint16 little-endian**, 0–65,535
(i.e. at most **1/65,535** per cell rounding error), and emitted
a *derived grid* – never original polygon coordinates. Its two derived-grid
SHA-256 receipts were:

- Window **#28**: `11fda6f33fb45e374078ceb6c5d1f4ea849800c7d753ff0d0dc4b5d92d4da83e`
- Window **#29**: `405d0fdb003646973b38d9a24c7580e3d5d6e4d18271d206e19b89ef6655f17c`

The two immutable original WSF masks and both source-derived uint16 grids
were re-hashed and joined **in read-only Neon SQL**, without exporting WSF
mask pixels into Git or inserting original raster/provider coordinates into
Neon. Every grid has **1,024** source-aligned cells.

## Actually measured exploratory area overlap

Units are **native WSF2019 fractional pixel-area equivalents**, ~10m-scale
cells expressed as area, **not counts of buildings**, and not absolute
insured losses. Metrics compare the original-source Bavarian present-day
cadastral polygons with **2019** remote-sensed settled-area class pixels.

| Real two-vintage measurement | WSF #28 | WSF #29 |
| --- | ---: | ---: |
| Original HU-BY polygon candidates in broad projected bbox | 2 | 94 |
| Official HU-BY footprint area in native pixels | 0.242725 | 251.813581 |
| WSF2019 class-255 settlement pixels | 0 | 482 |
| Area-weighted polygon∩WSF intersection | 0 | **241.537835** |
| Polygon∪WSF area | 0.242725 | **492.275746** |
| **Exploratory intersection-over-union (IoU)** | 0.000000 | **0.490656** |
| Fraction of HU-BY footprint area inside WSF-positive pixels | 0.000000 | **0.959193** |
| Fraction of WSF-positive pixel area covered by HU-BY footprints | Undefined (0 WSF cells) | **0.501116** |

Interpretation, **strictly bounded**: for sample #29, about **95.9%**
of the 2026-source cadastral footprint area falls in pixels WSF2019
classified as settled; official polygons cover about **50.1%** of WSF
positive area. That does **not** show a 49.1% classification accuracy
nor an error in either product. WSF settlement includes non-building
urban surfaces, both datasets have different spatial support and
survey/reference vintages, and 1,024 cells is not population-wide
representativeness. For sample #28 the tiny 0.243-cell source footprint
and no WSF-positive cells makes IoU zero and a WSF-coverage fraction
mathematically undefined, not a valid systemic error estimate.

## Scope-of-truth and separation of data rights from scientific admission

The separate public
[ArcGIS mirror](https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/rest/services/Gebaeude_Bayern/FeatureServer)
declares **August 2025** source data republished into WebMercator. An earlier
anonymous mirror query reported 2 and 86 spatial intersects in these
windows, versus 2 and 94 candidate polygons in the **official original
2026 ZIP**. Different vintages, bounding/matching semantics or publisher
pipeline can explain differences; **do not interpret them as 8
missing buildings without row-level primary-source reconciliation**.
The primary scientific computations in this report did **not** use
the third-party mirror.

Neon insurance DB `research.source_sample_v0` retains only two new
**research metadata receipts**, independently read back:

- **#56** for original WSF mask #28: aggregate area and provenance, JSONB canonical SHA-256 `bc27b801f795125a3e5d0b9b930473fc4abda765b564f14c8ced2b07c64650f8`.
- **#57** for original WSF mask #29: aggregate area and provenance, JSONB canonical SHA-256 `11d2ba5ace6cc3ba3caf627470b2c02efbc81037f566793c89ded1868834ac65`.

Rights for `de.bayern.hausumringe` are scoped `verified /
allowed_verified` under the official BVV CC BY 4.0 evidence.
**Actual research sample state is metadata_only; source
admission_status remains not_admitted; model_input_approved=false.**
At the last independent read, research samples passed **57/57** internal
JSONB SHA256 checks, and **zero** samples were admitted to the CAT-model
input layer. These counts are a point-in-time snapshot and may change
as other source work progresses.

## Next independent scientific gates

1. **Temporal**: distinguish historical 2019 cadastral footprint
   truth from the observed present-day 2026 file; obtain comparable
   epoch or quantify changes before model calibration.
2. **Spatial validation**: repeat across independent, bounded urban,
   rural and residential/industrial sample windows, holdouts and
   jurisdictions; check omission/commission by land-cover and parcel
   context, not one urban point.
3. **Semantics and completeness**: classify building function, repeated
   rings/adjacent polygons, cadastral structure types, valid
   residential-versus-other occupancy and actual undercoverage.
4. **Insurance**: only after independently licensed building age/value,
   occupancy, replacement cost, TIV, vulnerability and market-share
   information could footprints contribute to *synthetic* insurance
   exposure. No unverified insurer-level portfolio assignment.
5. **Governance**: never promote source admission from a green source
   CI or one IoU. Audit separate legal, sample, scientific and model
   contracts first.

