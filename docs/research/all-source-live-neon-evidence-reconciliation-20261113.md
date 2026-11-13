<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Live source evidence reconciliation: 707 registry entries × Neon receipts (2026-11-13)

## Purpose

The canonical GitHub source inventory and the separately operated
insurance-risk-core research database track different things. The Git
inventory contains a **review snapshot**, while Neon has newer original-source
metadata/value receipts, bounded API observations and **product-scoped**
use-case rights. Comparing only `actual_sample_state` or only API logs gives
misleading "all candidates untested" conclusions.

This PR adds **one READ-ONLY PostgreSQL SELECT**
[`sql/research_all_source_evidence_decision_queue_v0.sql`](../../sql/research_all_source_evidence_decision_queue_v0.sql)
which recombines these evidence planes without changing any source status or
contract. It is an operational backlog, **not a licence or scientific
admission engine**.

## Reproducible read-only execution

Run in the authorized separate insurance-risk-core **Neon** research database,
never a public database or Pokémon schema. Run as a role with SELECT-only
permissions and export the result to a **private** operations workspace.
The query never downloads provider data, touches public Git sample files,
ingests source raw bytes, or writes any table or view.

```sh
# On an already configured private Neon psql connection:
psql -X -v ON_ERROR_STOP=1 \
  -f sql/research_all_source_evidence_decision_queue_v0.sql
```

The SQL returns a single row per **canonical inventory record** and includes
`record_type`, `source_registry_path` and `source_id`. In the verified
2026-11-13 snapshot, there are **707 records** (692 landscape candidates,
15 previously admitted manifests), but only **706 distinct source IDs**.
The source `copernicus.cems.gfm.v4.1.1` is intentionally present once as a
landscape candidate and once as a manifest. Do not count joined rows as
distinct providers or add samples twice for this source. The original
inventory is left joined to **per-source aggregated** evidence, so a source
with 15 receipts or seven product-rights decisions still contributes just
one result row for each register record.

The private Neon query was executed directly against the existing schema and
returned **707 result rows**, with the following *record-level* triage
distribution:

| Next-action gate | Entries | Meaning |
| --- | ---: | --- |
| `P1_retest_provider_with_trusted_runner` | 1 | Last external observation inconclusive (NOAA SWPC intermediary); other historical Actions may have verified the source separately |
| `P1_review_bounded_first_source_sample` | 1 | JRC Global Surface Water V1.5: data reuse recorded as allowed, but still **no private Neon original sample** or vetted automated host terms |
| `P2_reconcile_candidate_snapshot` | 5 | Private samples were recorded after the candidate-only `not_collected` snapshot |
| `P2_review_native_observation_sample` | 8 | Some research sample/preview evidence, no source-native observed-values sample in this table |
| `P2_scientific_native_sample_validation` | 11 | Research value evidence exists, independent scientific and consumer admission still open |
| `P3_review_rights_and_exact_access` | 653 | Rights/access remain unresolved at the general registry level; not a claim of commercial prohibition |
| `P4_commercial_use_restricted` | 10 | Product/permission restrictions, country and provider scope must be reviewed |
| `P5_commercial_use_prohibited` | 3 | Current default commercial use disallowed; seek separate licence before use |
| `P6_existing_manifest_validate_separately` | 15 | Historical manifest admission is kept distinct from newly tested source sample and model permissions |
| **Total** | **707** | One row per canonical register record |

At the same snapshot:

- **74 samples from 38 distinct IDs** existed in
  `research.source_sample_v0`; all **74 JSONB sample SHA-256** checks passed.
  This is **not** proof that full provider-source binaries are persisted or
  that all 74 original external-response hashes were independently verified
  in the GitHub trust boundary.
- The separate smoke-receipt table held **21 receipts from 15 IDs**, of which
  **20 marked successful**, **one inconclusive**, and **zero originated in the
  repository's strict trusted GitHub runner**. Source data validated in
  historical GitHub Actions may be absent from this table: do not mislabel
  those as "never tested" or "provider down".
- Rights ledger had **121 use-case entries for 17 source IDs**. For example
  JRC GSW has multiple product-specific review scopes; sum of rights rows is
  not number of legally clear datasets.
- All private `research.source_sample_v0` rows remain
  `model_input_approved=false`. Existing *metadata-only* manifest status
  is not equivalent to source-scoped model-data admission.

## Fail-closed interpretation

- `sample_sha256` verifies **Neon JSONB summary integrity**, not the raw
  source URL or original asset ZIP/TIFF checksum. The original provider
  digest is a different field with a different scope.
- `strict_runner_receipts=0` means only that the private **Neon smoke
  table** has no strict-GitHub-proven receipts; it is not a full scan of all
  GitHub Actions runs, some of which have their own original-provider proof.
- `native_or_observed_value_samples` is the existing
  `sample_kind=observed_values` classification. It may denote an aggregate
  raster class histogram, original label dictionary or source-record prefix;
  it **does not** prove policy-level insurance exposure, loss predictions,
  hazard calibration, independent validation or consumer admission.
- `scoped_commercial_results` and `scoped_api_automation_results` are
  clearly scoped to rights **product_scope** and **use_case**; never promote a
  source from these lists to a universal commercial automation allowance.
- `candidate_snapshot_stale=true` flags existing source samples that
  contradict a candidate-only `actual_sample_state=not_collected`. The
  query **does not** overwrite original candidate source records, as the
  larger original sample may still be metadata-only.
- The workflow's separate `reviewed_18` manually-dispatched live runner
  remains the required trust gate for those fixed probes. This SQL never
  dispatches it, modifies the 18 allowlist, or requests secrets.
- Priority tags identify **review work**, not a command to execute
  unreviewed HTTP requests. Before each live probe, check fixed request
  path/host, provider terms, rights, source byte scope and API rate policy.

## Offline protection

```sh
python -m unittest tests.test_research_all_source_evidence_decision_queue_v0 -v
```

The test file checks that the SQL stays one SELECT-only statement, joins all
four research evidence registers without multiplying by receipt/right rows,
recognizes the Dresden WSV API-source alias, validates JSONB sample digests,
does not confuse samples with original provider bodies, and preserves the
non-commercial/unknown-rights gates. Neither test nor SQL has database
credentials or makes external provider requests.

**Next:** inspect individual P1/P2 sources (especially the corrected JRC GSW
Occurrence, NOAA SWPC trusted-runner retest and eight metadata-only sources);
review legal automation and original byte/CRS/unit completeness *before*
changing any source's science or admission status.
