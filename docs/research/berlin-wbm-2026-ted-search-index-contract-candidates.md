<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2026: official TED Search index labels versus actual contract awards

**Date:** 2026-11-05. **Research only, not model exposure admission.** Complements the [original TED XML contract graph](berlin-wbm-2026-ted-eforms-winner-role-v0.md) and [original XML provenance receipts](berlin-insurer-ted-original-xml-preflight-20261105.md).

**Target:** [TED publication 668506-2026](https://ted.europa.eu/en/notice/668506-2026), WBM's September 2026 notice on nine pure commercial insurance objects. The original eForms bytes previously fetched once and pinned (21,837 bytes, SHA-256 `7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78`) are not reliably available for another complete fetch: TED has repeatedly replied HTTP 202. The official [Search API](https://docs.ted.europa.eu/api/latest/search.html) independently found exactly one matching official metadata record after fixing `checkQuerySyntax=false`.

## Material issue in the European Commission / Publications Office field list

The [official search field catalogue](https://docs.ted.europa.eu/ODS/latest/reuse/field-list.html) defines:

- **`winner-name`**: BT-500-Organization-Company with chain `OPT-300 → OPT-210 → OPT-310 → OPT-321 = OPT-320-LotResult[BT-142-LotResult='selec-w']`.
- **`winner-identifier`**: same index chain, BT-501 company identifier.
- **`winner-selection-status`**: `BT-142-LotResult`.
- **`contract-identifier`**: `BT-150-Contract`, **`contract-tender-id`**: `BT-3202-Contract`; **`contract-conclusion-date`**: `BT-145-Contract`.
- **`winner-decision-date`**: `BT-1451-Contract`.

**The index-defined winner name path does NOT itself require the `SettledContract → contract-tender-id` edge.** The eForms SDK separately calls `OPT-320-LotResult` the notice's *received tenders* (including underbidders); a selected `LotResult` does not make every received tender a winner. See the corrective source/contract graph in [PR #1369](https://github.com/pokekarten/OpenCatastrophe-data/pull/1369). A Search API value called `winner-name` can therefore only be treated as an **index-derived company candidate**, not an independently contract-verified underwriter. Similarly, returned contract identifiers and tender IDs are flattened **notice-level** fields with no per-row correlation to company names. Never zip the arrays by order, infer equal co-insurance percentage or multiply nine objects by three companies.

## New research-only official search preflight

The [candidate runner](../../research_runners/ted_wbm_contract_search_index_candidates_v0.py) asks the official `POST https://api.ted.europa.eu/v3/notices/search` for exactly publication `668506-2026`, with `limit=2`, `page=1`, published source fields, no syntax-only request and `onlyLatestVersions=false`. It reuses the [previous strict original publisher exact notice/buyer/title response checks](../../research_runners/ted_berlin_insurance_search_api_preflight_v0.py). The seven extra fields are explicitly allowlisted only for WBM's *award*, never the earlier Gewobag 2024 *competition/tender*. It deduplicates multilingual legal names, bounds field cardinality, length and nesting, rejects wrong-format tender references and unexpected result status, and separately reports *unpaired* company candidate names, contract-tender IDs, contract counts and dates.

Reproduction (no external raw data committed):

```bash
python -m unittest discover -s tests -p "test_ted_wbm_contract_search_index_candidates_v0.py" -v
python -m research_runners.ted_wbm_contract_search_index_candidates_v0
```

The 18 offline regression tests cover a selected result whose Search index shows a nonwinning bidder; missing fields; multilingual duplicates; invalid registration/name payloads; wrong notice/buyer/title; field/notice abuse; bogus contract-tender ID; bad status, excessive source values and nested JSON. Synthetic tests do not establish actual carrier roles; original raw TED JSON is never written to the repository or printed. Read public company candidate labels only as search suggestions. Identifier strings are never printed; counts are enough to indicate whether matching may be possible after separate official legal-entity verification.

**The live API workflow is advisory for PRs** because external publisher access can fail. A green CI means the parser is safe under test, *not* that the official API returned a usable value. Any independently obtained real receipt is separately documented with its response SHA and exact values, and no new insurer contract claim follows until the **original eForms `RES → CON → TEN → TPA → ORG` graph** has been re-verified against its pinned original XML SHA.

### Explicitly not proven

No carrier-specific insured property site, addresses, sums insured, property replacement TIV, participation shares, limits, deductibles, effective policy status, R+V-specific actual insurer portfolio, ceded reinsurance coverage or OEP/AEP input exposure is established by the index. Existing WBM 2025 residential apartments are not the nine 2026 commercial objects. No database/model admission or cross-insurer aggregation occurs.
