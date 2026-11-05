<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original JRC EuroCropsV2 corrected DE4 2023: Parquet footer receipt

Observed 2026-11-05. **Original partial-byte evidence only. NOT source/model admission.**

## Fixed original asset and byte-range observations

- Publisher: European Commission Joint Research Centre (JRC).
- Exact corrected original yearly asset: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/de4_2023.parquet
- Public original directory: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/
- Region/year: DE4 (Brandenburg), **2023**; this is not all Germany and not a multi-year stack.
- Original-provider HTTP Range `bytes=0-3` yielded four bytes `PAR1`.
- Range `bytes=-8` yielded eight bytes with a 32-bit little-endian footer length **16,258** and terminal `PAR1`.
- Exact 16,266-byte original footer-and-trailer range `bytes=-16266` was retrieved and decoded as Apache Thrift Compact Parquet FileMetaData. The entire 16,258-byte metadata body parsed; the terminal 8-byte length/magic agreed.
- SHA-256 of the **last 16,266 original bytes only**: `3ccb9177c49914f95e63d3942977c0d95a174b8434c004ba31f523be574b8d53`. **This is NOT the full-file SHA-256**, nor a publisher-signed digest; use it only to compare future exact footer receipts.

## What the original metadata really says

| Physical / scientific metadata | Observed value |
| --- | --- |
| Parquet FileMetaData version | 2 |
| Footer `num_rows` | **285,606** |
| Row groups | **1** |
| Row-group `num_rows` | **285,606**, consistent with footer |
| Leaf column count | **6** |
| GeoParquet metadata version | **1.0.0** |
| GeoParquet `primary_column` | **`geometry`**, **NOT `geom`** |
| GeoParquet geometry `encoding` | **WKB** |
| GeoParquet CRS identifier | **EPSG:3035** |
| Parquet writer (metadata) | parquet-cpp-arrow version 21.0.0 |

The exact original field names and observed column metadata:

| Column | Footer values | Footer `null_count` | Compressed column bytes |
| --- | ---: | ---: | ---: |
| `cropfield` | 285,606 | 0 | 985,098 |
| `original_code` | 285,606 | 0 | 140,089 |
| `original_name` | 285,606 | 0 | 142,835 |
| `off_area` | 285,606 | 0 | 1,176,768 |
| `geometry` | 285,606 | 0 | 138,108,208 |
| `area_ha` | 285,606 | 0 | 2,437,343 |

Further independently inspected original **footer-level min/max statistics**, not row observations:

| Source column | Reported footer minimum | Reported footer maximum |
| --- | ---: | ---: |
| `cropfield` (integer ID) | 1 | 285,783 |
| `off_area` (original submitted area) | 0.0002 | 248.7114 |
| **`area_ha` (computed projected area)** | **0.0** | **248.87251** |

The **zero minimum for `area_ha` is an actual original-metadata QA flag**. It indicates that the publisher's row-group statistics contain at least one reported zero value if the statistics are accurate. It does **not** yet prove that the corresponding polygon has zero geometric area: the stored area might have been rounded, truncated, or the source may have other production anomalies. A uniformly chosen subset of a few hundred rows could easily miss the affected record. We therefore added `original_footer_column_quality.any_row_group_footer_min_area_nonpositive` to the executable preflight, independently of its WKB sample, and require a targeted row-level follow-up before model admission.

The `cropfield` maximum of 285,783 exceeds the row count of 285,606, so IDs are **not a contiguous 1..N series**; this alone does not establish duplicates, omissions or portfolio counts. GeoParquet metadata also advertises an EPSG:3035 geometry bounding box `[4408648.375721003, 3145780.632999396, 4650737.518133259, 3382476.106293644]`. This is an original-metadata extent, not a verified union or the boundaries of every agricultural field.

Parquet physical types are `INT64` for `cropfield`, `BYTE_ARRAY` for `original_code`, `original_name` and `geometry`, and `DOUBLE` for `off_area` and `area_ha`. All six chunks report ZSTD compression (`CompressionCodec=6`). The provider originally described a `geom` field in its general README; **the actual corrected DE4 2023 file instead uses `geometry`**, as corroborated by its own GeoParquet primary-column metadata. Never hardcode `geom` for this source or mistake `off_area` for the computed projected polygon area `area_ha`.

The six `null_count=0` values are **publisher footer statistics**. They do not prove that any geometry is valid, that `area_ha` matches it, that crop codes are semantically known, that rows are unique, or that all fields in Brandenburg are represented. A `BYTE_ARRAY` original code may still be blank, synthetic, mismapped, or have a missing HCAT4 reference. No individual fields, farmer identities, coordinates, actual damage, or insurance exposure values were inspected.

## Engineering correction / remaining gate

The previous research preflight assumed `geom` and inspected only the first sample rows. Both assumptions were insufficient. The corrected runner at `research_runners/eurocrops_v202_preflight_v0.py` now:
- reads the declared GeoParquet `primary_column` (`geometry` or `geom` only), verifies it is an actual schema column, with WKB and EPSG:3035 explicitly evidenced;
- uses a source-SHA-seeded, deterministic uniform without-replacement sample **from all original file rows**, not the first 512. This DE4 asset has one row group, so multiple groups are not evidence of representativeness: row offsets across the single 285,606-row group are what matter;
- reads sample rows in bounded Arrow batches without materializing the entire row group, checks area/geometry/code integrity, and reports only aggregate counts;
- checks original footer area min/max and reported null counts **even if the random sample misses nonpositive fields**; missing footer statistics remain explicitly unknown, never a clean pass;
- preserves all source, rights, scientific and CAT admission as `NOT_REVIEWED_NOT_ADMITTED`.

The full corrected Parquet file was **not** acquired in the local runtime (JRC DNS inaccessible there), so original **full-file SHA-256, actual WKB geometries, source-row code frequencies and actual parcel area totals remain unverified**. Only targeted original header and footer byte ranges were read through the separate web retrieval route. No original file bytes were committed to this repository.

To graduate, execute the opt-in original-file acquisition outside Git, record full-file SHA-256 and publisher attribution, verify rights and run the schema/geometry preflight against the full original file. Do not promote a positive metadata receipt or a QC sample to actual agricultural exposure or CAT-model readiness.
