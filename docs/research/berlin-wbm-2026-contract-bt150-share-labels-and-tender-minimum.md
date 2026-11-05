<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WBM 2026: contract identifier percentage labels and 2026 insurance tender minimum

**Research status 2026-11-05:** 2026 WBM public procurement, **nine pure commercial properties**; this is *not* the 2025 WBM residential portfolio and not a verified insurer-risk site schedule. Our [original eForms winner-contract graph receipt](../../research/observations/ted_wbm_2026_original_eforms_award_graph_receipt_v0.toml) already proves three settled-contract links, source SHA-256 `7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78`, 21,837 bytes, from [TED 668506-2026](https://ted.europa.eu/en/notice/668506-2026/xml).

## Newly noticed contract *business identifier* text, to verify in original XML

A [public secondary award transcription](https://ausschreibungen-deutschland.de/2550217_Deutschland__Versicherungen__Industrielle_Sachversicherung_fuer_reine_Gewerbeobjekte_2026_Berlin) displays:

| Earlier original eForms role graph | Listed contract identifier (BT-150) in secondary transcription | Possible percentage label |
| --- | --- | ---: |
| CON-0001 -> TEN-0001 -> HDI Global SE | Status Quo 50% Beteiligung | 50% |
| CON-0002 -> TEN-0002 -> Helvetia Schweizerische Versicherungsgesellschaft AG | 40% Beteiligung Status Quo | 40% |
| CON-0003 -> TEN-0003 -> R+V Allgemeine Versicherung AG | 10% Beteiligung | 10% |

**Verified independently on 2026-11-05:** [dedicated original-source GitHub Action 42095017588](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42095017588) returned all three names and exact BT-150 labels above from the **original official 21,837-byte SHA-pinned eForms**. The original contract identifier text is verified, while the underlying signed/current policy participation share remains unverified. The [official eForms SDK](https://docs.ted.europa.eu/eforms/latest/schema/all-in-one.html) specifies **contract technical ID (OPT-316) = SettledContract/cbc:ID**, **published contract business identifier (BT-150) = SettledContract/efac:ContractReference/cbc:ID**, and optional **contract title (BT-721) = SettledContract/cbc:Title**. Do not confuse these three concepts.

The [read-only exact-original contract identifier reader](../../research_runners/ted_wbm_original_contract_identifier_labels_v0.py) requires: exact official XML immutable SHA+byte pin; WBM buyer and title markers; validated three `RES -> CON -> TEN -> TPA -> ORG` edges; unchanged reviewed original graph receipt; one unique published `BT-150` per CON; matching winning tender per CON; bounded identifier text; no data redistribution. It produces the business identifier string and a **percentage-number-in-identifier** candidate. It does **not** promote that number to policy coinsurance share, underwriter net retention, site values or verified CAT exposure, **even if the three labels sum to 100%**. A public award decision may precede actual policy inception.

## Earlier competition 286307-2026 (27 April 2026) and real uncertainty

The [original competition notice reference](https://ted.europa.eu/en/notice/286307-2026) was rendered by a [public tender transcription](https://ausschreibungen-deutschland.de/2477973_Deutschland__Versicherungen__Industrielle_Sachversicherung_fuer_reine_Gewerbeobjekte_2026_Berlin). It states:

- WBM's industrial property policy for **nine pure commercial properties**, with possible consortium; applicants could declare lead, follower, or sole carrier.
- **Minimum intended lead writing share: 30%. Minimum intended follower writing share: 15%.** The later *R+V 10%* contract identifier label, **if verified**, would appear below the earlier advertised 15% condition. The original competition **expressly permits a below-minimum participating offer for a residual share left when assembling 100% cover**, and allows the cheapest lead to be capped at 50% where cheaper followers exist. Thus **10% can be consistent with the published procurement rules**. Whether this exception was actually invoked for R+V is not proven, nor does a business identifier establish a signed insurance policy share. Both minima were independently corroborated in the original competition XML.
- Stated insured peril *requirements* include fire, storm, hail, flood, earthquake, tsunami, landslide, snow pressure, volcanic eruption, burglary and glass breakage, among others. Actual final policy wordings, sublimits and deductibles are not public in the presently checked source.
- The competition notice proposes insurance period **1 Jan 2027 to 1 Jan 2028** and up to **seven 1-year extensions**. This is a **planned** contract duration, not verified active cover at the time of research (5 Nov 2026).
- The published procurement specifically says more detailed risk information, contract terms and further underwriting documents would be supplied to selected bidders later. The public notice does **not** contain the address or insured reinstatement value of each of the nine individual buildings.

The tender specifies a **three-step price-based allocation**: pick the cheapest lead, potentially cap that lead at 50% if cheaper follower offers exist, fill remaining shares from lower-price offers, and **allow a smaller-than-minimum final participation to complete 100% coverage**. This published rule provides a credible **permitted route** to the 10% source label; we have no bidder-price evidence or final award decision memo proving the specific route used for R+V. Avoid assertions of a violation or of its exact commercial rationale.

## Review gates to unlock modeled R+V quota

1. Re-fetch original official TED XML for 668506-2026, require immutable pinned SHA and parse BT-150 *with the actual CON to winning TEN/company edge*, compare the three number labels against the mirror. Save source evidence as **published procurement identifier labels**, not modeled shares.
2. Verify 286307-2026 from the official primary original publication (or Search API source-only metadata) including procedure UUID and stated applicant minimums, risks and intended term.
3. Acquire and review real final wordings / insurance schedule / coinsurance contract (or a legally usable sanitized copy) to establish **actual R+V 10% participation**, insured locations, replacement value, sublimits, share basis and policy in-force dates.
4. Only then classify company-real-data exposure. Until then a fictional CAT scenario can use 50/40/10 as a declared **hypothesis** without claiming R+V actually insured those assets in a given period.

Code tests: `python -m unittest discover -s tests -p 'test_ted_wbm_original_contract_identifier_labels_v0.py' -v`; official replay: `python -m research_runners.ted_wbm_original_contract_identifier_labels_v0`.

**Non-equivalence:** three contract awards for a *single technical procurement lot* are not 27 real buildings; a source label of 10% is not a ten-percent share of nine **geolocated** property values; neither gross nor net CAT losses or OEP/AEP can be inferred from this source alone.

## Primary official TED procurement source retrieval succeeded (2026-11-05)

The [TED workflow 42095017588](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42095017588) independently retrieved the complete original **WBM 286307-2026 competition ContractNotice**, source **41,307 XML bytes** and SHA-256 **`54c0c84b379a9629f3e5774245ca763f66159e2cf45704ba985589202adcf9a1`**. The restricted-source parser verified the literal publication number, WBM buyer, nine pure commercial buildings, **30% lead and 15% participating minimum writing shares**, and requested storm, flood and earthquake cover. These original bytes were **not** retained or redistributed. The observed SHA+size have been pinned in the [official competition preflight](../../research_runners/ted_wbm_2026_competition_original_preflight_v0.py) for a second exact source replay; the first original successful capture is **not** an already completed independent pin recheck until another successful run matches.

In the same initial run the original award notice **668506-2026** matched its previously pinned SHA-256 `7650720183d0c26430e0433858bf2e8b854ea68bb93fbf679e96ee696ee8fc78`. The [contract label reader](../../research_runners/ted_wbm_original_contract_identifier_labels_v0.py) cross-validated source `BT-150` labels and original `RES→CON→TEN→TPA→ORG` edges:

- `CON-0001` → HDI Global SE: `Status Quo 50% Beteiligung`;
- `CON-0002` → Helvetia Schweizerische Versicherungsgesellschaft AG: `40% Beteiligung Status Quo`;
- `CON-0003` → R+V Allgemeine Versicherung AG: `10% Beteiligung`.

The three source-text percentage labels add to 100%, but this is **not a policy-coverage test**. The first original competition notice and earlier award refer to the same nine pure commercial objects, not nine assigned risks per insurer. The relevant uncertainty is whether the later **10% BT-150 text** overrides, exempts, or otherwise differs from the earlier **15% participant offer minimum**. Only reviewed later negotiation/addendum files or the signed coinsurance schedule can answer this; the observed original notices do not. We do not claim a legal violation.

The source extraction also checks that the original tender contains both the **maximum 50% lead-cap condition** and the **explicit final residual-under-minimum participation exception**. Both source markers are separate from the 30%/15% *initial offer requirements*; no company-specific exception application is inferred.

The [source observation TOML](../../research/observations/ted_wbm_2026_original_contract_share_labels_v0.toml) stores both original publisher SHA receipts, exact three company/CON/TEN/BT-150 pairs, 30/15 bidder minimum and explicit *NO insurer exposure admission* booleans. **All percentages remain provenance-tagged labels, not verified actual insurer TIV portions**. Do not feed the values directly into CAT model calibration or legal entity market shares.
