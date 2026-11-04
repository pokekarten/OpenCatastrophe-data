<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Annual 2025 EIA-860 ZIP: original-file integrity and Delaware FRS plant cross-check

**Original EIA-2025 annual ZIP proof executed and verified in public GitHub CI on 2026-11-04. Scientific source admission, GEM identity and insurance assignment remain blocked. No third-party bytes or individual source records committed to Git.** Continuation of [issue #1251](https://github.com/pokekarten/OpenCatastrophe-data/issues/1251) and the original EPA API-body receipt in [PR #1259](https://github.com/pokekarten/OpenCatastrophe-data/pull/1259).

## Official original product and rights

- [Official 2025 EIA-860 annual download page](https://www.eia.gov/electricity/data/eia860/); original ZIP URL: `https://www.eia.gov/electricity/data/eia860/xls/eia8602025.zip`. This **annual 2025 release** must not be confused with preliminary monthly EIA-860M or a pre-final **early-release 2025** version.
- [EIA public-domain and reuse statement](https://www.eia.gov/about/copyrights_reuse.php): US federal EIA published products are generally public-domain, may be reused with publication-date acknowledgment; third-party and trademark exceptions remain. No complete original ZIP/source-specific import-science approval is inferred.
- ZIP central directory observed from official HTTP **byte-range responses** on 2026-11-04: 13 entries, end-of-central-directory at offset 23,622,325, nominal complete ZIP length **23,622,347 bytes** (an **inferred original-file size from authentic-looking byte-range body segments**, not a full-archive hash). The central index includes `2___Plant_Y2025.xlsx` with **4,458,845 compressed**, **4,629,134 uncompressed** bytes in the outer ZIP and `4___Owner_Y2025.xlsx` with **501,586 compressed**, **514,124 uncompressed** bytes. The uncompressed Plant member is itself an XLSX/ZIP file; it contains separate internal worksheet XML. **The earlier byte-range alone did not prove the whole ZIP; the separate subsequent full-source acquisition and SHA-256 proof below now do.**

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
- The [real GitHub source-identity job](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41885583270) on PR #1291 completed **successfully** on 2026-11-04, exercising 15 deterministic synthetic tests and a genuine direct HTTPS GET of the annual original ZIP. Its full-archive checksum and nested Plant workbook checksum were independently recorded and subsequently pinned in the source runner. Exact-head CI should be rerun after pinning.

## What remains blocked

The full EIA original archive and Plant workbook checksums are now recorded and pinned. The runner requires the source SHA for live mode; unknown provider revisions **fail closed** rather than silently changing the 2025 benchmark. Independent review of original EIA survey methodology and reporting scope is still needed before scientific or commercial model admission. The EPA EIA-860 programme links, EIA 2025 inventory records and GEM September/October 2026 identities remain **separately typed**. No automatic project-unit/parent/LEI association, insurance portfolio allocation or CAT model admission. Retain issue #1251 until those independent proofs are done.

**Public reporting source attribution:** U.S. Energy Information Administration, Form EIA-860 annual detailed data, 2025 reporting year (published 2026; see original EIA page).

## Actual original-archive run: public CI evidence

The [2026-11-04 original source job](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41885583270) completed successfully on the exact source URL above with **15/15 synthetic tests passing**, and no raw ZIP, source workbook, physical-site rows, addresses or owners committed to Git. The direct public GitHub worker read all original provider archive bytes in memory and parsed the **Plant** worksheet using OOXML relationships and shared/inline strings.

| Original source evidence | Actual verified observation |
| --- | --- |
| Official 2025 EIA ZIP body bytes | **23,622,347** |
| Exact original ZIP SHA-256 | `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba` |
| Original ZIP member count | **13** |
| Inner `2___Plant_Y2025.xlsx` bytes | **4,629,134** |
| Exact Plant XLSX original member SHA-256 | `3c338f5e9d2647bb487dee8b3f4ed5c3fdd3e82db3b1bc5fdf206cee5470e059` |
| Total 2025 **Plant worksheet records** | **17,349** |
| Source-reported Delaware EPA EIA-860 IDs present with `State=DE` | **15 of 15** |
| Delaware EPA ID candidates absent from this 2025 annual Plant sheet | **0** |
| Delaware candidates present with mismatching state | **0** |
| Separate Pennsylvania EPA ORIS 3136 in EIA 2025 with `State=PA` | **Yes** |

**Precisely what was corroborated:** The exact public EPA FRS `EIA-860` program plant identifiers returned for Dover, Wilmington and Newark in 2026 exist in the EIA annual **2025** plant-level survey workbook, with the state matching Delaware. This is a genuine **independent two-provider, two-vintage plant-ID and state consistency check**. It does **not** prove that two EIA plant codes attached to one Wilmington FRS record denote the same physically unique asset, that coordinates or top-level FRS labels are correct, or that any company insures those plants.

**Untested outside this proof:** generator-unit/owner subrecords (the separate EIA Owner workbook was identified but not semantically parsed), plant/generator current operational state in 2026, GEM location/unit cross-ID, company legal ownership and observed versus imputed shares, financial replacement cost, BI downtime, source-specific admission decisions and any inward/outward treaty allocations. The separate disputed ORIS 3136 FRS top-level name/city conflict remains a **source data-quality blocker** despite matching PA ID.

**Scientific caution:** The first successful live probe captured a genuine HTTPS-body SHA for this EIA file. No external publisher-signed digest was available for comparison, so the checksum proves the specific bytes read and is now our reproducibility fingerprint, **not** cryptographic proof of the EIA publisher's signature.
