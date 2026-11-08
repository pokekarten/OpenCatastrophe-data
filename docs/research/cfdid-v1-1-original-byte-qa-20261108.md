<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CFDID v1.1 — independently retrieved original CSV integrity and hierarchy QA

**Executed:** 2026-11-08. **Scope:** read-only, exact original publisher CSV. This is an original-byte **research validation receipt**, not source admission, commercial redistribution clearance, an insurance-claims observation, calibration of a CAT model, an EP curve or an ingest into Neon. No original CSV rows, coordinates, third-party data or secrets are committed.

## Original publisher release and exact byte receipt

| Field | Observed value |
| --- | --- |
| Published dataset DOI | https://doi.org/10.5281/zenodo.22918521 |
| Associated peer-reviewed paper | https://doi.org/10.5194/essd-18-8129-2026 (published 2026-11-05) |
| Zenodo record | \`22918521\`, immutable version \`1.1\`, published \`2026-09-23\` |
| Exact source file | \`China Flood Disaster Impact Database.csv\` |
| Original content URL | \`https://zenodo.org/api/records/22918521/files/China%20Flood%20Disaster%20Impact%20Database.csv/content\` |
| Original byte count | \`337549\` |
| Original file encoding | UTF-8 with BOM, leading hex \`efbbbf\` (not UTF-8 without BOM) |
| Source-reported MD5 in Zenodo metadata | \`d8e828d7484fb5876000d2efab1d44a0\` |
| MD5 computed from independently retrieved original CSV bytes | \`d8e828d7484fb5876000d2efab1d44a0\` — exact match |
| SHA-256 computed over the same original CSV bytes | \`b2cc978a317710b5379fdc42cff787800f1bbaee505c5ce7c70370f31669f2bf\` |
| Publisher's file-level release license claim | \`CC BY 4.0\` in Zenodo metadata; upstream official reports/EM-DAT are separate rights sources |
| Source API | \`https://zenodo.org/api/records/22918521\`; public unauthenticated GET |
| Source storage in this repository | None; the original CSV was fetched in an isolated short-lived research execution environment only |

The upstream DOI, size and MD5 came from the Zenodo record JSON, **not an assistant-invented hash**. Independently downloaded source bytes matched the publisher MD5, then a SHA-256 was computed and used as the fixed identity gate for the exact GitHub code runner.

## Reproduced original-source preflight

**Original runner commit:** \`a1eb916fa7290dc8a4bb78eecfc07793b1b88330\` (before PR #1422 merged); original code at https://github.com/pokekarten/OpenCatastrophe-data/blob/a1eb916fa7290dc8a4bb78eecfc07793b1b88330/research_runners/cfdid_hierarchy_preflight_v0.py .

The original script was fetched from the immutable commit and run against the **full original 337,549-byte CSV** after separately computing its MD5 and SHA-256. The full CLI accepted the exact observed SHA-256 with exit code 0. It **rejected** a deliberately wrong \`000...000\` SHA-256 with exit code 2 and the expected mismatch error.

| Observed result | Value | Reason |
| --- | ---: | --- |
| Total records | 1716 | 1391 + 300 + 25 |
| L1 parent events | 1391 | Only L1 can enter comparable parent-event aggregates |
| Nested L2 events | 300 | Do not add to L1 |
| Nested L3 events | 25 | Do not add to L1 or L2 |
| Orphan parent IDs | 0 | Every L2/L3 has the corresponding immediate parent |
| L1 records with reported nominal direct economic losses | 1197 | Missing amounts are unknown, **not zero** |
| L1 records without reported nominal direct economic losses | 194 | Not 194 zero-loss events |
| Total missing start-day values, all event levels | 192 | Unknown calendar day; do not fabricate first day |
| Reported categories, all levels | rainstorm flood 1080; typhoon 621; snowmelt flood 7; dam-break flood 6; ice-jam flood 2 | Typhoon and flood event identity must be linked without double counting |
| Invalid event-start year identity | 0 | The first four digits of event ID match reported start year |
| Direct-loss amount summed over L1 nominal CNY | 4,117,420.058 **million CNY** | **Technical checksum-like audit aggregate only**, not adjusted for mixed years or a present-value insurance loss statistic |

All 1,716 records contain valid reported Start year and Start month. Where End month is present, the record also has End year; where End day is present, End month is present. Original v1.1 has 81 partial end-year/month dates and 9 year-only ends, so source-date precision is heterogeneous. These observations must remain explicit in any later event time join.

## Reproduction command — with caller-owned original file outside Git

\`\`\`bash
python research_runners/cfdid_hierarchy_preflight_v0.py \
  --csv /secure/local-source/China_Flood_Disaster_Impact_Database_v1_1.csv \
  --expected-sha256 b2cc978a317710b5379fdc42cff787800f1bbaee505c5ce7c70370f31669f2bf
\`\`\`

The input path in this example is illustrative; this repository does **not** contain the original file. Preserve the source filename/version/hash and ensure that subsequent downloaded original bytes still match. The runner performs metadata/schema/event checks, not full scientific calibration, and does not redistribute original observations.

## Blocking scientific interpretations

- Reported economic losses are Chinese **societal direct economic impacts**, not claims paid, insured TIV, residential-only physical building damages, contract-level gross/net, or an annual event-frequency model.
- The L1 nominal economic-loss total combines years 1994–2023, so it is deliberately **not** presented as inflation-adjusted current currency, industry insured loss, or a loss calibration target. Prefer the source's already provided 2023-constant-price column plus year-specific loss and explicit inflation semantics in any separate financial audit, with source-reported year-specific benchmarks.
- The source's 66 original official documents and its crosswalk to EM-DAT do not create 66 independent loss datasets. Annual government statistics and the derived published event reports share primary evidence.
- The exact CSV is a public Zenodo record with a CC BY 4.0 release claim, but underlying yearbook redistribution/commercial rights remain separately subject to review. This receipt changes **no** existing \`not_admitted\` / \`not_reviewed\` flags.
- Unknown days and dates are incomplete observation intervals, not zero-day floods; event matches require matching at supported spatial/temporal precision.

**Next bounded scientific gate:** compare year-specific L1 losses (with units and price year) against the released \`Official national annual totals_1994-2023.xlsx\` and the already registered independent flood event sources. The original Excel benchmark has publisher MD5 \`c2b7ae971efa5c4f886d824424141ad4\`; it has **not** been independently byte-verified in this run.


## Follow-up runner/date precision gate

The source runner was strengthened on this same branch with **original-field calendar checks** and an extra diagnostic \`rows_missing_reported_start_day\`. Invalid dates, end-month without end-year, end-day without end-month, missing/invalid start-year/month, and mismatched event-ID year fail closed. Unknown start days remain null/blank; no date is silently imputed.

**Independent verification of updated branch code:** retrieved exact upstream 337,549 bytes and checked the SHA-256 shown above, retrieved the modified source and tests from this PR branch, then ran the complete CLI in an isolated temporary directory. Original-run **exit 0** and **12/12 focused unittest cases passed**. A deliberately wrong SHA-256 again gave **exit 2** with expected SHA mismatch. Updated script SHA-256: \`673bd942f2d9ce8bac5870ad2bd9807acb6425b79cbe54ea938605f2a23f102b\`.

The original-run JSON reports \`rows_missing_reported_start_day: 192\`, \`reported_l1_loss_records: 1197\`, \`rows: 1716\` and \`by_event_level: {L1:1391, L2:300, L3:25}\`. No original data bytes are tracked, stored in Git or published here. This is **not** a full-repository CI run.
