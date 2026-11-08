<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Public named-insurer corporate-account report projection (Berlin v0)

**Scope:** A reproducible, research-only view of the [official April 2025 Berlin Senate answer 19/22033](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf) from the **already-merged, machine-readable** [six-company observation](../../research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml). This report is useful for several *named* insurers without producing speculative individually insured assets. The original publisher PDF SHA/byte independent check is tracked separately from this view; source authenticity and geography-to-insurer modelling are not inferred.

## Run

```bash
python research_runners/public_named_corporate_insurer_report_v0.py > /tmp/public_named_insurer_accounts_research.json
python -m unittest discover -s tests -p 'test_public_named_corporate_insurer_report_v0.py' -v
```

The command emits deterministic JSON to stdout (never a public data dump or a database write), including the SHA-256 of the exact input observation bytes, original public document URL, as-of date, sorted named carrier labels, eight named carrier→company *associations* over six companies, explicit consortium roles, and auditable booleans that forbid promoting these statements to actual insured assets. It does not download external material or contact an external service. These are **eight named associations, NOT eight separately negotiated contracts**.

### Example report interpretation

| Name in original publisher response | Linked public company accounts | What is **not** established |
| --- | --- | --- |
| R+V Allgemeine Versicherung AG | GESOBAU, WBM, degewo | Address/site TIV or share of degewo consortium; renewed business in 2026 |
| Allianz AG (original label) | degewo, STADT UND LAND | Share of degewo consortium, any per-building schedule or precise legal-entity LEI |
| ERGO and Generali (separate original labels) | Gewobag | Joint insurer consortium, insurer-specific split or exclusive building coverage |
| Westfälische Provinzial Versicherung AG (original label) | HOWOGE | Ownership, insurer geographic policy stock, 2026 renewal |

The official source documents *company-level building insurance providers*. Multiple providers named for Gewobag are **not** evidence of a formal insurer consortium. The degewo insurer consortium is explicitly named, but **neither exact participating percentage nor co-insurance share is known**. Other insurers' names being reported is not evidence that R+V never insured any property at those accounts.

The source describes company-wide blanket insurance relationships. Each housing company's *dwellings*, *buildings*, *policies*, *sum insured*, and *insurer-specific expected losses* are all different quantities. Any borough dwelling distributions from [the separate November 2025 Senate report 19/24229](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24229.pdf) must be kept as a **separate physical opportunity layer**, not automatically joined as verified carrier risks.

## Technical and scientific boundaries

- The export only trusts the exact existing input version and government provenance fields; it rejects source contradictions, duplicate carrier labels or companies, missing records, unobserved risk locations/TIV or claims of 2026 renewal. It uses original publisher labels, not guessed LEIs or canonical insurer groups.
- Any future generalization to other insurer/customer records needs a new versioned source adapter with its own government or corporate provenance checks. The current Berlin input is deliberately bounded to six specific company-source rows.
- It does not use or change the pending research PR that attaches independent original-PDF receipts to R+V borough sensitivity calculations. Source-receipt authenticity, contract evidence and insured-asset admission remain independent checks.
- This is **not** a `landscape/` discovery source or a `manifests/` accepted CAT input. It is a read-only projection of existing typed research evidence; no new rights are asserted, no third-party original PDF bytes, policyholder contact data or property site addresses are copied.
- An eventual report must cite the original source, show date/legal-label limitations, and distinguish observed corporate relationships from synthetic insurer exposure and calibrated model output.

**Next:** After source/licensing review, add insurer legal-entity resolution (e.g. official regulator/LEI mapping), as a separate original-backed observation; and independently build controlled hypothetical *opportunity* portfolios using physical building and product features without replacing these observed account relationships.
