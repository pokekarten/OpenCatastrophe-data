<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Germany: 14 provisional ADM1/NUTS2021 polygon candidates, Berlin/Bremen withheld

Date: 2026-11-01. Scientific/rights research only; not approved building/insurance geocoding or an official 2021 NUTS administrative concordance.

## Verified reason the existing all-16 source crosswalk is blocked

The existing exact original-source [workflow run 41317364634](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41317364634) downloaded geoBoundaries 2021 Germany ADM1 (16 polygons, original 6,254,151 bytes / SHA-256 `56e069593595c5006e7044d46b023c2afc6b4a109a669b570ee229e758c00682`) and Eurostat Nuts2json NUTS2021 at **20M simplified scale** (123 NUTS1 features, 16 German; original 194,955 bytes / SHA-256 `1cacacf29694f518f6446ec286b5f251f3fea109d84874eb317c50b7300419b1`).

The original reproducible, two-way projected-polygon crosswalk rejected only two source polygons under the unchanged minimum **75% of both source and reference** and runner-up overlap **below 10% of primary**:

| Official best NUTS2021 code | Source fraction covered | Eurostat reference fraction covered | Other-region overlap as fraction of primary | Admission |
| --- | ---: | ---: | ---: | --- |
| `DE3` (Berlin) | 0.898923 | 0.908861 | **0.112443** | **WITHHELD** |
| `DE5` (Bremen) | 0.825459 | 0.901874 | **0.176251** | **WITHHELD** |

Both meet the bidirectional 75% area criterion, but both fail the deliberately stringent second-candidate overlap criterion. The original diagnostic alone cannot distinguish cartographic boundary generalisation, simplification, geographic mismatch or political topological changes as the root cause. **Do not weaken the 10% cutoff or infer full legal regional equivalence.** The existing strict 16-region CAT2 crosswalk remains blocked, unchanged.

## New limited CAT3 research-only source join

`research_runners/geoboundaries_deu_nuts2021_partial_cat3_v0.py` **reuses** the existing immutable source fingerprint validators, the official 16 NUTS codes and precisely the same WGS84→EPSG3035 equal-area transformation. It determines each primary NUTS polygon by highest actual projected intersection. It accepts **only 14** uniquely covered provisional region pairings while explicitly withholding **exactly `DE3` and `DE5`**. If any additional region or different candidate fails, if the 14/2 cohort changes, if source digests change, or if best-code assignment ceases to be bijective, the entire operation fails.

A new standalone local SQLite `CAT3` file holds the fourteen *provisional, spatially supported* mappings plus the two explicitly withheld source IDs as different tables with CHECK constraints. It is new-only, cannot overwrite an existing database and must live outside Git, separate from prior CAT1 and CAT2 and from all persistent Neon/Pokémon databases. The read-only point lookup uses CAT1 original exact polygon containment, then CAT3 and reports only provisional `DE2`/other official NUTS codes or a **blocked** status (never an invented NUTS code) for Berlin and Bremen. Every result has `insurance_model_input_admitted=false`. No site-level building, hazard, exposure, insured value, property or premium data are integrated.

Only the derived 14/2 code-level summary and two blocked overlap ratios can be logged. The exact provider geometries, IDs, local SQLite source-identifier rows and point records are ephemeral inside a GitHub runner and deleted after use. The fixed test cities are public geography examples, not insurer or user locations.

## Reproducibility and future gates

Dedicated `.github/workflows/geoboundaries-deu-nuts2021-partial-cat3.yml` fetches the two previously SHA-verified original sources, runs synthetic strictness checks, builds temporary CAT1 and CAT3, then requires Munich/Stuttgart provisional and Berlin/Bremen blocked results. No original data/artifacts are retained.

Before exact-head tests and original-source run **succeed**, the 14-state database is only an implementation proposal, not a proven finished staging artifact. Even a successful 14-region CAT3 research join cannot establish an authorised **production NUTS mapping**. Such use needs proper Eurostat geography licensing/attribution, comparisons with sufficiently detailed original NUTS polygons (not only simplified 20M generalisation), independent survey control at difficult borders, EUBUCCO NUTS2016 mapping validation, and manual regional legal provenance.

A future independent source-quality fix may address the two withheld regions, but **must not use approximate names or silently assign NUTS2021 codes**. Do not treat two admitted sample city points as independently surveyed parcel boundaries.
