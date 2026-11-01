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
