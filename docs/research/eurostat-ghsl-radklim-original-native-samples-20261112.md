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

### Additional original DWD 2021 corrected NetCDF4 member confirmation

A second exact bounded Range GET of the **same** corrected 2021 supplement archive (`bytes=0-2047`; identical original prefix SHA-256 `741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867`) was decompressed in memory far enough to inspect **two TAR headers and the first eight NetCDF bytes**. It confirmed:

- The first TAR member is directory `2021/`; the next original source member is **`2021/RW_2017.002_202107.nc`** (July 2021), uncompressed TAR member size **91,356,907 bytes**. This is only the first TAR-listed month, *not* a completeness check or a promise of first chronological month.
- The first data bytes of this original NetCDF file are `89 48 44 46 0d 0a 1a 0a` — the **HDF5 magic signature**, confirming a real **NetCDF4/HDF5-formatted file**, not just an accessible `.tar.gz` path.
- The full actual HDF5 file was **not** downloaded or parsed, so no verified precipitation values, CF conventions, CRS, time coordinate, 2021 completeness or original archive end-to-end SHA are claimed.

This narrower original-source structural proof is retained as **private Neon metadata-only sample #58** with `model_input_approved=false`. Both DWD sample #55 (provider correction warning and gzip prefix) and #58 (native NetCDF4/HDF5 member signature) are **metadata receipts**, never provider array downloads.

## Machine-readable original archive index (without 566 MB / 18 MB acquisition)

Separate original `Range: bytes=-32768` suffix GETs on the **same two provider archives** were decoded directly as ZIP End-of-Central-Directory and complete central-directory metadata (names, sizes, offsets, compression, per-member CRC32). Both source-tail byte responses were independently hashed inside Neon; they are **not** full-archive SHA-256 values. No original raster or entire ZIP source bytes were persisted.

| Source | Internal entries | ZIP end-of-central-directory implied entire archive size* | Actual Neon metadata sample | Original suffix SHA-256 |
| --- | ---: | ---: | ---: | --- |
| JRC GHSL GHS-AGE R2025A, 1-km V1-0 | 7 | 18,663,320 B | **#59** | `20ba1a5e0a8129fe3b954a9c42b43c40b0a78d38ddb013d50798f1c30585fb60` |
| Eurostat Census Grid 2021 V3 | 9 | 566,125,577 B | **#60** | `590d677db2f9bf010dd5b00b738eee42e027e3fe6ade786124ed119495509a28` |

`*` Size is calculated from original ZIP central-directory offset plus directory size plus 22-byte no-comment EOCD, **not** separately independently verified from full-file download or HEAD.

Practical **source-format decision** for the 2021 V3 release, grounded in exact central-directory compressed sizes:

| Exact member | ZIP compressed bytes | Suggested source workflow |
| --- | ---: | --- |
| `ESTAT_Census_2021_V3.csv` | 49,110,575 | Controlled source-level CSV sanity test: preserve `CNTR_ID`, `GRD_ID`, confidentiality/other missing flags |
| `ESTAT_Census_2021_V3.parquet` | 55,211,012 | Candidate for scalable column-pruned research ingestion after original/full SHA and schema equivalence checks |
| `ESTAT_Census_2021_V3.gpkg` | 221,469,461 | Geometry-specific spatial research only; be cautious with country-straddling cells and non-geometric unallocated totals |
| `ESTAT_Census_2021_V3.tiff` | 30,762,675 | Multi-band gridded population; categorical/text identifiers omitted and unallocated population absent |
| `ESTAT_Census_2021_LAND_SURFACE_V3.tiff` | 5,751,483 | Distinct raster of floating land-surface area; do not assume the population TIFF holds it |

For GHSL AGE, the original 1-km `.tif` is **11,015,723 compressed bytes inside the ZIP**, and the entire, CRC-verified age legend is a separate 209-byte uncompressed `.csv` member. A pixel-index join requires the verified native TIFF geotransform and nodata values, not merely the colour legend.

The two file-inventory samples **#59 and #60** remain `sample_kind=public_metadata`, `model_input_approved=false` and `source_byte_persistence_authorized=false` and are distinct from the observed class/grid samples **#51/#52**.

## First original 1-km **non-missing** Eurostat V3 raster pixel (2026-11-12)

A new independent original provider **HTTP Range `bytes=535021482-535070633`** (49,152 B) read only the **local ZIP header and initial DEFLATE segment of the original `ESTAT_Census_2021_V3.tiff`** from [the exact V3 original source ZIP](https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip). It did **not** download the full TIFF or the 566-MB source archive.

