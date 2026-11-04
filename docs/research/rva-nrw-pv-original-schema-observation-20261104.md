<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NRW 2026-03-12 rooftop PV opportunity XLSX: exact-source semantic header canary for R+V scenarios

**Research-only as of 2026-11-04.** Target is a *fictional* R+V Allgemeine Versicherung AG solar/roof ancillary exposure scenario; publisher data are not actual R+V properties.

The already merged [first byte and structure verification](rva-nrw-rooftop-pv-original-xlsx-20261104.md) pinned original NRW government XLSX **1,506,519 bytes**, SHA-256 `a9730f844159781c0747a4eb816f88382924239d0cc1874ea69d7a70ce912071`, 5 actual worksheets with occupied row count `6/397/397/397/397` and max cell-count `2/254/254/9/9`. [NRW official OpenGeodata original and DL-DE/Zero 2.0 product listing](https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/photovoltaik/) is the source; source timestamp on page 12 March 2026.

## This new actual-source experiment

The new `research_runners/rva_nrw_original_pv_schema_observation_v0.py` imports the **existing pinned original reader** without weakening its exact SHA, byte, ZIP/macro/formula and five-worksheet-shape gates. It reads worksheet XML in memory, printing a bounded machine-readable **source header / aggregate-cell-type receipt**: sheet titles, *first row only* header labels (first 30 plus last four), 30 keyword-related possible semantic column labels, body row/occupied cell and numeric/text counts, potential suppression token counts and possible five-/eight-digit identifier **counts only** without emitting any original IDs. All row-level values (town names, municipality AGS, exact PV numbers) remain **unprinted**, even though the source may publicly contain them. Synthetic ten-test suite specifically verifies no municipality row leakage, pseudo-key candidates not promoted to verified AGS, shared-string index/Excel coordinate failure cases, fake macro and bytes-gate integrity.

Source-specific original workflow `.github/workflows/rva-nrw-original-roof-pv-schema.yml` uses read-only GitHub permissions and SHA-pinned checkout/setup-python actions; no secrets or raw workbook artifacts. **No installation count, rooftop panel value, insurer link, 2025 site coverage or TIV can be inferred from a PV potential spreadsheet.** The NRW technical rooftop potential and MaStR actually commissioned registered PV installation universes are different and must remain separate.

### Decisions to make after observing the real header/aggregates

1. Determine exact **municipality key** and reporting year from published sheet and field labels, including boundary version, numeric ID leading zeros and all 396 **candidate row elements**. A row element is **not yet a verified municipality**, because header/title totals and suppressed rows may be present.
2. Map the likely ~254 column family to **actual units, building classes, solar potential definitions and overlapping subtotals**. Do not sum 254 columns unless a data dictionary establishes they are disjoint. Check whether potential capacity is kWp or electricity output kWh/year, roof area m² or count; those are not fungible.
3. Separate *residential* versus *commercial* roof opportunity with original official category codes and negative tests for overlapping sizes, aggregation totals and special taxonomies.
4. Only after independent source terms, schema and reasonable totals: determine an optional **technical PV rooftop potential prior** by municipality, compare to separately aggregated BNetzA MaStR installed units, and preserve unknown R+V policy/endorsement take-up. Building stock/roof type from Zensus 2022 and state LoD2 are separate physical universes and might share upstream geometry.


## Real original schema receipt observed in GitHub original run #41907146126

Exact original-source canary after ten source privacy/safety tests **succeeded** for the source pinned at SHA-256 `a9730f844159781c0747a4eb816f88382924239d0cc1874ea69d7a70ce912071`.

| Original worksheet | Rows: header + candidates | Field pattern |
| --- | ---: | --- |
| `Bestand Leistung` | 397 | `AGS` / `Gemeinde` + **1990–2025** × 7 categories; header unit **kW** |
| `Bestand Ertrag` | 397 | Same 36 year tags × 7 categories; header unit **kWh** |
| `Potenzial Leistung` | 397 | 7 category columns; unit **kW** |
| `Potenzial Ertrag` | 397 | 7 category columns; unit **kWh** |

The seven categories are **Wohngebäude, Gewerbe und Industrie, Öffentliche Gebäude, Landwirtschaft, Sonstige Gebäude, Nicht zuordbar and Insgesamt**. Each of the four data worksheets shows **396 eight-digit AGS-shaped candidate codes** in the first columns, numeric cells in all category positions, and no observed spreadsheet suppression characters in the sampled complete source. This real original inspection is stronger than the previous sheet-count-only report, but **key uniqueness, cross-sheet alignment and whether 2025 `Bestand` means an *installed fleet*, cumulative portfolio or installation-vintage bin remain unproven pending the numeric runner.**

The new `research_runners/rva_nrw_original_pv_class_aggregates_v0.py` **fails closed** if the four exact header taxonomies, original SHA/size/worksheet structures, all 396 unique AGS keys, cross-sheet key set, 396×7 or 396×36×7 numeric cell completeness, nonnegative finite amounts or bounded range change. It will emit **only NRW-wide class aggregates** for the two *technical potential* sheets and for the **single 2025-labeled column** in the two stock sheets. It will also quantify the **unadjusted original six-class-versus-total residual** in rows/year groups instead of silently forcing accounting equality. An internally seen eight-digit code is **not printed** to logs or copied into a consumer portfolio. 13 synthetic tests check amount/unit/AGS failure cases; no original personal source data are committed. In particular:

