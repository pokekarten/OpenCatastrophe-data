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

**Until the new exact-pinned original XML extraction succeeds, these exact titles are transcribed external evidence only.** The [official eForms SDK](https://docs.ted.europa.eu/eforms/latest/schema/all-in-one.html) specifies **contract technical ID (OPT-316) = SettledContract/cbc:ID**, **published contract business identifier (BT-150) = SettledContract/efac:ContractReference/cbc:ID**, and optional **contract title (BT-721) = SettledContract/cbc:Title**. Do not confuse these three concepts.

The [read-only exact-original contract identifier reader](../../research_runners/ted_wbm_original_contract_identifier_labels_v0.py) requires: exact official XML immutable SHA+byte pin; WBM buyer and title markers; validated three `RES -> CON -> TEN -> TPA -> ORG` edges; unchanged reviewed original graph receipt; one unique published `BT-150` per CON; matching winning tender per CON; bounded identifier text; no data redistribution. It produces the business identifier string and a **percentage-number-in-identifier** candidate. It does **not** promote that number to policy coinsurance share, underwriter net retention, site values or verified CAT exposure, **even if the three labels sum to 100%**. A public award decision may precede actual policy inception.

## Earlier competition 286307-2026 (27 April 2026) and real uncertainty

The [original competition notice reference](https://ted.europa.eu/en/notice/286307-2026) was rendered by a [public tender transcription](https://ausschreibungen-deutschland.de/2477973_Deutschland__Versicherungen__Industrielle_Sachversicherung_fuer_reine_Gewerbeobjekte_2026_Berlin). It states:

- WBM's industrial property policy for **nine pure commercial properties**, with possible consortium; applicants could declare lead, follower, or sole carrier.
- **Minimum intended lead writing share: 30%. Minimum intended follower writing share: 15%.** The later *R+V 10%* contract identifier label, **if verified**, would appear below the earlier advertised 15% condition. This is an **unexplained difference**, not evidence of a legally defective award or an automatic change to actual quota.
- Stated insured peril *requirements* include fire, storm, hail, flood, earthquake, tsunami, landslide, snow pressure, volcanic eruption, burglary and glass breakage, among others. Actual final policy wordings, sublimits and deductibles are not public in the presently checked source.
- The competition notice proposes insurance period **1 Jan 2027 to 1 Jan 2028** and up to **seven 1-year extensions**. This is a **planned** contract duration, not verified active cover at the time of research (5 Nov 2026).
- The published procurement specifically says more detailed risk information, contract terms and further underwriting documents would be supplied to selected bidders later. The public notice does **not** contain the address or insured reinstatement value of each of the nine individual buildings.

Potential explanations for *10% versus 15%* include later negotiations, a current status-quo incumbent continuation, a waiver or different definitions of participation. **None are verified** by the public notices alone. Do not select one as fact.

## Review gates to unlock modeled R+V quota

1. Re-fetch original official TED XML for 668506-2026, require immutable pinned SHA and parse BT-150 *with the actual CON to winning TEN/company edge*, compare the three number labels against the mirror. Save source evidence as **published procurement identifier labels**, not modeled shares.
2. Verify 286307-2026 from the official primary original publication (or Search API source-only metadata) including procedure UUID and stated applicant minimums, risks and intended term.
3. Acquire and review real final wordings / insurance schedule / coinsurance contract (or a legally usable sanitized copy) to establish **actual R+V 10% participation**, insured locations, replacement value, sublimits, share basis and policy in-force dates.
4. Only then classify company-real-data exposure. Until then a fictional CAT scenario can use 50/40/10 as a declared **hypothesis** without claiming R+V actually insured those assets in a given period.

Code tests: `python -m unittest discover -s tests -p 'test_ted_wbm_original_contract_identifier_labels_v0.py' -v`; official replay: `python -m research_runners.ted_wbm_original_contract_identifier_labels_v0`.

**Non-equivalence:** three contract awards for a *single technical procurement lot* are not 27 real buildings; a source label of 10% is not a ten-percent share of nine **geolocated** property values; neither gross nor net CAT losses or OEP/AEP can be inferred from this source alone.
