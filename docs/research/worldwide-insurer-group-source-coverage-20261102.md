<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Worldwide insurance group seed census: official register read-only comparison (2026-11-02)

**Research-only; not a downloaded canonical provider asset, approved legal-entity import, global insurer census, exposure, or CAT-model input.** Results below are original-provider *page-text* inspection via the connected Exa reader, not independently pinned raw HTTP response bytes. No source group rows or rights-restricted data are reproduced here.

## Official group registries actually inspected

| Source | Published source period | Parsed groups | Key fields | Notes |
| --- | --- | ---: | --- | --- |
| [IAIS Internationally Active Insurance Groups](https://www.iais.org/register-of-iaigs/) | Explicitly 14 Oct 2026 | 61 | Rank, group name, group-wide supervisor, supervisor jurisdiction | 61 unique sequential ranks 1–61; 19 supervisor jurisdictions; **not a worldwide all-insurers census** |
| [NAIC Insurance Group Lead State Report](https://isiteplus.naic.org/lead-state/publeadstate/pubLSHtml) | 2026 Q2 | 682 | Group name, NAIC **group** code, regulatory lead state | 682 distinct group codes, 52 distinct jurisdiction abbreviations; US lead-state entries, **not 682 separate global ultimate parents** |

Both source pages were inspected on 2026-11-02. These are bounded parsed *research tallies* with no original HTTP byte receipt, no full original HTML hash, no archive or commercial redistribution rights assertion.

### Count method and limits

IAIS: selected markdown table rows whose first column was a numeric rank from 1 to 61, then checked uniqueness, coverage and published header count. NAIC: selected table rows with a non-empty group name, numeric group code and two-letter lead-state abbreviation, checked group-code uniqueness and the published `2026 - Quarter 2` page heading. Excluded headings and table separators. NAIC abbreviations need jurisdiction-dictionary validation before interpreting 52 values as US states; entries may include DC or Puerto Rico.

The IAIS table includes large internationally active groups reported by supervisory authorities; legal entity names and parent structures are different grains. NAIC group codes are a US insurance-supervision identifier and must not be confused with NAIC *company* codes, LEIs, group ownership percentages, risk locations or group parent domicile. IAIS and NAIC rows may overlap and cannot be added to a global-unique total.

## CAT-only Neon main cross-check (read-only; snapshot 2026-11-02)

Project `insurance-risk-core`, database `insurance`, branch `main`:

| Observed table / field | Count |
| --- | ---: |
| `research.insurer_directory_candidate_v0` third-party source candidates | 18,180 |
| Distinct directory `country_slug` | 181 |
| `entity.organization` verified legal organizations | 22 |
| Verified `GLEIF_LEI` identifiers | 18 |
| `entity.organization_candidate` candidate rows | 161 |
| Candidate rows linked to a verified organization | 5 |
| `research.insurer_directory_candidate_v0.model_input_approved=true` | **0** |

A strict casefold/Unicode/punctuation-normalised IAIS group-name versus verified Neon organization display/legal-name comparison found **two equal name strings** (Allianz SE; Münchener Rückversicherungs-Gesellschaft Aktiengesellschaft in München). **This is a low-recall string-only diagnostic, not group ownership resolution.** The remaining 59 IAIS groups must **not** be declared absent from the database: groups and licensed companies are different identity grains, and alternative brands and subsidiaries can exist. Do not auto-create new organizations or inferred parents from the string test.

## Next causal join, in order

1. Freeze official snapshots with provider date, original URL, HTTP status, digest, rights and regulator codes before accepting any row-level extraction.
2. Resolve the official group identity separately from the legal insurer / reinsurer entities, using regulator group code, national registration ID and GLEIF LEI Level 1/Level 2 *when independently supported*. Record relationship type, valid interval, reporting exception, and confidence.
3. Build a unique many-to-many group-to-subsidiary-to-market presence crosswalk. A branch, captive, representative office and cross-border service entry is not by itself a new global group.
4. Join annual public insurer premiums, LoB, balance-sheet, group financials and regulator source period only after identity reconciliation. Insurer CAT property TIV, catastrophe hazard and claims, treaties and retrocession are **not implied** by the registers.
5. Perform regulator confirmation and dataset-rights review before any read/write import into a permitted research staging lane. No automatic promotion to verified organizations, insured portfolios, model calibration, loss artifacts, or production.

## Work boundaries

These results are evidence of source discovery and bounded source parsing, not licence permission, legal classification, completeness of national markets, validated group corporate control, beneficial ownership, or insurer-specific exposures. The third-party 18,180 candidate cohort and its source-identity controls are managed separately in [PR #899](https://github.com/pokekarten/OpenCatastrophe-data/pull/899). This PR contributes complementary official supervisory source definitions only. Exact-head repository validation and source rights review remain outstanding.
