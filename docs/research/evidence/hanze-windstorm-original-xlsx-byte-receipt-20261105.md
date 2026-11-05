# HANZE 1950–2020 European windstorm original XLSX byte-identity receipt (research only)

SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

**As checked:** 2026-11-05. **Source identity checked; raw source not committed; original scientific/rights admission FALSE.** Companion canonical dataset entry: `landscape/sources-windstorm-observed-loss-validation-20261105.json`.

## Original upstream identity

- Original authors: Terefenko, Paprotny, Śledziowski and Giza, University of Szczecin / European Commission JRC commissioned windstorm-impact collection.
- Publisher record: [Zenodo v1.0, 2025-04-23, DOI 10.5281/zenodo.15266959](https://zenodo.org/records/15266959).
- **Actual single attached file** (regardless of catalogue narrative referring to CSV/GIS formats): `HANZE European Windstorm Impact Database 1950-2020.xlsx`.
- Canonical provider file endpoint: [original XLSX on Zenodo](https://zenodo.org/api/records/15266959/files/HANZE%20European%20Windstorm%20Impact%20Database%201950-2020.xlsx/content).
- Complete original file size: **292136 bytes**.
- Published file MD5 in Zenodo record/API: **`0a523543adf76003916186623812ab74`**.
- **Independently recalculated on the complete exact bytes: MD5 `0a523543adf76003916186623812ab74` — MATCH.**
- **Independently calculated full original file SHA-256: `c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944`.**
- ZIP/XLSX first four raw bytes: `50 4b 03 04` (PK ZIP local file header).
- Source metadata `access_right=open`, record licence ID `cc-by-4.0`. The separate [HANZE windstorm source site](https://www.windstorm.naturalhazards.eu/about) describes its data as for research purposes only and requires citations; the underlying provider records have their own conditions. **Neither third-party rights nor scientific model admission are confirmed by the Zenodo metadata licence alone.**

## Bounded original-byte verification protocol

An initial single proxy response was **silently capped at 59193 bytes** and was correctly rejected as a complete original-source receipt. The same public Zenodo file endpoint was then requested in **eight explicit, contiguous HTTP byte ranges**, each returned with its exact requested length:

```text
0-40959, 40960-81919, 81920-122879, 122880-163839,
163840-204799, 204800-245759, 245760-286719, 286720-292135
```

The chunks were assembled in order into a 292136-byte in-memory array (no missing/overlapping byte ranges). The MD5 and SHA-256 functions were independently validated against known empty-string and `abc` vectors **before** calculating the source hashes. The full-file MD5 matched exactly the published original publisher checksum; the resulting SHA-256 is independently reproducible from the file URL. The **truncated 59193-byte response SHA-256 is not a valid original identity and is intentionally not recorded as source proof**.

**No raw original XLSX, location/claims, personally identifying records, licence tokens or unrelated binary data were committed to Git.** An ephemeral in-memory byte stream and a source hash are distinct from a locally retained original archive. This receipt documents the identified file version and verified transfer completeness, not an indefinite publisher content guarantee or cryptographic signature from Zenodo.

## Previewed workbook scientific content (separately unadmitted)

The provider XLSX was independently converted into a *truncated* Markdown workbook preview. The observed first worksheet is `windstorms 1950-2020`, with 20 columns including event/country ID, year, country, start/end date, named storm source, affected NUTS2/NUTS3 regions, nominal losses and original currency, *2020 EUR millions*, free-text notes, CDS and original source references. The entire workbook was **not** parsed into a canonical event table or checked row-by-row for duplicates, NUTS vintage, units and provenance. No country-level event-loss output from this source is yet model-admitted.

Example `Kyrill` entries in the parsed view have country-specific IDs for Austria 20034, Belgium 20076, Czechia 20104, Denmark 20128 and France 20250, all spanning around 2007-01-18. **These are country contributions or reports to a potentially shared physical storm**, not five physically independent annual wind events. In particular Austria row 20034 explicitly states **"Modelled economic loss from CDS"**, an unacceptable *independent observed holdout* for C3S/CLIMK model validation. The other visible entries cite EM-DAT, Copernicus and third parties, with possible shared source ancestry and heterogeneous measurement status. Their economic loss values are not actual paid insurer claims or site-level severity.

## Required gates before scientific use

1. Validate **the complete original XLSX workbook schema and every source row** using the full source bytes under the current, pinned SHA-256. A truncated Markdown preview is insufficient for row-count claims or full deduplication.
2. Verify event naming, date-window intersection, NUTS administrative-vintage semantics and the original reference lineage. Treat missing loss as **unknown, not zero**; keep nominal, inflation-converted 2020 EUR and insured loss separate.
3. Separate primary *observed* source evidence from provider-modelled/derived values before any independently scored holdout. Enforce full storm identity deduplication across **country rows** and disclose partial country coverage.
4. Review downstream source rights and potential conflicts between record CC BY 4.0 and source-site "research purposes only"; retain raw source and any derived regulated claims outside public Git until approved.
5. Only then attempt source-bounded country-level economic-loss calibration/benchmarking. This source is **not** a stochastic occurrence-rate model, a fitted 24-asset damage-correlation coefficient, a direct insurer portfolio, a treaty/retro record, or a Gross/Net AEP/OEP result.

**All admission flags remain false; PR research Draft.**


## Reproducible pinned source acquisition implementation

The exact source receipt and the previously checked 8-range HTTP transport are implemented as a **standard-library-only** research utility, `research_runners/hanze_windstorm_original_xlsx_acquisition_v0.py`. Its default CLI only prints the expected file identity and performs **no network access**. The optional execution explicitly requests the same eight source byte ranges, requires exact HTTP 206 and Content-Range offsets and complete lengths, independently checks the pinned MD5 and SHA-256, and then checks Office XLSX ZIP members and CRCs. The original response and machine-readable, non-admitted receipt are written only to a caller-controlled external directory, with exclusive file creation and no overwriting.

```bash
# Always safe: no download, no authentication.
PYTHONPATH=. python3 research_runners/hanze_windstorm_original_xlsx_acquisition_v0.py

# Explicit public original-data acquisition. Choose a directory OUTSIDE Git.
PYTHONPATH=. python3 research_runners/hanze_windstorm_original_xlsx_acquisition_v0.py \
  --execute --out-dir /private/local-hanze-original-downloads
```

New offline tests use a **generated toy XLSX**, an injected fake HTTP range responder, and controlled malformed original-source inputs; they **do not embed, download or assert admission** of actual provider data. The live 2026-11-05 source hash in this receipt was independently calculated by byte-range reconstruction in the connected source-fetch environment, **not** by a CI run of the new Python utility. A green repo CI for the new tests confirms defensive code only, not a separate executed native source download.


## 2026-11-05 – full original two-worksheet row audit (not just workbook preview)

The **entire original 292,136-byte SHA-256-pinned file** was reconstructed in eight verified Zenodo byte ranges, decompressed as XLSX ZIP/XML and all original two worksheets inspected with original shared strings. This supersedes the prior truncated preview limitation for workbook structure. It does **not** establish that every publisher impact record is independent, observational or an insured claim.

- Archive: **12 ZIP parts**; **5,294 shared strings**.
- Impact worksheet dimension **A1:T1359**: 20 exact source columns; **1,358 impact country-event rows**, **1,358 unique publisher row IDs**, **33 country codes**, event year range **1950–2020**.
- References worksheet dimension **A1:E816**: **815 source/reference entries**, not 815 independently observed disaster events.
- The original economic-loss column named **"Losses (2020 euro) in milions"** (publisher spelling) has **720 nonblank cells** and **638 genuinely blank cells**. A preliminary unanchored pattern matcher incorrectly attached subsequent cell content to Excel self-closing blank cells, temporarily reporting 935 nonblank/423 blank. Strict cell-closed parsing corrected that. **Missing economic loss is unknown, never zero**.
- The separate original **CDS column S** contains **299 entries**, with the exact publisher text **"Modelled economic loss from CDS"**. These 299 are explicitly modelled economic losses, not independently observed claims or external truth for C3S/WISC/CLIMK calibration. The 1,059 other publisher rows are **not automatically independent observations**: original reference/circularity/insured/economic status must be checked.
- Twelve country-scoped named KYRILL rows occur around 18 January 2007; **four (AT, IE, LU, PL)** explicitly carry the modelled-CDS label. They are at most candidate country contributions to a potentially shared physical storm, **not twelve separately sampled annual storm events**.
- Preliminary literal-date comparisons flagged four apparent start-after-end cases. On strict review, **three** have valid source Excel 1900-system serial dates that must first be normalized. For example: raw 31263 = 1985-08-04; 31296 = 1985-09-06; 43641 = 2019-06-25. One source QA anomaly remains: publisher row **21072 (Spain)** with raw start 42768 = **2017-02-02**, raw end 41672 = **2014-02-02**. Do not silently alter the original row or infer that either date is the correct storm date.
- The original source file **does not give a verified unique cross-country physical parent-event ID**. Its 1,358 reported country impacts must never be treated as 1,358 annual independent occurrences or used directly to infer a storm Poisson rate.

New strict stdlib reader: research_runners/hanze_windstorm_original_workbook_audit_v0.py, with synthetic-only regression tests in tests/test_hanze_windstorm_original_workbook_audit_v0.py. The reader checks the exact original published file MD5 and full-source SHA-256 before parsing, validates 20 original column names, blocks unexpected formulas/DTD/entity declarations, handles shared strings, preserves truly missing cells and Excel date serials, ensures unique publisher IDs and produces only an aggregate **research not-admitted** report with Kyrill country IDs. Source-specific invariant checks pin observed dataset dimension, modelled row count and missing economic-loss count to detect drift. It never promotes country economic loss to insured claims or builds an annual OEP/AEP curve.

Optional existing-original-file, **no network** replay after authorized source download to an external directory:

    PYTHONPATH=. python3 research_runners/hanze_windstorm_original_workbook_audit_v0.py --original-xlsx "/private/local-hanze-original-downloads/HANZE European Windstorm Impact Database 1950-2020.xlsx"

The complete original workbook *was* analyzed as bytes in the research tool environment. The new Python regression and exact full-checkout CI are separate execution gates; until those are checked, do not claim the new local Python CLI has parsed the real original. No original XLSX was committed. No scientific provider/circularity/rights admission or insurer Gross/Net AAL, AEP or OEP has occurred.


## Kyrill cross-country report candidate contract – 2026-11-05

A strictly **non-admitted** candidate report grouping is now attached to the original workbook audit via `kyrill_country_source_candidate`. It recognizes the original twelve different **country-report publisher row IDs**, not twelve storms and not a verified shared physical event. The pinned original-source pairs are:

`AT/20034`, `BE/20076`, `CH/21154`, `CZ/20104`, `DE/20457`, `DK/20128`, `FR/20250`, `IE/20576`, `LU/20741`, `NL/20763`, `PL/20911`, `UK/21290`.

All their reported date windows share **18 January 2007**. The auditor checks each individual country's original reported start/end dates, a bounded 16–21 January source-review window, uniqueness of each original country+row identity, consistency of original source-country ID pairs on the **exact** pinned source file, and an actual common calendar-date intersection. It retains modelled-CDS country exclusion flags for **AT, IE, LU, PL** and explicitly reports countries with missing economic-loss values if any.

The candidate has **no native CLIMK/C3S/Oasis parent event ID**, no count of independently observed physical occurrences, no independently proven empirical loss, no annual frequency or AAL/AEP/OEP, and no insurer Gross/Net rights/admission. A common storm name and overlapping country dates are **necessary evidence to investigate**, but not sufficient to establish meteorological identity, original loss-source independence or attribution to a physical storm footprint. In particular, publisher ID `20457` is a **Germany country report identifier**, not an Oasis physical event ID.

The synthetic-only tests cover all twelve exact country IDs, both valid and invalid date intersections, duplicate publisher IDs, duplicate countries, invalid Python pseudo-Boolean original fields and improper attempts to classify the grouping as an independently observed or annually sampled insurance event. The **new exact HEAD Python/native source replay** is separately tracked in CI; the previous green HEAD does not validate this new crosswalk.

**Next research acceptance gate:** obtain and compare original physical storm path/footprint/event tags from an independently documented track (and the original CLIMK storm index/ERA5 day) before assigning even a provisional physical parent key. Then challenge *country-level economic* impact references independently; do not use the four modelled CDS country losses as independent held-out claims. A full 1950–2020 country impact report timeline is not an annual occurrence tape: omitted country reports and years without reports cannot be treated as no-events.


## 2026-11-05 – actual GitHub-hosted original-file replay and publisher-origin cross-tab

The **real public original 292,136-byte HANZE XLSX** was downloaded from the fixed Zenodo file endpoint into the ephemeral GitHub runner temp directory and checked with the *new production Python routines*, not just externally parsed in another research runtime. The original byte acquisition explicitly used the pinned MD5 `0a523543adf76003916186623812ab74`, SHA-256 `c2fe636c9e7a1e601d64f00f5bdef8fdf9aaa854060f4d5edcd02e1405140944`, eight exact HTTP partial ranges and original ZIP CRC integrity. The source was **not committed, uploaded as an Actions artifact or retained** after the job.

- [Successful original XLSX full-row CI replay 42092286511](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42092286511), commit `dbd64cfdbb1e93092f7761cd8c4ded47fba81734`: 23 offline Python negative/positive tests, actual source download/checksum, actual 1,358-row Python OOXML audit, exact source indicators, twelve-country Kyrill candidate checks, and automatic deletion. This **closes the previous "the Python CLI has not actually read the original" execution gap** at this pinned HEAD. It does **not** make the source scientifically admitted.
- [Successful independent original source-origin matrix replay 42092640290](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42092640290), commit `26c16cc76e0cae0bd8e53aa70d3ff463b756f417`: same full source verified and **23 synthetic tests** successful. It discovered the following original publisher-data quality structure:

| Original source label | Number of valid numeric published economic-loss cells | Nonblank but invalid/non-numeric source cells | Blank original economic-loss cells | Total source country reports |
| --- | ---: | ---: | ---: | ---: |
| Explicitly labelled `Modelled economic loss from CDS` (column S) | **278** | **21** | **0** | **299** |
| Not explicitly flagged CDS (**independence not verified**) | **409** | **12** | **638** | **1,059** |
| **Total** | **687** | **33** | **638** | **1,358** |

The 33 nonnumeric/unusable *nonempty* monetary cells are a **distinct source quality class**; they are **not zeros**, **not additional 33 numerical losses**, and **not 33 missing blank cells**. All 33 original publisher row IDs are included in the aggregate machine-readable source receipt for targeted review. The independent GitHub replay classifies them separately and does not print their original untrusted cell text as a dollar/Euro amount. The **409 numeric, non-CDS-flagged** values are **only candidates to review against original publisher citations**. No independent observational or insurer-paid-loss status is proven even for these 409: they may include correlated reported/modelled third-party estimates, country aggregations or different currency/reference vintages. The **278 numeric CDS-modelled values are not suitable as independent validation targets** for our related physical/economic-loss model.

The source auditor now requires this exact 2×3 matrix in addition to full file hash, event/country/row counts, missing-data count, and Kyrill identities **only for the pinned original source**. A future change to the source or to its interpretation will fail closed rather than quietly relabel any 21/12 nonnumeric rows as independent numeric loss data.

**Follow-up independent validation work, not performed:** inspect the original and linked sources of each of the 409 potential country economic-loss observations (starting with historical Kyrill and Germany) to identify primary vs modelled/derived/duplicated origins, full event storm path and physical parent ID, NUTS units and year, insured claim vs *total economic impact*, revaluation basis and legal rights. No claim source is admitted in this receipt. Zero years, annual frequency and insurer Gross/Net AEP/OEP remain explicitly unknown.
