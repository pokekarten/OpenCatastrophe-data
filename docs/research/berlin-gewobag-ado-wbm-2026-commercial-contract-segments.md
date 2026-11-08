<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Two Berlin public-property insurance cohorts: Gewobag 2019 ADO and WBM September 2026 commercial award

**Research checkpoint: 2026-11-05.** The evidence is deliberately *source-dated and cohort-specific*. It is a scientific *opportunity/contract research* constraint, not an admitted exposure file, per-site risk register, reinsurer treaty, or real CAT model calibration. Read-only [canonical typed observations](../../research/observations/berlin_lwu_procurement_named_property_segments_20261105_v0.toml) feed one [deterministic cross-source guard/export](../../research_runners/berlin_lwu_procurement_property_segment_crosscheck_v0.py), rather than copying numeric observations into another editable canonical source.

## Three independent source events

| Evidence | Original/source reference | Exact scope and important non-inferences |
| --- | --- | --- |
| **Gewobag 2024 property insurance tender** | [Official TED 558592-2024](https://ted.europa.eu/en/notice/-/detail/558592-2024), [readable public 2024 tender mirror](https://de.openprocurements.com/tender/2024-gebaudeversicherung-mkn/) | Gewobag procurement 221-24, notice 13 September 2024; separate **main building contract vs side contract** for about 6,000 dwellings historically acquired from ADO Properties on 1 December 2019, located broadly in Spandau and Reinickendorf. Source says insured-value calculation is based on usable dwelling/commercial floor areas and calls for harmonisation. Inclusion of additional subsidiaries/properties could be unreasonable beyond a 10% increase in floor area: **not observed growth**. The original TED XML/JSON bytes and actual 2024 awardee are **not** verified by this research; a tender itself is not a winner or a current policy. |
| **Gewobag 2024 IFRS original issuer accounting note** | [Gewobag 2024 IFRS annual report, printed page 54](https://berichte.gewobag.de/fileadmin/assets_2024/PDFs/Gewobag-Geschaefts-und-Nachhaltigkeitsbericht-2024-IFRS.pdf) | At 31 December 2024 the ADO-origin portfolio is described as **21 property objects, 5,894 residential dwellings, 65 commercial units, 1,433 parking spaces, 139 other units**. CBRE's published market fair value is **EUR 821.190 million**, including **EUR 15.010 million** of possible densification potential, compared with **EUR 819.481 million** in 2023. Original issuer report content was read from the public source, **not independently original-byte SHA-pinned** here. Investment property market value is NOT insured reinstatement value, and 21 property objects need not be 21 separate insured structures. |
| **WBM 2026 nine-commercial-objects property award** | [Official TED 668506-2026](https://ted.europa.eu/en/notice/-/detail/668506-2026), [public notice mirror](https://auftragsatlas.de/ausschreibung/industrielle-sachversicherung-fuer-reine-gewerbeobjekte-1172391) | Reported award 21 September 2026, published 29 September, for property insurance covering **nine purely commercial objects**. Named awardees: **HDI Global SE, Helvetia Schweizerische Versicherungsgesellschaft AG, R+V Allgemeine Versicherung AG**. The displayed EUR 0 figure is **not** real insurance premiums, actual claims, policy limit or reinstatement TIV; this source has not established each insurer's share or nine distinct geocoded insured buildings. We have not SHA-pinned original TED eForms bytes. |

The 2024 issuer source's **5,894** ADO-origin apartments and the 2024 tender's **approximately 6,000** historical acquired apartments are *not two additive portfolios*. They differ in exactness/reporting vintage, and may refer to the same cohort. As a separate later reference, the 2025 Senate row has **75,091** Gewobag corporate dwellings total. A 2019 acquired property cohort must not be **added** to those 2025 stocks or mapped to individual 2025 properties without a year-specific confirmed ownership/area crosswalk.

Similarly, the published 2025 Senate WBM **34,040** corporate dwellings are neither the nine pure commercial 2026 property objects nor nine established policy numbers. Three named awardee companies **do not** imply 27 separate insured buildings or any equal co-insurance percentages. The 2026 WBM property award is a stronger named-contract *lead* than a vague agency or bank channel, but exact legal counterparty, shares, perils/limits and original eForms verification remain separate gates.

## Cross-source automated checks and reproducibility

```bash
python research_runners/berlin_lwu_procurement_property_segment_crosscheck_v0.py > /tmp/berlin_property_segments_research.json
python -m unittest discover -s tests -p 'test_berlin_lwu_procurement_property_segment_crosscheck_v0.py' -v
```

The offline runner validates the existing original-Berlin-Senate-PDF receipt through the merged borough-stock validator, checks the original Senate 2025 Gewobag/WBM company totals, validates numeric issuer and published notice facts, and emits an SHA-256 of each **local typed research input**. It does **not** claim external original TED or IFRS files were downloaded and hashed in this run. Wrong awardee, wrong original date, 5,894 added to 75,091, market-value-to-insured-TIV promotions, 10%-option counted as realised growth, and automatic three-winner × nine-object exposure allocations must fail. The synthetic negative tests introduce no external data or actual customer asset addresses.

**Next best causal task:** Acquire the exact official **TED 558592-2024** and **TED 668506-2026** eForms XML or JSON responses, pin complete original-byte SHA-256, legal rights and original field paths, then independently verify winner entities and the real division of coverage if published. Separately compare Gewobag's 2019 ADO-origin stock to identifiable public company assets/areas, rather than forcing a county-level dwelling-to-insured-building conversion. Only after a licensed building archetype/valuation and explicit carrier allocation scenario can this research constrain synthetic property CAT portfolios. No database admission or risk-location export is authorised here.
