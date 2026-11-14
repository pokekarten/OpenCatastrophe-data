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

## Additional original-source observation: contract stock and reported claims

Independent visual/source inspection of the official annual report, **printed
p. 50 / PDF zero-based p. 51**, found its table **"Anzahl der mindestens
einjährigen Versicherungsverträge und der gemeldeten Schäden"**. For 2025 it
reports by HGB fire/property sub-line **year-end contract stock** and
**annual reported claims**. This is a new, materially stronger set of
calibration constraints than gross written premiums alone.

Independent *arithmetic* reconciliation of the printed fire-and-property
group and its four sub-lines (fire, contents, connected residential building,
other property):

| Published group control (2025) | Independently sum of four sub-lines | Published group amount | Arithmetic result |
| --- | ---: | ---: | --- |
| Direct gross **written** contributions, EUR thousands (printed p. 8) | 3,372,507 | 3,372,507 | Equal |
| Stock of contracts **at least one year** (printed p. 50) | 5,645,881 | 5,645,881 | Equal |
| **Reported claims**, annual all-claims universe (printed p. 50) | 405,700 | 405,700 | Equal |

These three checks refer to the same **HGB fire/property insurance
classification** at two pages of the **same original annual report**.
Never sum a fire/property parent row on top of its four direct children.
Even within property lines, one structure may have multiple policies and
a policy may cover more than one object. Therefore contract counts are
**not unique buildings** and reported losses are **not event/peril-only**.

Two focused, publicly reported line observations have an illustrative
research-only ratio: connected residential building (2025 written GWP
EUR 1,999.741m, year-end contract count 2,321,478, all claims reported
237,977) gives **EUR 861.41 annual written premium / year-end contract**
and **0.102511 all reported claims / year-end contract**. Home contents
(EUR 522.370m, contracts 2,946,112, reported claims 123,994) gives
**EUR 177.31** and **0.042087**, respectively. These **are not measured
policy rates, exact actuarial claim frequencies, individual TIV, mean
insured losses, regional allocations, weather-event counts or a company
CAT risk exposure**. Their numerators are annual flows whereas
denominators are year-end stocks and include changing policy mix.

**Executable, nonpromoting cross-table control:**
`research_runners/solo_insurer_stock_claims_control_v0.py` reuses the same
privately supplied PDF fingerprint and validates matching legal entity/year,
distinct source-page evidence, exact matched atomic LoB names and three
separately tested published parent controls (premiums, contract stock,
claims). It rejects a parent also counted as an atomic premium LoB,
overlapping rollups, unknown child lines, source/period mismatch and
silent CAT/geography assumptions. Derived reference ratios are returned
as labelled research diagnostics, never model inputs.
`tests/test_solo_insurer_stock_claims_control_v0.py` uses **17
independently invented** scenarios; no publisher PDF or external rows
committed as test fixtures.

**Original bytes gate is STILL BLOCKED:** The official PDF is visually
available through the public browser and the original source pages were
inspected, but this session's local container could not retrieve full
original file bytes. A separate service returned only a truncated base64
document. No current SHA-256 or full 64-page local byte receipt has been
claimed, and neither validation runner was executed against the full
real report bytes. No usage-rights decision or production Neon write is
implied by source-page visual verification or aggregate arithmetic.

## Independent gross NatCat observation: NOT an event-loss catalogue

The original Allianz Versicherungs-AG 2025 annual report, **printed p. 8 /
PDF zero-based p. 9**, additionally states that gross **expenses for
elemental damage within the reporting business year** were **EUR 277 million
in 2025** versus **EUR 906 million in 2024**. This is a public
insurer-specific CAT-associated accounting observation, distinct from the
**405,700 annual reported claims** in the broader fire/property LoB
population, distinct from group loss and distinct from a catastrophe-event
GUL/YLT. Do **not** classify all 405,700 reports as catastrophic events,
interpret this gross elemental expense as an AEL or 200-year PML, or infer
wind/hail/flood proportions from this one disclosed annual number.
For a NextGen annual CAT loss comparison, the reviewer must establish the
insured-peril definition, calendar/event/underwriting/reporting year,
gross / direct / assumed / net basis and reserve-development alignment.

Original issuer document: https://www.allianz.de/content/dam/onemarketing/azde/azd/unternehmenskommunikation/pdfs/unternehmen/zahlen-daten-fakten/geschaeftsberichte/GB_AZV_2025_websafe.pdf

## Executable fully synthetic geographic inverse problem

New repository files:
- research_runners/synthetic_regional_property_book_v0.py
- tests/test_synthetic_regional_property_book_v0.py

The operator supplies independently **fictional** solo national
year-end contract stock, annual written gross EUR cents, year-end and
fictional regions. Regions declare *synthetic* capacities in
contract-equivalent units, scenario prior weights, written-premium
relativities, *hypothetical* market elemental penetration and independent
assumed carrier-vs-market take-up multipliers.

A deterministic capacity-bounded weighted water fill + Hamilton rounding
**exactly** conserves total integer contract counts. A separate cent-exact
partition **exactly** conserves annual gross written premiums. The output
computes hypothetical elemental-cover contract-equivalents bounded by
allocated contracts. It does **not** identify insurer-specific coverage
or actual assets. Changing the assumed regional weights gives different
county distributions with the same nationally conserved stock/premiums.
Changing carrier elemental coverage assumptions changes the elemental
count without changing any observed original national control. This is
a constructive demonstration of **non-identifiability**.

Output explicitly rejects any claim that flow/stock ratios are technical
tariffs, that end-year contract counts are unique residential buildings,
that market elemental penetration equals company-specific penetration, or
that the generated rows are insurer observations, true risk-site
coordinates, CAT losses, TIV, reinsurance treaties or approved model input.

The GDV industry-wide 2026 data service states that in 2025
**10.6 million residential buildings** had broad elemental insurance,
**59% broad elemental penetration** relative to its residential building
fire reference population, versus **96% wind/hail residential building
coverage**. Some rainfall-only contracts are excluded from the broad
elemental statistic. Official:
https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-elementar/versicherungsquote-bei-elementarschadenversicherung-steigt-kontinuierlich--147644

The separately registered 2026 **GDV district-level** source documents
strong industry-wide spatial variation, **not any Allianz district
allocation**:
https://www.gdv.de/gdv/statistik/datenservice-zum-naturgefahrenreport/sachversicherung-elementar/versicherungsdichte-bei-elementarschadenversicherung-regional-sehr-unterschiedlich-183592

The already-registered official **Destatis Zensus 2022 buildings grid**
is downloadable with attribution and 10 km / 1 km / 100 m geometry.
Its 2022 reference date differs from the 2025 Allianz/GDV policy year.
The grid counts are neither unique company-insured risk sites nor
confirmed exposure locations. Confidentiality suppression and the
2022-to-2025 vintage change must be addressed before using regional priors.
Official:
https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_inhalt.html

**Remaining causal science gate:** normalize exact insurer, district,
industry elemental and Zensus population definitions and vintages.
Build two distinct permitted geographic priors to stress test
wind/flood modeled losses and compare only to compatible independent
public gross loss controls. The original Allianz full PDF byte SHA and
per-source redistribution review remain *blocked*, and the new runner
continues to use only fully invented inputs.
