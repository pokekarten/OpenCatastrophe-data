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
contract. Recorded run receipts below are retained as documentation, but
original external dataset bytes are not persisted; there is no CAT modelling
admission, long-term event coverage, event-vintage freeze or scientific
accuracy proof.
For scientific usage a separate bounded time/space/event identity, original
byte receipt, event update/version handling, rights and quality review are
required. A successful online probe cannot be substituted for these gates.

The *dedicated EMSC one-event workflow* does not run provider requests
on unrelated CI pushes; its network run requires a reviewed workflow change
or manual dispatch. As separately documented below, the shared
`fixed-public-source-probes.yml` matrix now also makes one bounded,
anonymous EMSC request on relevant pull requests. Neither route changes
a Neon database or requires credentials.

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

## Verified live one-event source receipt (2026-11-01)

The exact reviewed anonymous FDSN JSON probe completed successfully in
[GitHub Actions run 41312906117](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41312906117),
job `EMSC fixed anonymous one-event probe`, main commit
`074d79c27818dc78a7ab109625b2beadde261e1e`.

- Retrieval: `2026-11-01T13:47:00.516426+00:00`
- HTTP: `200`, response media type `application/json`
- Exact frozen request:
  `https://www.seismicportal.eu/fdsnws/event/1/query?format=json&limit=1&orderby=time&nodata=204&includeallorigins=false&includearrivals=false`
- Original response: **618 bytes**, one GeoJSON Point event feature
- Original response SHA-256:
  `683213de4a7cbabc5c38b248e0a00e484cbd8448d38f7fb873a3673c1d87efad`
- Trusted execution script SHA-256:
  `916eee391c9b0b52d9d26637eab64d65b8c063b08307ee765392715ee5a238f3`
- Original event details were *not* saved/logged; no model-input admission.

This is a single-request availability and response-compatibility proof. It
does not establish all-event catalogue coverage, independent scientific
quality, event stability, or a licensed and reproducible earthquake hazard
dataset. Follow-on research must freeze a distinct exact event/time-window
product and independently review the resulting data version and quality.

## Follow-up cross-workflow live verification (2026-11-01)

A second, independently executed one-event response was verified using the
shared fixed-source capability matrix in
[GitHub Actions 41316632298](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41316632298)
on draft PR #962, exact head commit
`86080791a8c2ba1d8c995c788c046937527a82b1`.
This reused the independent EMSC FDSN validator and already reviewed
`latest_event_json` operation, without downloading any event collection.

- Retrieval UTC: `2026-11-01T14:32:02.348650+00:00`
- HTTP 200, `application/json`, **608 bytes**, exactly one GeoJSON Point feature
- SHA-256 of this second transient JSON response:
  `70f81ad58a44de4f273da8c9fcb0c2f97fed1a3f24649347d264e3c6c8708826`
- API access-contract SHA-256:
  `cc3f8ab2af7ab6b688d998e6142586a47db3d4a1c918930c5da5ea760c6f6a99`
- Shared probe code SHA-256:
  `b5925ab0f574c8c6c4ba615656e4fc9d47ee66b70b724bcc62f852fd6f37821b`
- `provider_bytes_persisted=false`, `model_input_approved=false`,
  `scientific_event_parameters_verified=false`

The earlier frozen 13:47 UTC source receipt was 618 bytes and the 14:32
response was 608 bytes. **These are responses from a moving latest-event
query, not the same immutable event**; neither the byte difference nor
record shape establishes an earthquake revision, a new physical event, or
changes in seismicity. This provides *two independent live connectivity
receipts* and reinforces why production scientific event usage requires
exact event-ID, origin/source release and revision/version controls.

The source licence is for data excerpts under service-specific CC BY 4.0
with proper attribution; it does **not** authorize mirroring the full
upstream service or publishing an unreviewed production CAT event catalogue.

