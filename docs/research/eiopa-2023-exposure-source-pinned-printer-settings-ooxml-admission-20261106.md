<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EIOPA 2023 exposure XLSX: exact original printer-settings OOXML quarantine resolution

**6 November 2026 | SOURCE-BOUNDED METADATA/CRC ONLY | NOT a licensed insurer-loss dataset or model.**

The official EIOPA [Catastrophe Data Hub](https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en)
offers the historical insured-loss XLSX (28,209 bytes,
SHA-256 `201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6`)
and flood/wind insured exposure XLSX (5,593,551 bytes,
SHA-256 `f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79`).

## What we established from the exact original EIOPA exposure file

The initial fully untrusted XLSX quarantine refused to process the
original exposure workbook because it contained a binary ZIP member;
this was **a correct fail-closed default**. We did not assume the
untrusted binary was safe or allow arbitrary `.bin` content.

A subsequent **original exact-SHA-pinned central directory diagnostic**
([source run #42291363788](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42291363788);
only metadata [artifact #13539212630](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42291363788/artifacts/13539212630))
found exactly **one** quarantined item, classified as
`xl/printerSettings/*.bin`. Its original ZIP central directory
records **5,420 uncompressed bytes**, **443 compressed bytes**;
all original **31** archive members have aggregate declared
**76,586,443 uncompressed bytes**. No macro, external-link
or embedded-object category was flagged by this central-directory
scanner. No original ZIP member names, worksheet values, driver
configuration or original workbooks were uploaded.

The [ISO/IEC 29500/ECMA-376 OOXML Printer Settings Part description](https://ooxml.info/docs/15/15.2/15.2.15/)
and [ECMA printerSettings example](https://c-rex.net/samples/ooxml/e1/Part1/OOXML_P1_Fundamentals_Printer_topic_ID0EJEEO.html)
permit binary printer configuration parts in normal SpreadsheetML
workbooks. Their content is printer/manufacturer dependent and
**must not be interpreted or executed** during source acquisition.
This category does **not by itself demonstrate malware**.

We therefore implemented a **strictly limited original source
exception** inside
`research_runners/eiopa_catastrophe_2023_local_xlsx_metadata_preflight_v0.py`:
a print-settings `.bin` member is ignored *for semantic
interpretation*, while still streamed for ZIP CRC, **only when all**
of these hold simultaneously:

- Family equals official `FLOOD_WIND_EXPOSURE`.
- Complete original file SHA-256 equals the exact published-source
  evidence `f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79`
  and byte count equals **5,593,551**.
- ZIP member pathname matches the narrowly fixed
  `xl/printerSettings/printerSettings[1-9][0-9]*.bin`
  pattern, is not encrypted and has exactly **5,420**
  uncompressed / **443** compressed bytes.
- There is exactly one such matching printer part. All
  `xl/externalLinks/`, `xl/embeddings/`, `xl/activeX/`,
  VBA, other executable binary parts, malicious paths,
  inflated data, ZIP traversal and other non-allowlisted
  `.bin` files remain rejected.

**Successful independent source replay:** the updated parser
read only original ZIP integrity and safe workbook metadata
from the independently re-downloaded EIOPA source. Exact SHA
and 31-member original matched again; the original all-member
**ZIP CRC check passed**, and the workbook's metadata identified
**one worksheet**. No worksheet cell values, financial rows,
individual company exposure values, insurance contracts,
formulas or full sheet names were published. The successful
[source run #42292320403](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42292320403)
produced [metadata-only receipt #13540506478](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42292320403/artifacts/13540506478)
(expiry **2026-11-20T20:54:55Z**). The source was
read in a temporary GH runner directory only; no XLSX files
were retained or uploaded. The full method and evidence are
permanently recorded in
`research/observations/eiopa_2023_exposure_source_pinned_ooxml_metadata_receipt_20261106.toml`.

**Operational control:** the diagnostic original-download workflow
is now `workflow_dispatch`-only; it does not download the
5.6 MB publisher file on unrelated PR updates. It becomes
manually dispatchable after review/merge to the default branch.

## Still unverified, and therefore blocked

- **Workbook licence and TDM rights for this analysis** and any
  republication of worksheet/financial data. General EIOPA
  site-wide attribution rules are not automatically a complete
  licence for data that may include third-party rights.
- **The meaning of actual worksheet columns and cells**,
  NUTS2 suppression/aggregations, currency and date units,
  insurer/claim exposure denominators or residential/commercial
  split. These have not been inspected.
- An independent **repeat download source hash** for the
  exposure file via a separate retrieval path beyond GH TLS
  (the same original SHA has matched across multiple GitHub runs,
  but this is not independent TLS provenance).
- **No event join**: the EIOPA 2020 observed insured wind event
  is **Ciara/Sabine**, not original XWS Daria **1990**.
  EIOPA 2020 GWP participant sample is not all Germany/R&V
  insured buildings.
- German/R&V wind vulnerability calibration, source-consistent
  event frequency, GUL/IL/RI, treaty/retro chronology and
  any genuine annual Gross/Net OEP/AEP.

**Result: GO for original EIOPA XLSX file identity, ZIP CRC
and workbook sheet-count metadata. NO-GO for insurer claim-cell
analysis, source redistribution, German wind-loss calibration
and 1990 Daria policy model.** Retain open
[Issue #1401](https://github.com/pokekarten/OpenCatastrophe-data/issues/1401)
and Draft [PR #1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373)
until independent rights and science requirements are met.
