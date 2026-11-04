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