In-memory decoding of this nested TIFF and its first metadata directory produced these **native, not inferred** raster properties:

| Original TIFF evidence | Verified value |
| --- | --- |
| Raster dimensions | **5,700 columns × 4,600 rows** |
| Format | Classic little-endian TIFF; **14× signed int32** bands |
| TIFF internal strip compression | DEFLATE/zlib, pixel-interleaved, one raster row per strip |
| Source CRS | **EPSG:3035** from GeoKey, ETRS89-LAEA Europe |
| GeoTIFF PixelScale | (1000, 1000, 0) m |
| GeoTIFF tiepoint | (pixel 0,0) at projected x=900,000 m / y=5,500,000 m |
| GDAL TIFF NoData | **-9999** (not a real negative population) |
| GDAL band names from original XML | T, M, F, Y_LT15, Y_1564, Y_GE65, EMP, NAT, EU_OTH, OTH, SAME, CHG_IN, CHG_OUT, POPULATED |

Using TIFF `StripOffsets`/`StripByteCounts` and the original ZIP-compressed prefix, source raster rows 100, 150 and 180 were **fully decompressed to 319,200 bytes of all 14 source bands each**. The following exploratory **top-edge-only**, nonrepresentative row quality preview was observed:

| Row (zero-based) | Valid T cells (not -9999) | T positive | T NoData |
| --- | ---: | ---: | ---: |
| 100 | 88 | 2 | 5,612 |
| 150 | 225 | 8 | 5,475 |
| 180 | 226 | 9 | 5,474 |

**One actual positive population cell** has been isolated at TIFF row **100**, column **4118** (zero-based); the complete **14-band source values** and source-range SHA-256 are retained **only** in private Neon **sample #63** and not reproduced as raw source cell values in this public, reference-only repository. The native EPSG:3035 cell-centre location is **X 5,018,500 m, Y 5,399,500 m**. This confirms a real positive total-population reading, not an observation about insured persons or buildings.\n\nThe **exact 49,152-byte original ZIP source response** is independently SHA-256 hashed in private Neon as **`80238bea7841928b220fbf61c980bafd61290f4bf2214a997686441593c09155`**. It is **only the bounded response SHA**, not the complete ZIP, TIFF, CSV or provider release. The original source TIFF metadata (projection, transform, NoData, 14 band labels) and actual pixel values were decoded from the binary TIFF, not copied from the separately sampled CSV; the CSV cross-check for the exact same grid ID remains to be performed.

**Strict limitations:** TIFF alone lacks `CNTR_ID`, `GRD_ID`, unallocated country totals and the CSV's `LAND_SURFACE`; cross-border duplication, land-only ratios, disclosure suppression `-8888` and missing `-9999` must be independently handled. No original full-archive checksum, all-strip coverage, original full-file CRS-scientific regression or underwriting model admission was conducted. No individual resident, policyholder, building location or insured-value record was collected.

New **offline, standard-library-only** [GeoTIFF exact 49,152-byte range QA script](../../research_runners/eurostat_gisco_v3_geotiff_one_cell_v0.py) pinning source URL/member, SHA-256, ZIP and TIFF schema, geokeys/affine transform, NoData, 14 band names, selected row 100 and column 4118; it **also verifies the TIFF scanline zlib stream (including Adler-32)** when run on locally supplied original Range bytes. Its [synthetic regression tests](../../tests/test_eurostat_gisco_v3_geotiff_one_cell_v0.py) construct a **different synthetic population pixel** and check version, CRC/integrity, ZIP identity, CRS, NoData and bad band structure. The script **has no network and was not yet itself run against the real original source bytes in this session**; original live provider bytes were independently decoded above. **Do not claim a live original Python-runner pass solely from offline CI.**

```bash
python -m unittest tests.test_eurostat_gisco_v3_geotiff_one_cell_v0 -v
# After separately fetching the exact original 49,152-byte Range:
python -m research_runners.eurostat_gisco_v3_geotiff_one_cell_v0 \
  --original-range /path/to/bounded-original-49152-bytes.bin \
  --expected-sha256 80238bea7841928b220fbf61c980bafd61290f4bf2214a997686441593c09155
```

The selected cell is a **population exposure covariate** for statistical research; it is **not** an independently geocoded insured building, flood hazard intensity, policy count, sum insured, modelled claim or CAT loss.

### Private research-only PostGIS spatial projection (source cell #63)

The private `insurance-risk-core` Neon database already has PostGIS 3.5.7. An additive, **read-only, fail-closed** source-specific PostGIS view was created and made reproducible in [SQL](../../sql/research_eurostat_census_2021_v3_pixel_research_v0.sql):

