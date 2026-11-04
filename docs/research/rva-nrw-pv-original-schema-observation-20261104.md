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
