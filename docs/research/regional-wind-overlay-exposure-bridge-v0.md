<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Wind footprint → NUTS2 sampled exposure bridge v0

## Scope and actual improvement

The existing `regional_wind_footprint_overlay_v0.py` calculates the
measured, area-weighted and maximum gust (m/s) for each compatible,
nonoverlapping NUTS2 polygon from exactly **one** EPSG:3035 synthetic
exratropical storm footprint. It already quarantines overlapping region
interiors and overlapping storm cells. Separately,
`regional_exposure_hazard_join_v0.py` validates NUTS2 windstorm
exposure snapshots, the storm's physical event identity and dates, and
reports **only a sampled wind-exposure comparison**.

These components previously had no executable, reviewed handoff. The
new `regional_wind_overlay_exposure_bridge_v0.py` composes those
exact existing functions and rejects an unsafe implicit assumption:
**a region with missing storm footprint cells is unknown weather,
not zero wind**.

Only regions with **reported full coverage** (`covered_area_fraction
== 1.0`, no unknown coverage flag, non-null maximum gust) are passed
to the typed downstream join. The existing spatial overlay reports
coverage at nine decimal places and uses a small floating tolerance.
Consequently this is **full at the current reporting resolution**, not
a new independent proof of physically complete weather observations.

Any other exposures are explicitly labelled as:
- NUTS vintage not the same as the storm geometry;
- region absent from the supplied boundary dataset; or
- footprint incomplete, with weather **unknown rather than zero**.

A complete-region storm with no matching exposure is reported as
unmatched. Every submitted exposure is validated *before* selecting
complete regions, so invalid rows do not disappear because weather
was missing.

## Bound input contract

The CLI accepts three **local**, independently prepared JSON files:

1. `regions`: current NUTS2 polygon contract, EPSG:3035, reviewed
   NUTS boundary vintage and explicit `source_sha256` **claim**.
2. `storm`: one compatible extratropical windstorm grid-cell footprint,
   m/s ten-metre maximum gusts and original physical event identity.
3. `exposures`: `{"exposures": [...]}` containing the existing typed
   `regional_exposure_hazard_join_v0.py` records.

Each file is limited to **20 MB** and must match the
**caller's separately supplied exact SHA-256**. Strict JSON rejects
duplicate fields and nonfinite numeric constants. This proves the
supplied local input bytes were unchanged relative to the caller's
digest, *not* that provider source bytes, provenance, copyright,
commercial reuse, geospatial accuracy, insurance values or a
third-party hazard model are independently authenticated. Source
`source_sha256` claims in the JSON remain unverified by this bridge.

The existing model strictly retains the single physical event,
event date, NUTS vintage, and `extratropical_windstorm` subset of
`windstorm`. No new vulnerability curve, storm probability,
return period, claims, insurer attribution, ground-up loss, treaty,
reinstatement, Retro, or stochastic trial is inferred.

## Run locally

```bash
python -m unittest discover -s tests -p 'test_regional*.py' -v

python -m research_runners.regional_wind_overlay_exposure_bridge_v0 \
  /local/approved/regions.json /local/approved/storm.json \
  /local/approved/exposures.json \
  --regions-sha256 <exact_sha256> \
  --storm-sha256 <exact_sha256> \
  --exposures-sha256 <exact_sha256>
```

All three inputs are private/local to that run. The tool has
**no HTTP access or database writes**. Source geometry/grid cells are
not copied into the output; only source byte digests, approved-type
aggregate gust, event/region IDs, sample TIV from the original input
and explicit nonadmission flags are returned. Do not publish a
comparison output from proprietary source inputs until attribution,
privacy and source terms are checked.

## Tests and next scientific threshold

Thirteen new synthetic integration tests cover correct complete
weather, unknown partial weather, version/country mismatch, strict
byte pins, fake JSON fields, malformed exposure even under
incomplete weather, invalid cross-region geometry, temporal
leakage, a physical peril mismatch, unmatched sampled exposure
and deterministic input order.

The complete local available checkout's
`scripts/check_all.py` cannot run against an extracted ZIP **without
an actual Git checkout**. GitHub's full Python matrix/source/REUSE
pipeline must pass on the exact branch before merging.

Next: pin real, lawful and independent administrative/footprint/
exposure source bytes and exact geometric coverage per event;
obtain physical wind hazard and vulnerabilities, and only then
separately engineer insured loss and shared-world Monte Carlo
contracts. Other perils need their **own** physics and unit-specific
spatial adapters; do not relabel the wind adapter for flood or EQ.
