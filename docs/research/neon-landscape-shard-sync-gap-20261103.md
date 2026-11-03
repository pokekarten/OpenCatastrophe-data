<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GitHub landscape shard vs CAT-only Neon registration gap (2026-11-03)

**Snapshot identity:** Public `pokekarten/OpenCatastrophe-data` main at commit
`012f1290121e2a795826748357e692e0007e12d0` (read-only GitHub
contents listing under `landscape/`), independently compared with Neon
project `insurance-risk-core`, database `insurance`, **default branch**
`main`, via an explicit read-only SQL query. No source rows imported,
database structure changed, secrets exported, or scientific rights granted.

## Verified difference

| Registry object | Count |
| --- | ---: |
| Canonical GitHub `landscape/sources*.json` shards | **61** |
| Neon `registry.source_record` landscape-candidate shard receipts | **41** |
| GitHub shard paths missing from Neon | **20** |
| Shared paths with changed original Git blob SHA | **0** |
| Neon landscape receipt paths absent from GitHub | **0** |
| Neon landscape raw-source admissions | **0** |

These are **files/shards**, not 61 unique dataset providers or 20 automatically
usable source datasets. A shard may list dozens of provider products. All
existing Neon landscape receipts remain non-admission research metadata.

### Exactly 20 missing canonical JSON paths

- `landscape/sources-air-verisk.json`
- `landscape/sources-cede-oed-tools.json`
- `landscape/sources-global-deep-research-20261102.json`
- `landscape/sources-global-event-geocoding-infra-20261103.json`
- `landscape/sources-global-insurer-registers-20261102.json`
- `landscape/sources-global-observation-gaps-20261102.json`
- `landscape/sources-gvp-votw-wfs-v5-4-20261102.json`
- `landscape/sources-monitoring-repo-upstreams-20261102.json`
- `landscape/sources-nasa-gfwed-fwi-v2-20261102.json`
- `landscape/sources-nasa-opera-dswx-s1-20261102.json`
- `landscape/sources-natural-earth-public-domain.json`
- `landscape/sources-nfip-penetration-2026.json`
- `landscape/sources-peer-cat-repositories-20261102.json`
- `landscape/sources-regional-loss-climate-hazard-20261102.json`
- `landscape/sources-transclima-compound-cat-20261102.json`
- `landscape/sources-usgs-3dep-s1m-20261102.json`
- `landscape/sources-validation-functions-exa-20261102.json`
- `landscape/sources-wfp-chirps-gefs-forecast-20261103.json`
- `landscape/sources-worldmonitor-upstream-20261102.json`
- `landscape/sources-worldwide-cat-data-20261102.json`

## Reproduce without privileged repository access in the checker

Export only the public GitHub **contents metadata** (JSON objects with
`path`, `sha`, `type`) at the pinned commit:

```text
https://api.github.com/repos/pokekarten/OpenCatastrophe-data/contents/landscape?ref=012f1290121e2a795826748357e692e0007e12d0
```

On the separately connected CAT-only Neon database, export the **metadata
columns only** via a read-only statement:

```sql
SELECT source_key,source_id,classification,git_path,git_blob_sha,
       admissible_for_raw
FROM registry.source_record
WHERE git_path LIKE 'landscape/sources%.json'
ORDER BY git_path;
```

Never export `raw_metadata`, original provider bytes, credentials, claims,
customers or insurance company-level private rows. Run the offline comparison
on the two exported JSON arrays:

```sh
python scripts/audit_insurance_landscape_sync_v0.py \
  --github-inventory /private/github-landscape-contents.json \
  --neon-export /private/neon-landscape-records.json
python -m unittest tests.test_audit_insurance_landscape_sync_v0 -v
python scripts/check_all.py
```

Exit 2 = manual review required (missing paths, drift, wrong type/identity,
unexpected raw admission); 1 = invalid inventory; 0 = path/blob identities
match. Even exit 0 **does not** allow automatic import or model admission.

## Proposed controlled reconciliation (not yet executed)

1. Pin the current `main` commit again and repeat this comparison immediately
   before any proposed staging; the list may grow as other agents merge PRs.
2. For each missing shard independently validate canonical JSON,
   source-candidate uniqueness, generated Markdown parity, rights/science
   fields and exact immutable Git SHA-1 blob. Reuse existing
   `landscape_file:<stem>` source-key and `sources-<...>` source-ID semantics.
3. Prepare metadata-only **append** receipts in an isolated Neon branch, with
   unchanged explicit `admissible_for_raw=false`. Do not overwrite existing
   blob identities or treat a renamed source as a new independent provider.
4. Execute negative tests (duplicate shard, wrong hash, unexpected rights
   admission, changed Git base), obtain review, and only then discuss a
   controlled production metadata-sync transaction. Source rights or scientific
   model inputs require **separate** approvals; syncing this catalogue
   cannot perform provider downloads or grant CAT/NextGen model use.

The earlier `scripts/audit_insurance_access_sync_v0.py` covers a **different**
namespace: `access/*.json` contracts. This script focuses on the
`landscape/sources*.json` shard namespace and must not change access status,
source contract revision history or any existing source research classification.
