<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Aon Risk Analytics Platform (RAP): public capability and OpenCatastrophe gap review

**Reviewed:** 2026-11-10 (public-source desktop research only).  
**Status:** research / competitor capability benchmark; **no source or model admission**, no Aon account, API, contract, licensed dataset or production integration verified.

## Purpose and evidence boundaries

This document investigates [Aon RAP](https://rap.aon.com/) as a *functional benchmark* for OpenCatastrophe, OpenCatastrophe-data and NextGen. It is not a claim that the products are interchangeable or that Aon data can be imported.

Evidence categories: **P** = Aon original public statement; **R** = observed current repository state; **I** = inference / our engineering proposal; **U** = unknown, not verified.

On 2026-11-10 the public RAP landing URL was discoverable by the web reader as “Risk Analytics Platform” but yielded **zero readable page lines**. There is no authenticated RAP walkthrough in this review. Therefore **do not claim** to know RAP's exact screens, schemas, API, pricing, login policies, service terms or data-export mechanisms. No undocumented endpoints were probed, and absence of a published interface in this research does not prove none exists.

## Verified product separation

| Product / layer | What the primary source establishes | What it does **not** establish |
| --- | --- | --- |
| **RAP / Risk Analytics Platform** | **P:** Model-agnostic, brings together catastrophe data, vendor models and Aon insight; a single access point to Underwriting Analytics and Event Analytics. [Aon 2026-09-03](https://aon.mediaroom.com/news-releases?item=138640) | Public RAP API, OED/ORD ingest/export, free access, open source code, redistributable hazard scores. |
| **RAP Underwriting Analytics** | **P:** Announced 2026-09-03. Assesses *prospective* business relative to existing portfolio accumulations at location/policy/portfolio level; uses Global Hazard Scores, building characteristics and hazard susceptibility for risk appetite, diversification and capacity decisions. [Aon release](https://aon.mediaroom.com/news-releases?item=138640) | Exact score definition, hazard score units, threshold formulas, vendor model execution within a customer tenant, or guaranteed API. |
| **RAP Event Analytics** | **P:** Aon states its Event Analytics consolidated hazard, exposure and loss information in RAP, with a Catastrophe Tracker, mapping and customized reports. [Aon impact report 2026-04-06](https://www.aon.com/en/about/our-impact/2025/supporting-energy-resilience-and-a-transition-to-a-low-carbon-economy) | Public event feed, refresh SLA, export license, external customer usage or historic-event byte availability. |
| **Digital Infrastructure Risk Aggregator (DIRA)** | **P:** Announced 2026-09-07; analyses data-center concentration by location, geography, operator and dependencies, using locations connected with RAP; offered to clients as quarterly/annual analysis. [Aon release](https://aon.mediaroom.com/news-releases?item=138642) | That DIRA is a downloadable RAP module, a public dataset, or a full CAT event model. |
| **Impact Forecasting / ELEMENTS** | **P:** Separate Aon catastrophe modelling suite/platform. Aon explicitly documents Oasis LMF financial-engine compatibility, OED modifiers, own/vendor models, EP reporting and **ELEMENTS APIs**. [Aon Catastrophe Model Insight](https://www.aon.com/en/capabilities/reinsurance/catastrophe-model-insight) | That the ELEMENTS API is a RAP API, or that ELEMENTS licensed model content can be redistributed via OpenCatastrophe. |
| **ImpactWorkbench** | **P:** Separate exposure-transformation product with an API and OED export support. [Aon ImpactWorkbench](https://www.aon.com/reinsurance/impact-workbench/default.jsp) | RAP endpoint availability or any implied free access to translated exposure data. |

**Critical distinction:** Aon documents an API for **ELEMENTS** and for **ImpactWorkbench**, **not necessarily for RAP**. The three products must not be conflated.

## Existing OpenCatastrophe overlap (repository evidence, 2026-11-10)

**OpenCatastrophe-data, public source landscape:** [sources-oasis-public-models-20261105.json](../../landscape/sources-oasis-public-models-20261105.json) already lists **four**, not two, distinct Aon Impact Forecasting / OasisLMF Scenarios candidate records:

- `oasislmf.scenarios.impact-forecasting.euws` — EUWS European windstorm *deterministic* scenarios: physical November 2023 storms Ciarán and Domingos; three alternative footprint interpolations per storm, **not six stochastic annual occurrences**. Source has reported empty occurrence.bin, a candidate event-set default typo (`cieren` versus `ciaran`), and unresolved data rights.
- `oasislmf.scenarios.impact-forecasting.maeq` and `...treq` — two distinct earthquake scenario package references; exact geography, source rights, run and annual measure not verified.
- `oasislmf.scenarios.impact-forecasting.ustc` — a US tropical-cyclone source-data lead, with **no complete runnable model package verified**.

All four entries have `rights_review_status=not_reviewed`, `scientific_review_status=not_reviewed`, `admission_status=not_admitted`. None is an RAP endpoint or RAP-access entitlement. The [Oasis scenario annualization preflight](oasis-scenario-annualization-preflight-v0.md) warns that named events, event-set alternatives and even requested EP output do not establish a valid annual probability measure.

**OpenCatastrophe engine:** the [German wind annual EP admission gate v14](https://github.com/pokekarten/OpenCatastrophe/blob/main/docs/wind_annual_ep_gate_v14.md) permits conditional selected-event sensitivity but **blocks** annual AAL/OEP/AEP and Gross/Net treaty EP absent complete hazard support, defensible event frequency and financial-chain inputs. Its 7,998 locations are fictional interests, **not** actual R&V property exposure. The [NextGen global CAT v1 interop contract](https://github.com/pokekarten/OpenCatastrophe/blob/main/research/nextgen_global_cat_v1_interop_contract.md) is a **proposal, not a shipped native integration**, and explicitly requires shared physical events and zero-event years.

Neither repository code search for `rap.aon.com` (data) nor the bounded Aon/RAP search above demonstrated an existing RAP integration. Search coverage is limited to accessible indexed/default-branch material; this is not exhaustive proof of absence.

## Engineering gap analysis: benchmark capabilities versus honest OpenCatastrophe targets

| RAP benchmark | OpenCatastrophe candidate path (**I**, proposed) | Minimum audit / acceptance gate |
| --- | --- | --- |
| New-risk / portfolio accumulation | Synthetic baseline OED exposure plus candidate location/policy; compare before/after TIV and event-conditioned loss by spatial cluster, peril and coverage | Same hazard/version/footprint and policy terms in both cases; `delta = candidate_post - baseline_pre`; deterministic unit and conservation tests; missing hazard is *unknown*, not zero |
| Location hazard context | Source-labelled observation/model hazard with peril, site geometry, CRS, units, timestamp, source and grid distance | No invented global score; missing building attributes and geocoding quality explicit; licence and peril coverage checked |
| Event Analytics | Named physical-event register; optional independently licensed footprints, mapped synthetic exposure and event loss/report | One physical storm across alternative hazard reconstructions; separate scenario branches, no event duplication |
| Multi-model comparison | Oasis / OpenQuake adapter + independent model/version provenance; same portfolio and financial conditions | Compare event/period/sample and currency semantics, not only displayed headline losses; model rights independent |
| Insurer / reinsurance capital decisions | financial-capital modelling after insured loss, shared annual simulations, treaty chronology and reinsurance/retrocession parity gates | Zero-event years retained; identical annual worlds gross and net; rank and hash parity; never label conditional stress as OEP/AEP |
| Digital infrastructure accumulation | Optional **synthetic** data-center locations, owner/operator, correlated dependencies and common peril events | Attribution of shared dependencies; no assertion of real Aon asset inventory, insured limit or commercial data rights |

### Focused, reproducible P0 experiment (no Aon bytes needed)

Use an independently authored synthetic German residential (or fully synthetic data-center) portfolio and two synthetic underwriting proposals:

1. Pin baseline site/policy keys, covered value, geography, peril mapping, as-of date, currency and scenario hashes.
2. Apply proposal A in an existing concentration area and proposal B in another area with equivalent synthetic insured value; compare TIV and **conditional** scenario GUL/insured loss deltas, retaining any missing footprint mask as unresolved.
3. Confirm exact additive exposure reconciliation for supported, non-overlapping interest measures; distinguish shared-policy coverage, deductible, occurrence aggregation and location duplicates. Do **not** infer that scenario risk-adjusted pricing or annual-frequency reduction is justified.
4. Produce an auditable machine-readable before/after result with source hashes, `risk_metric_kind=conditional_scenario`, `annual_ep_admitted=false` and confidence/coverage metadata. No Aon-like proprietary Hazard Score is calculated.
5. Run adversarial synthetic tests: altered source hash, missing footprint for a new site, same physical event split into alternatives, duplicate policy ID, changed currency, and a scenario wrongly marked annualized must all be blocked.

**P0 acceptance:** site/policy/portfolio impact demonstration is repeatable, hash-pinned, source-conservative and works on fiction-only exposure without upgrading source admission. **P1** should cover normalized hazard/intensity definitions and multi-model comparison only when exact rights and semantics are reviewed. **P2**: annual gross/net OEP/AEP after independently validated event-frequency, shared-year, contract and financial-model gates.

### External integration decision

**No direct RAP integration currently approved.** Before designing one, obtain *official* RAP documentation or a permitted client/demo account and verify independently:

- Is there a supported customer-facing RAP API? If yes, get the published endpoint/schema, scopes, auth flow, rate limits, export and retention terms **from Aon**, not by endpoint guessing.
- What can clients export: locations, Global Hazard Scores, footprints, event IDs, modeled loss, score definitions or only visualization?
- Which rights govern the **specific** product/version, original input, derivative, commercial processing, redistribution, retention and publication? Do vendor-model licences differ from platform software terms?
- How are model version, hazard intensity, perils, time windows, return-period definitions, aggregation and financial terms specified? Does an annual probability measure exist for each exported product?
- Can a strictly synthetic, authorized sample be used for one bounded parity experiment, with outputs kept outside public Git until reviewed?

Until answered: document as **capability benchmark**; no scraping behind login, no automation circumventing access controls, no unauthorized vendor model downloads, no customer data, no credentials, no inferred score formula, and no Aon original/derived bytes in Git or Neon production.

## Source register (public provider statements only)

1. [Risk Analytics Platform landing URL](https://rap.aon.com/) — **P/U**, URL/page title discoverable 2026-11-10, no readable UI text in this inspection.
2. [Aon RAP Underwriting Analytics announcement, 2026-09-03](https://aon.mediaroom.com/news-releases?item=138640) — **P**, underwriting, Global Hazard Scores, model-agnostic RAP and Event Analytics relationship.
3. [Aon DIRA announcement, 2026-09-07](https://aon.mediaroom.com/news-releases?item=138642) — **P**, digital infrastructure aggregation, quarterly/annual analysis and RAP linkage.
4. [Aon impact report, published 2026-04-06](https://www.aon.com/en/about/our-impact/2025/supporting-energy-resilience-and-a-transition-to-a-low-carbon-economy) — **P**, 2025 Event Analytics consolidation into RAP, Catastrophe Tracker and reporting.
5. [Aon Catastrophe Model Insight](https://www.aon.com/en/capabilities/reinsurance/catastrophe-model-insight) — **P**, Impact Forecasting/ELEMENTS, Oasis, OED, EP and **ELEMENTS** APIs.
6. [Aon ImpactWorkbench](https://www.aon.com/reinsurance/impact-workbench/default.jsp) — **P**, separate transformation/API product.

**Review result:** Public product capabilities are supported by Aon's own statements. RAP user-level implementation details, APIs, access entitlements, model/data licensing and potential scientific calibration remain **unknown**. This document is original repository-authored commentary linking to provider pages, **not** an imported Aon dataset, scientific calibration, official partnership or admission decision.

## Executable fictional underwriting accumulation benchmark (2026-11-10)

The P0 comparison above now has a **runnable, standalone, stdlib-only** reference implementation in
[research/aon_rap_fictional_accumulation_v0.py](../../research/aon_rap_fictional_accumulation_v0.py)
and eight regression methods in
[tests/test_aon_rap_fictional_accumulation_v0.py](../../tests/test_aon_rap_fictional_accumulation_v0.py).
It uses one **invented** physical storm, two fully synthetic regional damage ratios (HIGH 30%, LOW 5%),
one-to-one fictional risk/policy pairs, and per-risk EUR-cent policy deductibles and caps.
It is *not* a geographic model, a risk score or an Aon algorithm.

From the repository root:

\`\`\`sh
python -m research.aon_rap_fictional_accumulation_v0
python -m unittest discover -s tests -p 'test_aon_rap_fictional_accumulation_v0.py' -v
\`\`\`

Both proposed risks add **EUR 50,000 TIV** with identical EUR 250 per-risk deductible
and EUR 50,000 per-risk insured limit. Baseline fictional TIV is EUR 200,000;
baseline gross scenario loss EUR 35,000 and insured scenario loss EUR 34,500.
Adding proposal A in the higher-risk synthetic zone increases conditional
GUL by **EUR 15,000** and insured scenario loss by **EUR 14,750**.
Adding proposal B in the lower-risk synthetic zone increases GUL by
**EUR 2,500** and insured loss by **EUR 2,250**.
The two proposals are **counterfactual alternatives**, not simultaneous risks.
All amounts are integer-cent calculations; rounding is half-up to one cent
at individual-risk gross loss before deductibles and limits.

The result explicitly reports
\`risk_metric_kind=conditional_scenario\`,
\`annual_ep_admitted=false\`,
\`aon_data_or_score_used=false\`,
\`actual_insurer_data_used=false\` and
\`source_original_bytes_verified=false\`.
Its \`fictional_fixture_sha256\` binds the constructed **fixture only**;
it does **not** authenticate provider hazard observations, Oasis outputs,
a vendor score or any externally licensed source. One event and the same
invented risk terms are used on both sides, so zero-event years, CAT XL,
retro, risk-premium pricing, annual frequencies and OEP/AEP are unsupported.

**Fail-closed controls:** strict integer cents and 0–10,000 integer damage
basis points, no float/Boolean coercion, EUR currency only, no duplicate
location or policy IDs, equal proposed TIV/terms, separate proposed zones,
and no missing hazard zone (missing footprint is unknown, **not** zero loss).
Unknown input fields, annualization flags and multi-event claims are
rejected instead of being silently ignored.

**Executed scope:** the exact two resulting Python source Git blobs were
re-fetched and matched the locally executed source: module
\`bafd43ff5c5b591bdaf25813b67ab40c54e3a6cd\`, test
\`29766b365f259eab994139da37df18f41dee56f8\`.
**8/8 isolated CPython unit tests passed**; module invocation and
\`compileall\` succeeded. Full public repository CI must independently
run on the final PR HEAD before considering any **research-only** merge.
No rights, source data, insurer location, native model or financial-science
admission status is changed.
