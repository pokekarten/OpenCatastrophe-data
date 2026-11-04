<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic geocoder candidate benchmark (offline v0)

**Scope:** evaluation plumbing for the GIS toolchain, NOT a real provider test,
building identity decision, asset inventory or CAT source admission.
No external API, credentials, real addresses, private exposure or spatial data
bytes are necessary. This builds on the licensed-source research merged from
[PR #1240](https://github.com/pokekarten/OpenCatastrophe-data/pull/1240)
and complements proposed sources from
[PR #1239](https://github.com/pokekarten/OpenCatastrophe-data/pull/1239).
It does not modify the geometry matcher in
[PR #1107](https://github.com/pokekarten/OpenCatastrophe-data/pull/1107).

## Purpose

Measure how well a geocoder ranks a small set of known **synthetic** coordinate
candidates under a fixed EPSG:4326/50m threshold. This is a scientific
evaluation harness and cannot validate real providers until a separate
approved data licence, truth-set provenance, import pipeline, and independent
holdout test exist. Distance to a reference point is **not** proof of a
correct building or insured loss location.

## Input

Create a *local* \`/tmp/synthetic-geocoding.json\` with the structure below:

\`\`\`json
{
  "schema_version": "oc-geocoder-benchmark-synthetic-v0",
  "synthetic_only": true,
  "crs": "EPSG:4326",
  "distance_threshold_m": 50,
  "truth": [
    {"case_id":"synthetic:A","latitude":49.0,"longitude":6.0}
  ],
  "runs": [
    {
      "engine":"pelias",
      "engine_version":"test1",
      "index_snapshot_id":"synthetic_snapshot1",
      "candidates":[
        {"case_id":"synthetic:A","rank":1,"latitude":49.0,"longitude":6.0}
      ]
    }
  ]
}
\`\`\`

Run:

\`\`\`bash
python scripts/geocoder_synthetic_benchmark_v0.py --input /tmp/synthetic-geocoding.json
python -m unittest tests.test_geocoder_synthetic_benchmark_v0 -v
\`\`\`

Strict fields reject address text, source content, opaque provider IDs, unknown
cases, invalid coordinates, duplicate ranks, gaps in rank 1..3, non-finite JSON,
non-synthetic case identifiers and non-4326 coordinates. Bounded to 128 KiB,
200 truth cases, five engines and three candidates per case. Output contains
aggregate coverage, recall@1 and recall@3 (all truth cases as denominator),
median/p95 first-ranked spherical-point error, and whether each engine declares
the same index source snapshot. It never outputs truth case identifiers or
individual coordinates. No existing geocoding endpoint is called.

## Limits and next falsifiable test

A shared \`index_snapshot_id\` is merely a user declaration, **not independent
evidence** that imported indexes share identical OSM/OpenAddresses/GeoNames
vintages. Before real Luxembourg testing, separately prove exact original
snapshot hashes and release, geocoder/index version, license, source lineage,
municipal/address-point ground-truth geometry and a stratified independent
holdout. Evaluate ambiguous and no-candidate cases. Compute exact
building-to-point and polygon correspondence with the existing separately
governed building matching workflow, keeping multi-address buildings, units,
parcels and split/merge candidates distinct.

Neither passing this fixture nor a low distance error authorizes an external
source for insurer use or production model input.
