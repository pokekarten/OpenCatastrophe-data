<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NYC BUILDING as-of-2024: local full-record canary and independent tax-lot source

**Research date:** 2026-11-05. **Decision:** offline, source-specific, non-admitted.
No original 2024 full-stock NYC BUILDING archive has been downloaded,
authenticated, incorporated or inferred from the City of New York current
BUILDING geometry or the demolished-only BUILDING_HISTORIC view.

## Actual state of our repository

Previously merged [NYC OTI footprint receipt PR #1371](https://github.com/pokekarten/OpenCatastrophe-data/pull/1371)
added a local-only file SHA-256 and eight-field header gate for an original
NYC BUILDING 2024 archive. It never reads original data rows. Earlier
[#1354](https://github.com/pokekarten/OpenCatastrophe-data/pull/1354),
[#1357](https://github.com/pokekarten/OpenCatastrophe-data/pull/1357),
[#1365](https://github.com/pokekarten/OpenCatastrophe-data/pull/1365)
and [#1367](https://github.com/pokekarten/OpenCatastrophe-data/pull/1367)
document current-footprint BIN/DOITT/BBL crosswalks, a 30-case nonrandom
LL84 2024 cohort and an incomplete historic-change archive interpretation.
The current snapshot must **never** be silently relabeled 2024.

## New research: actual 2024 tax-lot reference distinct from full polygons

Official NYC Department of City Planning's [PLUTO source and prior-version
landing page](https://www.nyc.gov/content/planning/pages/resources/datasets/mappluto-pluto-change)
explicitly says all PLUTO/MapPLUTO versions are archived on its BYTES of
the BIG APPLE releases. An official
[PLUTO November 2024 **24v4** source README attachment](https://data.cityofnewyork.us/api/views/64uk-42ks/files/200f83b8-31f3-400f-8566-68c1a753254b?download=true&filename=pluto_readme.pdf)
describes the historic property-tax-lot release and states that its OTI
building-footprint **centroid** input was dated **2024-11-18**. These are
useful as a source-version anchor, not as historical original polygons.

This original municipal 24v4 README is **not** a checksum of the underlying
24v4 PLUTO data package, a downloaded dataset, an insurer portfolio or a
complete 2024 BUILDING physical outline snapshot. The 24v4 data-package
bytes and hashes have not been verified here. Historical 24v4 tax-lot
grain and today’s 26v2 tax-lot grain may differ, including condominium
billing-lot handling. Before joining to an archived footprint snapshot,
acquire **both** source data artifacts, record independently confirmed
vintages, file checksums, stable BBL definitions and counts.

Separately, the [original NYC BUILDING 5zhs-2jue source](https://data.cityofnewyork.us/d/5zhs-2jue)
provides a public Dataset Changelog with prior-version export controls.
Per the [Socrata Dataset Archiving documentation](https://support.socrata.com/hc/en-us/articles/9486838238743-Introducing-Dataset-Archiving),
an export reconstructs a previous full CSV; changelog display is not
itself the actual archive file. A full NYC building-stock version
**at or before 2024-12-31** and its provenance are still missing.

## New runnable source-byte row-consistency gate

The source-specific new
`research_runners/nyc_building_archive_full_row_diagnostic_v0.py`
**depends on the already merged local hash/header preflight** rather than
inventing a new provenance representation. It supports either an original
local CSV or a ZIP containing exactly one CSV, validates whole-container
SHA-256 against a provided digest, strictly parses every local CSV record
while holding neither raw rows nor identifiers in its returned report, and
checks that actual row count conserves the **caller-provided** expected
row count. It refuses malformed UTF-8, CSV with wrong column count,
suspicious ZIP framing or counts exceeding five million.

Usage *only after* obtaining real original data and independent file hash
and provider-reported row count:

```bash
python research_runners/nyc_building_archive_full_row_diagnostic_v0.py \
  /secure/local/building-source-archive.csv \
  --expected-sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --provider-version-date 2024-12-30 \
  --expected-rows 1000000
```

**The CLI values above are illustrative, not verified real file
checksum/date/row-count facts.** A real original file must be inspected,
and the actual date and row count must be replaced by externally
verified source-specific values. Never paste a source row, coordinate,
identifier, personal data or unlicensed raw file into Git.

The aggregate-only scan distinguishes:

- well-formed/invalid/borough-specific unassigned million BINs and
  positive/zero/invalid DOITT IDs (DOITT uniqueness is **not** proven);
- valid/invalid physical `BASE_BBL` and PLUTO-billing
  `MAPPLUTO_BBL` keys, and equal-vs-different namespaces without
  conflating the condo billing lot with the physical lot;
- ordinary building code 2100, placeholder triangle 1003 and other
  features;
- nonempty-vs-missing geometry (no WKT/GeoJSON, topology, CRS or area
  verification claimed);
- missing/malformed construction years or construction after 2024,
  and missing/malformed edit timestamps or last edit after 2024.
  These are **review flags**, not independent evidence of individual
  building 2024 presence/absence.

The gate hashes the source container again after the row scan to catch
source-file changes while reading. Only the existing source-specific
NYC eight-field schema is expected; if an older archive lacks a field,
that must be explicitly researched, reviewed and represented in a
separate original-version mapping rather than silently dropped.

**Critical contractual limits:**

- `whole_csv_record_count_verified_against_caller_claim=true`
  proves *only* local parsed rows equal the supplied integer.
  **The integer is not a city-issued, signed row-count receipt.**
- `official_2024_inventory_release_authenticated=false`,
  `source_rights_or_model_admission_approved=false`,
  `actual_polygon_geometry_topology_validated=false`,
  `global_bin_uniqueness_verified=false`,
  `global_doitt_id_uniqueness_verified=false`,
  `insured_tiv_or_loss_calculated=false`.
  Passing local CSV tests **does not** make a 2024 historical insurer
  portfolio, actual physical exposure or calibrated CAT model.
- This scanner has no network access and does not persist source rows,
  company data, geocoordinates, addresses or original source
  identifiers. It does not write Neon, OED, NextGen or original
  Git blobs.
- `tests/test_nyc_building_archive_full_row_diagnostic_v0.py`
  contains 14 synthetic/offline test cases, including ZIP integrity,
  multiline CSV cells, wrong cardinality, raw row leakage, oversized
  numeric strings, false dates and placeholder identifiers.

## Concrete scientific next step

1. Obtain an official **actual version-dated** full 2024
   BUILDING archive from NYC's changelog or through
   [NYC Open Data contact](https://www.nyc.gov/opendata/contact-us).
   Log its original release/revision ID, complete file size, actual
   original data bytes SHA-256, original field dictionary,
   complete source row count and terms. No provider request has been
   dispatched by this research.
2. Independently acquire and hash the original official 2024
   **PLUTO 24v4** file package. Preserve its November 2024
   centroid-vintage caveat and month-end mismatch rather than claiming
   the file is a 2024-12-31 ground truth.
3. Run the byte/header preflight and full row-consistency scanner
   offline. Independently verify official provider version identity
   and release date, completeness and provenance; do **not** treat
   a successful caller-provided hash/date/count as provider proof.
4. Run source-version-specific historical BIN / DOITT / BASE_BBL /
   MAPPLUTO_BBL crosswalk, polygon CRS/topology/overlap and demolition
   evidence reconciliation. Separately parameterize synthetic
   replacement cost and insurable interest with uncertainty; do not
   impute insurer policies or real TIV from geometry alone.

This independent technical work advances readiness for actual 2024
source bytes without making unsupportable statements about current NYC
footprints, archived historical property identity or insured loss.