`research.eurostat_census_2021_v3_pixel_research_v0`

It includes **only** the official V3 original TIFF research sample profile with a **verified canonical sample JSON SHA**, `research_only=true` and `model_input_approved=false`. Each row contains original ZIP-Range SHA, source version, raster row/column, 1-km `geometry(Point,3035)` centre, PostGIS-transformed `geometry(Point,4326)` centre and the selected public aggregated population fields, with explicit `commercial_underwriting_authorized=false` and `nextgen_cat_model_input_admitted=false`. It never exposes a person, household, original raster bytes, a policy or a building polygon.

The existing original raster **sample #63** was independently projected in Neon/PostGIS:

| Coordinate interpretation | Verified coordinate |
| --- | --- |
| TIFF centre (ETRS89-LAEA, EPSG:3035) | **POINT(5018500 5399500)** |
| PostGIS WGS84 centroid (EPSG:4326) | Longitude **29.081945°**, latitude **70.856388°** |
| Original individual cell population counts | Private Neon sample #63 only; not republished here |
| Source NoData and admissibility | **-9999**, research-only, **not admitted** |

The WGS84 position is a **coordinate transformation** of the original grid centre; it is not a new original Eurostat `CNTR_ID` or proof of a particular insured location. Crosswalk against administrative coverage, `GRD_ID` and multi-country provenance is still necessary.

### Quality gate code execution clarity

A standalone [offline original-range validator](../../research_runners/eurostat_gisco_v3_geotiff_one_cell_v0.py) and [synthetic fixture regression tests](../../tests/test_eurostat_gisco_v3_geotiff_one_cell_v0.py) were added to the same draft PR. The **original provider live ZIP byte ranges were independently parsed in this session**, not executed using that Python script; therefore the GitHub CI exercises **synthetic data only**, not a second production byte fetch. The original range SHA used by the runner is independently pinned to the actual observed provider response and can be verified externally against exactly the frozen Range.

The initial CI reported one **synthetic test-data construction error** (a deliberately invalid band label was too long for the fixed-size synthetic GDAL metadata region). This was fixed by mutating a **same-length** band label instead; it still exercises the intended invalid-band parser branch. Do not claim final CI success until the new commit has completed. The original `#63` research sample and its Neon canonical hash check were unaffected.

## Independent official GISCO grid identifier and country check (2026-11-13)

To independently validate the **geographic cell identity** of Eurostat Census V3 research raster **sample #63**, the exact same raster centre was first transformed by private Neon PostGIS (EPSG:3035 → WGS84, longitude **29.081944969**, latitude **70.856388278**). The original [European GISCO ID service](https://gisco-services.ec.europa.eu/id/api-docs/) was then queried using **only the rounded WGS84 cell centre (29.081945, 70.856388)**. The two separate, fixed **single-point GETs** were actually executed against `gisco-services.ec.europa.eu`:

