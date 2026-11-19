<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MaterialCities Germany to original 2022 AGS: independent administrative CODE preflight

2026-11-08, RESEARCH ONLY. This is a **source code identity and historical
administrative-change challenge**. It proves no same-era polygons, insured
R+V building exposures, actual property TIV, direct spatial attributes,
land-use, hazard-cell crosswalk or commercial use authorization.

## Original source bytes and lineage

Four original sources were fetched independently into a transient isolated
Python 3.11 research process. Original zip files and the derived region-level
402-row mapping were **not** committed, uploaded, retained or inserted into
NeonDB.

| Source | Exact publisher artifact and vintage | SHA-256 |
| --- | --- | --- |
| BKG official VG250 | 31.12.2022 GK3 shape Ebenen, original provider 2022 archive https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/vg250_12-31.gk3.shape.ebenen.zip | dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de |
| GADM | GADM 4.1 original German ADM2 GeoJSON ZIP https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_DEU_2.json.zip | add290173fedaca349d9bd312523d63bf7f9ef9389d473a78e1ce530c3450d7a |
| MaterialCities | 2026.9, original MaterialCities_adm_gfa_csv.zip https://zenodo.org/records/22306604 | ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38 |
| Destatis Zensus 2022 | Original 2022-05-15 400-Kreis building aggregates already pinned in research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml | original published workbook SHA-256 82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551 |

BKG provider documentation: https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/verwaltungsgebiete/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html .
The **historical 2022 archive path** is essential: the current product
download page now serves a different, more recent geographical snapshot.

The BKG ZIP has 66,587,759 bytes, and its VG250_KRS.dbf contains **430
shape/geography records but 400 distinct AGS identifiers**. Multiple geometry
parts in one AGS must not be counted as multiple independent Kreise. The
BKG **400** distinct codes exactly equal all **400** source-observed Zensus
2022 Kreis AGS codes (including leading zeroes).

Original GADM 4.1 has **403** ADM2 GeoJSON features. MaterialCities contains
**402** distinct matching GADM feature IDs. Exactly one GADM feature
without a valid CC_2 code is **not** in MaterialCities:
GADM GID_2 DEU.1.5_1, provider name Bodensee, CC_2 NA. Do not infer
a missing entire real Bodenseekreis or Germany-wide insurance coverage
from this GADM source irregularity: other valid GADM-coded regions exist.

Of the 402 MaterialCities GADM ID / historical CC_2 pairs:

- **399** CC_2 codes are an exact character match to the 2022 BKG
  official AGS dataset;
- **3** use older district codes, which were independently challenged
  against official state or county history:
  - old 03152, Göttingen, and 03156, Osterode am Harz: both proposed
    2022 target AGS 03159, after their **01.11.2016** merger;
  - old 16056, Eisenach: proposed 2022 target AGS 16063
    (Wartburgkreis), after **01.07.2021** incorporation.

Provider history:
- Lower Saxony state statistics office, official 2016 merger:
  https://www.statistik.niedersachsen.de/presse/zahl-der-kreise-und-gemeinden-in-niedersachsen-geht-zurueck-148228.html
- Official Landkreis Göttingen history:
  https://www.landkreisgoettingen.de/Landkreis/Portr%C3%A4t/Geschichte/
- Thüringen official territory history and Eisenach former AGS:
  https://statistik.thueringen.de/datenbank/gebiet1.asp?auswahl=krs
- Thüringen current official Wartburgkreis AGS list:
  https://statistik.thueringen.de/datenbank/auflistung.asp?auswahl=krs

Only with these **explicitly qualified historical code candidates**,
the 402 source GADM-coded rows collectively reach all 400 official 2022
AGS identities: 398 one-to-one target groups and 2 multiple-source-code
groups. No source key was discarded. These totals are source-key algebra,
**not an independently verified area/sum-preserving geographic polygon
crosswalk**, and DO NOT create a 400-row enriched building-loss dataset.

## Executable and reproducible research gate

Script:
research_runners/materialcities_bkg_gadm_2022_code_crosswalk_v0.py

Run using separately acquired, legally allowed **unaltered** source files:

    python -m research_runners.materialcities_bkg_gadm_2022_code_crosswalk_v0 \
      --bkg-zip /external/vg250_12-31.gk3.shape.ebenen.zip \
      --gadm-zip /external/gadm41_DEU_2.json.zip \
      --materialcities-zip /external/MaterialCities_adm_gfa_csv.zip \
      --out /tmp/materialcities-ags-code-only-research-receipt.json

The script reads the exact full source SHA-256 of all three ZIPs, reads
only BKG DBF AGS records, GADM 4.1 source GeoJSON properties, MaterialCities
ADM2 identifier column and the existing original Destatis 2022 observation
on disk. It rejects missing/duplicated source IDs, unknown historical codes,
changing source snapshots, 2022 BKG-versus-Zensus AGS disagreement,
uncoded GADM regions in MaterialCities, source drift and incomplete
candidate AGS coverage. The explicit destination exceptions are not a
general fuzzy spelling/name matching rule.

Synthetic offline test command:

    python -m unittest discover -s tests \
      -p 'test_materialcities_bkg_gadm_2022_code_crosswalk_v0.py' -v

Observed on independent Python 3.11 runner: **18/18 PASS**. The
**unchanged original four-source pipeline also executed PASS** in
that runner. Public repository CI on the final PR HEAD is a separate
merge gate.

## Still BLOCKED: spatial and commercial model admission

- A GADM CC_2 code does not prove its polygon geometry represents the
  exact area of the corresponding BKG AGS, especially after mergers.
  Calculate source-original valid polygon intersection/union/omission
  under consistent projected metric CRS and documented error bounds,
  with holes and BKG multipart geometry handled explicitly, before any
  area/GFA reassignment, 10k fictional geocoding or hazard sampling.
- Census snapshot is 2022-05-15, BKG archive is 2022-12-31, GADM
  original is a 4.1 release from 2022; this **does not prove**
  cross-source geometry vintage or 2025 carrier territory equivalence.
- GADM original licence explicitly **forbids redistribution or
  commercial use without prior permission**:
  https://gadm.org/license.html .
  BKG 2022 official source is attributed under **Datenlizenz Deutschland
  Namensnennung 2.0**, which does not grant permission to ignore the
  separate GADM and MaterialCities upstream-rights chain.
- Neither the source 15-component floor-area totals nor the original
  Zensus residential-building counts are actual R+V insured asset
  locations, actual market share, structure/vulnerability observations,
  policy TIV, premium-to-TIV conversion or EP model outputs.

All output states remain research-only, no independent geographic
overlap, no model input admission, no insurer geolocation certification,
and no persistent source byte or derived geographic row exports.
