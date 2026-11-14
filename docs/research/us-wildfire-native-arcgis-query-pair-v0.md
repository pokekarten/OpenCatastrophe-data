<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FPA FOD x MTBS native ArcGIS query-pair audit (2026-11-03)

**Research-only, fail-closed.** This script audits *caller-supplied response snapshots* of two small ArcGIS REST `/query` calls without inventing polygon primary keys or inferring CAT model loss. It does not fetch any URL, import any original dataset or update Neon. Zero real-event or confidential bytes are checked into the public repository.

## Original provider inputs

- USDA FS FPA FOD 7th edition, [feature MapServer layer 0](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0), or its official **2024 year-view layer**: use only `FOD_ID`, `MTBS_ID`, `FIRE_YEAR`, `returnGeometry=false`, `f=pjson`, and an explicit bounded row count. The current-edition service is mutable and does not attest the archive version by itself.
- MTBS 2024 [burned-area polygon layer 82](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/82): use only `FIRE_ID`, `YEAR`, `FIRE_TYPE`, `PERIM_ID`, `MAP_ID`, `returnGeometry=false` and `f=pjson`. Query exact selected FPA `MTBS_ID` values. `FIRE_ID` is the **event** key; a repeated `FIRE_ID` represents ambiguous source-row multiplicity, not multiple independent events. `PERIM_ID` is a satellite image scene reference and is frequently null; `MAP_ID` relates to mapping activity. Neither is promoted to a physical event, polygon component or insurance-policy key.

The query snapshots must contain only a `fields` array with exactly those selected native ArcGIS field names/types, an `attributes`-only `features` array (1-250 rows), and optionally `exceededTransferLimit`. Reject geometry or other unrequested columns, to prevent the diagnostics from ever logging original coordinates or free-form source attributes. The input byte bound is 250 KB per snapshot.

The two snapshots are **explicitly caller-selected** and must each have a lowercase SHA-256 of those exact downloaded response bytes. The runner **cannot independently authenticate the query URL or original publisher** and does not compare against the native archive GPKG/SQLite hashes. It does not make any request on its own.

## Original publisher count-only observations (2026-11-03)

Four bounded, aggregate-only provider REST `/query?returnCountOnly=true` responses were tested on the current live services (no raw rows or geometry retrieved). The [FPA FOD 2024 year-view layer](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/2024) reported **87,708** fire occurrence rows (`where=1=1`); the same layer with `mtbs_id IS NOT NULL` reported **415** rows, equivalent to roughly **0.47% of FPA 2024 occurrence records carrying this cross-catalogue ID**. This is a *key-population ratio* for a live service snapshot, **not** a random matching success rate, an annual insured fire frequency, complete event incidence or proof that 99.53% of records are unsuitable.

The [MTBS 2024 burned-area boundary layer 82](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_MTBS_01/MapServer/82) reported **1,051** boundary features (`where=1=1`), and `fire_type = 'Wildfire'` reported **411**. Grouped native provider statistics `groupByFieldsForStatistics=fire_type` with count of `objectid` reconciled to **411 `Wildfire`**, **638 `Prescribed Fire`** and **2 `Other`** (=1,051). The `Other` label is *not* recognized by our reviewed event-kind mapping and must be quarantined as `unknown`; it must never be silently treated as `wildfire`. Controlled burns are a distinct source type and must never be counted as natural-catastrophe wildfires by default.

Both REST services are mutable; these observations have **no pinned HTTP original-response checksum, license release approval or provider archive frozen-byte identity**. Treat as transient 2026-11-03 research observations, not admitted CAT data or historical actuarial truth. The query-pair runner intentionally never estimates the national joining rate from selected small `mtbs_id IS NOT NULL` samples. Before frequency calibration, inspect original publisher catalog scope, small-fire coverage, missing source IDs, prescribed-fire treatment and sampling/selection mechanisms.

## Command

```sh
python -m research_runners.us_wildfire_native_arcgis_query_pair_v0 \
  --fpa-response /private/fpa-2024-small-response.json \
  --fpa-sha256 COPY_EXACT_SOURCE_RESPONSE_SHA256 \
  --mtbs-response /private/mtbs-2024-small-response.json \
  --mtbs-sha256 COPY_EXACT_SOURCE_RESPONSE_SHA256 \
  --fpa-release FPA_FOD_20260615 \
  --mtbs-vintage MTBS-EXACT-REVIEWED-VINTAGE \
  --selection mtbs_id_present_2024
```

Selection must be stated **explicitly** as `mtbs_id_present_2024` or `unfiltered_2024`. This value is caller-declared only, not cryptographically proved by the query response. If source query says `exceededTransferLimit=true`, the report preserves it; otherwise missing/false still does not prove a complete annual event population. All reports contain only aggregate counts, a SHA-256 of each response, and conservative non-admission flags, never individual source identifiers.

**Exit 0** means all selected checks returned bounded research results, not rights or model approval. **Exit 1** means detected ambiguity/unknown fire type requiring review. **Exit 2** means missing or invalid data/format/byte receipts.

## Observational motivation and failure controls

The preceding live source probes [documented here](us-wildfire-2024-original-service-bounded-query-20261103.md) selected 25 FPA FOD records with already nonnull MTBS IDs and found 25 corresponding 2024 perimeters. A separately selected first 50 **unfiltered 2024 FOD_ID-ordered records** all lacked an MTBS link. Neither is statistically representative. The purpose of this auditor is to preserve these differences **without mistaking a selected 25/25 match for nationwide event coverage**.

Live observed MTBS `FIRE_TYPE` labels include `Wildfire` and `Prescribed Fire`; reuse the reviewed conservative dictionary from the original layer metadata preflight. Unknown labels stay unknown, not wildfire by default. Both source-reported feature counts and MTBS FIRE_ID multiplicity are retained; never naïvely multiply ground-up losses by joined polygon rows.

This audit has **no spatial geometry**; no source area, burn severity, event frequency, claim cost, insurance portfolio, original asset provenance, reuse rights, physical event equality or treaty occurrence is established. Scientific and licence admission must be reviewed independently before a CAT model consumes derived data.

To validate the synthetic-only controls: `python -m unittest tests.test_us_wildfire_native_arcgis_query_pair_v0 -v`, then `python scripts/check_all.py` in the official Git checkout.
