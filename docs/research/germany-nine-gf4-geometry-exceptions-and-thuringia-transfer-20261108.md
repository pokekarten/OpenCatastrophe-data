<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Nine Germany GF4 geometry exceptions: original-neighbor challenge (2026-11-08)

**Research-only. No admission of buildings, insurer sites, commercial GADM
usage, GFA allocation, CAT model geometry, TIV or vulnerability.**

This is the direct follow-up to PR #1436 (all BKG surfaces) and PR #1442
(BKG GF=4 land corrected). The preceding investigation found **391 / 400**
German AGS code regions with at least 0.95 intersection-over-union (IoU)
against GADM; nine land comparison cases remain below this **diagnostic**
threshold.

## Four source-original release identities

The executable audit uses the earlier fail-closed four-source
BKG↔GADM↔MaterialCities↔Zensus crosswalk. Each original provider file
is downloaded separately, source SHA-256 checked, and handled
transiently in an isolated Python 3.11 scientific research session.

| Artifact | Source edition and SHA-256 |
| --- | --- |
| Official BKG VG250 district shape archive | **2022-12-31**, https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/vg250_12-31.gk3.shape.ebenen.zip ; dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de |
| GADM German level 2 | **4.1**, https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_DEU_2.json.zip ; add290173fedaca349d9bd312523d63bf7f9ef9389d473a78e1ce530c3450d7a |
| MaterialCities ADM GFA archive | **2026.9**, https://zenodo.org/records/22306604 ; ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38 |
| Destatis original 400-Kreis Zensus workbook | **2022-05-15**, independently represented in the repository's pinned 400 AGS observation, original file SHA256 82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551 |

The exact provider BKG/KRS dataset contains **400 GF4 land** geometry
records and **30 additional GF2 water** geometry records covering 27
official AGS districts. The BKG specification explicitly distinguishes
coastal/Lake Constance water components from land:
https://sg.geodatenzentrum.de/web_public/gdz/dokumentation/deu/vg250.pdf .
The GADM CC_2→BKG 2022 AGS candidate crosswalk still maps the two old
Göttingen codes and old Eisenach code only as **historical code hypotheses**.

## All nine actual source-original sub-95% cases

IoU below is for original BKG **GF4 land** versus the matching
GADM 4.1 polygons projected to the equal-area EPSG:3035 coordinate
system. Rounded values are source diagnostics, not row-level mapping.

| 2022 AGS | Official district | GF4 land IoU | GF2 extra water in BKG original? | Review focus, not established cause |
| --- | --- | ---: | --- | --- |
| 01054 | Nordfriesland | 94.1502% | Yes | Coastal / shoreline coverage |
| 03405 | Wilhelmshaven | 93.9912% | Yes | Coastal / shoreline coverage |
| 04012 | Bremerhaven | 94.4927% | Yes | Coastal / shoreline coverage |
| 08335 | Konstanz | 94.1297% | Yes | Bodensee geometry / vintage |
| 13003 | Rostock | 94.8252% | Yes | Baltic shoreline / water semantics |
| 13075 | Vorpommern-Greifswald | 92.3505% | Yes | Baltic shoreline / water semantics |
| 16054 | Suhl | 70.8987% | No | 2019 administrative change |
| 16070 | Ilm-Kreis | 94.7693% | No | 2019 administrative change |
| 16072 | Sonneberg | 93.3896% | No | 2019 administrative change |

Rostock 13003 and Vorpommern-Greifswald 13075 **were above** 95%
when BKG GF2 water was included, but **fall below** with land-only
geometry. This non-monotonic source-interface effect is expected for
different coastline/water polygons and prevents blanket assertions that
land-only IoU always improves a source crosswalk.

The six coastal/Lake Constance cases remain under 95% after excluding
BKG GF2. Further independent shoreline, lake, enclave, scale and
source vintage work is needed; no precise causal attribution was
proved by this study.

## Official 2019 administrative changes and exact polygon neighbor support

Official Thüringer Landesamt für Statistik 2019 historical change
records: https://statistik.thueringen.de/datenbank/gebiet4.asp

