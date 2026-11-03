<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Actual isolated Neon landscape metadata staging — executed 2026-11-03

**Scope:** independent CAT-only Neon project `insurance-risk-core`, database
`insurance`. Staging branch **`landscape-metadata-stage-20261103`**,
Neon ID **`br-raspy-cell-ba5j7191`**, created from default
`main` (`br-late-recipe-ba1cr8hc`). The project's **production main
was not modified**.

The original public GitHub repository tree was pinned to **main commit
`d156e9e654652717179286caaa8cdf14636f9db2`**. It had exactly
**62** canonical `landscape/sources*.json` shard files, of which
**41** already had exact matching metadata rows in the independent
Neon source registry and **21** were missing.

## Operations actually completed

1. Created the isolated Neon branch from its own CAT-only parent.
   Original branch state: **114** source records (58 access contracts,
   15 admitted-manifest identities, 41 landscape shards), no raw admissions.
2. For each of the 21 missing **metadata** JSON shards, retrieved its exact
   GitHub blob at the same pinned commit; checked the returned Git blob SHA
   against the pinned directory listing; parsed the original JSON and
   verified its `entries` collection and **every entry** had
   `admission_status=not_admitted`,
   `rights_review_status=not_reviewed`,
   `scientific_review_status=not_reviewed`.
3. Appended one `registry.source_record` **per missing shard** on the
   isolated branch only, in six bounded explicit insert batches. Each
   receipt has the verified original Git blob SHA, exact original tree
   commit, canonical file path and metadata JSON, and
   `classification=landscape_candidate`,
   `review_status=non_admission_discovery_only`,
   `rights_status=not_reviewed`,
   `admissible_for_raw=false`. No overwrites or deletions.
4. Independently refetched the pinned GitHub directory and compared all
   62 Git file/blob identities against the staged Neon registry.

## Observed checks (actual live database readbacks)

| Check | Isolated staging branch | Production main |
| --- | ---: | ---: |
| Landscape source-shard receipts | **62** | **41** |
| Newly staged, pinned 2026-11-03 main commit | **21** | **0** |
| Total registry records | **135** | **114** |
| Raw-admitted records | **0** | **0** |

Final stage-wide validation:
- **62/62** GitHub pinned paths exactly represented, **0 missing**,
  **0 stale** paths, **0 original Git blob hash mismatches**.
- **62 distinct** source keys and **62 distinct** shard paths.
- **430 source candidate entries across the 62 JSON shards**;
  these are research entries, *not* necessarily independent datasets
  or 430 valid model providers.
- **0** unexpected raw admissions; **0** nonstandard
  `not_reviewed` rights values or non-admission review statuses;
  **0** malformed 40-hex commit/blob identifiers.
- The SHA-linked identity of the original **114 records** was compared
  independently between production main and the staged branch:
  same 114 rows and exact same ordered full-row metadata fingerprint,
  `7e5a39f3dc0703b4f6fe38ab71534e23`
  (MD5 for controlled comparison only, **not** a provider authenticity proof).
- The live read-only verifier
  `research_runners/sql/insurance_landscape_metadata_stage_readonly_verify_v0.sql`
  returned: 62 shards, 21 newly staged, 41 historical, 430 entries,
  **zero** malformed IDs, status deviations or permission elevations.
  It also returned explicit `false` for production sync, raw provider
  acquisition and CAT model-input authority.

## Publication and production gate

**This branch is an internal metadata rehearsal, NOT a production data import
and NOT an original-data download.** Source rights, provider API/automation
terms, scientifically valid data versions, original geospatial file
integrity, event dependence, insurer-exposure and loss models remain
unreviewed or explicitly blocked.

Do not automatically promote the Neon branch into default `main`, and do
not infer model-run permissions from green checks. Before any potential
production metadata-only append, an independently reviewed migration must
(1) pin a fresh live GitHub and Neon snapshot, (2) verify exact 21 (or changed)
identities, provenance and source rights boundary, (3) preserve current
historical records byte-semantically, (4) run failure-injection on a second
staging branch, and (5) produce a post-transaction receipt for the 114
preexisting registry rows and absence of raw admissions.

The existing [GitHub register-comparison PR #1166](https://github.com/pokekarten/OpenCatastrophe-data/pull/1166)
was independently merged with all CI checks passing. Its offline comparator
is separate from this later live staging receipt and cannot itself write SQL.

**No Pokémon database, licensed vendor dataset, insurer original data,
financial treaty, exposure asset, simulation table or production CAT record
was touched.**
