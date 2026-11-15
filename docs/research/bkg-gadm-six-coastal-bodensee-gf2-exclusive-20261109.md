<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original GF4/GF2 coastal and Bodensee source-exclusion audit

**Research date 2026-11-09. Original-source non-commercial scientific
analysis; NO GADM/MaterialCities commercial/redistribution permission,
insurer location or TIV, 400-Kreis geographic enrichment, or Oasis
model admission.**

## What the marine/shoreline hypothesis actually measures

The original Germany BKG/GADM land-only spatial audit
(PRs #1436, #1442, #1451) found six German AGS with IoU below
the diagnostic 0.95 threshold and an original official BKG GF2
marine/Bodensee piece. It is unsound to assume that all
GADM-versus-BKG land discrepancy must be marine water.

BKG VG250 official specification documents land **GF=4** and
additional North Sea, Baltic Sea, Bodensee **GF=2** components:
https://sgx.geodatenzentrum.de/web_public/gdz/dokumentation/deu/vg250.pdf .
The original 2022 BKG KRS archive holds 400 GF4 land records and
30 additional GF2 water records (27 AGS); those are still 400
administrative district keys.

The original source SHA-256s verified in this run:

| Source original edition | Exact provider address | SHA-256 |
| --- | --- | --- |
| BKG VG250 2022-12-31 GK3 SHAPE ZIP | https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_1231/2022/vg250_12-31.gk3.shape.ebenen.zip | dc594b22fc4e6937c5a93894592d0a36d48cce68ef78cca24dda53a9fb6326de |
| GADM 4.1 German ADM2 GeoJSON ZIP | https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_DEU_2.json.zip | add290173fedaca349d9bd312523d63bf7f9ef9389d473a78e1ce530c3450d7a |
| MaterialCities 2026.9 ADM-GFA archive | https://zenodo.org/records/22306604 | ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38 |

The original Zensus 2022 400-Kreis source is independently pinned
in research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml .

## Area set operations in EPSG:3035

After exact original-source identity preflight, the same
Python 3.11 / Shapely 2.1.2 / pyproj 3.7.2 / pyshp 2.3.1
research environment measured all polygons in ETRS89 LAEA EPSG:3035.

For each of six official Kreis source keys:
**L** = BKG 2022 GF4 land, **W** = its own BKG 2022 GF2 water,
**G** = GADM 4.1 source polygon.

- Source difference GADM-only = area(G \ L).
- Reciprocal official land-only = area(L \ G).
- GADM-only portion intersecting the official GF2 = area((G \ L) ∩ W).
- Remaining GADM-only outside BKG land and GF2 = area((G \ L) \ W).

This is NOT a GADM water classification, proof of an identical coast
or modelled flood cell, GADM licence, or insurance location.

## Verified direct original-source measurements

| Official Kreis / AGS | GADM outside BKG land (km²) | Of this, inside its BKG GF2 (km²) | Marine source overlap of GADM-only | Remains outside GF4 and GF2 (km²) |
| --- | ---: | ---: | ---: | ---: |
| Nordfriesland 01054 | 104.992 | 0.286 | **0.27%** | 104.706 |
| Wilhelmshaven 03405 | 1.762 | 0.397 | **22.52%** | 1.365 |
| Bremerhaven 04012 | 0.628 | 0.029 | **4.67%** | 0.599 |
| Konstanz 08335 | 48.267 | 0.311 | **0.64%** | 47.956 |
| Rostock 13003 | 6.930 | 6.025 | **86.94%** | 0.905 |
| Vorpommern-Greifswald 13075 | 303.916 | 154.056 | **50.69%** | 149.861 |

- Rostock has a very substantial GADM-only overlap with BKG GF2
  (**86.94%**), supporting a source-interface explanation for
  most of its mismatch.
- Vorpommern-Greifswald remains with **149.86 km²** of GADM-only
  source polygon outside BKG land and its own GF2 water component.
- Nordfriesland and Konstanz have negligible overlap with their
  BKG own GF2 regions. Do NOT explain these entirely as additional
  BKG water polygons.
- Wilhelmshaven and Bremerhaven also remain below 95% IoU after
  filtering GF2 and need separate shoreline/boundary checks.

The full German 400-Kreis land-only result stays **391/400**
above IoU 0.95, nine review cases, including these six. That
threshold is a research diagnostic, not admission of an insurer
or hazard model source.

## Source implementation and tests

Extend the canonical runner only:
research_runners/materialcities_bkg_gadm_geometry_overlap_v0.py .

It requires the same four exact source identities; validates the six
version-pinned review AGS against the nine previously measured cases;
computes symmetric source exclusives, GF2 intersection and residual
without inventing source land use; and emits only six summary-scale
research diagnostics.

No original polygon coordinates, source ZIP bytes, full 400-row
region geometry table, insurance sites, loss curves or MaterialCities
building GFA rows are published or committed.

**43/43 dependency-free offline synthetic tests PASS**, including
nine new fail-closed cases for negative/nonfinite or impossible
source areas, both denominator directions, missing marine area,
and the explicit false source-rights/insurance-admission states.

**The exact committed branch code has also passed the end-to-end
original four-source replay**, all three ZIP SHA256s confirmed,
400 regions validated, and six new original geometry diagnostics
calculated. Full GitHub CI is assessed separately in the PR.

Reproduce with licensed original files stored outside Git:

    python -m research_runners.materialcities_bkg_gadm_geometry_overlap_v0 \
      --bkg-zip /external/vg250_12-31.gk3.shape.ebenen.zip \
      --gadm-zip /external/gadm41_DEU_2.json.zip \
      --materialcities-zip /external/MaterialCities_adm_gfa_csv.zip \
      --out /tmp/bkg-gadm-six-coastal-20261109-research.json

## Rights and no-model admission

The BKG source is provided under **Datenlizenz Deutschland –
Namensnennung 2.0** with modification notice and sources:
https://gdz.bkg.bund.de/index.php/default/digitale-geodaten/verwaltungsgebiete/verwaltungsgebiete-1-250-000-stand-31-12-vg250-31-12.html .

Source and alteration attribution for this research:
**© BKG (2022) dl-de/by-2-0 (Daten verändert);
Datenquellen: BKG VG250**. The provider's detailed Quellenvermerk
and attribution links must be preserved for any external reuse.

GADM expressly restricts redistribution or commercial use without
prior permission: https://gadm.org/license.html . MaterialCities's
Zenodo CC BY 4.0 metadata does NOT supersede this upstream rule.

No actual R+V insured sites, risk portfolio, replacement TIV,
company market share, Oasis GUL/IL/RI, vulnerability calibration
or gross/net OEP/AEP curves were inferred. The source case
classification and GIS agreement are NOT an approval for
commercial insurance exposure.

Next independent scientific step: original BKG 2018/2022/2025
coastal snapshot comparison and separate rights-cleared, finer-scale
coastline/lake source validation. The historical 2018 BKG ZIP may
be intermittently served with bytes different from the pinned release;
any mismatching SHA must be rejected, not silently adopted.
