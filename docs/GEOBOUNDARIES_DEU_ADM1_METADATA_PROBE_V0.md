<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# geoBoundaries gbOpen DEU/ADM1 — frozen metadata and provenance probe v0

## Why this source

geoBoundaries provides administrative polygons and provenance for geographic
join/validation tasks. They are **not** building footprints, insured locations,
risk values, event footprints or CAT losses. The initial source-specific
contract `access/geoboundaries.gbopen.json` reviews one anonymous gbOpen
metadata response for Germany ADM1 (states), not all countries/regions.

The exact live provider metadata was independently checked on 2026-11-01:
`boundaryID=DEU-ADM1-10402087`, `boundaryISO=DEU`,
`boundaryType=ADM1`, `boundaryYearRepresented=2021`,
`admUnitCount=16`, asset commit `9469f09`, provider `Federal Agency
for Cartography and Geodesy`, original licence `Data license Germany -
Attribution - Version 2.0` and `licenseSource=www.govdata.de/dl-de/by-2-0`.
The mutable `/current/` alias may change later: do not auto-adopt new IDs,
pinned commits, original licences, source names or year/unit counts.

- Official API and semantics: https://www.geoboundaries.org/api.html
- Exact canary: https://www.geoboundaries.org/api/current/gbOpen/DEU/ADM1/
- Original licence: https://www.govdata.de/dl-de/by-2-0

## Deterministic implementation

```bash
python -m unittest tests.test_probe_geoboundaries_deu_adm1_v0 -v
python scripts/probe_geoboundaries_deu_adm1_v0.py --live
```

The second command opts into **exactly one** official HTTP GET.
After merging the PR, a manual GitHub Actions invocation can run
`.github/workflows/geoboundaries-deu-adm1-metadata-receipt.yml`.
The workflow executes on an explicit manual dispatch **or once when its own
workflow definition changes on main**. It does not run on ordinary pushes to
other repository paths, on PRs, or on a recurring schedule. Regular CI runs
only deterministic offline synthetic tests. This small scoped one-shot main
run supplies a genuine provider connectivity receipt after the workflow
revision is merged, without checking in provider response bytes.

The implementation rejects redirected/altered hosts, mutable identity drift,
original licence changes, non-JSON, duplicate JSON keys, missing field
provenance, unreviewed asset-link targets and over-64-KiB responses.
The receipt prints UTC, request URL, response byte count and SHA-256,
code SHA-256, exactly reviewed source metadata, and four commit-pinned asset
**link references only**. These URLs are **not downloaded**. Credentials
are not used, and provider bytes are never saved by the probe.

## Scientific and engineering gates before an actual spatial dataset

1. Freeze the *specific* geometry asset (URL, commit, length, SHA-256 and
   upstream attribution/licence); consider exact original licence obligations.
2. Verify correct CRS, GeoJSON shape, precisely 16 unique state identifiers,
   feature validity, geometry coverage, overlaps and source-year semantics
   with a separate offline, strict geometry validator.
3. Preserve the provider ADM1 boundary vintage as 2021; do not silently
   join to NUTS 2016/2021/2024 or use as proof of current buildings.
4. Keep raw bytes in a separate rights-reviewed CAT data store, not public
   Git or the independent Pokémon database. Require explicit admission
   before treating the asset as a reproducible modelling or calibration input.

A successful metadata receipt only proves that an exact, reviewed
metadata endpoint currently serves the expected response. It does not
prove geometry acquisition, scientific readiness, model suitability or
permission to publish provider bytes.
