<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA Hurricane Michael: first live STAC item metadata and source-access receipt

**Checked:** 2026-11-01. **Role:** research-only original provider metadata and a small source-shaped synthetic validation gate. No GeoTIFF, individual FEMA assessment, raw imagery, original flight file, imagery derivative, machine-learning labels or building/insurance data were acquired or committed.

## Official source and access paths

- Parent NOAA NGS InPort metadata, identifier `gov.noaa.nmfs.inport:57759`: https://www.fisheries.noaa.gov/inport/item/57759
- NOAA Digital Coast tile listing for imagery ID **8883**: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/index.html
- Exact source-wide STAC catalog: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/catalog.json
- Original publisher ISO metadata XML: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/2018_NGS_NaturalColorImagery_m8883_met.xml
- Original source tile-index ZIP: https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/tileindex_HurricaneMichael_2018.zip
- Direct STAC item examples, **metadata JSON only**, both successfully fetched and parsed:
  - https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0855400w301330n.json
  - https://coastalimagery.blob.core.windows.net/digitalcoast/HurricaneMichael_2018_8883/stac/20181011aC0853300w302100n.json
- Original publisher states **9,580 collected aerial images** across approximately **10,756 km²**, acquisition period **2018-10-11 to 2018-10-14**. This is not a count of individual Digital Coast rectified GeoTIFF tiles. Digital Coast lists approximately **85 GB** for the entire raster collection. Do **not** confuse aerial exposures with processed tile counts or bulk download the collection.

The first STAC catalog is reachable and has individually linked items. Its public display may be truncated by text-only retrieval, so there is **no claim that every catalog item/asset has been exhaustively inspected**. The publication date of the metadata itself can be years later than actual 2018 image acquisition; neither implies reconstruction-era coverage or historical building inventory.

## Exact two metadata-only items verified

| Field | Tile 1 | Tile 2 |
| --- | --- | --- |
| STAC ID | `20181011aC0855400w301330n` | `20181011aC0853300w302100n` |
| STAC version/type | `1.0.0` / `Feature` | `1.0.0` / `Feature` |
| CRS | `EPSG:4326` | `EPSG:4326` |
| BBox `[W,S,E,N]` | `[-85.9001,30.1999,-85.8749,30.2251]` | `[-85.5501,30.3249,-85.5249,30.3501]` |
| Raster shape | `[9340,9340]` | `[9340,9340]` |
| Bands | 8-bit RGB + alpha | 8-bit RGB + alpha |
| `properties.datetime` | `2018-10-11T00:00:00Z` | `2018-10-11T00:00:00Z` |
| `start_datetime` / `end_datetime` | Oct 11–14 2018 | Oct 11–14 2018 |
| `properties.license` | `NLPL` | `NLPL` |

Both are **rectified tile metadata**, not necessarily original flight-image metadata. The sample asset raster `proj:transform` and `proj:shape` provide an explicit grid footprint and native EPSG. The bounding rectangle is not an occupancy/building coverage polygon; the alpha band and source mosaic geometry need inspection before asserting an actual observed roof pixel. Longitude/latitude coordinates are public source tile envelopes, not privately identified building locations.

The item-level midnight `datetime` and 4-day collection-wide `start_datetime/end_datetime` **do not establish exact capture time**. Preserve real flight or scene-level timestamp only after finding/validating it in the exact upstream source. Do not infer that a tile was flown at 00:00 UTC or that the same event-time stamp applies to all exposures.

## Verified SPDX licence meaning, unresolved per-asset mapping

- The current original [NOAA InPort dataset record](https://www.fisheries.noaa.gov/inport/item/57759) explicitly states **CC0-1.0** and identifies NOAA as the imagery creator, with no access restriction; it also cautions against critical applications without understanding source limitations and against litigation use.
- The two inspected Digital Coast STAC **item** metadata files state literal `properties.license = "NLPL"`. This string is an **official SPDX identifier for the [No Limit Public License](https://spdx.org/licenses/NLPL.html)**, not "no licence provided", "unknown" or a noncommercial licence. The [STAC licensing specification](https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md) permits SPDX identifiers.
- Both named instruments are *broadly permissive*, so different identifiers **do not by themselves prove a restrictive licence or infringement**. Their identity differs; the reason for the Digital Coast item-level assignment and exact applicability to rectified GeoTIFFs/derived assets has **not** been verified directly with NOAA. This is an asset-rights *mapping and provenance* question, not a proven noncommercial block.
- Therefore keep `rights_review_status=not_reviewed`, `model_input_admitted=false` and `asset_specific_licensing_review_completed=false` until the exact asset origin, rights statement and permitted consumer scope are confirmed. No new licensing conclusion is granted to Mapbox/DigitalGlobe/OSM *before-event* imagery in NOAA's viewer; those are separately sourced.

## Lineage and spatial validation no-go

- FEMA historical damage public layer `DR-4399`, `ASMT_TYPE=RS`, `DMG_TYPE=WI` contains **23,682** remote-sensing classifications. **All lack `IMG_DATE` and `PROD_DATE`** in provider aggregate queries. Original interpreter/source imagery is therefore **unidentified**.
- NOAA source imagery was collected to assist disaster response with coordination involving FEMA. Source collection by NOAA is documented but **scientific independence from FEMA RS damage labels is not established**; NOAA imagery may have informed the same labels.
- Not a valid direct join: a NOAA rectified tile STAC ID, FEMA `OBJECTID`/point, FEMA `DR-4399`, a building polygon and an insurance policy are different identifiers. Even an exact bbox intersection only shows a *candidate* geographic overlap and cannot prove that a given building was observed, dated, independently assessed or insured.
- Florida DEP field-survey findings refer primarily to the **coastal building zone**, while FEMA `DR-4399` has 7 Florida counties and extreme Bay County sample concentration. Coastal selection, roof/wind vs surge/wave/erosion mechanism, survey timing, ordinal categories and possible common NOAA imagery must all be checked.
- NOAA image metadata plus FEMA RS assessments do not produce verified loss amounts, replacement values, vulnerabilities, first-floor elevations or event-sample representativeness.

## Executable bounded next step and acceptance test

The new code `research_runners/noaa_michael_stac_preflight_v0.py` accepts **one caller-supplied STAC item** and verifies source-native 2018 tile naming, WGS84 bbox/polygon consistency, declared UTC collection period, exact NOAA asset host/path, raster shape/grid affine envelope, RGB+alpha bands, and known source item license claim. The paired test file `tests/test_noaa_michael_stac_preflight_v0.py` uses **synthetic fixture values** with negative cases for incorrect source links, dates, rights, projection, pixel dimensions and coordinates.

Output explicitly marks `exact_capture_time_verified=false`, `pixel_coverage_verified=false`, `independent_of_fema_rs_labels_proven=false`, `asset_specific_licensing_review_completed=false` and `commercial_model_input_admitted=false`, while recognizing SPDX `NLPL` without treating a licence-identifier difference as an independently proven restriction.

**Next research gate:** select only a **single** exact NOAA tile and verify source image bytes, source license semantics, actual scene acquisition time and alpha coverage; then obtain the appropriate event-era independent building polygon/version and imagery provenance for a tiny rights-reviewed locality. No bulk image download, property join, event loss calibration or model admission until these are separately proved.
