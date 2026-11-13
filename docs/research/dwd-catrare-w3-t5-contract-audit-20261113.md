<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# DWD CatRaRE W3/T5 Eta 2026.01 — complete rights/route/probe preflight

Both existing, non-admitted registry candidates have an original-provider 4096-byte CSV-range history. This review is **a gate on the existing original runner**, not a new provider acquisition. Two separate exact contracts:
- `dwd.catrare.w3-eta.v2026.01`: 12,410,601-byte original W3 CSV, historical 4096-byte digest `a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12`.
- `dwd.catrare.t5-eta.v2026.01`: 17,208,653-byte original T5 CSV, historical 4096-byte digest `5dc4b6f0dac14f0a442103b78c16f647556bd870898aabff6d9f62aa4534f542`.

Authoritative catalogues: [W3 DOI](https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_CatRaRE_W3_Eta_v2026.01-de.html), [T5 DOI](https://opendata.dwd.de/climate_environment/CDC/help/landing_pages/doi_landingpage_CatRaRE_T5_Eta_v2026.01-de.html).

The official DWD [CDC terms dated May 2024](https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf) apply **Creative Commons Attribution 4.0** to its CDC data (commercial use and redistribution subject to attribution and changes notice). DWD public uncredentialed file hosting and those terms support a tiny bounded original HTTP-file GET. They do **not** grant unlimited automatic crawling, a blanket high-volume API rate, or model/data publication through OpenCatastrophe. Rights and scientific review remain separate. Source-by-source access contracts enforce HTTP range, product version, known original SHA, maximum 4096 raw bytes, no redirects or retries, and no raw-body persistence.

**Actual evidence already known from the canonical source landscape:** both original W3 and T5 prefixes were previously returned by the official host and SHA-256-pinned. The new version must pin the exact 2026.01 originals rather than an older DOI landing-page hyperlink. The original first three event rows and 67-column schema prove only a narrow original provider source witness, **not** the whole file's SHA, complete event catalogue or spatial geometry.

**Scientific dependence:** W3 and T5 represent two different threshold-selection schemes based on the same RADKLIM-RW 2017.002 precipitation data. They are neither independent rainfall observations nor independent event frequencies. Unique event IDs are scoped by variant and release. RADKLIM as validation reference would be a shared-parent/lineage consistency check, not an independent model validation. Persist this relationship in any eventual event catalogue manifest.

## Exact follow-up for eventual manifest
1. Review existing exact access contract, and run the one fixed 4KiB original source range per catalogue from trusted GitHub main after PR review; preserve 206/Content-Range and source SHA receipts. The existing workflow does not conduct live provider requests on PRs.
2. Separately review whole 12/17MB CSV acquisition budget, record exact full original SHA, event counts, uniqueness, timestamps, missing values, licences and source version corrections. The 4KiB probe must **not** be treated as a full catalogue.
3. Obtain and validate exact official 2026.01 ESRI FileGDB event-zone / maxima geometries, source RADOLAN CRS and temporal/spatial event definition; document scientific sampling bias, missingness and occurrence semantics.
4. Require explicit independent scientifically reviewed source admission and downstream CAT model calibration. Until then both candidate `admission_status` remain `not_admitted` and no model input is approved.

No Git-hosted provider bytes, private insurer locations, full DWD files, direct model loss calculations or Neon production writes are part of this change.
