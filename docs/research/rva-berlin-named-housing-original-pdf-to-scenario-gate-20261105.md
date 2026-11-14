<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# R+V Berlin housing accounts: connect original PDF provenance to the hypothetical borough scenario

**2026-11-05. Research only, no actual insured R+V asset count or TIV.** This small integration binds two merged but previously separate evidence layers:

1. [#1339](https://github.com/pokekarten/OpenCatastrophe-data/pull/1339): publicly named building-insurance corporate clients (WBM, GESOBAU and Allianz/R+V degewo consortium) and public company housing *dwelling* stock 12-borough matrix with three hypothetical 0/50/100%-degewo R+V participation/covered-stock sensitivity cases, NOT insurance schedules.
2. [#1342](https://github.com/pokekarten/OpenCatastrophe-data/pull/1342): actual publisher-downloaded, SHA256-byte-pinned Senate PDFs `19/22033` and `19/24229` with six/five pages and original file size; original source CI redownloads both and checks provenance.

Previously the fictional borough scenario runner checked its local public insurer/stock TOML records but had **no explicit dependency on the later original PDF receipt**. The new `validate_pinned_original_pdf_receipt()` is now called **at the very beginning** of `validate()` before either corporate source is used. It enforces two expected immutable original SHA-256 hashes, complete original bytes and pages, exact original URLs, printed source dates, original positive semantic marker counts and all relevant exclusion flags, based on original-source registry `research/observations/rva_berlin_senate_2025_original_pdf_receipts_v0.toml`.

## Why this protects the model

- A scenario computed from an outdated or tampered original source registry must **fail**, not silently reuse source-unattested Berlin housing account labels.
- The scenario audit reports `official_2025_senate_two_original_pdf_hashes_matched=true` but explicitly distinguishes that **this run verifies the pinned attestation**; it does **not** itself fetch either PDF, parse all twelve borough rows from the source again, or verify ongoing URL availability. The independent original-source CI in #1342 performs publisher redownload and SHA matching.
- An original 2025 R+V building master client relation does NOT prove all 165,731 linked corporate *dwellings* are covered; 162,883 is the corporation's Berlin borough dwelling physical-opportunity sum, not an object insured exposure total.
- The 0/50/100% degewo cases are user-invented sensitivity assumptions, not actually observed insurer participation, reinsurance coinsurance, net of deductibles, co-insurer shares, geographic R+V policy site assignment or covered gross/net TIV.
- No PII, insured risk addresses, source PDFs or individual residential property is added to Git. Full official public attribution and source-vintage annotations remain mandatory.

## Correct downstream next experiment

Separately build a **fictional commercial-landlord building archetype** by borough using true publicly reported owner-company dwelling density, transparent guessed `dwellings_per_building` and `building_replacement_cost` parameter ranges and audited external cost-index source, never treating rented dwellings as R+V insurance policies. Keep degewo insurer involvement as a separate hypothetical participation parameter. Then only when licensed wind/hail/flood hazard and independent vulnerability and hypothetical coverage/treaties are present, run a complete event-key-consistent native CAT GUL → IL → outward RI/Net → AEP/OEP sensitivity. A generic Senate source cannot support a company-specific real loss curve without those assumptions and further validations.
