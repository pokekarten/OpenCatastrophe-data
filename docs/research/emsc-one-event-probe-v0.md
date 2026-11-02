<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EMSC FDSN Event: bounded one-event connectivity preflight (v0)

## Role and source contract

This standalone, dependency-free Python adapter implements the existing
[EMSC one-event access contract](../../access/emsc.seismicportal.fdsn-event.json).
The first probe is exactly one FDSN event in JSON, ordered by latest origin
time, with no arrival or alternate-origin expansion. The official provider
documents the service and its data as CC BY 4.0:

- https://www.seismicportal.eu/fdsn-wsevent.html
- https://www.seismicportal.eu/fdsnws/event/1/redoc
- https://www.seismicportal.eu/terms.html

## Execution

Run synthetic offline tests:

```sh
python -m unittest tests.test_emsc_one_event_probe_v0 -v
```

Inspect a **synthetic local JSON fixture** without any provider connection:

```sh
python research_runners/emsc_one_event_probe_v0.py --fixture /path/to/synthetic.json
```

An explicitly approved, one-shot network probe is available with:

```sh
python research_runners/emsc_one_event_probe_v0.py --probe
```

The provider call has a hard-coded HTTPS host/path/parameters, 30-second
timeout, no redirects, no automatic retries, no supplied credentials,
no user-controlled host/URL/query, identity encoding only, and a 1 MiB
maximum response. A non-200 (including 204) or structurally invalid
response fails closed. Live raw response bytes are never printed or
persisted; successful output is only a SHA-256 receipt and boolean
scope gates. The provider's mutable catalogue may change between runs,
so any scientific workflow must separately pin and review original
event identifiers, event updates, completeness and data use.

## Scientific and database boundary

This is *connectivity/schema evidence only*, not a hazard dataset
acquisition or earthquake CAT calibration. A success does not
establish seismic recurrence, intensity fields, completeness, loss,
insured exposure, insurer identity, claims, stochastic years, or
rights to rehost original output. Do not import to Neon, update the
canonical access-contract admission status, merge without CI review,
or interpret a local synthetic fixture as provider evidence.

Next: review the exact PR commit and required CI jobs; perform the
one-shot original-provider probe in an approved execution plane and
store an externally auditable hash/time/code receipt (not source bytes).
