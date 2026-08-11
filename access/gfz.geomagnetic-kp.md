<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/gfz.geomagnetic-kp.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `gfz.geomagnetic-kp.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** gfz.geomagnetic-kp

## Source ids

- gfz.geomagnetic-kp

**Provider:** GFZ Helmholtz Centre for Geosciences

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://kp.gfz.de/en/data>

**Service root:** <https://kp.gfz.de>

**Api version:** `null`

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- definitive_kp_day_json

### Path templates

- /app/json/

**Parameter rules:** The probe request is repository-constructed only: start=2024-01-01T00:00:00Z, end=2024-01-01T23:59:59Z, index=Kp and status=def. The fixed one-day historical window intentionally requests only definitive Kp values. Callers cannot supply a host, arbitrary path, headers, index, status, time range or unrestricted query parameters. Any later realtime, nowcast, alternate-index or variable-window query requires a separately reviewed bounded operation rather than widening this probe contract.

## Response contract

### Expected media types

- application/json

**Format:** GFZ Kp Web Service JSON response for the fixed definitive-Kp probe window.

**Scientific semantics:** Kp is GFZ's planetary three-hour geomagnetic activity index derived from contributing observatories. This contract deliberately requests definitive Kp only; it does not treat nowcast values, derived ap/Ap/Cp/C9 indices, Hp indices or forecasts as equivalent. A successful probe demonstrates service connectivity and response-contract compatibility only, not scientific fitness for infrastructure-loss modelling or an immutable identity for future operational data.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** No repository-specific rate-limit assumption is made. This contract permits exactly one small fixed historical probe request; any broader or repeated retrieval requires a separately reviewed execution decision that rechecks current provider guidance.

**Mutability notes:** GFZ distinguishes continuously updated nowcast products from definitive Kp. The probe freezes a historical definitive window and status=def; every future receipt must still bind retrieval UTC, normalized request identity, trusted execution-code SHA, response byte count and SHA-256. The DOI archive is the durable scientific dataset identity, separate from this live service route.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://doi.org/10.5880/Kp.0001>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** GFZ Data Services records the Geomagnetic Kp index under CC BY 4.0, and the GFZ Kp data page explicitly provides the Web Service API for programmatic retrieval. This records the source-service rights ceiling only. The landscape source remains not admitted, so this contract does not authorize committing future response bytes, derived samples or model inputs without exact asset/sample, provenance and repository review.

## Probe contract

**Mode:** provider_specific

**Operation:** definitive_kp_day_json

**Requires credentials:** `false`

### Expected evidence

- provider success status without unsafe payload logging
- application/json response media type
- response byte count and SHA-256
- bounded fixed-window definitive-Kp response-contract validation
- retrieval UTC and trusted execution-code identity
- external_bytes_persisted=false

**Implementation decision:** build_later

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://kp.gfz.de/en/data>
- <https://doi.org/10.5880/Kp.0001>
- <https://dataservices.gfz-potsdam.de/panmetaworks/showshort.php?id=escidoc%3A5216888>

**Notes:** Static contract only. GFZ documents programmatic JSON access using start, end, index and optional definitive-status parameters. This slice freezes one definitive Kp day before any target-value inspection and adds no adapter or live network execution. Future hosted probing must use the reviewed trusted Actions network plane and must not treat connectivity as source admission, scientific validation or publication approval.
