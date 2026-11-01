<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EMSC / SeismicPortal FDSN one-event probe (v0)

## Purpose and current rights boundary

`access/emsc.seismicportal.fdsn-event.json` is the reviewed access contract.
Its status is `probe_ready`, not proof of actual live acquisition or
permission to treat an operational earthquake catalogue as CAT hazard input.
The official SeismicPortal service documents FDSN Event API 2.2 and the
service-specific CC BY 4.0 licence:
[service documentation](https://www.seismicportal.eu/fdsn-wsevent.html),
[OpenAPI](https://www.seismicportal.eu/fdsnws/event/1/redoc),
[terms](https://www.seismicportal.eu/terms.html).

`scripts/probe_emsc_fdsn_event_v0.py` makes only the contract's exact
`latest_event_json` request. A human explicitly opts into the network call:

```bash
python -m unittest tests.test_probe_emsc_fdsn_event_v0 -v
python scripts/probe_emsc_fdsn_event_v0.py --live
```

After merging the workflow into the default branch, operators may alternatively run
`.github/workflows/emsc-one-event-receipt.yml` with the manual
**Run workflow** action in GitHub Actions. It uses the same frozen CLI and
prints only the bounded receipt. CI never invokes this live job by default.

The live command has no generic URL, date, event ID, coordinate, header,
credential, pagination or bulk-harvest parameters. It disables proxies and
redirects, uses TLS, enforces a 30-second request timeout and a 1 MiB response
ceiling, and expects exactly one well-formed GeoJSON point feature with an
EMSC source identifier. It prints **only** a receipt: the trusted request
identity, UTC time, response byte length and SHA-256, parser shape and
script SHA-256. Coordinates, magnitudes and event identifiers are not printed
or saved; the response bytes remain in memory during this invocation.

An HTTP success proves only that this one response met the expected
contract. No live probe result has been checked in, no original external
dataset bytes have been persisted, and there is no CAT modelling admission,
long-term event coverage, event-vintage freeze or scientific accuracy proof.
For scientific usage a separate bounded time/space/event identity, original
byte receipt, event update/version handling, rights and quality review are
required. A successful online probe cannot be substituted for these gates.

CI executes **offline synthetic-only** tests. It does not make a provider
request, change any Neon database or require credentials.

## One-shot provider receipt on a reviewed workflow revision

The dedicated `.github/workflows/emsc-one-event-receipt.yml` workflow also
runs **once when its own workflow definition is updated on `main`**. This is
a narrow and intentional first-party live evidence check after source-specific
tests have passed. Ordinary unrelated pushes and pull requests do not call
the provider, and there is no schedule or bulk harvesting. Every subsequent
workflow change remains subject to normal review before causing another
single bounded provider request.

A live run's result is authoritative only for its one request: record the
exact workflow run URL, UTC, content SHA-256 and response size in this document
after verification. A failed upstream request or changed response contract
must remain a reported blocker, not be silently treated as success.
