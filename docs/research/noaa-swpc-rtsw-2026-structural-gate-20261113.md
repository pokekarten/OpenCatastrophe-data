<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA SWPC RTSW 2026 multi-spacecraft JSON shape — false-positive regression gate

**Date:** 2026-11-13. **Scope:** existing approved fixed public-source probe
`noaa.swpc.real-time-solar-wind`; no new source, endpoint, rights,
request frequency or live-network automation.

## Evidence and concrete false-positive

The previous `scripts.probe_fixed_public_sources_v0.verify_response`
accepted **any nonempty JSON object or list** from the SWPC magnetometer
endpoint, including `[{"satellite":"x"}]`. This could classify an HTML-avoiding
error/wrong-product JSON as a successful response without timestamps,
spacecraft identity or even a magnetic field. A research Neon API observation
for this source was already classified `inconclusive`, not trusted success.
A stronger local validator does **not** replace the still-missing original
strict GitHub-runner receipt.

NOAA/NWS **Service Change Notice 26-21 (2026-03-02)** officially describes
the 2026 replacement product at the already frozen
`https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json`:

- each replacement product includes `source` (observing spacecraft) and
  Boolean `active` (SWPC operationally selected at observation time);
- the magnetometer fields `time_tag`, `bx_gsm`, `by_gsm`, `bz_gsm`,
  `bt` are retained, but numeric values are now numbers rather than
  quoted strings;
- the product is a rolling multi-spacecraft stream, not a stable
  homogeneous time series, historical climate observation, flood/hail
  hazard or insurance CAT input.

Official dated notice:
https://www.weather.gov/media/notification/pdf_2026/scn26-21_Data_Format_Changes_Impacting_SWPC_Products.pdf

## Strict bounded offline structure check

The existing fixed-source probe now requires a bounded **nonempty array of
record objects**, with these exact fields present on each record:

- `time_tag`: parseable calendar timestamp in the observed NOAA
  year-month-day/second layout; no invented time range or freshness claim;
- `source`: printable nonblank spacecraft identity and `active`: Boolean;
- `bx_gsm`, `by_gsm`, `bz_gsm`, `bt`: each numeric finite or `null`
  (instrument gaps are valid), at least one numeric magnetic observation
  somewhere in the response.

The shape gate rejects a non-array, wrong-product list, missing source/active,
string-encoded numeric readings, malformed timestamps, non-finite numbers,
all-empty observations and out-of-bound record counts. The verifier also
rejects repeated observations for the same spacecraft and UTC instant,
including equivalent `T...Z` and space-delimited times, and refuses more
than one `active=true` spacecraft at one instant. SWPC documents at most one
operationally active spacecraft per timestamp; `active=false` does not imply
low measurement quality. These are conservative structural checks only. It **does not** log
times, spacecraft identifiers or magnetic measurements, but outputs typed
structural flags and a response digest from the existing reviewed probe
wrapper. No arbitrary host, new query, redirect, retry or credentials are
introduced. The max response bytes remain the reviewed **4 MiB** bound.

```sh
python -m unittest tests.test_probe_fixed_public_sources_v0 -v
python -m unittest tests.test_source_api_readiness_v0 -v
python scripts/check_all.py
```

All new test payloads are invented synthetic measurements. No actual provider
sample or original response is distributed in Git. Provider license and API
terms remain the previously reviewed source-specific contract; this
contribution does not independently re-license any spacecraft data.

## Independent original-provider gate still open

The existing `source-api-readiness.yml` workflow has an explicit manual
`reviewed_18` opt-in path; ordinary PR CI runs only offline checks. A real
trusted-runner receipt must require the existing HTTP 200, original decoded
body under 4 MiB, exact static path, response type, raw-byte SHA-256 and
updated 2026 shape. If the provider legitimately changes its schema or
returns unavailable sensor values, report **BLOCKED** for review instead
of weakening the test or treating it as real-time hazard/CAT calibration.

**Model/data status remains not admitted.**
