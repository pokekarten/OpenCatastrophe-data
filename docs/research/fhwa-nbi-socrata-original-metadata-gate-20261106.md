<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FHWA NBI 2026 Socrata: source-schema metadata gate (research only)

**2026-11-06 — metadata-only, non-admitted.** Companion to FHWA source candidate in `landscape/sources-industrial-epc-bridges-20261105.json` (PR #1376). No actual bridge rows, insurer assets, coordinates or monetary losses have been loaded.

Official source pages:

- FHWA / DOT portal: https://data.transportation.gov/Roadways-and-Bridges/National-Bridge-Inventory/pced-83j4 (published dataset **124 columns**; metadata updated 2026-11-02; dataset temporal applicability 2024/2025).
- Original metadata API: https://data.transportation.gov/api/views/pced-83j4.json . A bounded **actual original-response metadata audit** subsequently completed successfully in GitHub Actions on 2026-11-06; see the exact proof below. Original individual bridge rows were not fetched.
- FHWA annual files and standard notes: https://www.fhwa.dot.gov/bridge/nbi/nbi_data.cfm . The 2026/2027 SNBI coding transition requires separate vintage/crosswalk review. A November 2026 catalog update does not establish 2026 observations.

## Source-schema gate

`research_runners/fhwa_nbi_socrata_metadata_gate_v0.py` reads only locally acquired, bounded original Socrata metadata JSON bytes. It checks exact dataset ID `pced-83j4`, title, tabular view, **124 public fields** (excluding colon-prefixed Socrata internal system columns), unique API names, and required field identities: year, state code, structure number, latitude, longitude and construction year. Record year and state code must have numeric metadata types; structure ID must be textual. Duplicate JSON keys, HTML/error pages, unexpected schema types, field omissions and changing public column counts fail closed. Outputs contain only SHA-256, field counts and required type indicators, never raw coordinates. Operator-computed SHA-256 is *not* a provider signature.

```shell
# Independently acquire official JSON into a temporary directory outside Git.
# The script itself makes no request and accepts no credentials.
python -m research_runners.fhwa_nbi_socrata_metadata_gate_v0 \
  --original-metadata /tmp/fhwa-nbi-pced-83j4-original.json \
  --out /tmp/fhwa-nbi-metadata-only-receipt.json
python -m unittest tests.test_fhwa_nbi_socrata_metadata_gate_v0 -v
```

**Still blocked:** Metadata validation does not confirm real source row values, bridge-year uniqueness, structure ID changes, 2026/2027 SNBI crosswalk, spatial coordinate encoding/CRS, rights, bridge site fragility, insurance ownership, TIV or model calibration. Source `LAT_016` and `LONG_017` may contain encoded bridge coordinates rather than verified WGS84 decimal numbers. Public-road bridge condition ratings are not catastrophe fragility functions.

**Next evidence gate:** Acquire and independently checksum a bounded official original metadata response, confirm licensing and reporting vintage, and only afterward run a separate, conservatively bounded row-level schema/geometry/duplicate inspection. Neither original metadata nor bridge-level raw rows may be silently promoted into Neon or insurer CAT models. Keep Draft / `not_admitted`.

## 2026-11-06 original public metadata live receipt (not row-level validation)

After seven synthetic corruption tests passed on the same GitHub runner, the dedicated [exact-original FHWA NBI workflow run #42248429002](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42248429002) completed **SUCCESS** against the original public endpoint `https://data.transportation.gov/api/views/pced-83j4.json`. The bounded response was **188,587 bytes**, SHA-256 **`c062703a1886f66551e00e7cb86924874cd96c66a20c8f22ca50ed1fad498e26`**, with dataset ID `pced-83j4`, exactly **124** non-Socrata-internal public API fields and all required field/type checks satisfied. Original metadata was held only in a temporary runner file and was not committed or published as an artifact. This independently executed transport/source-identity check remains **not an externally publisher-signed checksum**.

**Next scope is unchanged:** no original public bridge **row** or inspection date has been checked; legacy NBI/SNBI field mapping, physical coordinate encoding, condition semantics, original individual-asset attribution, data-use rights and CAT/insurance vulnerability are separate unresolved gates. The schema receipt is not a substitute for source vintage or real bridge-year samples. Scientific/insurance admission remains explicitly **false**.
