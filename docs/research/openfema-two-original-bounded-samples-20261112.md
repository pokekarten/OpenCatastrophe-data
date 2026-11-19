<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Two fixed original OpenFEMA provider API research receipts — 2026-11-12

**Scope and status:** two non-sensitive *original* research requests, no source/model admission, no bulk collection, no individual underwriting or claims decisions. The underlying canonical candidate sources remain in `landscape/` with `rights_review_status=not_reviewed`, `scientific_review_status=not_reviewed`, `admission_status=not_admitted`. A web service answering HTTP 200 is not a legal or scientific admission.

## Original terms (reviewed on 2026-11-12)

- [Original OpenFEMA Terms and Conditions](https://www.fema.gov/about/openfema/terms-conditions), especially **Secondary Use**, **Reidentification**, **Citing Data**.
- OpenFEMA usage is **solely for statistical research or as a reporting record**; do not reidentify persons or publish facts enabling reidentification.
- OpenFEMA observations must **not** determine any individual's rights or eligibility for benefits; a commercial insurer's automated decisions, claims denial, pricing or policyholder assessment are **not authorised** by this sample.
- The source has an obligatory non-endorsement statement in downstream reuse: **"This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA. The Federal Government or FEMA cannot vouch for the data or analyses derived from these data after the data have been retrieved from the Agency's website(s)."**
- Citation must name the **exact versioned endpoint** and access date/time; FEMA may withdraw access, and provider data can change after retrieval.

These are **custom OpenFEMA service-use conditions**, not an unconditional CC0 licence merely because the agency is federal. The programme-specific/research-only approval is narrower than a general commercial dataset grant.

## Tested provider requests and actual samples

Both live GETs were **already executed once** against the original `www.fema.gov` OpenFEMA API in this session, on 2026-11-12, with exact `$top=2`, 2 original records in each response. Research-only selected public columns were staged in the **private** Neon `insurance-risk-core.research.source_sample_v0`; no provider response body, personal identifier or claim/policyholder coordinates was committed into Git.

| Canonical source ID | Frozen API URL | Original response bytes | Original SHA-256 | Private Neon sample |
| --- | --- | ---: | --- | ---: |
| `fema.openfema.nfip-residential-penetration-rates.v1` | [NfipResidentialPenetrationRates v1, top 2](https://www.fema.gov/api/open/v1/NfipResidentialPenetrationRates?$top=2) | 938 | `90b88c623e37a41f49d218b037fb32bbc9e258fa07d7eb53132be7da290a1a6e` | 41 |
| `fema.openfema.disaster-declarations-summaries.v2` | [DisasterDeclarationsSummaries v2, top 2](https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$top=2) | 2098 | `ac55a377dd407f46778319b323622ed9f56a0130e8171833adfb333396eefab2` | 42 |

- The first dataset contains **county-level** aggregate National Flood Insurance Program residential penetration against an **NSI 2022** estimated building denominator. Some ratios can exceed 100% and are not software errors; this dataset **does not include private flood-insurance penetration**.
- The second dataset is an administrative **disaster declaration/declared-area catalogue**, not an event footprint, hazard severity, insured loss, observed damage or independent peril occurrence frequency.
- Both row-order snapshots are mutable: `$top=2` without source `$orderby` is a capability canary, *not* a deterministic historical sample selection. Exact original response SHA-256 and retrieval UTC identify the observed snapshot.
- The two samples are `research_only=true`, `model_input_approved=false`, `source_byte_persistence_authorized=false`: only selected original public row fields and derived context appear inside private research JSONB; the complete original response is not stored.

## Reproducible offline and explicit-live probe

`scripts/probe_openfema_fixed_public_v0.py` accepts **only the two fixed, versioned HTTPS requests above**. It has no arbitrary host/path, user-selected fields, paging, date overrides, cookies, credentials or response file output, and refuses to contact FEMA unless the operator supplies `--live`. It rejects redirects, malformed/oversized JSON, duplicate object keys, incompatible metadata version/request/row count, negative counts, non-finite rates and duplicate row IDs. It deliberately emits **only** source identity, byte count, SHA-256, high-level data quality flags and `model_input_approved=false`. All synthetic offline tests reside in `tests/test_probe_openfema_fixed_public_v0.py`.

Run offline synthetic tests:
```bash
python -m unittest tests.test_probe_openfema_fixed_public_v0 -v
```

Optional **manual** bounded new provider calls, after accepting the current OpenFEMA terms:
```bash
python -m scripts.probe_openfema_fixed_public_v0 --source fema.openfema.nfip-residential-penetration-rates.v1 --live
python -m scripts.probe_openfema_fixed_public_v0 --source fema.openfema.disaster-declarations-summaries.v2 --live
```

No scheduled retrieval or widening the general source API allowlist is introduced. The real API results above came from the original provider via an independent bounded read, not from the new Python runner. **The runner is not claimed to have itself executed a live provider request** in this PR.

## Neon read-only verification

```sql
SELECT sample_id, source_id, product_version, sample_kind,
       sample_sha256 = encode(sha256(convert_to(sample_json::text, 'UTF8')), 'hex')
           AS sample_hash_valid,
       research_only, model_input_approved
FROM research.source_sample_v0
WHERE sample_id IN (41, 42)
ORDER BY sample_id;

SELECT source_id, product_scope,
       commercial_cat_modelling, automated_api_access,
       internal_neon_source_sample, research_sample_count, admission_status
FROM research.source_rights_matrix_v0
WHERE source_id IN (
 'fema.openfema.nfip-residential-penetration-rates.v1',
 'fema.openfema.disaster-declarations-summaries.v2');
```

The product-specific private rights matrix stores **14 separate use-case decisions** for these two products. Commercial CAT modelling is `conditional` (**research/statistical reporting only**, no individual decisions). API automation and any wider bulk/reuse/distribution remain separately reviewable.

**Next steps:** independently review versioned FEMA API dataset-level lineage, product-specific retention, record types and privacy constraints; consider a source-specific `access/` contract if recurring automated execution becomes necessary; test joins with other administrative disaster data using aggregates only, with no policyholder/claims-level inference and no promotion to CAT model use.

## Follow-up: v3 high-sensitivity Claims/Policies safe metadata-only probes

The original **NFIP Redacted Claims v3** and **NFIP Redacted Policies v3** APIs are **not equivalent** to the two low-sensitivity v1/v2 public data products above.

**A live safety discovery:** Attempting `$top=0` produced a large default response, rather than zero records. It was rejected as oversized and not saved, and there was no attempt to decode/store claim or policy content. A request without a positive bound is unsafe for a capability canary. The corrected provider requests each use **exactly one** public, non-sensitive column and `$top=1`, with no user-controlled paging/filtering.

| Canonical source ID | Original exact tested GET | Returned | Private metadata sample | Original response SHA-256 |
| --- | --- | ---: | ---: | --- |
| `fema.openfema.nfip-redacted-claims.v3` | [v3 Claims – one yearOfLoss field](https://www.fema.gov/api/open/v3/NfipClaims?$top=1&$select=yearOfLoss) | 294 response bytes; metadata v3; one transient year field | **45** | `97265c34d1200f45f85db33da5456848abb63d70e4a4224aaeb873470fddedc2` |
| `fema.openfema.nfip-redacted-policies.v3` | [v3 Policies – one policyEffectiveDate field](https://www.fema.gov/api/open/v3/NfipPolicies?$top=1&$select=policyEffectiveDate) | 349 response bytes; metadata v3; one transient date field | **46** | `aced680b68a08d5d16d2dc814908f75cb00814a53e8f2d1add86988df186ee29` |

**The actual selected year/date values are deliberately not stored** in these two Neon metadata samples; no IDs, county/census geographies, claim payments, policy coverages, coordinates, transaction details or individual records are persisted. The summary contains only provider dataset identity/version, one selected field name, bounded response size and source SHA. Both are `sample_kind=public_metadata`, `research_only=true`, `model_input_approved=false`, and `source_byte_persistence_authorized=false`.

Product-scoped rights in the private source-use matrix are separately recorded for both v3 products. `internal_neon_source_sample=unknown` and `external_raw_redistribution=unknown`: an accepted **metadata-only** canary does not authorize persisting actual claims or policy rows. Commercial CAT use remains conditional on a separately reviewed statistical purpose and OpenFEMA's ban on individual entitlement/eligibility decisions. Programme vintage, data retention, deduplication, transaction semantics, privacy and derived use remain open.

A new [exact-source script](../../scripts/probe_openfema_nfip_v3_metadata_v0.py) supports manual opt-in **only** for these two one-field, positive-`$top=1` original routes. It must be executed explicitly with `--live`, emits SHA/shape only and refuses extra fields. The purely [synthetic tests](../../tests/test_probe_openfema_nfip_v3_metadata_v0.py) include regression cases for the dangerous `$top=0` fallback and unexpected PII-like source fields. No recurring GitHub Actions or automated bulk download is added; the Python runner was **not** itself executed live in this PR.

```bash
python -m unittest tests.test_probe_openfema_nfip_v3_metadata_v0 -v
```

These v3 one-column checks test API metadata/readability only, **not availability of a legally reusable claim/policy dataset**, nor any substantive insurance-loss/sample modelling or cross-table join. Full claim/policy data remain intentionally uncollected.

## All 707 source-record API coverage dashboard (private Neon, reproducible SQL)

This same session additionally applied `research.source_api_smoke_receipt_v0`, `research.source_api_coverage_v0` and `research.all_source_api_coverage_v0` to the private Neon database. The complete schema and two views are maintained in [SQL](../../sql/research_source_api_coverage_v0.sql), with **zero** provider payload storage or source admission by these receipts.

After the four original FEMA tests and the earlier bounded NOAA/European-source reads, **10** capability observations were staged: **9** parseable JSON/expected-shape smoke responses and **1** inconclusive NOAA SWPC response due to a malformed/truncated web transport capture. No provider outage is claimed for SWPC. The three earlier NOAA/FEMA v1/v2 real-source samples have receipts 6–8, the NFIP claims/policies v3 metadata checks have receipts 9–10. Provider SHA-256 and original data extracts, when present, are separately recorded in `research.source_sample_v0`.

The full `research.all_source_api_coverage_v0` view joins **692** discovery candidates and **15** pre-existing admitted manifests. It maps the fixed WSV Dresden access-contract ID to the matching **admitted manifest**, rather than inventing a new landscape candidate. Current 707-record snapshot:

| Registry type | Records | Parseable bounded smoke | Inconclusive smoke | No matching direct bounded smoke |
| --- | ---: | ---: | ---: | ---: |
| Landscape candidates | 692 | 8 | 1 | 683 |
| Existing admitted manifests | 15 | 1 | 0 | 14 |
| **Total** | **707** | **9** | **1** | **697** |

**Crucial definition:** `not_tested` means **no bounded original HTTP request receipt is present in this table**, not an API failure, no source licence, or no other prior research. Some of the 707 sources are DOI catalogues, website portals, static file products or restricted providers and **have no API that should be blindly probed**. Existing manifest admission is pre-existing and not newly revalidated. A smoke probe never grants new source rights, model admission, or persisted raw-provider bytes.

The `$top=0` large-response hazard discovered on both v3 endpoints is intentionally rejected in [the offline synthetic tests](../../tests/test_probe_openfema_nfip_v3_metadata_v0.py). To expand beyond these fixed operations, review the exact source's live API terms, access contract, sensitivity and acceptable byte limit first.
