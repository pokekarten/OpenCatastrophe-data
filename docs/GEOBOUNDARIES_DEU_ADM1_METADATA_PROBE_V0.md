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

## Exact first-party live acquisition receipt (2026-11-01)

A single official metadata HTTP response passed the reviewed bounded probe in
[GitHub Actions run 41312575287](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41312575287),
job `Fixed geoBoundaries gbOpen DEU ADM1 metadata check`, commit
`f3d047f6e67e8ac3140b295368325b8b5de4032d`.

- UTC receipt timestamp: `2026-11-01T13:42:53.636994+00:00`
- Frozen canonical request: `https://www.geoboundaries.org/api/current/gbOpen/DEU/ADM1/`
- Response media type: `application/json`
- Response size: **1,812 original provider response bytes**
- Original response SHA-256:
  `65af06f80e837028997c396d2c67d74fb1e1752d884e9a0638d5c736ee8c345a`
- Trusted execution script SHA-256:
  `69c168a8d72eff78f3d85c64e5be8f54b246f478d9387febf0ecf60afa01cd96`
- Verified exact source identity: `DEU-ADM1-10402087`, 2021,
  16 administrative units, commit-pinned provider asset links at `9469f09`.
- Metadata bytes were **not persisted** and geometry was **not downloaded**.
  No CAT-model admission or insured-exposure inference occurred.

This receipt is immutable evidence for the **single request**; it is not a
general uptime guarantee, a receipt for the asset files, or evidence that
future `/current/` responses are identical. Re-run the same bounded
request only after intentionally checking whether its source contract still
matches the provider state.
