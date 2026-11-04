<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Annual 2025 EIA-860 ZIP: original-file integrity and Delaware FRS plant cross-check

**Research only — live original ZIP receipt and EIA-2025 year-specific membership are *not yet verified* at initial commit. No third-party bytes, individual source records or insured assets committed to Git.** Continuation of [issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251) and the original EPA API-body receipt in [PR #1259](https://github.com/pokekarten/OpenCatastrophe-data/pull/1259).

## Official original product and rights

- [Official 2025 EIA-860 annual download page](https://www.eia.gov/electricity/data/eia860/); original ZIP URL: `https://www.eia.gov/electricity/data/eia860/xls/eia8602025.zip`. This **annual 2025 release** must not be confused with preliminary monthly EIA-860M or a pre-final **early-release 2025** version.
- [EIA public-domain and reuse statement](https://www.eia.gov/about/copyrights_reuse.php): US federal EIA published products are generally public-domain, may be reused with publication-date acknowledgment; third-party and trademark exceptions remain. No complete original ZIP/source-specific import-science approval is inferred.
- ZIP central directory observed from official HTTP **byte-range responses** on 2026-11-04: 13 entries, end-of-central-directory at offset 23,622,325, nominal complete ZIP length **23,622,347 bytes** (an **inferred original-file size from authentic-looking byte-range body segments**, not a full-archive hash). The central index includes `2___Plant_Y2025.xlsx` with **4,458,845 compressed**, **4,629,134 uncompressed** bytes in the outer ZIP and `4___Owner_Y2025.xlsx` with **501,586 compressed**, **514,124 uncompressed** bytes. The uncompressed Plant member is itself an XLSX/ZIP file; it contains separate internal worksheet XML. These byte-range observations do **not** cryptographically authenticate the entire EIA original archive.

## Causal research question

Does the **actual EIA annual 2025 Plant worksheet**, on the exact source ZIP, include the 15 source-reported EIA-860 programme IDs returned by [three bounded EPA FRS Delaware city queries](epa-frs-eia860-live-original-json-receipts-20261104.md)? The separate historical EPA ORIS 3136 source identity is challenged against a 2025 Pennsylvania plant row. Distinguish:

- **Present in EIA 2025 and state DE** — independent plant-identifier plus state concordance across two source products; not geocoded building identity or insurance coverage.
- **Present in EIA 2025 but state not DE** — source discrepancy requiring review; no override by name/geographic proximity.
- **Absent from this EIA 2025 reporting universe** — *not* evidence that the underlying physical facility was demolished, was never insured, or cannot exist in another survey/vintage.
- **ORIS 3136 PA challenge** — the [EPA original source record](epa-frs-eia860-live-original-json-receipts-20261104.md) carried inconsistent top-level facility location/name attributes; an annual EIA ID match cannot fix those attributes without separate site-identity/coordinate proofs.

The annual EIA plant ID is **not** an individual generator; the EIA `Owner` workbook is a *generator-specific reporting product* and cannot establish legal shareholder/insurance-group membership, gross replacement-cost TIV, premium, treaty, physical-event loss or business-interruption value.

## Implemented contract and validation

- [Bounded Python original ZIP reader](../../research_runners/eia860_annual_2025_original_zip_v0.py) and [offline synthetic tests](../../tests/test_eia860_annual_2025_original_zip_v0.py). Standard library only: archive SHA-256 and ZIP integrity, restricted source member, exact `Plant` sheet via OOXML relationships, shared/inline XLSX strings, exact `Plant Code`, `State`, `Plant Name` header, unique numeric plant IDs and at most 50,000 source plant rows. Original response and XLSX bytes are processed in memory, never written or committed. Only aggregate tallies and two hashes are printed.
- Offline operation: `python research_runners/eia860_annual_2025_original_zip_v0.py --original-zip /approved/local/eia8602025.zip --expected-original-sha256 EXACT_REVIEWED_64HEX`.
- Explicit, single-target live operation: `python research_runners/eia860_annual_2025_original_zip_v0.py --live`. One direct HTTPS GET with a bounded response (28 MB), reject redirects, no bearer tokens, no credentials, no user-selected URL, no source data persistence. First successful live run **captures** the original SHA-256 but does not consider the SHA previously pinned or independent of the same observed stream.
- A source-specific GitHub job, if network egress is available, runs the deterministic tests and the original archive proof once for this change; its logs can be used to record the body SHA in a follow-up pinned commit. **Do not claim the live 2025 source scan has succeeded until a real job log and exact HEAD check confirm it.**

## What remains blocked

Original-EIA-2025 success requires a recorded full-archive SHA-256; then pin the expected hash as a guard and independently review the EIA original XLSX Plant workbook header/units and its reporting scope. The EPA EIA-860 programme links, EIA 2025 inventory records and GEM September/October 2026 identities remain **separately typed**. No automatic project-unit/parent/LEI association, insurance portfolio allocation or CAT model admission. Retain issue #1251 until those independent proofs are done.

**Public reporting source attribution:** U.S. Energy Information Administration, Form EIA-860 annual detailed data, 2025 reporting year (published 2026; see original EIA page).