- 2019-01-01: Gehlberg and Schmiedefeld am Rennsteig moved from
  **Ilm-Kreis 16070 to Suhl 16054**.
- 2019-01-01: Lichte and Piesau moved from
  **Saalfeld-Rudolstadt 16073 to Sonneberg 16072**.

**Original polygon evidence executed 2026-11-08**, after the full
four-source SHA-checking code preflight, using pyshp 2.3.1,
Shapely 2.1.2 and pyproj 3.7.2:

| Geometric difference | Source-exclusive area | Overlap with historically adjacent other-source Kreis | % support |
| --- | ---: | ---: | ---: |
| BKG Suhl land outside GADM Suhl | 41.05 km2 | 39.89 km2 in GADM Ilm-Kreis | **97.19%** |
| GADM Ilm-Kreis outside BKG Ilm-Kreis | 41.98 km2 | 39.96 km2 in BKG Suhl | **95.18%** |
| BKG Sonneberg land outside GADM Sonneberg | 29.01 km2 | 27.87 km2 in GADM Saalfeld-Rudolstadt | **96.06%** |

The two original source polygons are *not independent observations* of
where any individual building was actually located. The neighbor
overlaps are direct geometric evidence supporting the **vintage
mismatch hypothesis**, not proof that the exact source differences
equal the four named municipality polygons. Source geometry simplification,
generalization and actual legal effective dates could explain residuals.
**Do not treat these figures as actual transferable GFA or insured TIV.**

### What the runner now does differently

The existing file
research_runners/materialcities_bkg_gadm_geometry_overlap_v0.py
has been extended without introducing another geographic authority:

1. Requires the **exact nine original GF4 sub-threshold AGS keys**
   after SHA-pinned full input processing, and fails if the original
   source result changes.
2. Classifies each as source GF2 coastal/Lake Constance or possible
   2019 Thüringen vintage case, **not a proven causal conclusion**.
3. Records *only* nine manual-review research cases and their directional
   area-overlap diagnostics; refuses to export the full 400-region
   mapping or geometry.
4. Measures the source-exclusive polygons of the three Thüringen
   comparisons against the former/updated neighbor source polygons,
   reporting both source area and overlap share with
   historical_vintage_transfer_proven = false.
5. Preserves both **GF4-only** and legacy all-geofactor IoU.
   All insurer/building/calibration/rights admission fields stay false.

No polygon coordinates, GADM/MaterCities source bytes, region-derived
building-floor-area values, all-400 crosswalk, actual R+V addresses,
policies or TIV have been committed.

## Reproduction and scientific limitations

Run with the official original ZIPs under research rights as in
docs/research/materialcities-bkg-gf4-land-only-correction-20261108.md:

    python -m research_runners.materialcities_bkg_gadm_geometry_overlap_v0 \
      --bkg-zip /external/vg250_12-31.gk3.shape.ebenen.zip \
      --gadm-zip /external/gadm41_DEU_2.json.zip \
      --materialcities-zip /external/MaterialCities_adm_gfa_csv.zip \
      --out /tmp/geometry-nine-cases-research.json

The existing source-observed Zensus TOML is the fourth input.
Dependencies for the original geometry research runner:
shapely==2.1.2, pyproj==3.7.2 and pyshp==2.3.1.

Execute **34/34 dependency-free synthetic negative regressions**:

    python -m unittest discover -s tests \
      -p 'test_materialcities_bkg_gadm_geometry_overlap_v0.py' -v

Both the 34 synthetic tests **and the actual four-source archive replay
against this exact branch** passed in isolated Python 3.11. The source
original results are diagnostic, not independent building observation
and not enough to authorize an R+V 2025 insurer allocation.

**Rights:** GADM 4.1 explicitly requires prior permission for
commercial/redistribution uses:
https://gadm.org/license.html . MaterialCities's public CC BY 4.0
record cannot remove GADM's upstream requirements. BKG's separate
attribution terms do not grant GADM commercial rights. No official
commercial source reuse approval has been obtained in this study.

Next science gate: independent municipality-specific 2019 polygon
identity check and coastal/Bodensee surface reconciliation, then
rights review and building attributes/vulnerability calibration before
any region-level GFA weight or Oasis/R+V CAT model admission.
