<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2026 original TED eForms: winning tendering-party role preflight

**Research only (2026-11-05).** The prior official TED XML acquisition of publication 668506-2026 produced 21,837 original bytes and SHA-256 7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78. A subsequent official re-fetch failed with HTTP 202. A winner list from an unpinned mirror cannot replace the original source. **Live role extraction may report confirmed award relationships only if original bytes match this pinned SHA-256 and byte size.**

## Role chain, rather than textual name matching

Official [eForms Parties and Roles](https://docs.ted.europa.eu/eforms/latest/schema/parties.html) and [Competition Results](https://docs.ted.europa.eu/eforms/latest/schema/competition-results.html) document:

1. A true winner begins in ContractAwardNotice / NoticeResult / LotResult, where TenderResultCode is selec-w.
2. LotResult references a LotTender technical ID TEN, which must itself refer to the **same lot identifier LOT** and a TenderingParty ID TPA.
3. That TenderingParty contains one or more Tenderer organization references ORG. A group of multiple tenderer organizations does not imply multiple copies of the awarded nine buildings.
4. Each ORG must resolve uniquely via Organizations / Organization / Company / PartyIdentification to its exact published legal company name. The separately identified ContractingParty must remain the WBM **buyer**, not a winner.
5. A company mentioned in the original XML but only in a losing tender, a review body, or descriptive prose **is not awarded a contract**. Unresolved/dangling/duplicate references are blocked rather than guessed.

The [read-only extraction runner](../../research_runners/ted_wbm_eforms_winner_role_v0.py) enforces these paths, exact immutable original XML SHA + size, XML/UBL namespace, unique IDs, single buyer and correct lot linkage, and emits only a sorted list of source-identified winning tendering party members with their technical result/lot/tender/party IDs.

The source winner labels are compared (exact text only) to the three companies named in the earlier public secondary award index: HDI Global SE, Helvetia Schweizerische Versicherungsgesellschaft AG, and R+V Allgemeine Versicherung AG. A mismatch is reported and never silently normalized to the secondary index. A buyer, nonwinning bidder or contract signatory cannot become a winning property insurer solely because their name occurs in XML.

## Independent verification commands

Run unit regression with: python -m unittest discover -s tests -p 'test_ted_wbm_eforms_winner_role_v0.py' -v

Attempt original live publisher verification with: python -m research_runners.ted_wbm_eforms_winner_role_v0

The synthetic tests use mock eForms documents with an explicit three-organization winning party and a separate losing bidder. They temporarily substitute a synthetic fixture SHA. **Passing synthetic tests does not prove the original TED winner links were successfully extracted.** The dedicated Actions workflow attempts live independent source verification but cannot claim it succeeded if TED replies 202; only a strict matching real-source result can establish award-role extraction.

## Portfolio and legal limits

A winner role is not the same as a signed or currently operative insurance policy; winner-group membership is not a verified coinsurance share; and three reported names are not three independently insured portfolios of nine commercial properties. The WBM September 2026 award is **separate from the 2025 Senate residential dwelling count**. Original eForms result links do not provide actual insured site location coordinates, replacement cost or market value TIV, policy limits/deductibles, per-peril coverage, ceded treaty net retention, or gross/net OEP/AEP. Do not create a CAT model exposure or insurer x ZIP join from these observations.

Next, verify the original contract award result and SettledContract references (if publisher HTTP 200 succeeds), then request independently public, licence-cleared property risk schedules and carrier participation or produce explicitly synthetic alternatives with documented uncertainty. No external original XML bytes, customer addresses or insured risk locations are committed.
