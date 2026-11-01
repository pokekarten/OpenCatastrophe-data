<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg GeoBase Buildings 2026: original-ID and provider-source quality gate v0

**1 November 2026.** Research-only reproducible source QA on one official 1 October 2026 ACT GeoBase Buildings theme. Not an insurance exposure import, model input, approved source, original building-object crosswalk, construction-year proof or scientifically independent building survey.

## Verified upstream

The original provider ZIP was previously fetched and verified in merged PR #926 and original GitHub source job 41309676157:

- Primary ACT resource: https://data.public.lu/en/datasets/bd-l-geobase/
- Exact original: https://download.data.public.lu/resources/bd-l-geobase/20261001-010523/buildings-20261001.zip
- Publisher MD5: `f414154f993128a63f539aae2644c75a`.
- Original ZIP SHA-256: `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`.
- Original GeoPackage SHA-256: `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`.
- Original feature layer `Buildings_BU_Building`, 230,353 rows, `MULTIPOLYGON` declared, `EPSG:2169` declared, columns `id`, `geom`, `BU_BuildingID` and `Source`.
- ACT original is part of the same provider family as ACT2013 and ACT2023v2, but their versions, geometry definitions and object IDs are **not** presumed interchangeable. A 2026 source layer is not itself a construction-date register or evidence a building existed in 2013.

## Actual next step

New `research_runners/luxembourg_geobase_2026_id_quality_v0.py` requires the **prior independent ZIP SHA-256**, reuses the existing complete publisher-MD5 ZIP archive/GeoPackage checks, validates the 86 MB original GeoPackage SHA and exact fixed feature layer, and runs only aggregate read-only SQLite queries:

- original row count and primary SQLite ID distinct count;
- null geometry rows;
- missing/blank `BU_BuildingID`, nonblank count, distinct count and duplicate **excess** rows;
- missing/blank `Source`, nonblank count and distinct nonblank source-label count.

It does **not** enumerate or export original building IDs, source label strings, individual geometries, addresses, elevations, cadastral identifiers or policy data. The source is retrieved from a single frozen HTTPS URL, verified, temporarily extracted to a private workflow directory and destroyed; neither original source bytes nor geospatial extracts are committed or uploaded. The source data remain outside the insurance Neon metadata registry.

Synthetic unit tests cover missing/duplicated ID and source fields, count drift, path symlink and original-digest rejection. Run via GitHub specialized workflow or locally after an authorised original download:

    python -m unittest tests.test_luxembourg_geobase_2026_id_quality_v0 -v
    python -m research_runners.luxembourg_geobase_2026_id_quality_v0 --source-zip /private/local/buildings-20261001.zip

The specialized workflow output is the only authority for actual observed quality counts. **No original data quality percentages or cross-source matches are claimed until that job succeeds.**

## Interpretation and next proof gates

A unique `BU_BuildingID` in the 2026 source establishes **intra-file** uniqueness only. It does not prove that `buildingid` from ACT2023v2 uses the same ID namespace or that EUBUCCO LU00 uses the original official 2013 CityGML object ID. Resolve these identifiers through official schema definitions, known control records, release chronology and a manually adjudicated split/merge sample before any cross-vintage matching.

Unknown or contradictory source rights, axis order and roof-versus-ground geometry semantics remain blocking. No output represents sum insured, replacement value, construction year, insurer exposure, CAT damage or loss.

## Verified original-data execution (1 November 2026)

[GitHub workflow run 41310484331](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41310484331) retrieved the exact previously fingerprinted ACT October-2026 GeoBase ZIP, revalidated official MD5 and independently observed original ZIP/GPKG SHA-256, and ran the aggregate-only read-only original GeoPackage SQL. Eight synthetic quality tests passed first. The resulting original-file counts were:

| Exact original GeoBase field | Observed quality | Count |
| --- | --- | ---: |
| Buildings_BU_Building | original feature objects | 230,353 |
| id | distinct internal primary IDs | 230,353 |
| geom | NULL geometry rows | 0 |
| BU_BuildingID | nonempty building IDs | 230,353 |
| BU_BuildingID | distinct nonempty building IDs | 230,353 |
| BU_BuildingID | duplicate-excess IDs | 0 |
| Source | nonempty source labels | 230,344 |
| Source | missing/blank source labels | 9 |
| Source | distinct nonempty source labels | 5 |

These are **actual aggregate observations from the original source**, not manually sampled rows or inferred counts. This verifies full field presence and intra-file key uniqueness, NOT consistency across survey years, different GeoBase/ACT ID namespaces, the published source labels' legal permission, physical polygon validity, observed construction dates or source independence. Do not treat the 2026 230,353 count as the same objects as 2013 or 2023; any growth/change number requires a reviewed building identity crosswalk and split/merge treatment. No original provider row was exported or persisted.
