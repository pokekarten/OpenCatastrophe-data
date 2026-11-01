<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source-access checkpoint: live anonymous canaries and repository-wide queue (2026-11-01)

**Status:** evidence-only research checkpoint. All provider bytes were read transiently by scoped
GitHub Actions and are not committed, uploaded, or admitted as CAT-model input. Repository
source-access contracts remain the canonical access records; this document does **not**
upgrade static contract status or licence/admission state.

## Deterministic full-registry snapshot

The existing `python scripts/build_source_access_inventory.py --summary` was executed on the
PR branch via [GitHub Actions 41315508490](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41315508490)
at commit `e5cb112789b2b5bc6f11ea07ee8e86170d7f8bc3`.

| Field | Observed count |
| --- | ---: |
| Registry records | 278 |
| Non-admitted landscape candidates | 263 |
| Admitted source manifests (predominantly metadata-only) | 15 |
| Reviewed source-access contracts | 42 |
| No concrete access contract | 236 |
| Contract documentation only | 31 |
| Bounded probe defined (static contract classification) | 6 |
| Credentials required | 3 |
| Terms-restricted | 2 |

These classifications are **contract states**, not success/failure counts from real
HTTP requests. A source may have separate original-asset workflow evidence without its
access contract status changing. The inventory never authorizes automatic bulk downloading.

## Actual live read-only provider calls

Each provider request below was strictly fixed and bounded before execution.
Response hashes are SHA-256 of the **transient full HTTP response body**, not original
downstream datasets; the provider can change a live response without breaking its API.

| Source / exact bounded scientific role | Original execution | Response bytes | Response SHA-256 | Outcome |
| --- | --- | ---: | --- | --- |
| GFZ Kp definitive 2024-01-01 day JSON (structural only) | [run 41315407113](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41315407113) | 361 | `f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a` | JSON object validated, no scientific Kp values certified |
| NOAA SWPC fixed rolling 1-minute magnetic JSON (structural only) | [run 41315407113](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41315407113) | 1,197,998 | `bcceadedf65be2c7e6cad0e9aa51bd2aa649bc1043295620b5d99f7368227889` | JSON collection validated, sensor lineage not certified |
| geoBoundaries gbOpen DEU ADM1 fixed metadata | [run 41315407113](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41315407113) | 1,812 | `65af06f80e837028997c396d2c67d74fb1e1752d884e9a0638d5c736ee8c345a` | Fixed boundary ID `DEU-ADM1-10402087` and licence fields valid; downstream geometry not acquired in this probe |
| DWD CDC historical 10-minute extreme-wind *directory only* | [run 41315579812](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41315579812) | 185,479 | `ca31acda79d834cc5089a825e99bace611c14e73285d34c0a54effceeb4d3bfd` | 1,080 valid archive filename identities, 312 unique station IDs, 2 reversed-date links quarantined |
| PEGELONLINE Dresden station `Q` metadata only | [run 41315834470](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41315834470) | 722 | `afaeea603a827482888f6fd4e68b4152ac34ea3dc9598e05b14f513515ae2a0e` | Fixed Dresden UUID, Q unit/semantics, 15-min sampling verified; zero measurement values requested |

DWD index filename coverage runs from 1990-01-01 through 2025-12-31; **none of its 1,080 listed ZIP archives was downloaded in this checkpoint**.
PEGELONLINE metadata confirm 900 seconds between samples. The next separate
target-value experiment must preserve the predeclared 2020–2023 temporal holdout,
long-term raw Q JSON local-time offsets, availability/completeness and the exact
GloFAS comparison semantics; this metadata test did not collect that Q series.

The live canary runner from this PR uses only allowlisted providers and requests,
enforces static reviewed terms, content-type and byte/time caps, rejects redirects,
validates typed source identities, and emits receipt hashes with
`provider_bytes_persisted=false` and `model_input_approved=false`.

**Do not count these five successes as five fully admitted CAT sources.**
They establish a bounded, reproducible access capability for each exact request.

## Other already executed original-source workflows (separate from this checkpoint)

- [Luxembourg ACT2023v2 vs EUBUCCO original polygon overlap 41308584880](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41308584880): 149 ACT roof polygons and 45 EUBUCCO polygons in a 250m square; only nine illustrative unique high-IoU candidates; no building identity accepted.
- [EUBUCCO LU00 original source-label audit 41308236889](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41308236889): 186,171 input records, original Parquet digest verified; no insurer TIV.
- [ACT LiDAR2024 MNT/MNS bounded COG sample 41314112544](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41314112544): 277,202 coincident valid raster pixels; **not** roof-masked building heights.
- [geoBoundaries original DEU ADM1 SQLite staging 41314234471](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41314234471): 16 valid source polygons, SHA-verified original 6,254,151-byte file, ephemeral CAT-only spatial index and point joins.

Those original-source bytes were not persisted to Git or to an approved live model-input database.

## Next bounded work queue

1. **Complete existing access contracts**: group the 236 no-contract entries by
   source family, de-duplicate source identities across landscape/manifest records,
   and prioritise official access endpoints for flood, wind, earthquakes, buildings,
   topography, observed loss and insured market aggregates. Start from
   `python scripts/build_source_access_inventory.py`; do not create a second
   independently edited source inventory.
2. **Move source-by-source through the ladder** T0 authoritative documentation,
   T1 bounded anonymous metadata probe, T2 approved credentialed probe when
   required, T3 exact bounded original-sample byte receipt and independent
   schema/CRS/unit/temporal validation, T4 optional operational monitoring.
   Save results as evidence with exact Git code and access-contract identity.
3. **Real CAT data staging only after rights/science gates**: preserve file SHA,
   native fields, coverage, quality/missingness, geometries, observation vintage,
   uncertainty and upstream lineage; do not infer insured assets from geospatial
   overlap. Use isolated CAT object storage / staging, not shared Pokémon tables.
4. **No unauthorized automation**: hold `restricted_by_terms`, registration,
   commercial-use, or unknown-reuse sources until the exact intended access
   and intended use are approved. In particular, do not scrape ESWD, EM-DAT,
   PERILS or other agreement-limited sources as a workaround.

A green GitHub check alone is not a provider-data availability claim.
For the PR source jobs, inspect **each job's actual receipt**: the provider steps
have `continue-on-error: true` to distinguish transient upstream failures from
the deterministic offline code gate.
