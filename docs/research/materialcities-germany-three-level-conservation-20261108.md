<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# MaterialCities Germany: original-byte ADM0/ADM1/ADM2 conservation (2026-11-08)

## Scope and exact source

Research-only, from the **unchanged original 2026.9** MaterialCities publisher ZIP,
https://zenodo.org/records/22306604, with MD5
098f04f9b204d3102165ba4b3e2b8520 and SHA-256
ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38.
Three source members were inspected independently:
MaterialCities_adm_gfa_ADM0.csv, MaterialCities_adm_gfa_ADM1.csv,
MaterialCities_adm_gfa_ADM2.csv.

The original source bytes were read transiently in an isolated Python execution
environment on 2026-11-08; no original files, source rows or regional
floor-area figures are committed to the repository or the insurance database.

## Exact-source execution

The executable, source-pinned research gate in
research_runners/materialcities_deu_3level_conservation_v0.py completed
successfully against the original ZIP, using the already integrated original
MaterialCities ADM2 digest/schema gate.

| Source geography | German rows |
| --- | ---: |
| ADM0 | 1 |
| ADM1 | 16 |
| ADM2 | 402 |

All **15** construction-function/structure gross-floor-area components
reconcile within source-native floating-point precision across the national
ADM0 aggregate, the 16 ADM1 states, and all ADM2 regions grouped by their
declared parent GADM ADM1 identifier.

- Largest ADM1-to-child component difference: 0.0000000298 m2.
- Largest ADM0-to-all-ADM1 component difference: 0.0000001193 m2.
- Largest ADM0-to-all-ADM2 component difference: 0.0000001193 m2.
- The source itself contains no separate independent GFA-total column.
- Exact source rows have 16 unique state keys and 402 unique German ADM2 keys.

These are *internal model arithmetic checks*, not comparison with actual
building observations. A small conservation residual does not certify
original model accuracy, completeness, vulnerability, location accuracy,
valuation or any third-party insurance portfolio.

### Critical mismatch with independent Destatis 2022 Kreis dataset

The canonical original Destatis observation in
research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml
contains **400** 2022 Kreis rows across 16 Länder, keyed by five-digit AGS.
Its source and units differ from the GADM-based MaterialCities hierarchy.

A count-only state-level review, comparing the above source totals and the
exact existing Destatis 2022 AGS inventory, exposes two count differences:

| German state | Destatis 2022 Kreis rows | MaterialCities 2026.9 ADM2 rows |
| --- | ---: | ---: |
| Niedersachsen | 45 | 46 |
| Thüringen | 22 | 23 |
| All other 14 states combined | 333 | 333 |
| Germany total | 400 | 402 |

Equal state counts **do not** establish identical boundaries, geometry
vintages, cities, district names or one-to-one relationships. The different
definitions and source vintages require an independently reviewed GADM 4.1
to original 2022 AGS crosswalk before any spatial reconciliation. **Do not
pair the first 400 rows, replace missing rows with centroids, directly join
by counts or treat any source GADM ID as a Destatis AGS.**

## Reproduction

Obtain the original exact-source ZIP legally outside Git. Then execute:

    python -m research_runners.materialcities_deu_3level_conservation_v0 \
      --archive /external/MaterialCities_adm_gfa_csv.zip \
      --out /tmp/materialcities-deu-3level-research.json

Offline tests using independent wholly synthetic 1/2/3-level data:

    python -m unittest discover -s tests \
      -p test_materialcities_deu_3level_conservation_v0.py -v

Execution: **13/13 synthetic tests PASS** in isolated Python 3.11,
against exact GitHub branch files. The original publisher ZIP was also
successfully replayed on the same branch. The full repository check and
exact-head public CI are a separate merge gate.

## Scientific and rights boundary

The MaterialCities publication describes a CC BY 4.0 dataset, while
GADM 4.1 licensing and reuse terms require separate consideration:
https://gadm.org/license.html. Neither the source's public accessibility
nor the successful arithmetic gate is permission to redistribute its
geographical data or use upstream GADM products in a commercial insurer
application. All rights are **not admitted / not reviewed** in the public
source registry.

No geocoded insured assets, R+V locations, real 2025 carrier allocations,
TIV, vulnerability calibrations, Oasis inputs/ORD, CAT model outputs or
Neon database writes have been created by this study. Country/state
summaries remain research diagnostics, **not a portfolio allocation
algorithm**. Independent valuation, GADM-to-AGS geography, calibrated
hazard/vulnerability and insurer source rights remain downstream gates.
