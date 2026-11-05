<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V Berlin 2025 named housing insurers: direct Senate PDF original-source byte receipt

**2026-11-05.** This is a read-only source-provenance upgrade for the already merged, scientific-scope-bounded Berlin source register [#1339](https://github.com/pokekarten/OpenCatastrophe-data/pull/1339). The prior government numeric facts were manually reviewed against original public Berlin Senate PDFs, but the original file SHA-256 was **not verified** and the source register correctly records this limitation.

## Original publisher and strict two-document roles

- [Drucksache 19/22033, 1 April 2025, 6 pages](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf). Q2 is the original named-corporate-housing insurer evidence: GESOBAU AG and WBM have a building insurance contract with **R+V Allgemeine Versicherung AG**; **degewo** is part of a consortium with Allianz AG and R+V Allgemeine; other landlords have named **other insurers**. Q3 refers to corporate **overarching building master policies**, not one policy for every dwelling/physical building. WBM separate commercial policy terms must not be assumed R+V-covered; Q4 states peril cover types for the municipal housing companies generally, *not* exact R+V location schedules.
- [Drucksache 19/24229, 11 November 2025, 5 pages](https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24229.pdf). Q2 tabulates **12 Berlin borough × seven municipal housing-company *DWELLING* stocks**, dated **30 June 2025** for six state companies and **30 September 2025** for Berlinovo, plus non-borough-assignable other stock. Public totals are degewo **82,637**, GESOBAU **49,054**, WBM **34,040** dwellings, six main companies **376,278** and Berlinovo **18,666**. These are not building/contract/insured sums, not insurer claims or country-wide 2025 R+V policies.

The overlap of the three *R+V named corporate relationship* companies is a publicly evidenced **corporate customer presence**, not a proof all the company's dwellings, roofs and buildings are insured by R+V or its share in degewo's co-insurance.

## Reproducible exact original proof, no data redistribution

Source-only runner `research_runners/rva_berlin_senate_original_pdf_source_v0.py` downloads **only two allowlisted original `pardok.parlament-berlin.de` PDFs**, bounded at 5 MiB each, reject cross-site redirects and malformed/truncated PDF. `pdftotext` extracts transient text in a temporary directory, never exported to Git, artifacts, private files, stdout, or insurer database. The runner prints only per-document **actual SHA-256 digest, original bytes, page counts, count of positive source markers** and mandatory negative insurer-model admission flags. Revisions of the publisher PDF under an unchanged URL are not silently accepted after the first SHA is pinned.

**Initial run is for SHA discovery, so `exact_original_sha256=None` is honest rather than fictional.** A follow-up exact HEAD/CI-reviewed commit must pin both SHA hashes, byte sizes and re-run both original sources, then update the prior source receipts with *actual* original evidence. Success at merely finding a PDF does **not** validate all copied 12×7 cells; the original source was visually checked separately and the independent 12-row/7-column totals are all within source factual conservation tests.

The workflow uses fixed 40-hex GitHub Actions, read-only token, explicit `poppler-utils` installation and 11 synthetic negative tests for source scope, redirect, truncation, malformed numeric/categorical extraction, over-size, and truthful original-vs-fake model claims. No raw publisher PDFs are committed.

## Post-source proof use

Join an observed **named insurer-to-corporate customer relationship** to a separately publicly observed **corporate housing company's geographic dwelling count** only as *uncertainty-bounded market-opportunity research*. The existing 0%/50%/100% arbitrary degewo share weights in merged #1339 are explicit sensitivity parameters, not calibrated participation or claims.

**Still UNKNOWN:** 2025 exact company contractual covered-property list, coinsurance degewo share, TIV/insured replacement costs, site geocodes, actual property vs dwelling ratios, coverage deductibles/limits, insurance historical losses, current 2026 renewal, R+V national building-contract mass allocation, German CAT peril frequency and individual risk vulnerability, actual outward treaties and net loss curves. These must not be inferred from Senate document authenticity alone.
