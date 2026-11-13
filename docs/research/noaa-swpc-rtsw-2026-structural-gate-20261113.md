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


## Verified original-provider HTTPS source test: 2026-11-13

The former research API check's `inconclusive` status has now been
**superseded for one concrete retrieval** by a source-specific, **direct**
public GitHub Actions HTTPS test. This was **not** a permissive
external-intermediary JSON-shape check.

- [GitHub Actions run **43489514680**, job **132106651956**](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489514680/job/132106651956) executed exactly one reviewed static request on **2026-11-13T19:09:57.147645Z** under source-branch commit `4a579279e240c9429e6e66360194446c7c6e48b9`.
- Original decoded response HTTP **200**, `application/json`, **1,719,377 bytes**, SHA-256 **`bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159`**.
- Fixed request identity SHA-256 **`9c8cff6ed4aa0ba97edb2a8d179728c5696e446c25437fbf9dfc758d20ac31d2`**; probe code SHA-256 **`80b80b5b214c471eb43ae3d303e95748afb7be624dea351f663a057f52333281`**, access-contract SHA-256 **`28a80ab81521d4b4a3b5332cfd0d38343b7b41bdb9168cc8833c8aa0320292ca`**.
- New 2026 native multi-spacecraft JSON record validator **passed**: parseable observation timestamps, per-record spacecraft `source`, Boolean `active`, numeric/null finite `bx_gsm/by_gsm/bz_gsm/bt`, no duplicate spacecraft-time record or two active streams at one instant, at least one magnetic reading.
- **16 synthetic source-specific offline tests** also passed in the same public runner. The provider returned actual original bytes transiently for hashing/structural validation; **none** are stored as Git files, logs, research samples or model inputs.
- The temporary *one-shot* workflow was **deleted** after the test; the standard reviewed-18 manual network workflow remains unchanged. This pull request contains only durable contract code, offline tests, and this documentary receipt, with no new scheduled provider polling.

The SHA-256 pins precisely **this time-varying rolling JSON snapshot**. A subsequent
response **must not** be expected to have identical bytes. Successfully
validated connectivity/shape **does not** prove sensor calibration, 24-hour
series continuity, complete 2026 provenance, provider cadence compliance
for automated monitoring, or usefulness for CAT loss/risk modelling.
`model_input_approved=false`, `data_source_admitted=false` and
`sensor_lineage_verified=false` were explicitly recorded.

**Private DB caveat:** the current
`research.source_api_smoke_receipt_v0` schema contains a hard
`CHECK (NOT strict_repository_runner_executed)`. The source's direct
GitHub trust proof cannot be recorded with a truthful `true` flag in
that historical table until a separate reviewed schema is available.
We did not bypass this check or write a deceptive `false` record.

## Manual ongoing-probe gate and remaining science

The existing `source-api-readiness.yml` workflow has an explicit manual
`reviewed_18` opt-in path; ordinary PR CI runs only offline checks. The **single** trusted direct source check above has passed. Future live runs
must still use the manually reviewed 18-source workflow and preserve HTTP 200,
bounded body, exact original static URL, native shape and original-body digest.
If the provider legitimately changes its schema or returns unavailable
sensor values, report **BLOCKED** rather than weaken the validation. No
unreviewed recurring acquisition cadence or model-source admission is granted.

**Model/data status remains not admitted.**
