<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg AGE HQ100: exact original 2021-model / 2022-release archive receipt

**Status: read-only provider file-format and provenance gate. No flood depth / hazard footprint admission.**

## Publisher source and version

Publisher is the Administration de la gestion de l'eau (AGE). The official
[HWGK2021 HQ100 catalogue](https://data.public.lu/en/datasets/flood-hazard-maps-100-year-flood/)
describes *modelled 100-year floodplain and water depth* pursuant to Directive 2007/60/EC.
It lists the original [ZIP resource](https://download.data.public.lu/resources/flood-hazard-maps-100-year-flood/20220613-154804/hwgk2021-hq100.zip)
as **3.9MB** with resource UUID `1f529004-dd4d-42f1-8bd3-3b33a3f54ffd`,
publisher SHA-1 `41b58cb5e0c9509d39824919dce85702ceda0540`,
updated **13 June 2022** and catalogue label **CC0**. The paired 63.4MB
GeoJSON resource has a *separate* original SHA-1 and must not be assumed
byte- or object-equivalent before independent comparison.

**Separate product:** The INSPIRE Natural Risk Zones HQ100 catalogue
https://data.public.lu/en/datasets/inspire-annex-iii-theme-natural-risk-zones-flood-hazard-maps-100-year-flood-3/
lists its GML asset as **modified 8 December 2025**, not 11 August 2026.
Its separately listed WMS service was updated **16 February 2026**.
A WMS publication date is not an underlying hazard model date; never assume
those products share feature IDs, depth intensity semantics or vintage.

## Reproducible exact-original source gate

`research_runners/luxembourg_age_hq100_2021_original_preflight_v0.py`:

1. Requires a regular non-symlink ZIP within a fixed byte limit, exact
   **publisher SHA-1**, and records an additional SHA-256 receipt. SHA-1 is
   publisher-reported version identity, not a secure signature or independent
   authenticity guarantee.
2. Rejects ZIP path traversal, symlinks, encryption, duplicate members,
   decompression bombs, oversized expansion and inconsistent or malformed
   SHP/DBF/PRJ headers.
3. Fully streams every member for CRC checking. Reads *only* SHP main
   header (shape type), DBF metadata/field descriptor names and declared row
   count, and bounded PRJ text for **keyword hints**, without emitting any
   source feature, coordinate, geometry, depth measurement or identifier.
4. Prints only archive-level member suffix counts and bounded file-header
   findings, with explicit `depth_units_verified=false`,
   `actual_hazard_geometry_read=false` and
   `model_input_admitted=false`. Original bytes are deleted in the
   GitHub runner, not stored in Git/Neon, or exposed in action artifacts.
5. Uses synthetic-only regressions to reject changed source SHA, unsafe
   ZIP paths, symlinks and corrupt inputs.

The separately scoped GitHub Actions workflow
`.github/workflows/luxembourg-age-hq100-2021-original.yml` fetches only
the exact resource at the fixed official HTTPS URL, and runs this script
after its synthetic gate. **Actual file structure and observations must be
taken from a successful real-original run, not inferred from the catalogue
description.**

## First actually verified original ZIP outcome (2 November 2026)

Full exact-origin [GitHub workflow 41408171685](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41408171685) **passed**, including four synthetic archive-integrity regressions. The official ZIP matched publisher SHA-1 `41b58cb5e0c9509d39824919dce85702ceda0540`; its reproducibility SHA-256 is `a2b107c577a06ea2d6264ef916c954767e5d9b11899b9298f58d3c18b7e35571`. Original compressed size is **4,093,773 B**, eight ZIP members (seven regular members and one directory), with aggregate expanded bytes **21,408,941 B**.

The archive contains **one shapefile group**, with exactly one each of `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`, `.sbn`, and `.sbx`. SHP main header declares **ESRI Polygon shape type 5** and its physical file size is **21,407,956 B**; the DBF header declares **exactly one row**, fields **OBJECTID (integer-like numeric), Shape_Leng (float), Shape_Area (float)**. The PRJ WKT currently has only a `LUXEMBOURG` keyword match; no source-specific CRS/axis has been independently approved.

**Important content correction:** This actual official 3.9 MB ZIP contains **no DBF depth field at all**. Although the AGE dataset catalogue mentions modelled floodplain and water depths, this ZIP **does not provide a DBF numeric intensity attribute for depth**, so it cannot be used to produce building-specific flood depth, vulnerability or loss calculations. Its one DBF row suggests an aggregate spatial zone or multipart shape; the **actual SHP record count, number of rings and coordinates still require a separate bounded, checksum-pinned source-record structural scan**. Do not equate one DBF record with a single physical flood zone, property, gauge or event, or infer that the companion GeoJSON contains the same semantics without independently inspecting it.

Source bytes, geometry and attributes were never logged, committed, uploaded to an artifact or written to Neon. `model_input_admitted=false`.

## Actual full original SHP record structure (2 November 2026)

The second fixed-original [GitHub workflow 41408573653](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41408573653) **passed** after verifying the same exact SHA-1, SHA-256 and ZIP CRC receipts. The enhanced standard-library source reader scans *only structural SHP record metadata*, validates record byte conservation, rejects impossible part-index sequences and skips the raw coordinate bytes without decoding or exporting them.

**Measured from the actual provider polygon source:**

| Original source measurement | Full source result |
| --- | ---: |
| SHP record count | **1** |
| DBF record count | **1** (matches SHP) |
| ESRI polygon shape type | **5** |
| Ring/part offsets in that one record | **6,379** |
| Polygon coordinate pairs skipped without decoding | **1,336,393** |
| Shape bytes declared and verified | **21,407,956** |
| Source attribute field for flood water depth | **none** |

**Interpretation:** this is one **very large multipart polygon record** with 6,379 declared parts. The count of parts is neither an independently validated count of connected floodplain regions nor a count of rivers, buildings, claims or flood events; polygon validity, hole/shell semantics and geographic CRS are not yet approved. The format can support an *extent-only* spatial screening only after a bounded actual geometry integrity/CRS gate. The ZIP's `Shape_Area` field is geometry area, **not simulated water depth**, and must never be reinterpreted as intensity.

The newly added source regression must reject malformed SHP record lengths/part offsets, source checksum drift, unsafe archive members, nonpolygon shapes, and SHP-vs-DBF population mismatches. No original coordinates or hazard values were persisted or printed.

## Original PRJ geodetic metadata screen (2 November 2026)

Dedicated fixed-provider-content [GitHub Actions run 41408965658](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41408965658) **passed**, including pinned `pyproj==3.7.2`, synthetic valid/invalid WKT cases and the real official ZIP. After independently validating the original file and all ZIP structure/CRCs, `research_runners/luxembourg_age_hq100_2021_prj_crs_screen_v0.py` read **only the original 445-byte PRJ WKT** and reported:

| Declared original-source PRJ property | Verified parser outcome |
| --- | --- |
| WKT parsed | true |
| CRS authority match ≥90% confidence | **EPSG:2169** |
| Coordinate system projected | true |
| Axis unit name | **metre** |
| Original polygon coordinate order and survey epoch field-controlled | **false** |
| Physical ACT2026 building location matched to this 2021 HQ100 scenario | **false** |
| CAT input authorized | **false** |

The 2021 AGE flood archive and 2026 ACT building data both declare **EPSG:2169**. This removes an important **declared CRS namespace mismatch**, not actual original *axis-byte-order*, precision, flood geometry validity or survey-vintage discrepancies. A projected CRS identity is not an independent check of 1,336,393 polygon coordinate pairs, actual flood intensities, 100-year recurrence calibration or physical insured building location. Never auto-approve a spatial join on this result alone.

**Depth next-step source strategy:** an official 2021 flood hazard map is independently exposed as a Geoportal WMS/WMTS render layer `eau_Hochwassergefahrenkarten_HQ100_2021`, while the 2021–2027 flood risk management plan and official gauge information describe classified depth bands. A rendered hazard map legend is **not** a raw raster or per-building depth value. Verify exact numeric depth layer access, temporal/return-period semantics, provider use rights and numeric units independently; if numeric surfaces are not public, request period-correct modelled depths or water-surface elevation layers from AGE. Do not infer flood depth from polygon extent, `Shape_Area` or map pixel colors.

## Next scientific steps

- Verify the original actual file format, complete record and field counts,
  CRS and axis ordering; identify how the provider encodes simulated
  water depths and units (or whether the ZIP contains only polygons).
- Freeze source release, coordinate transformation, scenario, depth units,
  and numeric decoding rules with a separate, small *real original-feature*
  inspection, whose detailed locations never enter Git.
- Make a bounded exact-source spatial overlap study against the separately
  tested Luxembourg ACT 2026 GeoBase physical polygons; distinguish
  independent source vintages and interpretation of 100-year scenario.
- **No real insurance portfolio or insured property value is available from
  official flood and building geometry alone.** A model loss requires
  separately sourced physical exposure meaning, vulnerability, insurer TIV,
  policy and reinsurance conditions and an admitted hazard intensity layer.

