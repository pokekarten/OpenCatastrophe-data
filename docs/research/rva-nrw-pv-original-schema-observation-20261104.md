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
