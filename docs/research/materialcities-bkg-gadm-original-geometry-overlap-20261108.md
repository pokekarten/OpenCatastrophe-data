<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original geometry challenge: BKG 2022 vs GADM 4.1, MaterialCities 2026.9, Germany

2026-11-08. **Research-only, not an insurance exposure source admission.**

## Verified original-provider inputs

This audit directly continues the exact-source administrative CODE gate from
research_runners/materialcities_bkg_gadm_2022_code_crosswalk_v0.py.
The original inputs were fetched transiently from their public providers,
SHA-256 checked, read in an isolated Python 3.11 execution environment,
then not retained in Git or persisted to NeonDB.

| Original source, exact edition | SHA-256 |
| --- | --- |
| BKG VG250 source 31.12.2022, GK3 Shape Ebenen archive: https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/vg250_12-31.gk3.shape.ebenen.zip | dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de |
| GADM 4.1 DEU ADM2 original GeoJSON ZIP: https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_DEU_2.json.zip | add290173fedaca349d9bd312523d63bf7f9ef9389d473a78e1ce530c3450d7a |
| MaterialCities 2026.9 original publisher ADM GFA ZIP: https://zenodo.org/records/22306604 | ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38 |
| Destatis 2022 source pinned by the existing 400-Kreis TOML observation | Original workbook SHA-256 82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551 |

The existing crosswalk first validates exact edition and 400 official AGS
identities, 430 BKG geometry pieces, 403 GADM features, 402 matching
MaterialCities GID_2, and the historical code hypotheses
03152→03159, 03156→03159 and 16056→16063.

The original BKG PRJ is a Gauss-Krüger zone 3 ESRI WKT with explicit
EPSG:31467 source authority. pyproj 3.7.2 normalizes its E/N axis
representation to EPSG:5677. The runner validates the exact source WKT
authority, the accepted PROJ-normalized identifier and the pinned source
archive SHA. It transforms the source WKT geometry (not guessed WGS84)
and GADM original WGS84 geometry into a common **ETRS89/LAEA EPSG:3035**
equal-area plane. It groups the original multipart BKG source shapes by
AGS and combines historical GADM shapes only as a research hypothesis.

## Exact-original execution result

The new executable original-byte runner
research_runners/materialcities_bkg_gadm_geometry_overlap_v0.py executed
successfully on the exact three original ZIPs and the existing pinned
Destatis observation. Environment: **Python 3.11, shapely 2.1.2, pyproj 3.7.2,
pyshp 2.3.1**. It found all 400 source AGS geometry comparison candidates.

| Metric | Original replay |
| --- | ---: |
| Exact 2022 German AGS targets compared | 400 |
| BKG 2022 shape records (multipart administrative pieces) | 430 |
| GADM 4.1 raw ADM2 features | 403 |
| GADM features lacking a usable administrative code | 1 |
| MaterialCities source ADM2 region IDs checked | 402 |
| Overlap IoU >= 95% | **389 / 400** |
| IoU below 95%, manual review required | **11 / 400** |
| Median IoU | **99.3805%** |
| Minimum IoU | **70.8987%** |

A diagnostic threshold of IoU >= 0.95 is **not an approval** for
geographic, modelled building area, building construction/structural
typology, underwriting or insurer portfolio joins. An IoU below the
threshold is a research challenge that must not be ignored.

### Three structurally important case studies

| AGS | Place | BKG 2022 area km2 | GADM 4.1 area km2 | IoU |
| --- | --- | ---: | ---: | ---: |
| 03159 | Göttingen (historical Osterode merger candidate) | 1,754.88 | 1,755.12 | 99.4932% |
| 16063 | Wartburgkreis (historical Eisenach incorporation candidate) | 1,370.01 | 1,411.23 | 96.6262% |
| 16054 | Suhl (regional-vintage investigation) | 142.86 | 102.56 | 70.8987% |
| 01001 | Flensburg (coastal administrative geometry) | 56.89 | 49.35 | 85.7607% |
| 09162 | München Stadt (routine geometric control) | 311.42 | 311.50 | 99.3842% |

The official Thüringen state statistics office documents a **2019-01-01
municipal boundary change**: former Gehlberg (20.43 km2) and
Schmiedefeld am Rennsteig (18.17 km2) were incorporated into Suhl.
The two historical municipal areas sum to about 38.60 km2, close to
the 40.30 km2 difference between the original BKG/GADM projected
county areas. This is a strong **source-vintage hypothesis**, NOT yet
a polygon-based causal reconciliation or scientific independent
proof that the exact difference equals the incorporated areas.

Original state change records:
https://statistik.thueringen.de/datenbank/gebiet2.asp?krs=54
https://statistik.thueringen.de/datenbank/gebiet3.asp?nr=54000

Flensburg and other coastal cases may reflect water/coastline
boundary semantics, rasterization, drawing scale, source simplification,
or boundary vintage. No specific cause has been proved.

The program intentionally returns only country-level quality summary
and selected review examples; it does not publish the 400-region polygon
geometries, intersection areas, region-by-region mapping or MaterialCities
region-level building GFA/structural-type tables.

## Reproduction outside Git

Install optional, **research-only** spatial Python dependencies:

    python -m pip install shapely==2.1.2 pyproj==3.7.2 pyshp==2.3.1

Acquire legally authorized unmodified original ZIPs outside Git, then:

    python -m research_runners.materialcities_bkg_gadm_geometry_overlap_v0 \
      --bkg-zip /external/vg250_12-31.gk3.shape.ebenen.zip \
      --gadm-zip /external/gadm41_DEU_2.json.zip \
      --materialcities-zip /external/MaterialCities_adm_gfa_csv.zip \
      --out /tmp/materialcities-germany-geometry-research.json

The Zensus original observation is sourced from the canonical TOML in
the repository. The CLI refuses to overwrite existing research receipts.
If source SHA, projection, feature schema, historical code identity,
polygon validity or full 400-region coverage changes, the gate must fail.

Synthetic unit tests do **not** depend on Shapely/pyproj/pyshp and run:

    python -m unittest discover -s tests \
      -p test_materialcities_bkg_gadm_geometry_overlap_v0.py -v

**15/15 original-independent synthetic regression tests passed** on the
exact research branch in Python 3.11. The corrected original-source
geometry code was also executed end-to-end on the original bytes.

## Non-admission and next independent evidence

- Original GADM 4.1 rights restrict redistribution/commercial uses absent
  prior permission: https://gadm.org/license.html. MaterialCities CC BY 4.0
  does not override upstream GADM rights; BKG attribution is separate.
- Census is 2022-05-15, BKG 2022-12-31 and GADM geography may represent
  different vintages. Exact code mapping does NOT prove identical spatial
  support or time alignment. Suhl is a clear counterexample.
- IoU is a *geographical agreement statistic*, not a replacement
  for building-footprint source identity, risk-unit matching, inventory
  completeness, insurance market share, TIV, occupancy, fragility or
  native hazard/vulnerability/financial model validation.
- Every low-IoU case needs source-level water-vs-land and historical
  polygon-change diagnosis before any regional enrichment. Do not
  blindly allocate the source-modelled 15 MaterialCities structural
  GFA columns into the 2022 Zensus 400-Kreis roster.
- No R+V locations, true insurer building counts, company-specific TIV,
  policy terms, licensed Oasis or gross/net EP outputs are established.
  Model admission remains **FALSE** regardless of code or CI success.
