<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Three exact original native-source micro-receipts — GHSL AGE, GISCO Census 2021 and DWD RADKLIM RW

**Date:** 2026-11-12. **Mode:** deliberately bounded original-provider HTTP Range GETs and private-Neon research observations; **no entire raster or provider ZIP/TAR committed**. Product-scoped source licensing is not API automation permission or scientific CAT model admission. Research-only, no private insurance data and no exposure/TIV inference from individual source observations.

## 1. JRC GHSL GHS-AGE R2025A 1-km original embedded age-class legend

**License**: [Original JRC product copyright: CC BY 4.0](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/copyright.txt). **Original ZIP directory**: [GHS_AGE R2025A V1-0](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/V1-0/).

Original ZIP: `GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0.zip`. The full original file was **not downloaded**; ZIP End-of-Central-Directory and central directory were decoded from an original 32768-byte suffix Range; seven ZIP members identified. The small embedded `.csv` member (`GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0.csv`) has original ZIP-local offset **139**, compressed size **145**, uncompressed size **209**, and expected ZIP CRC32 **`abea4f34`**. We fetched the exact **`bytes=139-588`** range, inflated the entire 209-byte legend in memory and **verified the original local-header CRC32**. The range itself has SHA-256 `6696ddc23a3c7bf8f472e90a231ea7a65af35d0380c1e0b4b339507557dfec8f`; it is **not the SHA of the complete ZIP**.

Original category semantics (no original TIFF pixels sampled):

| Grid code | Meaning |
| --- | --- |
| 0 | Not built-up |
| 1 | Before 1980 |
| 2 | 1980–1990 |
| 3 | 1990–2000 |
| 4 | 2000–2010 |
| 5 | 2010–2020 |

Saved to private Neon `research.source_sample_v0` as **observed-values sample #51**, `model_input_approved=false`. This is a **raster class dictionary**, **not known construction years for individual buildings**. The final source needs a full archived TIFF identity/SHA, projection/NoData/units/overviews and validation before any exposure enrichment.

## 2. Eurostat GISCO 2021 Census population grid, release 30 May 2026 V3

**Original [2021 Census Grid download page](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids)** and [2021 census product-specific CC BY 4.0 rights](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution). **Never transfer this grant to restricted old GEOSTAT 2006/2011/2018 or EuroGeographics boundary geometries.**

Exact [original V3 ZIP](https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip). The archive's original 32768-byte suffix exposed nine ZIP members and offsets: country-level CSV ZIP, land-surface TIFF, continental `ESTAT_Census_2021_V3.csv`, GPKG, Parquet, raster TIFF, SDMX metadata ZIP and a `read.me`, plus the directory record. **No full 566MB archive or boundary assets downloaded.**

An original Range starting at the local ZIP member header offset **566121942** was fetched. Its complete 5428-byte compressed-member `read.me` was decompressed in memory. It identifies version **3.0**, EPSG:3035, 1-km grid and original national-statistical inputs received **2025-01-22**, despite the packaged V3 public release in **2026-05-30**. The README documents:

- `-8888`: cell/statistic withheld **for confidentiality**; must NOT be converted to zero.
- `-9999`: **other missing data**; must NOT be converted to zero.
- `T` total population need **not** equal `M+F` or other category totals due to statistical disclosure controls.
- `EMP` may exceed `T`. `POPULATED=1` can occur with `T=0`. Coastal cells can carry `T>0` and zero `LAND_SURFACE`.
- `CC_unallocated` country totals exist for **FR, IT, FI, BG, EL, SE, DK, NO, BE, LV, LU, SI**. Unallocated cells have no geometry in GPKG and are **not in GeoTIFF**; they must not be silently dropped when reconciling national totals.
- TIFF drops text variables `GRD_ID` and `CNTR_ID`; land surface is a **separate float32 TIFF**, while population bands are int64. A plain raster-only join therefore loses geographic provenance and unallocated records.

Actual `ESTAT_Census_2021_V3.csv` begins at local-header offset **209230036**. We fetched original **`bytes=209230036-209234131`** (4,096 bytes), decompressed an **incomplete CSV-member prefix** containing **219 complete original records**, checked schema/CRS, retained only **ten** first ordered public 1-km source cells and calculated a **50-record QA** preview. First 50 records contained **9** `M+F != T` differences and **25** `POPULATED=1` flags; the sum of nonnegative `T` values in those specific first 50 ordered records was **11,196**. These are **not representative European or insurer exposure statistics** and should not be aggregated as a national sample. The observed first cells include multi-national codes such as `AT-CH-LI` and `AT-LI`: **do not treat a multi-country cell as three independent 1-km cells**.

