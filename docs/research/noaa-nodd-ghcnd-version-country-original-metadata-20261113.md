<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA NODD GHCN-Daily: two exact rolling metadata objects — 2026-11-13

## Scope and acquisition boundary

This is one **bounded original-content metadata-only research check**, not a
global climatological source-admission or station-observation ingestion. The
existing reviewed contract
[`access/noaa.nodd.ghcnd-version-country.json`](../../access/noaa.nodd.ghcnd-version-country.json)
allows only the two frozen anonymous NODD S3 text objects below, up to 4,096
bytes each and never a configurable path or station archive.

On 13 November 2026 the two endpoints were independently fetched via an
external read-only web-content intermediary and returned as base64-encoded
source-body bytes. SQL in a separate insurance research Neon environment
decoded each body transiently, verified byte counts, parsed its exact
documented schema, and computed SHA-256 over the **decoded source body**.
Raw external response bodies, station observations, bulk files and
credentials were not committed to Git or saved to Neon.

**Critical limitation:** These are external intermediary observations;
neither original HTTP status/redirect chain nor the
`source-api-readiness.yml` reviewed strict runner was independently
verified by these receipts. Therefore this report is *not* a
`reviewed_18` workflow PASS claim.

| Exact original metadata object | Original bytes | Intermediary-returned response SHA-256 | Verified shape | Neon sample | API receipt |
| --- | ---: | --- | --- | ---: | ---: |
| `https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-version.txt` | 270 | `2d1a088b6e4fe0adba537e62f8b23309ebec71ae200aea0d973ab278972f6816` | One rolling update and one last fully reprocessed version | #74 | #21 |
| `https://noaa-ghcn-pds.s3.amazonaws.com/ghcnd-countries.txt` | 3,659 | `dfc325c0f89cc6f95e03ed5d4155a78b644ad28b044017c76fcb709df104df7f` | 219 valid, unique GHCN-native two-letter codes | #73 | #20 |

Both are `application/octet-stream` and contain strict UTF-8 text.
The original version document declares:

- Current rolling version: **`3.35-upd-2026111017`**.
- Last fully reprocessed version: **`3.35-por-2026103023`**.

These identify the NODD metadata's observed release state, **not** an
immutable snapshot of every NCEI station file. Both rolling and reprocessed
versions are `3.35`; the update timestamp is later than the full
reprocessing timestamp. This is newer than the older `3.34` example
recorded in the separately scoped NCEI general access documentation.
**Do not overwrite NCEI contributor-rights conclusions from a NODD metadata
observation.**

The country list has **219** nonempty, distinct, well-shaped code/name
lines. GHCN's two-character native country codes are **not ISO 3166**;
no ISO crosswalk was accepted. The country inventory is not evidence of
219 freely usable national climatology series.

## Data-rights and scientific boundary

The
[NOAA Registry of Open Data GHCN distribution](https://registry.opendata.aws/noaa-ghcn/)
describes a CC0 1.0 public NODD distribution. This receipt only applies
to the two exact NODD metadata files. Other NCEI services, station-level
contributor rights (including WMO Resolution 40 restrictions), republication
or commercial use of observations require separate reviews.

Both samples were entered in `research.source_sample_v0` as
`sample_kind=public_metadata`, with a **distinct canonical JSONB SHA-256**
and `model_input_approved=false`,
`source_byte_persistence_authorized=false`. The probe logs in
`research.source_api_smoke_receipt_v0` explicitly set
`strict_repository_runner_executed=false` and record the intermediary
limitation. No raw NOAA provider body was persisted.

Use this read-only SQL to verify the two durable summaries in the
designated insurance research database:

```sql
SELECT sample_id, source_id, sample_kind,
       sample_sha256 =
         encode(sha256(convert_to(sample_json::text, 'UTF8')), 'hex')
         AS canonical_sample_hash_ok,
       model_input_approved, source_byte_persistence_authorized
FROM research.source_sample_v0
WHERE sample_id IN (73, 74)
ORDER BY sample_id;
```

## Next strict gate

1. Run the existing `source-api-readiness.yml` in **manual**
   `workflow_dispatch` mode `reviewed_18`; inspect the exact
   `noaa.nodd.ghcnd-version-country` pair of original response digests
   emitted by `scripts/probe_ghcnd_nodd_version_country_v0.py`.
2. Record whether provider rolling version/byte content has changed, without
   treating changes as parser failures unless contract-level expectations are
   broken.
3. Evaluate the fixed reviewed U.S.-station CSV separately. Do not download
   global GHCN archives, infer weather-observation completeness, grant CAT
   scientific admission or treat GHCN-native country codes as ISO values.
