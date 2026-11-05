<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2026 — TED procedure UUID lineage: competition versus award

**As of 2026-11-05.** Research provenance only; not an insurer exposure or policy claim.

## Why this matters

WBM's [competition notice 286307-2026](https://ted.europa.eu/en/notice/286307-2026) and [contract-award notice 668506-2026](https://ted.europa.eu/en/notice/668506-2026) both discuss nine pure commercial properties and German industrial property insurance, yet **matching buyer, title, internal buyer tender reference and risk description is not proof of the same legal procurement procedure**. Web-index notice UUIDs may differ while a shared procedure UUID identifies a consistent procedure. The [official eForms schema](https://docs.ted.europa.eu/eforms/latest/schema/notice-information.html) distinguishes:

- **BT-701 — Notice Identifier:** root `cbc:ID[@schemeName='notice-id']`. Each notice normally has its *own* UUID.
- **BT-04 — Procedure Identifier:** root `cbc:ContractFolderID`. This globally unique UUID is the primary identity for connecting competition and result eForms notices. Identical BT-04 IDs are strong direct same-procedure evidence; **different BT-04 IDs are a substantive conflict**, even if the same WBM buyer, internal identifier, title or insurer references appear.
- **BT-22 — Internal procedure identifier:** optional `cac:ProcurementProject/cbc:ID[@schemeName='InternalID']`, chosen by the buyer, useful for discovery but **not a substitute for BT-04**.
- **OPP-090 — Previous Notice:** `cac:NoticeDocumentReference/cbc:ID[@schemeName='ojs-notice-id']` can provide an explicit reference between differently numbered publications, separate from the BT-04 identity. Unrecognized ID schemes are never silently interpreted as publication references. See [official eForms notice linking FAQ](https://docs.ted.europa.eu/home/eforms/FAQ/index.html) and [previous-notice reference](https://docs.ted.europa.eu/eforms/latest/schema/procedure-lot-part-information.html).

## Exact-original, fail-closed procedure lineage gate

[The read-only source-pinned runner](../../research_runners/ted_wbm_2026_procedure_lineage_v0.py) requires the **complete official original bytes** of both notices:

| Notice | Expected root | Reviewed original bytes | Reviewed original SHA-256 |
| --- | --- | ---: | --- |
| Competition 286307-2026 | `ContractNotice` | 41,307 | `54c0c84b379a9629f3e5774245ca763f66159e2cf45704ba985589202adcf9a1` |
| Result 668506-2026 | `ContractAwardNotice` | 21,837 | `7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78` |

It separately applies the reviewed competition [source pin](../../research_runners/ted_wbm_2026_competition_original_preflight_v0.py), award [pin](../../research_runners/ted_berlin_insurance_original_xml_preflight_v0.py), and the already proven WBM [three-company awarded contract role graph](../../research_runners/ted_wbm_original_award_graph_receipt_v0.py). Only then does it compare the two root procedure and notice UUIDs, buyer internal IDs and explicit previous publication references.

The output has one of three precise classifications: `SAME_PROCEDURE_CONFIRMED_BY_BT04`; `DIFFERENT_BT04_BUT_EXPLICIT_EARLIER_PUBLICATION_REFERENCE_REVIEW`; or `DIFFERENT_BT04_NO_DIRECT_SAME_PROCEDURE_PROOF`. **Neither of the two differing-ID states implies that the earlier WBM terms can automatically be inherited by the later award.** A reference to a previous notice is a separate observation, and matching internal buyer IDs do not overwrite contradictory BT-04 UUIDs. No unsupported graph coalescing or automatic insurer model admission is performed. No raw XML is redistributed.

The [21 no-network regression tests](../../tests/test_ted_wbm_2026_procedure_lineage_v0.py) cover same/different BT-04 UUIDs, distinct BT-701 notice UUIDs, matching buyer internal references, explicit previous-publication references, malformed ID schemes/UUIDs, DTD, duplicate IDs and a synthetic source failing the immutable SHA-pinned live proof.

Run:

```bash
python -m unittest discover -s tests -p 'test_ted_wbm_2026_procedure_lineage_v0.py' -v
python -m research_runners.ted_wbm_2026_procedure_lineage_v0
```

## Interpretation and next step

Run the dedicated [TED GitHub workflow](../../.github/workflows/berlin-insurance-ted-original-xml-preflight.yml). The official XML source sometimes returns HTTP 202; PR workflows deliberately mark the external fetch advisory and do **not** count a green suite as proof of live BT-04 verification. Only a successful **pinned complete original replay** yields the UUID comparison. Retain the two procurement records separately unless both BT-04 procedure IDs match or a defensible explicit predecessor linkage is independently reviewed.

All confirmed September WBM awarded company relationships and BT-150 source percentage labels remain valid **for the September result publication only**, independently of whether the April competition is identified as the same BT-04 procedure. The quoted 30% lead / 15% participant and residual-share exception may **not** be assumed to govern the September result without resolving procedure lineage. Neither source establishes final policy inception, site allocation, building TIV, actual 50/40/10 coinsurance or ceded net exposure.

## Separate official TED Search API index fallback (not equivalent to original XML)

When `/en/notice/{publication}/xml` is temporarily unavailable (observed official HTTP 202), the dedicated [Search API candidate runner](../../research_runners/ted_wbm_2026_procedure_search_index_v0.py) can query **only** the original EU publisher `https://api.ted.europa.eu/v3/notices/search` for exact `286307-2026` and `668506-2026`, reading the documented source fields `procedure-identifier` (BT-04), `previous-notice-id-proc` (OPP-090), `publication-number`, `buyer-name`, and `notice-title`. The [official field list](https://docs.ted.europa.eu/ODS/latest/reuse/field-list.html) explicitly lists these field names. Requests have `checkQuerySyntax: false` so they **execute** rather than merely validate queries, and are bounded to two rows, exact notice, WBM buyer and insurance subject, one properly formed UUIDv4 value per document. The [22 no-network Search API tests](../../tests/test_ted_wbm_2026_procedure_search_index_v0.py) check source host, JSON/cardinality, publication, UUID, wrong roles and false provenance.

**Interpretation:** `INDEXED_SAME_BT04_REQUIRES_ORIGINAL_REPLAY` or `INDEXED_DIFFERENT_BT04_REQUIRES_ORIGINAL_REPLAY` are *provisional indexed clues*, not pinned original XML receipt. The Index API response is not treated as an original XML document. Publisher response SHA/bytes are recorded only as dated structured metadata receipts, not immutable TED original source pins; raw API responses are not printed or committed. The original-source validator remains the stronger gate and is necessary to confirm the exact published UUID.

## Observed official Search API result on 2026-11-05 — different procedure IDs

The live, exact-notice official publisher Search API call succeeded in [GitHub Actions run 42104879468](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42104879468). The **indexed procedure UUIDs differ**:

| Notice | Official Search API BT-04 | API JSON response byte count | API response SHA-256 |
| --- | --- | ---: | --- |
| 286307-2026 (April competition) | `7df98c35-4cae-41ff-8385-141125426a4a` | 7,127 | `1998036c56be615eeba7a7b2c518a428fb544b802b5d079076319af4f27aa844` |
| 668506-2026 (September award) | `0988b2e4-9489-4b3b-9487-cd3a2a624cf5` | 7,127 | `565057622b9d69bbd48aef73ec74a17f35e80500bf86dc35ca99427c1d2e1829` |

The `previous-notice-id-proc` index field did not return April's `286307-2026` as an explicit predecessor of the September award. **This negative search field is not proof that no reference exists in the XML.** The comparison is recorded in a [source observation](../../research/observations/ted_wbm_2026_search_bt04_lineage_observation_v0.toml) with 8 anti-merge tests.

**Corrected scientific inference:** two distinct official *indexed* BT-04 values are strong evidence **against automatically treating the publications as one procedure**. Do not imply that the April 30% lead, 15% follower and residual below-minimum exception governed the September HDI/Helvetia/R+V award. The April terms and exceptions remain accurate for April's own verified source, while the September three company-contract edges and 50/40/10 *business identifier texts* remain accurate for September's own verified source. Their connection remains under review, not assumed.

The exact-head original-XML two-source comparison attempted in that run was **blocked by TED HTTP 202 for the April competition**, so the two BT-04 values are *currently confirmed only in official Search API metadata*, not in a fresh simultaneous exact-original replay. Their dated API response SHA values are audit receipts, not immutable publisher original XML hashes. A future original re-fetch may confirm or contradict the indexed UUID values; treat the raw source as decisive.

