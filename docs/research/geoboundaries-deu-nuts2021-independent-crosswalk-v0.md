<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Germany 2021 ADM1 ↔ Eurostat NUTS1 independent polygon crosswalk

## Objective and scientific limitation

The live-reviewed geoBoundaries Germany ADM1 source has 16 original 2021
polygons. The previously verified CAT-only RTree staging can locate WGS84
points inside those state geometries, but the original geoBoundaries
`shapeID` is **not itself an official Eurostat NUTS identifier**. The
new source-specific crosswalk uses independently obtained **Eurostat NUTS1
2021** polygons and area-overlap evidence rather than a manually guessed
state-name mapping.

Both sources describe Germany at administrative/regional level, but the
geometries are not identical: Eurostat's `20M` cartographic release is
**simplified**. Even an unambiguous matching region is NOT a demonstrated
exact boundary, a legal administrative register or a building-level
geocoder. NUTS2021 is not EUBUCCO's **modified NUTS2016** partitioning.

## Two immutable original-source identities

| Field | geoBoundaries ADM1 | Eurostat Nuts2json NUTS1 |
| --- | --- | --- |
| Source & vintage | `DEU-ADM1-10402087`, represented year 2021 | Official Eurostat NUTS 2021 |
| Exact Git commit | `9469f09` | `8186be451525164ea24b43560cb943fda7c5520c` |
| Product | Full `geoBoundaries-DEU-ADM1.geojson` | `pub/v2/2021/4326/20M/nutsrg_1.json` |
| Original bytes | 6,254,151 | 194,955 |
| Exact SHA-256 | `56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682` | `1cacacf29694f518f6446ec286b5f251f3fea109d84874eb317c50b7300419b1` |
| Geometry | 16 original polygon features, CRS84/WGS84 | 123 EU NUTS1 features, 16 DE, WGS84 at 20M |

Official Eurostat source:
https://github.com/eurostat/Nuts2json/blob/8186be451525164ea24b43560cb943fda7c5520c/pub/v2/2021/4326/20M/nutsrg_1.json

Official Nuts2json project README:
https://github.com/eurostat/Nuts2json/blob/8186be451525164ea24b43560cb943fda7c5520c/README.md

Nuts2json repository licence: **European Union Public Licence 1.2**
(https://github.com/eurostat/Nuts2json/blob/8186be451525164ea24b43560cb943fda7c5520c/LICENSE).
GISCO/Eurostat source data attribution and specific NUTS boundary reuse
obligations require separate consideration before publication of derived
features or redistribution. geoBoundaries collection is CC BY 4.0, with the
specific DE source attributed under **Datenlizenz Deutschland –
Namensnennung – 2.0**. The crosswalk is deliberately local and not
automatically cleared for public derived-geometry release.

## Algorithm and safety gates

1. Verify **both** original file byte counts and SHA-256 *before parsing*.
   Do not confuse Git-LFS pointer with original full geoBoundaries geometry.
2. Validate all 16 geoBoundaries original OGC-valid features and Eurostat's
   exact 123-feature 2021 NUTS1 release; require the 16 known distinct
   German codes `DE1..DE9, DEA..DEG`. Do not reinterpret `shapeISO`
   as the missing Eurostat NUTS1 code.
3. Transform both independent sources from WGS84 to
   **EPSG:3035 equal-area coordinates** with a non-ballpark transformation.
   Measure polygon overlap in *square metres* (not square degrees).
4. For each geoBoundaries ADM1 polygon, select the single greatest
   intersection with Eurostat NUTS1 polygons. Require overlap covering
   at least **75% of both** polygons, and a runner-up covering less than
   10% of the best intersection. Require all 16 NUTS codes to be
   reached **exactly once**; otherwise fail closed. These are **conservative
   research acceptance thresholds**, not official boundary-certification.
5. Locally create a **new CAT2 SQLite crosswalk**, separate from
   the original 16-polygon CAT1 spatial database. Retain original
   `shapeID` to NUTS1-code mapping, both area-overlap fractions and
   both immutable source SHA-256 values. Query only if the stored
   application ID, source digests and NUTS year agree with the exact
   reviewed 2021 pair. Do not mutate any production, Neon, Pokémon or
   existing CAT database.
6. For point-based lookup, first apply CAT1 **exact polygon containment**,
   then find its ID in CAT2's 16-row mapping. Points outside Germany,
   on overlapping administrative boundaries, or with missing/ambiguous
   NUTS rows cannot silently receive invented region assignments.

## Locally reproducible evaluation

```bash
python -m pip install -r requirements-eu-flood-spatial.txt
python -m unittest tests.test_geoboundaries_deu_adm1_nuts2021_crosswalk_v0 -v
python -m research_runners.geoboundaries_deu_adm1_nuts2021_crosswalk_v0 \\
  --geo-original /secure/source-geoBoundaries-DEU-ADM1.geojson \\
  --nuts2021-original /secure/nutsrg_1-2021-4326-20M.json \\
  --output /secure/cat-data/staging/deu-adm1-nuts2021.cat.sqlite
```

The output path must be absolute, outside Git, new and end in
`*.cat.sqlite`. It is **not** a database migration or an approved
persistent production CAT source. The reviewed GitHub workflow
`.github/workflows/geoboundaries-deu-adm1-nuts2021-crosswalk.yml`
runs synthetic tests during PR review. On a workflow revision merge it
fetches both exact originals, builds temporary separate CAT1 and CAT2 files,
and requires actual fixed Munich/DE2 and Berlin/DE3 lookups. Afterward it
deletes both source files and both databases. No source polygons or
local original feature IDs are printed in routine public logs.

## The next actual building/insurance data requirements

- A **separately source-admitted building dataset** with verified geometry
  vintage and per-attribute provenance: building centroids can be assigned
  to a 2021 NUTS1 region with the exact tested point join. Buildings
  spanning borders need an explicit review, not only a centroid.
- **EUBUCCO v0.2 NUTS2 partitions use modified NUTS2016**, therefore the
  present NUTS2021 state crosswalk does **not** establish a verified
  EUBUCCO partition match. Do not infer one from a similarly spelled
  NUTS code or name.
- No construction-year, vulnerability, roof type, replacement value,
  insured share, insured location or damage metric is inferred by this
  crosswalk.
- Any new building import needs licensing, separate CAT data governance,
  source-date and no double-counting checks before model admission.

The real original-source workflow URL, quantitative overlap minima and
unexpected scientific differences must be entered only after the
live validation, not predicted from the synthetic fixtures.

## First real original-source outcome: blocked (2026-11-01)

The first strictly pinned two-provider workflow executed on
[GitHub Actions run 41317067892](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41317067892).
Both download steps and initial geoboundaries CAT1 stage succeeded; the
independent two-way overlap gate **rejected at least one German NUTS1
candidate**, emitting
`BLOCKED: no unambiguous high-coverage NUTS1/ADM1 match`.
No CAT2 crosswalk was created. Crucially, **a 16-code match is NOT yet
verified by real source overlay**, despite 16 synthetic offline tests in
the neighboring geoBoundaries job and 7 synthetic crosswalk tests here.

The research must inspect **per-code projected overlap fractions** before
any decision. Do not silently lower the 75% threshold, use state-name
correspondence as proof, or represent the full 16-region crosswalk as
production-usable. A second one-shot bounded live workflow will report
only suspect NUTS code(s) and numeric overlap fractions (no provider
feature identifiers or coordinates) and keep the same fail-closed cutoff.
