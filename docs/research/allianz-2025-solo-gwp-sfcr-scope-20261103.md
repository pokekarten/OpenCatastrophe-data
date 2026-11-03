<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Allianz Versicherungs-AG 2025: solo written-premium scope audit

**Research-only dated review 2026-11-03. No external PDF bytes or transcribed source data are committed; no Neon writes or model admission.**

## Exact authoritative original documents identified

- [Allianz Versicherungs-AG, Geschäftsbericht 2025](https://www.allianz.de/content/dam/onemarketing/azde/azd/unternehmenskommunikation/pdfs/unternehmen/zahlen-daten-fakten/geschaeftsberichte/GB_AZV_2025_websafe.pdf), **64 PDF pages**. Original publisher [report index](https://www.allianz.de/unternehmen/zahlen-daten-fakten/geschaeftsberichte/), heading "Allianz Versicherungs-AG".
  - Printed p. 8 / **PDF zero-based p. 9**: table "Gebuchte Bruttobeiträge der Allianz Versicherungs-AG"; direct business broken into policy classes, separately accepted (inward) reinsurance, and combined total.
  - Printed p. 49 / **PDF zero-based p. 50**: GWP, gross earned and **net earned** on the same page, with HGB class hierarchy, including a fire/property subtotal and underlying home contents / building / other property lines. **Do not include both a subtotal and its children.**
  - Printed p. 33 / PDF zero-based p. 34: GWP minus ceded **written** reinsurance = net written premium; net earned premium differs due to unearned-premium reserve movements.
- [Allianz Versicherungs-AG, SFCR 2025](https://www.allianz.de/content/dam/onemarketing/azde/azd/unternehmenskommunikation/pdfs/unternehmen/zahlen-daten-fakten/solvabilitaet/AZV_SFCR_2025.pdf), **106 PDF pages**. Original publisher [SFCR index](https://www.allianz.de/unternehmen/zahlen-daten-fakten/solvabilitaet-und-finanzlage/), "Allianz Versicherungs-AG".
  - Printed p. 13 / **PDF zero-based p. 12**: expressly states **S.04.05 country-of-risk presentation is omitted** under the at-least-90%-home-premium rule. It also reports **0.5% of gross premiums from abroad** in 2025; this **does not** establish a foreign building address or country x LoB matrix.
  - Printed p. 14 / **PDF zero-based p. 13**: gross earned, reinsurers' share and net earned premiums by selected **Solvency II lines**, not identical to HGB written premium categories.
  - Printed p. 85 / **PDF zero-based p. 84**: appendix form S.05.01.01, accounting-based premium/claims/expense table (as labelled in actual report).
- [EU Implementing Regulation 2023/895](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32023R0895), Annex II instructions to S.04.05 and S.05.01. S.04.05 public solo reporting is **exempt where home country represents at least 90% of GWP**. For *reinsurance*, the regulation uses **cedant domicile**, not the actual locations of the insured primary risks, as the "country of risk".
- [EIOPA Q&A #3164](https://www.eiopa.europa.eu/qa-regulation/questions-and-answers-database/3164_en): confirms S.04.04 underwriting location and S.04.05 risk location may differ for inward reinsurance.

## Verified public arithmetic only: scope boundary

Manual read of the annual report **written** premium table (printed p. 8)
shows one exact, visible reconciliation in **EUR thousands**:

`direct written gross 13,024,629 + separately accepted written gross 57,035 = combined written gross 13,081,664`.

The first figure comprises all directly written insurance lines, **not** solely catastrophe property. The second figure is inward assumed reinsurance and must not silently become a primary policy location or be added again after a group-level consolidation.

The annual report's total **ceded written premium** is different from its
year-end gross/earned premium and the SFCR's net earned premium. Published
written and earned amounts, HGB vs Solvency II line classes and source
accounting contexts must be retained independently: the SFCR business
explanation does not provide a missing county/town or company x
country x LoB table.

**Why this matters:** A national insurer's 90% threshold exemption does not
mean "100% German risk sites"; likewise the 0.5% abroad does not reveal
foreign company risk locations or exposure value. Even if all risk sites
were geographically known, written premiums would not identify property TIV
without an admitted hazard/coverage/rate model.

## Implemented executable preflight

`research_runners/solo_insurer_gwp_control_v0.py` consumes an **operator-local**
normalized JSON table and the exact operator-local issuer PDF. It:

1. Requires explicit `solo`, `local_statutory_gaap`, `gross_written_premium`,
   `thousand_eur`, calendar year-end and a public HTTPS original source.
2. Computes SHA-256 over the **actual operator-supplied PDF bytes** and rejects
   a mismatch with the declared 64-hex digest. This proves local byte
   consistency only; publisher identity still needs external inspection.
3. Checks unique atomic direct LoB codes and exactly conserves separately
   reported direct, assumed and combined premiums using `Decimal`.
4. Rejects input claiming known country-of-risk from a premium-line table,
   group scope, missing/suppressed/negative rows, net vs gross, or earned vs
   written premium, and unverified fields beyond the explicit contract.
5. Emits an **audit receipt** (sha, page index, counts, semantic flags) but no
   source premium row values. `model_input_approved=false`, extraction
   verified=false, rights reviewed=false and geographic/TIV fields=false.
   It does **not** load, relicense or approve observed data in Neon.

Offline checks are deliberately **fully invented**, with a toy local PDF
signature and unrelated round numbers in
`tests/test_solo_insurer_gwp_control_v0.py`. No Allianz source numbers or
publisher PDF bytes are fixtures. The algorithm cannot assert its manually
transcribed rows match visual source tables without an **independent reviewer**.

## Next bounded source-evidence step

Acquire exact publisher PDF original bytes **outside Git** under a reviewed
product rights/access decision; calculate SHA-256 and file size, then
independently transcribe every *atomic* printed-p.8 GWP LoB row into
operator-private JSON with the exact source page reference. Run the
preflight locally and compare the count, original period and currency.
Separately compare the S.05.01 **earned** by LoB and the annual-account net
written/earned flows without forcing incompatible measures to equal.

This pilot is **only a financial-statement control**. To construct a
data-grounded synthetic Allianz Germany property book, acquire an
independently reviewed *regional* risk/insurance penetration prior,
property-value distribution, cover type and rating uncertainty; preserve the
unknown foreign-premium residual; then calibrate a scenario ensemble in
NextGen without asserting policy-level real observations.

## Current data-store / progress boundary

Earlier independent Neon main inventory: 22 verified organisations,
`entity.published_metric=0`, `exposure.portfolio=0`,
`exposure.exposure_unit=0`, `model.simulation_run=0`. The present change
does **not** import the annual-report values, claim legal or commercial
permission to run bulk report extraction, create an insured portfolio, or
alter any current data/database admission flag.
