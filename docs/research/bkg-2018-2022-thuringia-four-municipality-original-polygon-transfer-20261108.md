<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Independent original BKG 2018-to-2022 municipality geometry challenge for Thüringen

2026-11-08. **Original-byte reproducible research study; not any insurer
geolocation, TIV, policy data, vulnerability model or CAT model admission.**

## Independent official-source justification

The previous original GADM 4.1 vs BKG VG250 2022 comparison found
nine German land-polygon Kreis differences with intersection-over-union
under 95%. For Suhl, Ilm-Kreis and Sonneberg, the 2019 municipality
reform was strongly suggested by county-neighbor overlaps. This
study checks those relationships using **BKG 2018 genuine Gemeinde
level (GEM) polygons and BKG 2018/2022 Kreis level (KRS) polygons**,
without depending on restricted GADM source geometry at all.

| Original official source | Exact 31 December edition | Original ZIP SHA-256 |
| --- | --- | --- |
| BKG VG250 Ebenen GK3 SHAPE | 2018-12-31; https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2018/vg250_12-31.gk3.shape.ebenen.zip | 481d33de5c133fa55bcdc9f2964c48b2f5c21682acd3ec0885ec6d88bc2e75e7 |
| BKG VG250 Ebenen GK3 SHAPE | 2022-12-31; https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/vg250_12-31.gk3.shape.ebenen.zip | dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de |

The original BKG archive 2018 has **69,963,521 bytes**, and the 2022
archive **66,587,759 bytes**. Both original publisher SHA-256 digests
were separately computed and verified before the executable accepted
them. The 2018 VG250_GEM.dbf has **11,354 physical original records**,
from which the runner selects only the following four still-independent,
2018 GF=4 municipalities:

| Municipality original 2018 AGS | Municipality source name | 2018 donor Kreis | 2019 recipient |
| --- | --- | --- | --- |
| 16070017 | Gehlberg | Ilm-Kreis 16070 | Suhl 16054 |
| 16070046 | Schmiedefeld am Rennsteig | Ilm-Kreis 16070 | Suhl 16054 |
| 16073049 | Lichte | Saalfeld-Rudolstadt 16073 | Neuhaus am Rennweg, in Sonneberg 16072 |
| 16073066 | Piesau | Saalfeld-Rudolstadt 16073 | Neuhaus am Rennweg, in Sonneberg 16072 |

These are **eight-digit AGS municipality keys**, not five-digit county
keys. The official Thuringian statistics office documents legal
effective date **2019-01-01** and the corresponding former/new keys:
https://statistik.thueringen.de/datenbank/gebiet4.asp .
The legal change date comes from this independent historical record,
**not** inferred from the 2018 and 2022 GIS polygons. Other province,
municipality, or copyright systems must not adopt unreviewed IDs.

### Original 2018 versus 2022 geometry execution

The source-pinned runner in
research_runners/bkg_thuringia_2018_2022_gemeinde_transfer_v0.py
successfully processed original 2018 GEM plus 2018 and 2022 KRS
polygons with Python 3.11, shapely 2.1.2, pyproj 3.7.2 and
pyshp 2.3.1. It verifies the original Gauss-Krüger source WKT and
projects all originals to **ETRS89 LAEA EPSG:3035**.
Every municipality source polygon is present, has an exact original
AGS + name + GF=4, and overlaps the original 2018 donor Kreis.

| Original geometry statistic | Suhl receiving from Ilm-Kreis | Sonneberg receiving from Saalfeld-Rudolstadt |
| --- | ---: | ---: |
| The two former 2018 municipalities, union | 39.8581 km² | 27.8194 km² |
| 2018→2022 recipient Kreis new GF4 land area | 40.4841 km² | 27.8319 km² |
| Former municipalities overlapping recipient gain | 39.6165 km² | 27.4531 km² |
| **Percentage of recipient gain explained by original municipality polygons** | **97.8570%** | **98.6391%** |
| Percentage of former municipalities inside 2022 recipient | 99.3938% | 98.6833% |
| Recipient-gain polygon IoU vs former municipalities | 97.2765% | 97.3577% |
| 2018→2022 former donor Kreis lost land area | 40.3216 km² | 28.2255 km² |

