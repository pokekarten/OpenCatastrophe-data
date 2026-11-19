<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hazard Plain 2026-10: original provider-manifest read-only receipt

**Observed:** 2026-11-08T22:06:51Z from public GitHub Actions run
[42528564849](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42528564849),
job 128877465052, using the source runner
\`research_runners/hazardplain_202610_manifest_preflight_v0.py --official-live\`.

**Original manifest URL:** <https://files.hazardplain.org/r/2026-10/bulk/manifest.json>

## What was actually verified

The original publisher manifest JSON, not the underlying dataset bytes, was
fetched in memory on a public CI runner and passed the pin/lineage checks.

| Receipt field | Observed original manifest result |
| --- | --- |
| Original fetched manifest size | 59,508 bytes |
| Original fetched manifest SHA-256 | \`e04a707ab5b96a71e81f6ac29a584f3cb43acb5ec88c5e9669e092b5076434b4\` |
| Product and release | Hazard Plain / 2026-10 |
| As-of | 2026-09-30 |
| Build timestamp | 2026-10-17T19:57:41+00:00 |
| Selected table count | 3 |
| Selected table rows, byte sizes, SHA-256 | Confirmed *as fields of this manifest*, **not independently checked on source CSV bytes** |
| Selected table field names and source lineage | Matched selected manifest declarations |
| Real provider CSV/Parquet bytes acquired | **No** |
| Original source data admitted for model use | **No** |
| Independent empirical hazard/claim validation demonstrated | **No** |
| Modelled or observed insured losses calculated | **No** |

Separate ordinary CI executes synthetic-only negative cases for missing/
changed source metadata, inconsistent release date, duplicate JSON/file keys,
unsafe paths, untrusted redirect hosts, wrong file checksum claims and
upstream-source lineage changes. This source-receipt canary is explicitly
nonblocking because third-party reachability is not an offline scientific
contract. The actual live step succeeded in the cited run; do not infer that
future releases or raw source downloads will necessarily succeed.

## Scientific interpretation and controls

- **Do not treat Hazard Plain as new independent ground truth.** Its three
  tables are derived from previously known FEMA NRI 1.20, NOAA Storm Events,
  Census county adjacency and OpenFEMA NFIP multiple-loss property data.
  A researcher who calibrates to those same parent releases must not then
  label Hazard Plain's transformed outputs an independent validation holdout.
- The 58,176 county-hazard records contain modeled expected annual loss
  (AAL/EAL) and exposure context, not event-level ELTs/YLTs, policy coverage,
  insurer claims, or site-specific replacement values.
- The 45,853 outlier diagnostics are method-dependent flags with missingness,
  neighbor and storm-event evidence limitations. A flagged county is not an
  empirically established loss correction.
- The 3,232 county-level NFIP repetitive-loss aggregates describe a selected
  federal flood insurance population, **not** unique properties in an entire
  county, multi-peril claims, or insured spatial portfolios.
- Provider documentation claims CC BY 4.0 for its text and derived tables, but
  source-specific license/attribution, upstream OpenFEMA terms, and derived
  publication scope remain \`not_reviewed\`. No admission and no external bytes
  in Git.

## Next real acquisition gate

Review the exact distribution and upstream terms for each of the three
candidate products, then acquire the **exact three original provider CSV
files** in a rights-authorized external environment; compute SHA-256 and byte
size independently against the pinned original manifest. Only after that
check the actual row counts and numeric fields, establish correct county FIPS
vintage and modeled-versus-observed provenance, and define a bounded
experimental role that avoids training/holdout leakage.

The canonical source candidates and provider-claimed CSV digests are in
\`landscape/sources-us-hazardplain-nri-outlier-nfip-20261108.json\`; this
research note is historical evidence of the verified manifest acquisition,
not a second independently editable data-catalogue contract.
