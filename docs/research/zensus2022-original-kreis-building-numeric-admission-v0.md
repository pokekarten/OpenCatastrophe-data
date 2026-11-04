<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original 2022 Zensus Kreis building counts: reproducible, strict admission probe

**2026-11-04. Goal:** Move from verified 16-*Land* physical-building opportunities to exact **2022 Landkreis / kreisfreie Stadt building counts**, without treating a geographic opportunity as a 2025 actual insured R+V asset.

## Original-source chain and copyright/rights provenance

Original public publisher [Destatis Zensus 2022 buildings/dwellings regional table](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html), exact official file:

`https://www.destatis.de/static/DE/zensus/gitterdaten/Regionaltabelle_Gebaeude_Wohnungen.xlsx`

Prior GitHub Actions actual acquisition already established original file **21,451,209 bytes** and SHA-256 **`82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551`**, eight source worksheets, including `CSV-Gebäude`, `CSV-Wohnungen`, and methodology. See [previous exact-byte receipt](zensus-gdv-2022-2025-insurer-district-bridge-20261103.md). Official [Zensus original open-data terms](https://www.laiv-mv.de/Statistik/Zensus/Ergebnisse/) explain attribution and Deutschland Data Licence; verify exact product use terms before commercial distribution.

[Original Zensus database building classifications](https://ergebnisse.zensus2022.de/datenbank/online/variables) explain:

| Source exact `CSV-Gebäude` column | Class meaning |
| --- | --- |
| `GEBAEUDEART_SYS_1` | Buildings with living space, **including mixed-use** |
| `GEBAEUDEART_SYS_11` | Residential buildings |
| `GEBAEUDEART_SYS_111` | Residential buildings excluding dormitories |
| `GEBAEUDEART_SYS_112` | Dormitories |
| `GEBAEUDEART_SYS_12` | Other buildings with living space (often commercial/administrative mixed use) |
| `_RS` plus `Regionalebene` | **Hierarchical geographic identifiers**: both a Kreis-identifier condition and level label must match; Länder, Regierungsbezirke, Gemeinden and municipal associations must be **excluded**, not summed with Kreise |

The **2002 vs 2022** / **2022 vs 2025** question does not arise here: original physical source refers to **15 May 2022** while company property policy stock and premium totals refer to **31 December 2025**. They are not the same statistical population.

## New code and limits

`research_runners/zensus_kreis_original_numeric_receipt_v0.py`:

- Uses the existing original publisher URL and published SHA-256 pin. A changed official file **fails** until reviewed; no source-edition drift.
- Reads the original `CSV-Gebäude` sheet via bounded, streaming standard-library XML/OOXML ZIP handling; does not confuse published Excel shared strings with numbers or raw 2022 numeric observations with labels.
- Requires exact nine-column source schema, five-digit AGS and explicit *Kreis* administrative level. Duplicated Kreis keys, missing state coverage, implausible numeric values, source errors, and `/` / `-` / `...` / suppressed counts all **fail** rather than converting to zero.
- Separately records five original building types, the 2022 reporting date and hierarchy inconsistencies (the source may have statistical non-additivity). Outputs **aggregate source receipt** (row count, classification totals, source SHA, original source values hash, Länder presence, dates) and optionally a machine-readable TSV of **public county aggregate values** for auditor review. It does **not** output actual individual buildings/addresses or copy the raw copyrighted original workbook.
- Is checked with 12 entirely synthetic 400-district workbook tests. New addition to **`zensus2022-original-workbook-receipt.yml`** runs those tests, then explicitly downloads the real original in GitHub Actions and attempts the exact-Kreis extraction; **CI fails** if original network, edition, source header or suppression/geography checks fail. This is a separate original-acquisition lane, not the normal general repository test CI.

To reproduce:

```bash
python -m unittest discover -s tests -p 'test_zensus_kreis_original_numeric_receipt_v0.py' -v
python research_runners/zensus_kreis_original_numeric_receipt_v0.py --official-live
python research_runners/zensus_kreis_original_numeric_receipt_v0.py --original-xlsx /path/to/unmodified/Regionaltabelle_Gebaeude_Wohnungen.xlsx
```

## Scientific gates remaining after numeric validation

If the original-source workflow succeeds, county building opportunities can be admitted as a **2022 public physical source**. They **do not** create actual R+V insurer risk addresses, 2025 insured building values, 2025 policy county counts, flood endorsement, or a calibrated Oasis wind/flood catalogue. To build a real **synthetic district-weighted insurer hypothesis**, next connect the **exact publicly observed 2025 R+V Allgemeine national 1,060,546 contracts and annual 997,710 TEUR booked GWP** using the already tested conserved allocator with explicit unknown conversion per building. Geographical R+V company affinity should be treated as uncertain, varied across plausible sensitivity scenarios and **never asserted to be measured**.

Do not use the GDV interactive natural-hazard maps for bulk data mining without their required permission; this new source lane is limited to independently published German official **Zensus** statistics.

**Verification note:** existence of the script/CI alone is not evidence of live full Kreis admission. The exact-head source-audit job and source numeric receipt must be checked; report failure transparently if it fails.


## **Verified public 400-Kreis original-source acquisition / model bridge (2026-11-04)**

The live source-provenance workflow [#41907363439](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41907363439) **SUCCEEDED**, after exercising source-defensive cases for original Excel shared strings, suppressed subcategories and official **Cell-Key** non-additivity. The original-full workbook SHA is unchanged: `82da8578a4657e20752b436a756ed27846c77f96e3f7333bdea7f4fe29a8b551`. Canonical original 400-Kreis source row SHA: `a48c2d17a6e00c97fb4a151b1d990df78642de17dfd6ddf932479357e2589ca1`.

**New canonical attributed source dataset, not a synthetic value:** [400 Kreis observed official values, 2022](../../research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml). It contains only 400 *published official county-level building aggregate* rows, not original personally identifying building addresses, insurance policies, insurer locations or original workbook binary. Original numeric category coverage and national sums (note that these are summations of published Kreis cells, not unperturbed underlying true counts):

| 2022 official published Kreis aggregate | Kreis rows numeric / 400 | Sum where numeric |
| --- | ---: | ---: |
| Buildings with any residential use (`GEBAEUDEART_SYS_1`) | 400 | **19,957,288** |
| Residential buildings including dormitories (`_11`) | 400 | **19,488,949** |
| Residential buildings excluding dormitories (`_111`) | 400 | **19,474,175** |
| Dormitories (`_112`) | **393** | **14,802 (in the 393 published numeric counties, NOT Germany total)** |
| Other/mixed-use buildings with residential space (`_12`) | 400 | **468,301** |

The separately printed 2022 **Germany total** in an independent government publication is **19,957,268**, **20 lower** than the sum of all 400 original Kreis cells. This is not an error to be repaired by adding/removing 20 buildings. The official publisher [Cell-Key confidentiality explanation](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Datenbank/geheimhaltung-cell-key-methode.html) warns that published census subtotals need not add to the published marginal total. A single Kreis category hierarchy had a published excess of **4**, inside the explicit scientific QC bound of 10. Seven dormitory cells were unavailable; these are stored as `"missing"`, **never zero**, with source coverage separately documented.

**Now executable 2025 R+V study:** [`rva_2025_kreis_zensus_real_prior_fictional_book_v0.py`](../../research_runners/rva_2025_kreis_zensus_real_prior_fictional_book_v0.py) consumes actual 2022 public Kreis physical-building counts and the existing original **2025 R+V Allgemeine HGB solo national contract/premium** dataset. It generates three alternative **fictional insurer** county distribution hypotheses and conserves exactly:
- **1,060,546** original published nationwide *year-end connected-building insurance contracts*;
- **EUR 997,710,000** original HGB annual direct booked building GWP (not earned premium, risk TIV or regional underwriting tariff).

The scenario variants are **(1) all buildings with residential use**, **(2) residential non-dormitory buildings**, **(3) invented fivefold affinity multiplier for mixed-use in addition to residential buildings**. The source building counts are true published *statistical observations* for 2022; their use as R+V 2025 county insurance-contract *weights* is **fictional** and not estimated from company records. No geography represents a company address list. No GDV data/rights are implicated in this step.

Reproduce source and aggregate-conservation checks:

```bash
python research_runners/zensus_kreis_original_numeric_receipt_v0.py --official-live
python research_runners/rva_2025_kreis_zensus_real_prior_fictional_book_v0.py
python -m unittest discover -s tests -p 'test_rva_2025_kreis_zensus_real_prior_fictional_book_v0.py' -v
```

The last modeling step cannot claim a German native Oasis GUL/IL/RI/net catastrophe run or company-calibrated OEP/AEP. At least **2025 insured-policy geography, insured values and site coordinates, insured cover terms and endorsement mix, independent German peril catalogue/vulnerability, and outward treaty terms** remain unobserved. The 400 Kreis population improves the **real physical opportunity prior** while keeping these gaps explicit.

### Citable original provenance

- [Official Destatis regional Zensus 2022 spreadsheet product](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Publikationen/publikationen-akkordeon-regionaltabellen.html)
- [Official German census building classifications, GEBAEUDEART_SYS classes](https://ergebnisse.zensus2022.de/datenbank/online/variables)
- [Publisher Cell-Key disclosure control and marginal non-additivity](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/Datenbank/geheimhaltung-cell-key-methode.html)
- [Publisher German data license and attribution context](https://www.laiv-mv.de/Statistik/Zensus/Ergebnisse/)
- [Actual source-download and admission evidence: GitHub Actions original workbook workflow](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41907363439)
