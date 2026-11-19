<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT Luxembourg BD-Adresses: 2026-11-02 original CSV full-byte / CRS challenge

**Research-only; no source admission.** Official source: https://data.public.lu/en/datasets/adresses-georeferencees-bd-adresses/ . The ACT resource ID is 5cadc5b8-6a7d-4283-87bc-f9e58dd771f7. Its independently fetched original-provider metadata (2026-11-04) specifies the original asset URL https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/20261102-033122/addresses.csv, MD5 946114c1a24b49471b580bc225e4cb25 and size **28,209,815 bytes**. Publisher MD5 alone is not an independently calculated SHA-256.

## Direct source-byte evidence

A bounded HTTPS original-object range request of exactly the first 2,048 bytes was completed on 2026-11-04. The UTF-8 BOM and semicolon-separated, exact 13-column original CSV header were observed:

rue;numero;localite;code_postal;id_caclr_rue;id_caclr_bat;lat_wgs84;lon_wgs84;coord_est_luref;coord_nord_luref;id_geoportail;commune;lau2

The first original data row was checked only for matching column count and numeric text syntax in the four coordinate fields; **no individual address values or raw position values are recorded in this repository**. A 2-KiB range read is not a complete original-file hash or proof of all records.

## Exact implementation and scope

- New research runner: research_runners/lu_bd_adresses_original_csv_quality_v0.py. Zero-network default; --live permits **one hardcoded version-pinned HTTPS GET** with no redirects.
- Exact original file length **28,209,815 bytes**, absolute cap **32,000,000**, pinned original publisher MD5 and **independently computed entire-file SHA-256**. Fail closed on missing/truncated/altered bytes.
- Original bytes are temporarily spooled only in the isolated execution runtime and deleted after analysis. A strict BOM-aware UTF-8 semicolon parser requires exactly 13 pinned columns and enforces a maximum of 1 million rows.
- Numerics are checked for finiteness, paired presence, and broad Luxembourg coordinate envelope bounds. Only aggregate counts of rows, missing WGS84/LUREF pairs, repeated original coordinate strings and duplicate or missing CACLR-building-identifier strings are output. An address ID is **not** a physical footprint ID or insured asset.
- With --transform and an independently pinned pyproj runtime, EPSG:2169 east/north is converted to EPSG:4326 lon/lat with always_xy=True; median/p95/max discrepancy is reported. This tests internal field consistency, **not independent survey positional accuracy**.
- Offline fictional regression tests: tests/test_lu_bd_adresses_original_csv_quality_v0.py, 12/12 passed locally under Python 3.13 with resource warnings treated as errors.
- Isolated CI workflow: .github/workflows/luxembourg-bd-adresses-original-csv-quality.yml. Runs focused synthetic tests, pyproj==3.7.2 and one actual original source GET, outputting aggregates/hashes only. No original address records or source ZIP/CSV is uploaded as an artifact.

## Limits and link to the modelling platform

This extends previously merged #1239 (source/metadata), #1241 (synthetic geocoder rank@1/@3) and #1248 (synthetic point-to-polygon linkage), without overlapping their edited paths. It is intentionally **not a new geocoder**. ACT's own documentation cautions that coordinates can be parcel-centroid or building-centroid placements, duplicates may exist and many official addresses lack points.

Existing ACT GeoBase Buildings 2026-10-01 data are derived from the same national cadastral family. A successful ACT-address-to-ACT-building join is a useful linkage test, **not independent geographic ground truth**. A later spatial proof must preserve per-file vintage, separate building/parcel/unit identity, duplicate candidates and the provenance of each side. No CAT hazard, building TIV, insured policy, vulnerability, loss calibration or model admission is inferred.

The official dataset portal advertises CC0. The exact original-release use/rights, personal-record handling, original file byte SHA-256, empirical row-level QA and downstream scientific review are **not established until the new exact-head CI/original job has completed**. Output flags remain rights_admitted=false, building_identity_proven=false, cat_model_input_admitted=false, coordinate_source_independent=false.


## Executed full-original evidence — 2026-11-04

The exact-head focused GitHub Actions original-source job completed **successfully**: https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41800041417 . Its zero-network synthetic tests passed 12/12, then the isolated runner made one complete official HTTPS original CSV GET and computed the fingerprint below. This is **empirical original-file evidence**, not a synthetic estimate.

| Measure | Measured full original |
| --- | ---: |
| Original file bytes | 28,209,815 |
| Complete CSV rows, excluding header | **179,768** |
| Exact schema columns | 13 |
| Missing WGS84 latitude/longitude pairs | 0 |
| Missing LUREF easting/northing pairs | 0 |
| Distinct original coordinate text pairs | 179,735 |
| Repeated exact coordinate rows (beyond first) | **33** |
| CACLR building-identifier empty rows | 0 |
| Rows with previously seen CACLR building-identifier text | **584** |
| EPSG2169-to-EPSG4326 paired transform observations | **179,768** |
| Median / p95 / maximum spherical point difference, rounded to millimetres | **0.002 / 0.002 / 0.002 metres** |
| Full original SHA-256 | f163ed856200eedd8b501da2d7787e01ee373be1a55a4d79abcf57c96982a99c |
| Publisher-provided original MD5 matched complete bytes | true |

The above SHA-256 was calculated **from the downloaded full source bytes**, independently of the publisher's weaker MD5. After this observation, the research runner now pins the resulting original SHA-256 as well as the original size, MD5 and schema, so any later upstream change fails closed and requires a new reviewed vintage. The job had no source-file artifacts and only logged aggregate proof. Aggregate duplicate counts **do not identify** which buildings, properties or policy risks share those features.

**Interpretation:** The approximately 2-millimetre coordinate agreement only checks that the two coordinate columns encode compatible positions under the selected transform. It is **not** evidence that coordinates are ground-truth entrances, that ACT polygons match independent records, or that 179,768 independent insured building risks exist. The 584 rows with repeated CACLR-building-ID strings and 33 repeated coordinate rows explicitly caution against a one-address/one-building assumption.

The current per-file original receipt is now real and repeatable. Admission remains **false**: no property-level exposure, loss, vulnerability, insurance contract or independent footprint reference was validated in this job.
