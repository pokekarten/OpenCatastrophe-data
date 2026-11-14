<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source-native CACLR singleton address-position check (Apr/Nov 2026)

**2026-11-04. Research-only. Not a building/insurer/CAT source admission.**

[Original ID overlap PR #1300](https://github.com/pokekarten/OpenCatastrophe-data/pull/1300)
showed **178,254** April–November CACLR keys shared exactly and
**177,709** of those occur once on both sides. It also rejected
`AD_AddressID` ↔ `id_geoportail` equality (zero intersection).
The 545 shared, non-singleton CACLR groups remain deliberately
excluded from one-to-one distance evaluation.

## Sources

Only original SHA-pinned ACT GeoBase Addresses 2026-04-01 ZIP/GPKG and
BD-Adresses 2026-11-02 CSV are accepted, using the exact strong
hash contracts from the already merged source studies:

- ZIP: `edaf17ed2c802c155fd75caecfe44cbd23581a4b0a59f25935fa2d71a5e0b2eb`.
- Inner April GeoPackage: `b357e7aa76a61ecabee45df28d68f3cdbce4ecdebf6f396d4d83ad2ba648fc12`.
- November CSV: `f163ed856200eedd8b501da2d7787e01ee373be1a55a4d79abcf57c96982a99c`.

The official ACT GeoBase Addresses layer is EPSG:2169 `MULTIPOINT`;
the original November CSV includes EPSG:2169 easting/northing.
No CRS approximation, nearest-neighbour linking, crosswalk coercion or
WGS84 comparison is required. The parser follows the
[OGC GeoPackageBinary header/envelope/WKB standard](https://www.geopackage.org/spec130/)
with a pinned Shapely WKB decoder. Empty or multi-location geometries
are counted as *unevaluable*, never silently turned into a centroid.

## Output / acceptance

Compare only pairs whose exact CACLR `AlternativeIdentifier` /
`id_caclr_bat` occurs once on each side, then publish **only**
aggregate planar metre residual counts (≤0.01m, ≤1m, ≤10m, ≤50m,
over 50m), median, p95, p99 and max, with explicit counts of skipped
geometries. No address values, individual IDs, points, geometry bytes,
source-file artifacts, matched pairs, person records or insurer
locations are written to Git, logs or the insurance DB.

Even perfect coordinate agreement is a **self-consistency** result
within a shared ACT cadastral provenance, not independent survey-grade
geocoding, source independence, true building ownership, occupancy,
insured value or loss-model calibration. Position drift across seven
months is not evidence of new construction/demolition without a source
history. Rights and scientific admission must remain false.

**Execution status:** exact official-original job has not yet run.
An observed metric distribution may only be recorded after passing
synthetic tests, SHA-pinned original full download and GitHub CI.

## Executed original-source results (2026-11-04)

The [dedicated original SHA-pinned GitHub source run 41892290371](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41892290371)
completed successfully. All **11** wholly fictional GeoPackageBinary and
metric/failure regressions passed, then complete official April
GeoBase Addresses and November BD-Adresses originals were verified
from source bytes, matched in the same **EPSG:2169 metric CRS** by only
singleton CACLR key candidates, and analysed strictly in memory.

| Original-source metric | Observed |
| --- | ---: |
| Distinct CACLR keys occurring once on both releases | **177,709** |
| Original matched records with usable single-point geometry | **177,709** |
| Omitted empty or multi-location source geometries | **0** |
| Matched position distance **≤0.01 metre** | **174,839** |
| Matched position distance **≤1 metre** | **174,989** |
| Matched position distance **≤10 metres** | **177,398** |
| Matched position distance **≤50 metres** | **177,689** |
| Matched position distance **>50 metres** | **20** |
| Median / 95th percentile original-coordinate residual | **0.000 m / 0.000 m** |
| 99th percentile residual | **3.320 m** |
| Largest observed residual | **345.049 m** |
| Shared but non-singleton CACLR key groups excluded | **545** |

Each distance row is nested in the larger threshold row: do **not** add
cumulative threshold bins together. Exactly 20 original singleton-key
candidates have a discrepancy larger than 50 m, but their individual
addresses, identifiers and positions remain strictly unexposed. No
source rows, original geometry or original ID pair was written to Git
or stored in the model database.

**Scientific interpretation:** 174,839/177,709 approximately **98.4%**
of unique-key pairs agree within 1 cm **inside the same ACT cadastral
data lineage**. This is a reproducibility and source-relative
coordinate stability proof, **not independent positional accuracy**.
A zero rounded median and p95 reflect many identical source-position
coordinates; they are not zero physical uncertainty. The 20 residuals
over 50 metres (and 311 over 10 metres) could reflect source revision,
address relocation/renumbering, register semantics, associated parcel
centroids or other causes, **none adjudicated** by the current test.
Even the 174,839 near-identical pairs remain *address candidates*
rather than proven insured building footprints.

### Recommended non-admission and anomaly gate

Keep the **20 >50 m** cases and the **545 repeated-key groups**
outside any automated forced one-to-one building join, together with
a conservative pending-review flag for all cases not independently
adjudicated. Use a secured, authorized holdout workflow to inspect
publisher version history and independently confirmed building
geometry/entrances where available; do not print an anomaly list
or asset-level details into public CI output. An appropriately licensed
CAT exposure inventory and actual insurer portfolio allocation still
require independent evidence and a separate explicit review.
