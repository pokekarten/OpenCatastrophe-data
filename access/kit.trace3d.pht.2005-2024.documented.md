<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/kit.trace3d.pht.2005-2024.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `kit.trace3d.pht.2005-2024.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** kit.trace3d.pht.2005-2024.documented

## Source ids

- kit.trace3d.pht.2005-2024

**Provider:** KIT / Mohr et al. / DWD radar

**Interface type:** web_portal

**Status:** documented_only

**Documentation url:** <https://doi.org/10.3389/fenvs.2026.1736782>

**Service root:** <https://doi.org>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** other

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /10.3389/fenvs.2026.1736782

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- text/html

**Format:** 15577 potential hail tracks from 3D radar PZ volumes

**Scientific semantics:** Published 2026-02-06. Article validated against building insurance data; no public direct track-file link established. Data availability statement points to https://opendata.dwd.de/weather/radar/sites/pz/ and ERA5 regimes https://zenodo.org/records/17080146; confirm historic PZ access separately from operational directory. Paper does not provide hailstone diameter distribution. Request derived tracks and explicit rights or reproduce method with authorized radar archive.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** No derived track download established. Request 15577 tracks, schema, licence and allowed commercial model use from KIT; alternative reconstruct from separately approved historical DWD PZ archive. No direct ground hail-size labels.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.3389/fenvs.2026.1736782>

**Notes:** Open-first qualification queue. No derived track download established. Request 15577 tracks, schema, licence and allowed commercial model use from KIT; alternative reconstruct from separately approved historical DWD PZ archive. No direct ground hail-size labels. Discovery/access only: no admission, no external bytes in Git, no model approval.
