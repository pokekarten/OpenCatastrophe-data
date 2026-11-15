<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2026 original TED eForms: winning tendering-party role preflight

**Research only (2026-11-05).** The prior official TED XML acquisition of publication 668506-2026 produced 21,837 original bytes and SHA-256 7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78. A subsequent official re-fetch failed with HTTP 202. A winner list from an unpinned mirror cannot replace the original source. **Live role extraction may report confirmed award relationships only if original bytes match this pinned SHA-256 and byte size.**

## Role chain, rather than textual name matching

Official [eForms Parties and Roles](https://docs.ted.europa.eu/eforms/latest/schema/parties.html) and [Competition Results](https://docs.ted.europa.eu/eforms/latest/schema/competition-results.html) document:

1. A selected LotResult has TenderResultCode selec-w, but its efac:LotTender entries are **references to received bids (OPT-320)**, which can include **losing tenders**. **Do not** select every received TEN as a winner. This was a bug in the first eForms winner role preflight.
2. The selected LotResult must reference a **SettledContract CON (OPT-315)**, which must resolve to an actual NoticeResult/SettledContract. Only that SettledContract's own efac:LotTender references **(BT-3202)** can identify contract-linked winning tenders. Require a consistent LOT among the result, received bid (if listed), contract-linked tender and TPA; reject broken or duplicate edges. A cross-lot contract may list tenders for several lots: never select a tender for the wrong LOT.
3. The selected, contract-linked LotTender references a TenderingParty TPA, which contains one or more Tenderer organization references ORG. A group of multiple tenderer organizations does not imply multiple copies of the awarded nine buildings.
4. Each ORG must resolve uniquely via Organizations / Organization / Company / PartyIdentification to its exact published legal company name. The separately identified ContractingParty must remain the WBM **buyer**, not a winner.
5. A company mentioned in the original XML but only in a losing tender, a review body, or descriptive prose **is not awarded a contract**. Unresolved/dangling/duplicate references are blocked rather than guessed.

The [read-only extraction runner](../../research_runners/ted_wbm_eforms_winner_role_v0.py) enforces the **selected result → contract → awarded tender → tendering party → company** graph, exact immutable original XML SHA + size, XML/UBL namespace, unique IDs, single buyer, correct lots and **verified signed-party references**. It emits only source-identified contract-linked winning tender groups and their technical RES/CON/LOT/TEN/TPA/ORG IDs. **Contract signatories are recorded separately and do not automatically become winning underwriters.**

The source winner labels are compared (exact text only) to the three companies named in the earlier public secondary award index: HDI Global SE, Helvetia Schweizerische Versicherungsgesellschaft AG, and R+V Allgemeine Versicherung AG. A mismatch is reported and never silently normalized to the secondary index. A buyer, nonwinning bidder or contract signatory cannot become a winning property insurer solely because their name occurs in XML.

## Independent verification commands

Run unit regression with: python -m unittest discover -s tests -p 'test_ted_wbm_eforms_winner_role_v0.py' -v

Attempt original live publisher verification with: python -m research_runners.ted_wbm_eforms_winner_role_v0

The synthetic tests use mock eForms documents with an explicit three-organization contract-linked winning party, a losing bidder *also referenced in the selected result's received-offers list*, and a separate signatory who is not a winner. They temporarily substitute a synthetic fixture SHA. **Passing synthetic tests does not prove the original TED winner links were successfully extracted.** The dedicated Actions workflow attempts live independent source verification but cannot claim it succeeded if TED replies 202; only a strict matching real-source result can establish award-role extraction.

## Portfolio and legal limits

A winner role is not the same as a signed or currently operative insurance policy; winner-group membership is not a verified coinsurance share; and three reported names are not three independently insured portfolios of nine commercial properties. The WBM September 2026 award is **separate from the 2025 Senate residential dwelling count**. Original eForms result links do not provide actual insured site location coordinates, replacement cost or market value TIV, policy limits/deductibles, per-peril coverage, ceded treaty net retention, or gross/net OEP/AEP. Do not create a CAT model exposure or insurer x ZIP join from these observations.

Next, verify the original contract award result and SettledContract references (if publisher HTTP 200 succeeds), then request independently public, licence-cleared property risk schedules and carrier participation or produce explicitly synthetic alternatives with documented uncertainty. No external original XML bytes, customer addresses or insured risk locations are committed.

## Correction audit: received bid references are not winner references (2026-11-05)

The initial implementation of PR #1368 used `LotResult[selec-w]/efac:LotTender` as though every referenced TEN were awarded. The [official EU eForms Competition Results SDK](https://docs.ted.europa.eu/eforms/latest/schema/competition-results.html) explicitly calls those references **received tenders (OPT-320)** and separately requires a **settled contract reference (OPT-315)**. Each [SettledContract](https://docs.ted.europa.eu/eforms/latest/schema/competition-results.html) has its own **contract-to-tender link (BT-3202)**. This matters materially because the former program could mislabel unsuccessful bids as winning insurance carriers.

The revised validator and its expanded **26 offline positive/fail-closed unit tests** deliberately include a selected lot result containing both a winning and a losing tender. Only the tender referenced by the selected result's actual settled contract is reported as a winner; a buyer, a separately mentioned/losing organization, or even a contract signatory without a corresponding tenderer role cannot become a winning insurer. If no contract reference is published, the report explicitly **fails closed** rather than guessing the winner.

This repairs the **role evidence model**. It does not resolve the independent external availability problem: official TED can return HTTP 202 rather than complete original XML. A green test or CI result cannot constitute verified original winner extraction when the live publisher fetch is blocked. Even successfully verified award roles do not establish coinsurance shares or individual insured objects.

## First successful full original eForms role replay after HTTP 202 (2026-11-05)

[Actions run 42091432185](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42091432185) re-fetched complete official 668506-2026 XML and **matched the saved exact source SHA-256 and 21,837 bytes**. The corrected original-UBL parser successfully joined **three selected results to three settled contracts, three contract-linked tenders and three distinct companies**, all **in technical LOT-0000**: `RES-0001 → CON-0001 → TEN-0001 → TPA-0001 → ORG-9000` = HDI Global SE; `RES-0002 → CON-0002 → TEN-0002 → TPA-0002 → ORG-9001` = Helvetia Schweizerische Versicherungsgesellschaft AG; `RES-0003 → CON-0003 → TEN-0003 → TPA-0003 → ORG-9002` = R+V Allgemeine Versicherung AG. The buyer is WBM `ORG-0001` and is a contract signatory, not an underwriter. Full machine-readable [publisher-source graph receipt](../../research/observations/ted_wbm_2026_original_eforms_award_graph_receipt_v0.toml), [replay validator](../../research_runners/ted_wbm_original_award_graph_receipt_v0.py).

This replaces the previous *temporary unavailability* blocker for these exact award-role references. **It does not unlock insured-object allocations, actual contract participation percentages, 2026 policy coverage, premium, TIV, hazard site geocodes or gross/net risk simulations.** The award publication is dated 2026 and names three companies for one technical lot; there is no verified nine-object-to-company schedule in this evidence.
