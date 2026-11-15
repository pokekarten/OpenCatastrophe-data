<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Company-specific synthetic portfolio reconstruction: evidence, limits, executable v0

Reviewed **2026-11-03** using live public provider material, current GitHub main and
read-only insurance-only Neon research readiness. **This is research, not a source
admission, regulated portfolio representation, rights decision, proprietary
model output, insured TIV observation, underwriting advice or database update.**

## Scientific question and non-identifiability

We want a *distribution of possible* insurer, reinsurer, syndicate, MGA and ILS
risk-bearing portfolios **consistent with dated, independently verifiable public
constraints**, not an assertion that one hidden risk location or treaty can be
recovered from a group's financial statements.

- Entity hierarchy and risk-bearing perimeter are separate. Legal LEI identity
  and GLEIF accounting consolidation do not prove licence, group solvency
  perimeter, carrier risk retention or the relation between a delegated MGA and
  the carrier assuming risk. Use regulator-grade group membership and effective
  dates. Do not duplicate branch records, MGA production, Lloyd's managing
  agents and syndicate risks, or quota-share chains as extra unique assets.
- Premiums, policy count, reported insured limit/TIV, building replacement cost,
  claims, AEL, PML, SCR and a cat-bond notional have **different physical and
  financial units**; none converts to another without explicit models.
- An insurer's annual gross written premiums by country and separately by
  insurance line generally give **two marginals**, not the joint country x line
  table. Infinitely many joint allocations can satisfy those margins. A prior
  changes the answer. Missing / Other / Worldwide is not a reported zero.
- Disclosure geography varies: underwriting/sale location, **location of risk**,
  cedant domicile for accepted reinsurance, report consolidation location,
  home/host/passport and investment-property location are distinct variables.
  EIOPA QRT S.04.04 and S.04.05 deliberately distinguish these; report vintage
  and disclosure/95%-materiality residual must be preserved.
- Physical asset positions are not automatically insured by a target company.
  Observed market-level exposure grids and building counts constrain **industry
  asset opportunity**. Allocating a carrier's risks across these buildings is
  still synthetic, conditional on insurance penetration, product and business
  selection. No real customer or policy inferred from a nearby building.

## Source-product extraction priorities (do not duplicate existing records)

