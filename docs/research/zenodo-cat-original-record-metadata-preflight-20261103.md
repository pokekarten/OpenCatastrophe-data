<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Zenodo CAT original-record metadata preflight (2026-11-03)

**State:** deterministic offline original-record metadata identity test. No remote source bytes were fetched in this investigation, no database writes, no rights approval and no scientific/model admission.

## Provider record identity and scope

The offline runner at scripts/zenodo_cat_metadata_preflight_v0.py knows exactly six original Zenodo records from this PR:

| Candidate | Original published record |
| --- | --- |
| European sparse multi-hazard event arrays | https://zenodo.org/records/22080546 |
| IH-STORM 12,000-year ENSO-conditioned tracks | https://zenodo.org/records/15097665 |
| TRANSCLIMA GTSMv3/GESLAv3 cyclone surge hydrographs | https://zenodo.org/records/18170693 |
| TRANSCLIMA 262-entry source catalogue | https://zenodo.org/records/23736379 |
| GTSM-ERA5-E extreme coastal levels/statistics | https://zenodo.org/records/14671593 |
| GFSM 30 m derived global flood susceptibility | https://zenodo.org/records/20568218 |

The seventh candidate, Eurac EO4MULTIHAZARDS, is a separate PostgREST service and is intentionally outside this Zenodo preflight.

The [official Zenodo records API](https://developers.zenodo.org/) documents anonymous GET /api/records/:id metadata access. Zenodo [explains](https://support.zenodo.org/help/en-gb/2-content/21-can-i-get-permission-to-use-a-specific-record) that record metadata is CC0, while source files retain their declared license. Individual upstream data rights must be checked separately.

## Operator command with permitted public record metadata

This command is an example for an operator with normal HTTPS/DNS access; it has **not** been run successfully in this session:

~~~sh
curl --fail --silent --show-error --location --max-time 20 --max-filesize 5242880 \
  -H "Accept: application/json" \
  "https://zenodo.org/api/records/22080546" -o /tmp/zenodo-22080546.json
python scripts/zenodo_cat_metadata_preflight_v0.py \
  --source-id nl.vu.european-multihazard-sparse-events.v1 \
  --metadata /tmp/zenodo-22080546.json
~~~

All CLI work is local and offline: the input is a JSON file, not a URL; the runner performs no network access. It rejects unknown or mismatched record IDs/DOIs, inaccessible record metadata, missing declared license, paths with traversal, duplicate file keys, missing or malformed original publisher checksums, non-Zenodo or cross-record download links, suspicious URL parameters, or an input exceeding 5 MiB. The receipt includes a SHA-256 of **the metadata response bytes**, not the original asset files; any MD5/SHA256 reported for source files is merely the publisher-listed digest, not an independently computed digest. It cannot prove downloadable source bytes, scientific adequacy, insurer commercial reuse permission, or admission.

## Scientific boundaries and next executable evidence

1. Sparse European compound events: four input source families (C3S/ERA5-Land wind/heat, EFFIS wildfire, JRC satellite-derived flood depths) are previously known. Track exact version, original event ID, spatial-grid/sparse index, hazard-specific unit, start/end, affected-cell overlap and all upstream lineage. Pair overlaps are *not* independent observed claims or a loss correlation parameter.
2. IH-STORM: retain stochastic basin, climate regime (historic/neutral/El Niño/La Niña), simulated year and storm ID. These tracks do not supply wind-field intensities at property coordinates, frequency calibration independent from IBTrACS, vulnerability, or insured loss.
3. TRANSCLIMA surge: distinguish modelled GTSMv3 from gauge-derived GESLAv3 stations, source SID, UTC times, storm/tide/water-level reference and vertical datum. A hydrograph is not a 2D inundation map.
4. GTSM-ERA5-E return levels and GFSM susceptibility are screening/model challenge surfaces; neither is a true simultaneous historical damage event or CAT payout.

**Live probe blocker:** In the current Linux sandbox on 2026-11-03, a bounded GET of the official Zenodo records API was blocked by DNS resolution before receiving a response. Thus no real provider metadata rows, file hashes, NetCDF variables, rights grants, actual source bytes, or Neon model data are asserted by this PR.

**Validation:** python -m unittest discover -s tests -p 'test_zenodo_cat_metadata_preflight_v0.py' -v (synthetic negative tests). The repository CI runs all test*.py and must pass at the new head SHA; do not merge before full check, scoped rights review, and scientific quality review.
