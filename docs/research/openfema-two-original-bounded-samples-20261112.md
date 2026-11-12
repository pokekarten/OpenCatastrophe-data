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
