<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# First-party original DWD CatRaRE W3 / T5 2026.01 replay — 2026-11-13

**Status:** both original-provider HTTPS Range requests **succeeded** on the trusted GitHub Actions `main` runner following [PR #1546](https://github.com/pokekarten/OpenCatastrophe-data/pull/1546), squash-merged as commit `cf22ff485271d4d681a9b87f766440c2986bd13e`.

Authoritative public evidence: [GitHub Actions run #43480623017](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43480623017), successful original-source job `132075848823`. This was a **push to `main`**, not a PR synthetic test nor an external intermediary response. The old GitHub runner had earlier checked both exact original CSV prefix digests; the reviewed new contracts bind the expected historical prefixes and the actual first-party response with an immutable original source access contract SHA.

| Exact source | W3 Eta v2026.01 | T5 Eta v2026.01 |
| --- | --- | --- |
| Original total CSV size expected | 12,410,601 bytes | 17,208,653 bytes |
| Original request | `GET`, `Range: bytes=0-4095` | `GET`, `Range: bytes=0-4095` |
| Required original HTTP status | `206 Partial Content` | `206 Partial Content` |
| Original response verified | 4,096 bytes | 4,096 bytes |
| Original response SHA-256 | `a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12` | `5dc4b6f0dac14f0a442103b78c16f647556bd870898aabff6d9f62aa4534f542` |
| Original request SHA-256 | `cdafab234e55ec4e5800180faad0c3e5876c367c76b3f13942a6bf2573ce841c` | `e838175fe38591cc5abf2e196fd53e2f8a21e3482170e21553825e625c907815` |
| Canonical access contract SHA-256 | `819de3fd2a30096915f36b9adb6538cb37fad78cfc2b21507aecae6b3c848d52` | `2d342e8db510692bcc6ad7a11881fc41a3992d9738a4a64f2baa16169ba02fa4` |
| Probe code SHA-256 | `d5ffbe69e3f790da41be11e7b64b4032a23f0a4a35c3330e8e7fdaf6220dd878` | same |
| Observed UTC | `2026-11-13T18:14:13.418748+00:00` | `2026-11-13T18:14:14.096842+00:00` |
| CSV original structural proof | 67 distinct columns, first three complete events | 67 distinct columns, first three complete events |
| Original entire source hash verified | **No** | **No** |
| Original event polygons/CRS verified | **No** | **No** |
| CAT model input admitted | **No** | **No** |

**Independent proof from original runner code:** source hash, original declared source total, raw 4096 bytes, versioned `CatVersion`/first three `KEY_FIELD` events, HTTP status 206, matching `Content-Range`, no content-encoding and exact approved source access contract are mandatory conditions of the success exit code. GitHub runner log explicitly contains the original SHA-256 digests, UTC, source IDs, source-code SHA and access-contract SHA. The executed source code was reviewed before merge. No original provider body was persisted in Git, Neon or an Actions artifact.

## Neon evidence design: do not falsify v0 receipts

The older `research.source_api_smoke_receipt_v0` ledger is reserved for intermediary metadata observations, with a database **CHECK constraint requiring `strict_repository_runner_executed=false`**. Never rewrite or bypass that guard. Separate schema:
- `research_runners/sql/insurance_source_strict_original_probe_v1_schema.sql`: small additive research-only table with checked GitHub main commit, run/job identity, exact response SHA/bytes, contract/code SHA, no original bytes and no model approval
- `research_runners/sql/insurance_source_strict_original_probe_v1_seed.sql`: exactly two idempotent, metadata-only first-party receipts, no provider bytes, no personal data
- `research_runners/sql/insurance_source_strict_original_probe_v1_verify.sql`: read-only compare to existing older samples #26 and #27; both original 4KiB SHA hashes must agree

The creation and insertion of these two receipts are **not** a dataset manifest, nor a scientific completeness claim. For model input, full file hash and counts, original FileGDB EventZone geometries, event-selection method, UTC and source lineage with RADKLIM-RW v2017.002 still need independent checking. W3 and T5 are **not independent precipitation catalogue samples**.

The next action for the larger 18-probe reviewed-suite is still a **manual `workflow_dispatch` from a trusted reviewed main ref**. This two-probe source-specific main job does not claim that the central `reviewed_18` suite ran.