| Original official API read | Actual original response | SHA-256 of entire small HTTP JSON response |
| --- | --- | --- |
| [GISCO 2021 censusgrid ID](https://gisco-services.ec.europa.eu/id/censusgrid?x=29.081945&y=70.856388&epsg=4326&year=2021&format=json&geometry=no) | **146 B**; exactly one grid feature, ID `NO_CRS3035RES1000mN5399000E5018000`, NUTS-3 `NO074`, provider UID present | `efbc1beaf69b52af9236bfe961f648accdb765df3558306b364514a4fb63e55a` |
| [GISCO 2024 country ID](https://gisco-services.ec.europa.eu/id/country?x=29.081945&y=70.856388&epsg=4326&year=2024&format=json&geometry=no) | **49 B**; exactly one official country feature `NO` | `a5d423959f32c3fbbe09567a54d274724c650a8332070aedeb89114c5f9362bf` |

The GISCO cell ID **exactly matches** the 1-km TIFF raster origin calculated independently from source sample #63: `E5018000`, `N5399000`, corresponding to the known 500-m centre offsets. The original 2021 ID service returns a geographic cell ID and NUTS3, **not an independent copy of all 14 Census Grid V3 band values**. Also, the independent country service uses its **2024** boundary edition; neither ID-service call is itself an independent versioned V3 population-release digest.

Both original HTTP response hashes, source API URLs and only small geographic metadata appear in private Neon **research sample #65**, separate from original raster #63. The two actual bounded read-only API smokes are separately logged as **receipts #11/#12**. Original provider responses, user locations, insured persons, policyholder records, raw ZIP/TIFF and entire census CSV were **not** committed to public Git.

A new reproducible [private Neon PostGIS research view](../../sql/research_eurostat_census_2021_v3_cell_identity_review_v0.sql) joins independently hashed samples **#63 and #65**, and returns a row **only when the official GISCO country-prefixed cell ID agrees exactly with the mathematically derived 1-km EPSG:3035 TIFF grid origin**. Verified initial result: one matched grid ID, country `NO`, NUTS3 `NO074`. The view **always** asserts `independent_population_count_verification=false`, `full_zip_archive_sha256_verified=false`, `production_exposure_model_admitted=false`.

A separate [fully offline provider-response identity validator](../../research_runners/eurostat_gisco_2021_independent_grid_id_v0.py) requires two original short JSON responses and their **SHA-256 hashes**, refuses unexpected fields/countries/duplicate JSON keys/wrong grid centres and never prints source bodies. Its [synthetic-only regression tests](../../tests/test_eurostat_gisco_2021_independent_grid_id_v0.py) cover provider drift and mismatch detection. These actual provider GETs were observed through an independent small original-source web fetch, **not** by executing the new Python runner live.

### Next scientific gate

For exact V3 **population-count** parity, read the `ESTAT_Census_2021_V3.csv` member's record with `GRD_ID=CRS3035RES1000mN5399000E5018000` (and `CNTR_ID=NO`) from the *same* release and compare all 14 fields **without silently dropping `-8888` or `-9999`**. A GISCO ID response alone cannot establish that equality. The full released ZIP/TIFF SHA and publication rights/automation caveats remain outstanding before NextGen/Oasis production use.

### Independently verified official 1-km GISCO polygon outline (2026-11-13)

Beyond the separate GISCO grid ID / country responses, an **actual bounded original 391-byte GeoJSON HTTP response** was read from this exact original provider endpoint:

[GISCO 2021 Census Grid official original one-cell GeoJSON](https://gisco-services.ec.europa.eu/id/censusgrid?x=29.081945&y=70.856388&epsg=4326&year=2021&format=geojson&geometry=yes)

The response is a **single MultiPolygon feature** with the matching official 2021 grid ID `NO_CRS3035RES1000mN5399000E5018000`, NUTS3 `NO074`. In private Neon PostGIS, the official WGS84 geometry was transformed back into the original raster's EPSG:3035 and **independently compared with the mathematical TIFF grid cell** (EPSG:3035 lower-left `E5018000 N5399000`, 1000-m square):

| Original provider geometry check | Observed |
| --- | --- |
| Source GeoJSON parsed and PostGIS `ST_IsValid` | true |
| Official polygon `ST_Covers` the existing original TIFF-centre point | true |
| Official original polygon area in EPSG:3035 | **999,999.9276 m²** (about one km²) |
| Original GISCO GeoJSON boundary ↔ TIFF-derived 1-km square, PostGIS `ST_HausdorffDistance` | **0.0001448 m**, ~0.15 mm |
| SHA-256 of the **entire single original 391-B HTTP response** | `4cd38dea150a3abbe9fe7d43016a85f943c6e60c5d11d20fa4efa1ba6f06f445` |

**Private Neon metadata sample #66** saves the source URL, SHA, pass/fail flags and the derived numeric geometry metrics, with `original_polygon_geometry_persisted=false`, `research_only=true` and `model_input_approved=false`. No source GeoJSON coordinates or original response body are persisted in Git/Neon; those original bytes were used **transiently** for the independent comparison. The provider request is additionally logged as bounded API smoke **receipt #13**. The provider 2021 cell ID service may not separately attest the exact 30-May-2026 V3 population-data vintage.

The public repository includes a reproducible, additive [three-sample Neon integrity/geometry evidence view](../../sql/research_eurostat_census_2021_v3_polygon_parity_review_v0.sql), over source samples **#63 (original TIFF values), #65 (original GISCO IDs) and #66 (independent official polygon geometry receipt)**. The view filters to only verified original-source sample JSON hashes, exact linkages, matching cell ID, polygon coverage, area near 1e6 m², and the independently recorded boundary difference below 0.01 m. Its fail-closed output explicitly says `independent_population_count_verified=false` and `nextgen_cat_model_input_approved=false`.

This geometric comparison materially strengthens **spatial provenance**, but it does **not** replace the next missing test: the source V3 CSV row with exact `GRD_ID` and all 14 numeric population fields must still match the raster pixel to prove the census count's independent same-release parity. The source's complete ZIP/TIFF digest and bulk automation/redistribution review are likewise still open.