ZIP Range response SHA-256 **`c7f6598010350c185e835d4e33b2e6901402ea60440163bea3a1eacc024c6410`**, **not full ZIP or CSV-member digest**. Saved private Neon **observed-values sample #52**, `model_input_approved=false`; no whole archive, personal records, georeferenced building polygons or insured values were persisted.

## 3. DWD RADKLIM RW 2021 original NetCDF is officially unusable

[Original DWD DOI](https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_RADKLIM_RW_V2017.002-de.html) and [exact provider NetCDF notice](https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/readme.txt) confirm **2021 original NetCDF files are incorrect and should not be used**; corrected files are in the `supplement` directory. Rights: [DWD CDC CC BY 4.0](https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf). Original and corrected files are **different scientific assets** even under the same provider/product title.

Exact corrected file:
`https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/supplement/RW2017.002_2021_netcdf_supplement.tar.gz`

- Official directory listed **820,143,312 bytes** for corrected 2021 TAR.GZ, versus **820,110,127 bytes** for the **known-bad** original 2021 TAR.GZ.
- Fetched exactly **2,048 bytes** of corrected original archive `Range: bytes=0-2047`, verified **gzip/deflate** magic and decoded partial TAR header `2021/` in memory. Response prefix SHA-256 `741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867` (**prefix only**).
- Independently fetched and SHA-256 hashed the **740-byte** original source provider `readme.txt` explicitly forbidding original 2021 NetCDF. Private Neon **metadata-only sample #55**. No original NetCDF grid values, CF metadata, coordinate arrays or precipitation loss maps sampled.
- DWD also publishes year **2025** in a separate year directory in the same product family; version/year/DOI and correction state must remain separable.

**Fail-closed:** the [research runner](../../research_runners/eu_grid_native_sample_preflight_v0.py) explicitly blocks the original 2021 NetCDF URL and accepts only the corrected 2021 `supplement` URL **as a version-identity preflight**, not as downloaded/validated data. A full original-archive SHA and scientific QA remain necessary before admission.

## Offline input checks and private Neon verification

`research_runners/eu_grid_native_sample_preflight_v0.py` has **no network**, requires an externally pinned SHA-256 for all local file inputs and supports three distinct source contracts: (1) strict Eurostat V3 CSV prefix with confidential/other missing sentinels; (2) exact tiny JRC source class legend and ZIP CRC with no TIFF extraction; (3) the original-vs-corrected DWD 2021 annual archive URL gate. The [synthetic tests](../../tests/test_eu_grid_native_sample_preflight_v0.py) cover sentinels, dimensional types, nonrepresentative aggregation, missing cells, checksum changes, wrong EPSG grid IDs, GHSL class drift and DWD known-bad 2021 version rejection. **Synthetic tests include no original provider source rows or external input archives.**

```bash
python -m unittest tests.test_eu_grid_native_sample_preflight_v0 -v
python scripts/check_all.py
```

Independent private research DB verification:

```sql
SELECT sample_id, source_id, sample_kind,
       sample_sha256 = encode(sha256(convert_to(sample_json::text, 'UTF8')), 'hex')
         AS sample_hash_verified,
       research_only, model_input_approved
FROM research.source_sample_v0
WHERE sample_id IN (51,52,55)
ORDER BY sample_id;
```

The source candidate rows are **not** promoted to `admitted`. The GHSL and Eurostat statuses are narrower `actual_sample_state=collected_rights_cleared` for these **exact** small source-metadata/observed-value samples, while DWD remains `metadata_only`. All broad `rights_review_status` and `scientific_review_status` remain `not_reviewed`; scientific fitness for insured exposure and 10k-run CAT modelling is unproven.

### Next causal work

Freeze the exact whole original archive SHA for a 1-km Eurostat subset or JRC AGE TIFF and decode a **single valid pixel** with CRS, nodata and scientific provenance. Separately acquire and verify an entire corrected DWD RW2021 NetCDF member, CF metadata and time coordinate; do not sample the original bad 2021 archive. Preserve source rights and confidentiality sentinels in Neon before any NextGen/Oasis CAT source-admission proposal.
