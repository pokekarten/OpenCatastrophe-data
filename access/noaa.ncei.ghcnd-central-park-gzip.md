<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.ghcnd-central-park-gzip.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.ghcnd-central-park-gzip.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.ghcnd-central-park-gzip

## Source ids

- noaa.ncei.ghcn-daily

**Provider:** NOAA National Centers for Environmental Information (NCEI)

**Interface type:** http_file

**Status:** probe_ready

**Documentation url:** <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_station.txt>

**Service root:** <https://www.ncei.noaa.gov>

**Api version:** GHCN-Daily rolling station CSV, NCEI by_station original gzip distribution

## Access scope

- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- one_fixed_us_station_gzip_integrity_and_freshness_probe

### Path templates

- /pub/data/ghcn/daily/by_station/USW00094728.csv.gz

**Parameter rules:** Exactly one HTTPS GET without query/redirect/retry/caller-selected URL/path/range, fixed US GHCN station USW00094728; original response Content-Type application/gzip or reviewed gzip aliases. Maximum compressed original 12 MiB; maximum decompressed original CSV 24 MiB; up to 256 fully CRC-validated concatenated gzip members, non-gzip trailing data and invalid/partial members rejected. Require original station CSV schema, row-by-row element/day/flags validation and full hashes of both compressed original and inflated CSV. Compare latter with hash of verified NODD USW00094728.csv original obtained in workflow run 41501633985; report whether the exact original content is the same, dates and row counts. Never dump observation values or persist data to GitHub/Neon/model. NCEI may omit the eight-column CSV header; permit a validation-only exact GHCN header prefix in transient memory if the original first row is an exact eight-column fixed-station daily record. Do not alter original gzip or inflated CSV hash, persist normalization, or use normalized value as an original-source checksum.

## Response contract

### Expected media types

- application/gzip
- application/x-gzip
- application/octet-stream
- binary/octet-stream

**Format:** One complete NCEI provider original gzip object that may contain up to 256 concatenated RFC-1952 gzip members, each verified for stream integrity and CRC containing the eight-column USW00094728.csv station history. Exact raw gzip bytes SHA256 and decompressed station CSV SHA256, with all original CSV rows validated and no transformed observations. Original NCEI may be headerless; validate a temporary in-memory header-prefixed view while recording untouched original inflated CSV SHA and a separate header-normalized comparison SHA.

**Scientific semantics:** A single U.S. GHCN station is a technical research sample. Data can be revised without versioned snapshots; a more recent file date or later observation does not prove climatological homogeneity, completeness, scientific QA or worldwide model relevance. Original OBS_TIME 2400 remains a native non-normalized token. Source documentation may apply WMO Resolution 40 restrictions to data supplied by non-U.S. countries; this reviewed contract covers only the fixed U.S. Central Park object, and MUST NOT be generalized to non-U.S. stations or commercial cross-border reuse.

## Operational constraints

**Timeout seconds:** `60`

**Max probe bytes:** `5242880`

**Max sample bytes:** `12582912`

**Retry policy:** none

**Rate limit notes:** One anonymous bounded full object GET for fixed U.S. station after workflow review only; PR validation offline; no retries, discovery, pagination, bulk, mirrors, station IDs chosen by caller or scheduled ingestion. Generic source validator max_probe_bytes is 5 MiB; max_sample_bytes is an independent 12 MiB compressed source sample cap; 24 MiB decompressed cap is enforced by script. All members are validated individually and against a shared 24 MiB inflated cap; external junk remains rejected.

**Mutability notes:** Rolling object: record exact retrieval UTC, compressed and uncompressed whole-byte SHA256, original compressed/uncompressed lengths, source Last-Modified/ETag where well-formed, first and last observation, nonempty source/measurement/quality flags, native 2400 count, comparison to fixed 2026-11-02 NODD research hash. No atomic station-to-version binding or publication timestamp beyond provider headers.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://www.ncei.noaa.gov/archive>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** NCEI's archive licensing policy describes NOAA/Federal source data as public domain in the U.S.; this bounded contract fetches ONLY U.S. station USW00094728 and does not redistribute original bytes. NOAA's GHCN documentation also states some non-U.S. data have WMO Resolution 40 commercial/re-export restrictions, so the separate global GHCN access contract remains fail-closed and no global commercial admission follows from this US sample. Do not imply NOAA endorsement or unmodified government attribution for transformed data. The distinct NOAA NODD distribution's published CC0 license is NOT blindly applied to every upstream NCEI contribution.

## Probe contract

**Mode:** provider_specific

**Operation:** one_fixed_us_station_gzip_integrity_and_freshness_probe

**Requires credentials:** `false`

### Expected evidence

- Exact single HTTPS 200 from www.ncei.noaa.gov with reviewed gzip MIME; no redirect, compression wrapper, status 206, oversized raw gzip or appended gzip data.
- Bounded streamed inflation to at most 24 MiB, original gzip and normalized CSV whole-body SHA-256, original byte lengths, U.S. station ID, all rows validated with NOAA M/Q/S flags.
- First and last observation dates, row count, NODD 2026-11-02 historical verified 16,003,495-byte uncompressed-SHA comparison, explicit freshness gap rather than invented currency.
- No raw bytes persisted, no per-observation values printed or Neon/model admission; no rights or scientific claims for global GHCN.
- Original gzip member count (up to 256), every member checked for trailer CRC and valid deflate; concatenation is allowed only if every member is valid; arbitrary trailing bytes forbidden.
- Explicit original-header-present flag and separate original inflated CSV SHA versus transient header-normalized comparison SHA; no fabricated provider bytes or loss of first headerless source record.

**Implementation decision:** build_adapter_now

**Reviewed at:** 2026-11-02

## Evidence urls

- <https://www.ncei.noaa.gov/archive>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_station.txt>
- <https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/USW00094728.csv.gz>
- <https://www.ncei.noaa.gov/pub/data/cdo/documentation/GHCND_documentation.pdf>
- <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41501633985>

**Notes:** Exact NCEI 4 KiB original gzip HTTP range sample was externally reachable on 2026-11-02 with application/gzip MIME. It has not yet received the full-object script-and-byte proof until merged workflow executes. The NODD original compared against is a pinned prior observation and can be stale: comparison result never asserts absolute freshness or that NCEI is the latest scientific archive. First live workflow on 2026-11-02, run 41503180775, failed closed because original gzip ended one validated member before full response end. The fix recognizes standards-compliant concatenated gzip members while preserving CRC, size, exact-source, original whole-body hash and model-admission gates. Reviewed main gzip run 41504022738 reached CSV semantics and failed closed on absent expected eight-column CSV header. NCEI distribution can carry a headerless record stream. Adapter now recognizes only an exact eight-field USW00094728 first source record and uses a transient validation header, preserving the source original gzip and decompressed CSV SHA unmodified.