- **Do not sum 1990–2025 `Bestand` to create installed 2025 capacity** before the original source methodology states whether annual columns overlap, are vintages, or are cumulative.
- **Do not compute `PV potential minus Bestand 2025` as available roof capacity** until the source definitions and data vintages are reconciled.
- `Insgesamt` is a publisher total, so summing it again with the six named classes **double counts**.
- The aggregates may be used to challenge **physical rooftop exposure mix** (residential vs industrial vs agricultural). They do **not** represent actual R+V insured PV systems, installation values, rate-on-line, sums insured or claim risk.

## Real source-derived statewide numeric receipt (same SHA)

A new exact-source [read-only original workflow](https://github.com/pokekarten/OpenCatastrophe-data/pull/1331) successfully examined all **396 uniquely assigned eight-digit AGS** on each of the four publisher original sheets, verified the same set across all sheets, all **36×7** year-tagged class headers and both **7-class** technical potential headers, and generated *only state-wide class totals*. Source values are unchanged; output below is rounded to **0.001 of the explicitly printed source unit** (kW or kWh). The immutable machine-readable candidate receipt is [NRW original statewide source aggregates](../../research/observations/nrw_pv_official_municipality_class_state_20260312_v0.toml). The runner checks that the committed research receipt matches the original each run; the original raw workbook is not stored.

| Publisher building category | **Technical potential capacity, kW** | **Technical potential yield, kWh/year** |
| --- | ---: | ---: |
| Wohngebäude | 41,654,518.126 | 32,997,670,528.744 |
| Gewerbe und Industrie | 25,300,151.824 | 21,084,493,097.682 |
| Öffentliche Gebäude | 4,488,901.655 | 3,624,658,941.606 |
| Landwirtschaft | 9,058,205.432 | 7,082,135,214.501 |
| Sonstige Gebäude | 2,805,121.991 | 2,253,329,842.415 |
| Nicht zuordbar | 1,002,103.170 | 821,456,974.884 |
| **Publisher Insgesamt (separate total column)** | **84,309,002.198** | **67,863,744,599.832** |

This represents approximately **84.309 GW of modeled potential rooftop PV capacity** and **67.864 TWh/y of potential electricity yield** in NRW's exact 2026 publisher product. The six disjoint category values agree with the separately published total to the displayed milliunit rounding. Do NOT sum `Insgesamt` with component categories.

| Distinct original source field | Sum of 396 municipal **2025-tagged column**, not yet cumulatively interpreted |
| --- | ---: |
| `Bestand Leistung [kW] 2025 Insgesamt` | **12,848,498.954 kW** |
| `Bestand Ertrag [kWh] 2025 Insgesamt` | **11,409,467,071.152 kWh** |

**Vital scientific caveat:** these are *single 2025-labelled source spreadsheet fields*, not verified installations/cumulative installed fleet as of year end. The workbook lists `1990–2025` for each year but a publisher methodology proving whether such columns are cumulative, year-of-commissioning bins or another meaning has **not** been recovered. Therefore **no potential-minus-bestand availability estimate**, installed PV loss payout, insured PV penetration ratio, 2025 new capacity claim or historical CAT hazard model is authorized.

**Floating-point source precision:** The actual XLSX numeric strings carry tiny binary-to-decimal serialisation residuals. Source original category sums versus published `Insgesamt` have maximum absolute differences **4.732×10⁻⁹ kW** in potential capacity and **0.0000036019 kWh** in potential yield. These are vastly below actual model/source precision. The original runner now **fails** if any group exceeds **0.00001 kW** or **0.0001 kWh** respectively, rather than falsely counting all nonzero lexical noise as real data mismatches. Neither the published source totals nor category values were forced into equality. It is correct to keep the original exact bytes as provenance and the rounded state aggregate as a reproducible **physical opportunity** input candidate only.

R+V **2025 solo insurer contracts (1,060,546)** and HGB property premium are national controls; nothing in the original NRW solar spreadsheet allocates those contracts or their insured sums to these municipalities or building classes. This source may eventually inform a *conditional* rooftop PV technical-capacity stress by residential/industrial/agricultural occupation, **not** a company-specific R+V PV book and not installed physical coverage from MaStR.

## Explicit evidence classifications

| Object | State after this PR |
| --- | --- |
| NRW municipality PV potential source bytes, five workbook sheets | Original-byte verified, **unchanged SHA enforced** |
| Sheet header names, raw cell-type and key-format aggregate diagnostics | Observation candidate; assess original emitted receipt before model |
| Municipality identities and codebook mapping | **Not validated/admitted** |
| Statistical PV quantities, disjoint column relationships, original units | **Not validated/admitted** |
| Installed PV units, R+V risk location / asset identity / TIV | **Absent** |
| German hail/wind CAT vulnerability and AEP/OEP net | **Absent** |

The user-facing model can use this only after an additional, independent science/schema review; neither upstream original version identity nor successful offline synthetic tests imply calibrated R+V peril claims.
