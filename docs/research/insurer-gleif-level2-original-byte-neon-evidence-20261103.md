<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Verified insurer consolidation evidence: four official GLEIF source bytes (2026-11-03)

**Read-only evidence and technical research candidate, not authorised Neon group-relationship insertion, regulatory insurance-group membership, beneficial ownership, property exposure or CAT model admission.**

## Acquisition and source limits

On **2026-11-03**, four precise GLEIF public API URLs were fetched directly as **original HTTP response bodies** (`application/vnd.api+json`) with forced fresh retrieval. Local deterministic SHA-256 implementation was checked against the canonical `abc` test vector before hashing the returned original bytes. All four responses carried `meta.goldenCopy.publishDate = 2026-11-03T00:00:00Z`. The bytes themselves were **not committed** to GitHub or copied into Neon, only their exact lengths, source URLs, decoded relationship classes / exceptions and digests were recorded below.

| Official GLEIF source | Response bytes | SHA-256 of original HTTP body | Observed source fact |
| --- | ---: | --- | --- |
| [E+S Rück: direct parent](https://api.gleif.org/api/v1/lei-records/529900UCN37OZCXGVW88/direct-parent-relationship) | 1295 | `88a2204b3721a1916b36a1f0df390c8b7a5c0c1ca5551abb1194bd7e1017af9c` | `529900UCN37OZCXGVW88` directly consolidated by `529900KIN5BE45V5KB18`, relation `ACTIVE`, registration `PUBLISHED` |
| [Hannover Rück: direct parent](https://api.gleif.org/api/v1/lei-records/529900KIN5BE45V5KB18/direct-parent-relationship) | 1295 | `2ecb0188bd2ef2ebb2f8cfeed757fffc17e29e81638b4910f1bde8eb12b89653` | `529900KIN5BE45V5KB18` directly consolidated by `5299006ZIILJ6VJVSJ32`, relation `ACTIVE`, registration `PUBLISHED` |
| [Munich Re: direct-parent reporting exception](https://api.gleif.org/api/v1/lei-records/529900MUF4C20K50JS49/direct-parent-reporting-exception) | 531 | `df25b9584023978cb55ac6386d71e35ecd32a0071940453992fed961425008de` | `DIRECT_ACCOUNTING_CONSOLIDATION_PARENT` / `NO_KNOWN_PERSON`; **no parent LEI asserted** |
| [SCOR Global Reinsurance France: direct-parent reporting exception](https://api.gleif.org/api/v1/lei-records/549300KCPG3666EE4546/direct-parent-reporting-exception) | 533 | `a45bc039db8eae386f59bae7a570eacc562e6c4c14bb87882d85e44a20b2c84c` | `DIRECT_ACCOUNTING_CONSOLIDATION_PARENT` / `NON_CONSOLIDATING`; **no parent LEI asserted** |

These are direct accounting-consolidation relationships as defined by [GLEIF RR-CDF 2.1](https://www.gleif.org/en/lei-data/access-and-use-lei-data/level-2-data-relationship-record-rr-cdf-2-1-format). They do **not** measure shareholding, beneficial ownership, insurance licensing, group solvency perimeter, company catastrophe TIV, underwriting portfolio, claims or treaties. An exception must never silently be turned into a brand-based parent edge.

The repository already has an existing source validator and offline synthetic regression in `scripts/gleif_level2_relationship_pilot.py` / `tests/test_gleif_level2_relationship_pilot.py`. This work **reuses** the same precise LEI relationships and exceptions, supplying a fresh original-body receipt and independent current Neon matching, rather than inventing a competing model or blindly reusing October source status.

## Independent live Neon `main` read-only result

The newly committed exact-source query [`research_runners/sql/insurer_gleif_level2_original_receipt_neon_readonly_v0.sql`](../../research_runners/sql/insurer_gleif_level2_original_receipt_neon_readonly_v0.sql) was executed directly against **`insurance-risk-core` / `insurance` / Neon main** on 2026-11-03:

| Official research observation | Verified GLEIF LEI legal identities found | Result |
| --- | --- | --- |
| E+S Rückversicherung AG → Hannover Rück SE | 1 exact verified child, 1 exact verified parent | `RESEARCH_EXACT_GLEIF_ACCOUNTING_LINK_REVIEW_REQUIRED` |
| Hannover Rück SE → Talanx Aktiengesellschaft | 1 exact verified child, 1 exact verified parent | `RESEARCH_EXACT_GLEIF_ACCOUNTING_LINK_REVIEW_REQUIRED` |
| Munich Re direct-parent exception | 1 exact verified child, **0** parent identities asserted | `BLOCKED_GLEIF_REPORTING_EXCEPTION_NO_PARENT_EDGE` |
| SCOR Global Reinsurance France direct-parent exception | 1 exact verified child, **0** parent identities asserted | `BLOCKED_GLEIF_REPORTING_EXCEPTION_NO_PARENT_EDGE` |

All four checks returned `existing_neon_relationship_rows = 0`, `regulator_insurance_group_membership_verified = false`, `materialisation_authorized = false`, `neon_written = false` and `model_input_approved = false`. No database writes or new organisations were performed.

The strict join uses **both** endpoints' previously verified `GLEIF_LEI` and `entity.organization.identity_status='verified'`. It refuses multiple matches, missing LEIs, self-relations and reporting exceptions. A matching group hint, company branding or near-match is never considered legal evidence. These two exact candidate accounting edges are materially more useful than unreviewed `organization_candidate.group_hint` text, but still require explicit governance before entry into a relationship table.

## Next gate before any authorised database relationship write

1. Obtain sign-off for the legal relationship semantics: source-reported accounting consolidation is **not** identical to legal majority shareholding, a national insurer licence or parent company group supervision.
2. Check the destination schema's permitted `relationship_type` vocabulary and whether it can carry exact issuer, original-body SHA, source observation/publish date, relationship period and status; otherwise extend the schema **through reviewed migration** rather than losing evidence or overloading a generic `parent` label.
3. Recheck GLEIF legal entity validity, relationship registration and terms at the **time of any future write**, run uniqueness / cycles / chronology constraints and use the reviewed read/write access policy. At inspection, `registry.entity_feed` for `gleif_global` had `rights_status='cc0_verified'` but `automated_import_allowed=false`; do not circumvent this policy.
4. Maintain independent regulatory group membership and NAIC group/company-code source lines. The NAIC member-company source remains rights-held under [PR #1146](https://github.com/pokekarten/OpenCatastrophe-data/pull/1146), and unverified directory names under [PR #899](https://github.com/pokekarten/OpenCatastrophe-data/pull/899).

**Result:** Two source-dated, original-byte-hash-pinned, exact-LEI accounting parent-child **review candidates** and two explicit no-edge exceptions, proven on current Neon. No production relationships asserted and no model admission.