These independent official polygons provide **direct municipality-scale
spatial support** for the 2019 cross-county reform explanation,
stronger than the prior restricted-GADM-to-BKG whole-Kreis comparisons.
The differences are not exactly zero: BKG generalized source geometry,
county edition differences or unrelated updates can explain residuals
and must not be silently rescaled.

No municipality floor-area allocation, claims, premium, insurer geography
or policy TIV follows mathematically from these areas.

## Reproducible offline original-source check

Acquire the two publisher-original archives under their official
conditions **outside Git**. The executable does not network-download,
overwrite existing reports or export source polygons.

    python -m pip install shapely==2.1.2 pyproj==3.7.2 pyshp==2.3.1
    python -m research_runners.bkg_thuringia_2018_2022_gemeinde_transfer_v0 \
      --bkg-2018-zip /external/vg250_2018-12-31.gk3.shape.ebenen.zip \
      --bkg-2022-zip /external/vg250_2022-12-31.gk3.shape.ebenen.zip \
      --out /tmp/bkg-thuringia-2018-to-2022-original-research.json

It rejects incorrect SHA-256, wrong source WKT, missing/ambiguous source
municipal AGS or names, modified GF=4 source semantics, missing old/new
county polygons, impossible area and intersection measurements. Only the
two case-level aggregate diagnostics and public official AGS codes
are shown; **no provider original source ZIP, polygon coordinates,
building-level data or 11,354-row GEM inventory is committed**.

Standard dependency-free synthetic tests:

    python -m unittest discover -s tests \
      -p test_bkg_thuringia_2018_2022_gemeinde_transfer_v0.py -v

**13/13 synthetic regression cases PASS** on exact branch source code,
including all nonfinite/negative area directions, incorrect donor/target
areas, missing original pins, and commercial R+V model non-admission.
**Original two-ZIP end-to-end execution also PASS** against exact branch
code. Full repository CI checks are tracked separately in the PR.

## Licensing, insurer model and attribution boundaries

BKG's public VG250 specification states official use with attribution
under **Datenlizenz Deutschland – Namensnennung 2.0**:
https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/verwaltungsgebiete/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html .

**Attribution if reproduced, distributed or displayed:**
© BKG (2018 und 2022) dl-de/by-2-0 (Daten verändert);
https://www.bkg.bund.de and https://www.govdata.de/dl-de/by-2-0 ;
use the BKG-specific changes label as directed at
https://gdz.bkg.bund.de/index.php/default/hinweise-zu-nutzungsbedingungen-und-quellenvermerken/ .
data providers see the product's original Quellenvermerk.
The exact BKG 2018/2022 edition, relevant upstream data providers and
change notices must be preserved in any independent BKG-only product.

The separate **GADM 4.1** original source expressly restricts commercial
use and redistribution without permission:
https://gadm.org/license.html . A BKG-only original municipality
continuity result does **not** license GADM 4.1, MaterialCities or their
source-derived construction-class GFA allocations.

Neither successful geometry IoU nor official BKG archive usage proves
actual buildings, R+V insured locations/market share, insurance TIV,
specific 2019 municipal policy allocation, 2025 insurer book vintage,
secondary uncertainty, vulnerability or Oasis GUL/IL/RI gross/net
curves. These need their own source/rights/science and model admission
gates. The executable deliberately reports every such admission false.

## Next high-leverage step

Use **BKG-only 2018 and 2022 administrative polygon differences**
to document any other regional changes without depending on restricted
GADM data, then evaluate the six remaining coastal/Bodensee cases
against BKG GF4/GF2 official semantics and openly licensed,
source-vintage-specific coastlines. Only after source rights are
resolved can any source-derived MaterialCities GFA transfer be
considered for the explicitly synthetic insurer portfolio.