| Source and exact reference | Observation scope | Useful constraints | Critical exclusion / limitation |
| --- | --- | --- | --- |
| [EU 2023/895 ITS disclosure](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0895), [EIOPA current reporting](https://www.eiopa.europa.eu/tools-and-data/supervisory-reporting_en) | EU insurer **solo/group** SFCR and public QRT (2023+ taxonomy) | S.05.01 line GWP/claims; S.04.05 country information; S.17.01 non-life reserves; S.19.01 historical claims where disclosed; S.25 capital; group S.32 | Public tables differ from confidential supervisory templates; EU disclosures not global; reinsurance country is **not necessarily underlying risk situs**; 2026 draft ITS is not retroactive |
| [Allianz 2025 group/solo SFCR](https://www.allianz.com/en/investor_relations/results-reports/sfcr.html) | Group, Allianz SE and linked regulated operating legal entities | Dated entity-specific LoB, country, capital and narrative risk controls | Group and solo must not be summed; insurer vs parent/investment company and intragroup reinsurance not interchangeable |
| [Zurich 2025 iXBRL risk disclosures](https://www.zurich.com/-/media-assets/project/zurich/dotcom/sustainability/docs/ixbrl/ixbrl-viewer.htm) | Net natural-catastrophe AEL and annual aggregate 50/100-year PML by selected peril regions | Independent risk-calibration challenge after CAT + net reinsurance | 2025 AEL net of reinsurance, pre-tax, excludes unallocated loss adjustment expenses; not GUL or TIV. Farmers Exchanges **not owned by Zurich**; Farmers Re treaty separate |
| [Lloyd's 2025 syndicate accounts](https://www.lloyds.com/syndicatereports) | Syndicate-level class/region gross and net premiums, assumed/ceded reinsurance; examples [1945](https://assets.lloyds.com/media-651c0e64-c1d0-4f97-90f7-883c69fe2ef2/97482e49-6cb9-450c-b606-b41dd36047df/1945_Accounts_2025Q4_20260220_151609.html), [2988](https://assets.lloyds.com/media-651c0e64-c1d0-4f97-90f7-883c69fe2ef2/9542f82e-72b1-442d-ac82-3e063e941c34/2988_Accounts_2025Q4_20260220_164810.html) | Some **actual** region x class joint marginals, gross/net and delegated shares | Underwriting location vs risk situs may change between years; Worldwide/Other is not one country; syndicate asset ≠ delegated coverholder asset |
| [Florida OIR MIR](https://qsrng.floir.gov/Reports/ReportCriteriaWizard.aspx) | Reported carrier x policy-type and possible monthly county x ZIP reports from Jan 2025 | State legal insurer company plus product, policies, wind-structure exposure | Official reports explicitly unaudited, query-filtered and revision-prone; exact county/ZIP export must be separately acquired/rights-reviewed; not all-peril TIV |
| [Texas DOI 2025 Page 14](https://www.tdi.texas.gov/reports/report4.html) | 2025 statutory direct premium and loss by legal carrier / line in Texas | Strong carrier x state x LoB observation; crosswalk NAIC IDs | Different from NAIC's licensed full schedules; state direct GWP not group retained risks or insured asset geolocation |
| [Texas homeowners market snapshot](https://www.tdi.texas.gov/general/texas-homeowners-insurance-market-overview.html) | Texas 2025 preliminary market insured value, policy counts, company/group distinction | Regional industry-level covered-value calibration separate from premiums | Market universe/coverage definition; no carrier-level ZIP x TIV from statewide figure |
| [NAIC licensed financial data](https://content.naic.org/prod_serv_idp_info_pro.htm) | Schedules T/F/P/Y and page-14 and policy-count exhibits by insurer | State premiums, property reinsurance, claims development and group affiliations | **Licensed data product, not free redistributable full data**. Existing free NAIC share reports are different source products |
| [Bank of England UK insurance annual aggregates 2025](https://www.bankofengland.co.uk/statistics/insurance-aggregate-annual-data-report) | UK aggregate QRT-based CSV, 2025 | UK life/nonlife and capital macro priors | *Aggregate only*; UK Insurance Taxonomy from end-2024 differs from older EIOPA taxonomy; cannot ascribe to individual firm |
| [APRA quarterly P&C industry statistics](https://www.apra.gov.au/news-and-publications/quarterly-general-insurance-performance-statistics) | Australia industry/LoB/state totals | Macro/state exposure and premium priors | APRA explicitly says **institutional-level GI statistics are on hiatus** under new collection framework; do not pretend the current file is individual insurer data |
| [MAS company returns](https://www.mas.gov.sg/statistics/insurance-statistics/insurance-company-returns) | Singapore company/branch life, GI and reinsurance annual financial returns | Legal-entity financial calibration and Asian branch scope | Missing filings, differing financial year ends, branch vs consolidated group and territory of risk |
| [SEC EDGAR Companyfacts](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) | U.S. public issuer reports / XBRL | Segment-level property, reinsurance, geography and loss narratives | Nonstandard corporate segment tag taxonomy and holdings vs underwriting; not a universal regulator individual carrier statutory data feed |
| [Artemis cat-bond directory](https://www.artemis.bm/deal-directory/) | Deal / cedent / issuer / territory / peril / issuance size | Candidate risk-transfer edges and ILS market footprint | Third-party deal summaries; not ownership of fund holdings, actual treaty terms or original issuer docs; automated reuse rights unverified |

Already present elsewhere in **OpenCatastrophe-data**: EIOPA aggregate
S.05.01 and cross-border premium sources, OECD SDMX classes and underwriting,
GLEIF Level 1/2, NAIC public market-share publications, national licensed-entity
registers, global building footprint and hazard sources, plus Florida/Texas
*isolated* staged research. New named products must remain distinct instead
of duplicating existing candidate IDs.

## Actual examples for challenge design

- **Zurich 2025**: published **net** AEL (USD m): U.S./Caribbean/Mexico
  hurricane 231, U.S. severe convective storm 233, Europe wind 199,
  Central Europe hail 156, Europe flood 136; Europe wind 100-year net annual
  aggregate PML is USD 1,045m. Source explains that 2024 AEL values were
  restated after model changes. These are *holdout targets* for a separately
  fitted net-risk simulation, NOT observed building losses, gross event loss or
  retained catastrophe portfolio identity. Zurich reports a distinct Farmers Re
  all-lines quota-share participation; do not turn the Farmers Exchanges into
  Zurich-owned direct insurance risks.
- **Lloyd's Syndicate 1945**: 2025 gross written premiums in its UK/EU/US/
  Canada/Other x LoB cross-tab add to GBP 210.190m. Explicitly tag reinsurance
  acceptances as a **separate** line and retain Other unresolved. These are
  published cross-tab observations, not property TIV at risk locations.
- **Lloyd's Syndicate 2988**: 2025 gross and net risk-location geographic
  premiums are disclosed, but Other includes **multi-territory/worldwide**.
  A region allocation inside Other is a latent model assumption even when
  the marginal total is observed.
- **Texas 2025**: the regulator's homeowners market snapshot gives a
  preliminary USD ~2.405 trillion covered value and ~8.23m active policies
  for its reported market definition. This constrains industry-scale values
  separately from individual carriers' Page 14 premiums; cannot force an
  individual legal insurer's TIV from an average price-to-value ratio.

## Proposed entity-wide typed model (NextGen consumer, not new Neon DDL)

1. `legal_entity`: source-regulator ID + LEI, license status, effective times;
   `group_consolidation` only with sourced accounting/regulator edge type.
2. `risk_bearing_role`: direct carrier, inward treaty reinsurer, syndicate,
   special purpose reinsurer, ILS investor, MGA delegated **non-risk-carrier**,
   broker/servicer. One legal entity may have multiple dated roles.
3. `published_constraint`: source product, issuer, period/as-of, typed metric,
   currency/unit, gross/net/direct/assumed/ceded, IFRS vs solvency/statutory,
   geography basis, level of aggregation and uncertainty/rounding.
4. `peril_coverage`: actual confirmed covered vs excluded peril, deductible,
   limit and event/aggregate semantics. Never allocate an event peril by GWP
   alone; a motor book, liability cover and named-storm catastrophe policy are
   not interchangeable.
5. `physical_exposure_prior`: region/building/occupancy/industry stock,
   independently modelled replacement cost, vintage, insured take-up
   hypothesis and spatial clustering; **not** insurer ownership.
6. `synthetic_allocation_scenario`: one candidate company-region-LoB
   premium joint matrix and a conditional synthetic TIV/risk distribution;
   immutable seed and versions; separate scenario variation.
7. `contract_graph`: original underlying direct policy risk -> MGA delegated
   writer (optional servicing role) -> insurer retained gross -> outward
   treaty/ILS -> reinsurer inward -> retro. Contract edges carry retention,
   attachment, aggregate/event limits, reinstatements, inception, territory
   and exact uncertainty. NEVER clone the same asset on each node.
8. `cat_challenge_metric`: peril-model output with exact run profile,
   occurrence vs aggregate, gross vs net, return period, confidence and
   disjoint train/holdout role. A valid reported AEL alone does not create
   an event catalogue or validate vulnerability.

### Inverse calibration procedure

A. Choose one legal risk bearer, business year, fixed group consolidation
   perimeter, premium/accounting basis and geographic risk basis. Reconcile
   its filings to one *nonduplicated* direct/assumed/ceded premium universe.

B. Map **hard, mutually compatible** observed margins (e.g. carrier x US state
   x LoB from state Page 14), exact joint cells if truly available, and
   independent company share/report controls. No inferred zeros or negative
   suppression codes. Treat 95%-threshold disclosure Other as unallocated.

C. Build **soft priors**, conditional on class, distribution networks, property
   stock, industry, land use, true country operations, admitted market
   insurance penetration and rate-on-line assumptions. Keep physically
   unsupported cells as explicit *reviewed* structural zeros only.

D. Fit `company x risk-region x line` against hard margins using a
   minimum-relative-entropy / raking objective and retain multiple plausible
   prior specifications. For soft or conflicting constraints use an explicit
   uncertainty-weighted penalized objective; NEVER silently force conflicting
   country/line/quarter/group totals to agree.

E. Generate multiple independent synthetic risk-location draws conditional on
   the fitted cell weights. Sample building type, construction age, size,
   physical replacement cost, contents, business interruption, take-up,
   policy limit and deductible. Reject scenarios outside independent covered
   value, stock, known exclusions and policy-count bounds.

F. Calibrate premium with a declared technical rate distribution: roughly
   premium = sum(insured values x peril/coverage-dependent premium rate) plus
   loadings/fees, under harmonized timing and written-vs-earned definitions.
   **Premium/TIV conversion is never unique**. Perform wide-rate sensitivity.

G. Model direct portfolio GUL -> IL -> FI -> RI -> retro/ILS in NextGen with
   **joint event simulations and occurrence/aggregate ordering**. Keep
   synthetic cedant/treaty and inward share hypotheses conditional and dated.
   Calibrate gross portfolio where gross constraints exist; compare *net*
   modelled AEL/PML with net reported figures only after reinsurance modelling.

H. Hold out independent source families and time periods. Challenge *risk*
   outputs by peril/region and historical cat loss ranges; protect validation
   against leakage from the same disclosure used in calibration. Reject bad
   geography, unrealistically sharp TIV concentration, broken premium
   conservation, false parent/branch duplicates and inconsistent insured
   penetration. Produce a posterior **ensemble**, not a single asserted true
   portfolio.

### Evidence confidence labels

- **A / OBSERVED_PUBLIC**: dated, inspected original reporting table for its
  exact scope; external raw bytes and permitted rights stay outside public Git.
- **B / DERIVED**: reproducible transformation from A, with no extra fictional
  geographic or contract claim.
- **C / MODELLED**: inference from valid A/B and declared population/insurance
  priors; retains uncertainty and source vintage.
- **D / SYNTHETIC**: individual simulated locations, policies or treaties
  consistent with constraints; *never actual confidential underwriting*.
- **BLOCKED**: missing rights, unverified identity, wrong geography, mixed
  accounting basis, unsupported units, missing event/limit evidence,
  unexplained source contradictions or no defensible statistical prior.

A high-resolution building map can improve geographic support yet still yield
only D-level company-level asset assignments.

## Executable, bounded v0 now in this PR

`research_runners/synthetic_insurer_premium_marginals_v0.py` performs
deterministic two-margin fitting using explicitly supplied positive prior
weights and explicit structural zeros. It **rejects** assumed/ceded premiums,
cedant domicile treated as risk situs, unreviewed source observations,
unexplained missing cells, inconsistent totals, invalid numerical data and
infeasible allocation supports. Output carries `model_input_approved=false`,
`has_insured_tiv=false` and `observed_insurer_portfolio=false`.

`tests/test_synthetic_insurer_premium_marginals_v0.py` includes a
**non-identifiability regression**: two different priors yield different
region x line joint distributions with identical observed synthetic margins.
It proves the method preserves constraints; **it does not produce an
insurer-calibrated CAT exposure portfolio**. Run
`python -m unittest tests.test_synthetic_insurer_premium_marginals_v0 -v`
and the repository `python scripts/check_all.py` on a Git checkout.

## Executed local repo/Neon boundary and next admissible slice

Recent insurance-only Neon main inspection shows **22 verified organisation
rows, no production portfolios, no production exposure units, no model
simulation runs and no approved company-specific CAT calibration**.
`research.company_cat_readiness_v0` reports **10** entities needing inward
treaty/cedant exposure, **8** special-purpose entities needing funded risk
and contract evidence, **2** only legal identity, **1** missing geolocated
insured TIV and **1** missing subsidiary/consolidated exposure. Existing
Florida/Texas validation-branch data and 12 synthetic OED demonstration
exposures are not production company portfolios. Prior research already has
an independent original-source Florida MIR county/ZIP reconciliation
proposal and an EIOPA solo annual *market aggregate* CSV parser.

**Next smallest causal run**: acquire one exact 2025 Allianz Versicherungs-AG
SFCR public QRT with page/table/period/version/rights receipt, plus a
matching official Germany/EEA market total; normalize **solo direct** GWP by
LoB and location-of-risk without copying original bytes into Git. Independent
pilots: one Lloyd's *published* region x class matrix and one Florida OIR
**company x county x ZIP x product** original snapshot under separate
rights/coverage review. Only after true original-input checks should a
licensed, isolated research consumer apply an extended fitted model and
compare a holdout CAT loss metric.

### Key research literature

- Custer and Nishijima (2017), [Probabilistic disaggregation of a spatial
  portfolio of exposure for natural hazard risk assessment](https://doi.org/10.1080/17499518.2017.1371761):
  stochastic disaggregation rather than a falsely precise location assignment.
- Mistry and Lombardi (2023), [A stochastic exposure model for seismic risk
  assessment and pricing of catastrophe bonds](https://doi.org/10.1007/s11069-023-05884-4):
  location/attribute uncertainty materially affects losses and ILS economics.
- Pinelli et al. (2020), [Uncertainty Reduction Through Data Management in
  the Development, Validation, Calibration, and Operation of a Hurricane
  Vulnerability Model](https://doi.org/10.1007/s13753-020-00316-4):
  explicitly reconcile insurance, tax/appraisal, geospatial and hazard data
  and preserve epistemic uncertainty.
- Kozlowski and Mathewson (1995), [Measuring and Managing Catastrophe Risk](https://digitalcommons.unl.edu/joap/132):
  company market share may be a practical fallback but can badly misstate
  individual catastrophe loss.

No literature method, source report or disclosure by itself passes the
OpenCatastrophe source-specific rights/scientific gates.
