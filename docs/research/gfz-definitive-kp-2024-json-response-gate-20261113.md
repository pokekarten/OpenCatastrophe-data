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

**Outstanding:** run the approved manual `reviewed_18` mode in
`.github/workflows/source-api-readiness.yml` only from the reviewed trusted
`main` revision after merge. The ordinary PR CI and
`fixed-public-source-probes.yml` skip live original-provider requests on
unreviewed PR heads. A green PR alone must not be marked as a first-party
runner receipt. Original-response hashes, source rights and scientific/model
admission remain separately gated.
