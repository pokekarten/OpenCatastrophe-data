<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Exact synthetic Census 2026 parish → private OpenCat region shape (2026-11-03)

## What was independently checked

The public `OpenCatastrophe-data` PR #1100 research runner at
`research_runners/us_census_2026_parish_point_crosswalk_v0.py` emits
**synthetic, polygon-derived** `sample_region_assignments` records with
keys `asset_id`, `country_code`, `subdivisions`. The source receipt
pins a fixed official Census 2026 national COUNTY ZIP observed SHA-256
`b527c9ba7aeb8f17ef118f026eae5e5a938aa1d00b873bc32342d0dce59321c0`,
64 Louisiana parish polygons, and a deterministic digest of its 64
*synthetic* polygon-representative-point assignment labels
`1f54b0a387831fc7a20ba801632284142be685f03b0823ab6d72df60d8e4b57f`.

The distinct **private** OpenCatastrophe draft PR #16 module at
`research/subnational_region_peril_rollup_v0.py`, examined at exact
GitHub blob `3318f7dce95d1ec4d9118128a123dd8d4d6bf192`, requires typed
`RegionAssignment(asset_id: str, country_code: str, subdivisions: tuple[str, ...])`
with literal `country_code='US'` and hierarchical `('US-LA', 'US-LA-<five-digit-GEOID>')`
for Louisiana. It also requires an *actual matching loss-bearing asset roster*
and exact synthetic ground-up producer bytes. A public JSON list does **not**
automatically instantiate that private dataclass, verify its importable HEAD,
or run a regional loss reconciliation.

## Implemented offline, source-side safety gate

`research_runners/us_census_2026_opencat_region_contract_v0.py` verifies one
strictly bounded, operator-supplied `OC_CENSUS_2026_LA_SYNTHETIC_POINT_CROSSWALK_V0`
receipt. It requires:

- Exact publisher ZIP hash, namespace, 2026 date and the fixed 64-polygon /
  synthetic-point counts and recorded synthetic 64-roster digest;
- Exactly the three pre-existing, wholly invented sample labels
  `synthetic_sample_22051`, `synthetic_sample_22071`,
  `synthetic_sample_22087`, using the same original country/admin nesting
  as the current private code;
- Strict input fields, JSON parsing, duplicate-key rejection, byte budget
  and **negative** model, rights, actual-asset and original-geometry assertions.

Output is a **three-row structural research fixture only**. It explicitly
states that this tool has *not* independently authenticated the caller's
original source response, validated private HEAD identity, emitted the
complete 64 assignments, matched actual synthetic model asset IDs,
executed OpenCat's native loss rollup, established a real property location,
or approved any scientific/licence/insurer result. It does not require
private repository code, network access, Neon, geometry libraries or external
raw-source files in Git.

All seven synthetic tests in
`tests/test_us_census_2026_opencat_region_contract_v0.py` cover exact
samples and adversarial input. A prior source SHA-256 observed in a
GitHub workflow is **not** proof of immutability, exact issuer-signed
original bytes, or current legal access permission.

Example after creating a **synthetic receipt** outside the repository:

```bash
python research_runners/us_census_2026_opencat_region_contract_v0.py \
  --synthetic-crosswalk-receipt /path/outside/git/synthetic-crosswalk.json
python -m unittest tests.test_us_census_2026_opencat_region_contract_v0 -v
python scripts/check_all.py
```

## Required next phase

To claim actual native OpenCat regional integration, supply independently
authenticated, original source geometry and *explicitly synthetic* loss-bearing
asset IDs that match one producer source ledger, with fixed private source
commit IDs. Then execute private #16 native tests and the true loss conservation
checks. Never infer insured TIV, policy coverage or real geocoded buildings
from this synthetic source-derived representative-point receipt. Source/licence
approval, legal reuse, historical boundary vintages and calibrated hazard
are separate gates before any real CAT modelling.
