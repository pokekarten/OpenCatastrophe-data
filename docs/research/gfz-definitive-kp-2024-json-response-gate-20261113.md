<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GFZ Kp fixed definitive-day JSON response gate

**Review date:** 2026-11-13. **Source:** `gfz.geomagnetic-kp`.
**Scope:** Only the existing, reviewed anonymous public-source probe and
its exact frozen one-day query. Not a new acquisition, API endpoint or licence.

## Existing source evidence and false-positive

The old shared fixed-source runner classified any nonempty JSON object as
successful GFZ Kp API compatibility. Even `{"unexpected":true}` or a
single-element, wrong-date Kp array would pass. This is insufficient for the
fixed contract's `2024-01-01` **definitive** three-hour Kp observation day.

In the restricted research Neon source-sample ledger, original provider
sample #1 is already recorded for this exact definitive 2024-01-01 product,
with an original provider-response SHA. Read-only shape metadata inspection
on 2026-11-13 confirmed three aligned arrays
`datetime`, `Kp` and `status` of **eight** entries each, eight numeric
Kp values, and all source statuses `def`. The first and last original
timestamps are `2024-01-01T00:00:00Z` and
`2024-01-01T21:00:00Z`. These observations do not import or republish
any provider numeric measurements or original bytes into Git.

Authoritative API/service documentation:
https://kp.gfz.de/en/data

Dataset rights/DOI:
https://doi.org/10.5880/Kp.0001

## New fail-closed parser

The existing reviewed public-probe runner now rejects a response unless:

- its top-level JSON is an object containing three *actual* length-eight arrays;
- `datetime` is the exact ordered eight-element UTC three-hour clock for
  2024-01-01, not merely a parseable or vaguely nearby time;
- every `status` is the definitive code `def`;
- every Kp measurement is a finite, non-Boolean number in the permissible
  0–9 Kp index scale.

No provider numeric values, text `meta`, identities or arbitrary keys are
exported in the receipt. The output contains only bounded response SHA,
request/source/contract identity, fixed-window/definitive structural flags
and record count; **scientific_values_verified=false** and
**model_input_approved=false** are preserved. A strict schema match alone
does not independently prove instrument calibration, history completeness,
license to publish raw provider data, or CAT model applicability.

## Synthetic verification and strict live gate

Run offline:

```sh
python -m unittest tests.test_probe_fixed_public_sources_v0 -v
python -m unittest tests.test_source_api_readiness_v0 -v
python scripts/check_all.py
```

Tests include successful purely synthetic eight-bin response, and hard
rejections for non-Kp JSON, wrong time and order, missing bins, missing
definitive status, string/bool/null/out-of-range/non-finite Kp readings and
unbounded/malformed response. Existing source-specific allowed URL,
response-byte limits, timeout, no redirect, reviewed rights and no retries
are unchanged.

## VERIFIED direct original GFZ provider receipt, 2026-11-13

A **real one-request public GitHub Actions original-provider GET** was
executed from the combined NOAA/GFZ source branch, with the exact reviewed
fixed original GFZ endpoint and an actual strict eight-bin source parser:

- [Public GitHub Actions run **43491158483**, job **132112397671**](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43491158483/job/132112397671), source-branch commit `17da6a4a3250bc63e7c363a47f74213472196eeb`, retrieval **2026-11-13T19:19:54.407282Z**.
- Original HTTP **200**, `application/json`, **361 original response bytes**. Verified SHA-256 **`f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a`**; fixed request SHA-256 **`f766594d3b83d42a9a16ef247c7119f1a435a2ea00d5c004876e4cfab3cd7dfd`**.
- Code SHA-256 **`423e21bda179d5664a74f3c3bbe2a5e6d955aa4386305545d292a627b191affa`**, reviewed source access contract SHA-256 **`1c57d8e1147c511e14af0d9468b4a55fc80c5000c3c441b30660679673f1c02d`**.
- The entire eight-time-bin **2024-01-01 definitive** fixed-window field structure passed, all statuses `def`. The parser does not record or log any individual Kp numerical measurements, and has `scientific_values_verified=false`, `model_input_approved=false`, `data_source_admitted=false`.
- **18 synthetic probe regression tests** also passed in the same hosted source job; no real provider source bytes were checked into Git. The experimental one-shot source-workflow was **removed immediately** after its successful run, leaving no added polling or normal PR live behavior.

**Trust distinction:** The original public action and pinned code and response
digests are now directly verifiable, materially stronger than the older private
Neon sample #1 and offline simulation alone. This is an **API-format/source
identity pass**, not a universal provider rights licence, proof of Kp physical
accuracy, space-weather catastrophe model validation or permission to
publish raw source responses. GFZ states its Kp source data are **CC BY 4.0**
with attribution: https://kp.gfz.de/en/about-kp.

Future manual original GETs remain separately gated under the fixed reviewed
source program; normal pull-request CI remains offline. The separate private
Neon historical smoke table enforces `CHECK (NOT strict_repository_runner_executed)`,
so no false or impossible trusted-runner row was inserted there. A
distinct reviewed append-only trusted-origin receipt ledger is still needed
to reconcile source tests in Neon without changing historical source claims.

