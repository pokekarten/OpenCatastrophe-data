<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/psmsl.global-tide-gauge-sea-level.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `psmsl.global-tide-gauge-sea-level.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** psmsl.global-tide-gauge-sea-level

## Source ids

- psmsl.global-tide-gauge-sea-level

**Provider:** Permanent Service for Mean Sea Level (PSMSL), National Oceanography Centre

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://psmsl.org/data/obtaining/notes.php>

**Service root:** <https://psmsl.org>

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

- fetch_rlr_monthly_station

### Path templates

- /data/obtaining/rlr.monthly.data/\{station_id\}.rlrdata

**Parameter rules:** Future execution must be repository-constructed for one scientifically preselected numeric PSMSL Station ID and the RLR monthly representation only. The trusted implementation must substitute a canonical decimal station ID into the fixed path template and must not accept an arbitrary host, URL, path, headers, representation, filename or query parameters from a caller. Before enabling a probe/sample, freeze the station identity, confirm RLR availability, review the station documentation and data authority, and bind the PSMSL extraction/release identity. Metric data must not be silently substituted for RLR. Complete-dataset ZIPs and permanent year-end archives are authoritative secondary reproducibility infrastructure but are intentionally not executable paths in this first contract.

## Response contract

### Expected media types

- text/plain

**Format:** PSMSL RLR monthly semicolon-delimited station text: decimal year-month, monthly mean sea level, missing-day count and attention/QC flag.

**Scientific semantics:** PSMSL monthly RLR values are calendar-month mean relative sea level in millimetres, reduced to a station-specific Revised Local Reference datum using datum-history information supplied by the data authority. The decimal date is year + (month - 0.5)/12. Missing months inside the record are padded with -99999; an interpolated month uses missing-day count 99. Attention flag 001 means the associated documentation should be read, and 010 identifies mean tidal level content in a mean-sea-level series. RLR is generally the appropriate representation for time-series/trend analysis; Metric data are not an interchangeable fallback. Tide-gauge RLR observations are relative to local land and station datum, so values are not directly interchangeable between stations and do not by themselves define a storm-surge or tsunami event, hazard footprint, return period, damage/loss or insured loss.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `2097152`

**Retry policy:** bounded_backoff

**Rate limit notes:** No repository-specific request-rate assumption is made. Future execution must remain a single small preselected station-file request and must not turn the deterministic file service into bulk harvesting.

**Mutability notes:** Live station files reflect the current PSMSL database extraction and may change as source data, QC or datum history are updated. Every future receipt must bind retrieval UTC, numeric Station ID, RLR monthly representation, PSMSL extraction/release identity, response byte count and SHA-256. For release-stable bulk reproducibility, PSMSL's permanent year-end archives are preferable, but archive acquisition is outside this contract's executable path.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** PSMSL states that its data, products, archives, documentation and training information are free for all to use, and its referencing guidance asks users to cite the dataset and include the database extraction/retrieval date. This verifies a broad source-use statement but does not, in this review, establish a separate automated HTTP-service policy or an exact repository raw-byte redistribution ceiling. Commercial automation and raw persistence/publication therefore remain unknown and blocked until independently reviewed for the exact station/asset and intended repository scope.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://psmsl.org/data/obtaining/notes.php>
- <https://psmsl.org/data/obtaining/rlr.php>
- <https://psmsl.org/data/obtaining/complete.php>
- <https://psmsl.org/data/obtaining/year_end/>
- <https://psmsl.org/data/obtaining/reference.php>
- <https://psmsl.org/about_us/support_us.php>

**Notes:** Static access contract only. It selects one deterministic RLR monthly station file as the future bounded machine operation and records complete distributions/permanent year-end archives only as secondary reproducibility infrastructure. The current complete PSMSL distribution is stamped as extracted from the database on 2026-07-13, but this contract does not pin or acquire those bytes. No provider request, sample, ZIP, external byte, adapter or admission change is introduced. Before status can advance beyond documented_only, an independent review must freeze one scientifically justified Station ID and extraction/release identity, confirm the station's RLR/data-authority/QC semantics, and resolve the exact automated-service/persistence/redistribution scope.
