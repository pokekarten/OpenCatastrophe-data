<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Marche 2022 — source-native flood-depth vs water-surface elevation dictionary gate

**Executed 2026-11-08. Research-only, non-admitted; no individual observation, coordinate, address, survey identifier or third-party ZIP/workbook committed.**

## Unambiguous scientific finding

The source describes **two different hazard quantities** in original Form A:

| Quantity | Industrial Form A | Residential Form A | Original data dictionary | Role |
| --- | --- | --- | --- | --- |
| **Water depth outside building**, field **\`hw\`** | **\`AY\`** | **\`AG\`** | Industrial dictionary \`A\` row 50, residential \`A\` row 30: float, **metres**, dot separator. Publisher marks **7** industrial and **2** residential observations \`No Data\`. | Observed/reconstructed external inundation depth at surveyed locations; potentially useful **hazard input** when lawful handling and uncertainty gates pass |
| **Water surface elevation** | \`AZ\` | \`AH\` | Industrial dictionary \`A\` row 51, residential \`A\` row 31: \`terrain elevation + hw + ΔQ\`, based on an Italian 1-metre DTM. Publisher reports **57** and **21** \`No Data\`. | Derived **height/elevation**, **not** depth. Requires explicit vertical datum to compare with a hydraulic model |
| **Building/terrain level adjustment \`ΔQ\`** | \`AM\` | \`U\` | Industrial \`A\` row 40, residential \`A\` row 20: **metres**. | Component of the derived water-surface elevation; not a direct loss measure |
| **Maximum water depth inside, by affected floor** | Industrial \`Form_B.xlsx\` / \`B_Floors\` sheet | Residential \`Form_B.xlsx\` / \`B_Floors\` sheet | Industrial dictionary \`B_Floors\` row 8, residential \`B_floor\` row 9; **metres**, floor-level rows | Different hazard quantity with **one-to-many Form A ↔ floors** mapping; cannot be casually joined as 1:1 or treated as an independent event |

The original author describes the 247-depth sample in their peer-reviewed paper: https://doi.org/10.5194/essd-17-6487-2025 . **The original CSV-style numeric typing and units have now been independently checked against the immutable survey ZIPs and embedded Excel dictionaries.**

## Full original-byte reproducibility

**Immutable dataset release:** https://doi.org/10.5281/zenodo.17457884 (v1.0.1); conceptual DOI https://doi.org/10.5281/zenodo.15591850 is **not** the frozen source identity.

Original publisher assets (checked against SHA-256/MD5 from [previous original-source QA receipt](marche-2022-original-zip-privacy-gate-20261108.md)):

| Asset | Frozen SHA-256 |
| --- | --- |
| \`Industrial activities dataset.zip\` | \`a4e5a142450e3a9c63e0dcb964b674a55ca180a7c44ec852ecd8e48638d29847\` |
| \`Residential building dataset.zip\` | \`4785f5eae8940e5c8033758aac11d1b2d8b7e5f75fe19efab497dfd5453802cd\` |

The code [\`research_runners/marche_2022_water_surface_elevation_probe_v0.py\`](../../research_runners/marche_2022_water_surface_elevation_probe_v0.py) first executes the existing frozen original ZIP integrity/structure gate, then verifies the publisher's *original dictionary definition and units* for \`hw\` and the explicitly **derived** \`Water surface elevation\`, and returns **only sector-level type counts**.

| Original Form A property population | Numeric \`hw\` observations, metres | Non-numeric/no-data \`hw\` | Numeric derived water-surface elevation | Non-numeric/no-data derived elevation |
| --- | ---: | ---: | ---: | ---: |
| Industrial/commercial | 133 | **126** | **7** | 76 | 57 |
| Residential | 123 | **121** | **2** | 102 | 21 |
| **Total** | **256** | **247** | **9** | **178** | **78** |

**Important:** The column headings in this table should be read per declared order; \`hw\` observations are *outside-building* depths. Source data dictionaries define \`No Data\`, and the underlying source cells contain a non-numeric sentinel rather than necessarily a physically blank Excel cell. Neither non-numeric nor blank means a measured zero. Conversely an explicit numeric zero depth is a valid measurement, not a missing observation. The output contains **no original water heights, survey identifiers or site data**.

**Live execution:** original v1.0.1 ZIPs fetched into a temporary isolated environment; GitHub script retrieved from immutable commit \`dc32ff7fa8a49fcfda96f78e1f0cedc6a550f2f1\`; CLI exited **0**; **12/12 synthetic regression tests passed**. Tested source script SHA-256 \`10066c2dfb6c1d0ac129eb0c14007c78e5fed75cc56371f1b3e01017fd54dcd6\`. No full GitHub Actions run was claimed.

Run with local caller-owned originals outside Git:

\`\`\`bash
python -m unittest discover -s tests -p 'test_marche_2022_water_surface_elevation_probe_v0.py' -v
python -m research_runners.marche_2022_water_surface_elevation_probe_v0 \
  --industrial-zip /secure/provider/Industrial_activities_dataset.zip \
  --residential-zip /secure/provider/Residential_building_dataset.zip
\`\`\`

## Damage functions: what is admissible at this point?

The dictionaries contain many **binary/ordinal physical-damage observations** for structural parts, floors, machinery, assets, furniture and building systems. These are meaningful candidate outcomes for **conditional component damage occurrence/severity** against surveyed hazard depth. However, the original documents contain only sparse *monetary cleanup cost* fields (e.g. industrial \`D\` dictionary row 8 with **130/133 missing**, residential \`B_floor\` dictionary row 59 recording only two amounts), **not validated whole-building repair amounts plus replacement-value/TIV denominators**.

Therefore:
- **Possible later exploratory research:** geoprivacy-approved, one-event observational \`P(component damaged | surveyed building, external depth, sector, mitigation)\`, with floor-level deduplication and uncertainty. The training/holdout must be carefully separated and **not** presented as event-out-of-sample validation.
- **Not justified:** \`damage ratio = monetary loss / TIV\` for each building, insured gross/net, total replacement cost, annual Poisson frequency, stochastic event catalog, OEP/AEP or universal curves extrapolated from these *damaged-only* sampled properties.
- **Selection bias:** the 2025 paper reports surveys in **3 of 14** most affected Marche municipalities, and roughly **3%** residential / **15%** affected-business coverage, with Copernicus EMSR634 used in survey selection. Independent spatial hazard validation must account for selection; using EMSR634 both as selection/target and as purported independent truth is circular.
- **Legal/data minimization:** Zenodo v1.0.1 metadata claims CC BY 4.0 for the *dataset*, but property-level coordinates, business details and potentially personal remarks require a separate lawful-use/privacy decision. Do not copy those observations into public Git or Neon.

**Next concrete gate:** data dictionary-mapped, privacy-reviewed categorical \`damage=yes/no\` outcome contracts for industry vs residential and an event-aware grouped aggregate-only test, with explicit missing/not-applicable semantics. Separate **economic valuation/TIV** is required before a loss-severity/insured payout model can be asserted. No source admission, policy relaxation or model calibration was performed by this PR.
