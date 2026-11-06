<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EIOPA 2023 original XLSX: offline integrity / metadata intake only

**6 November 2026. Verified CODE/TOY tests; NOT original EIOPA workbook intake.**

The official [EIOPA Catastrophe Data Hub](https://www.eiopa.europa.eu/tools-and-data/catastrophe-data-hub_en)
offers two original XLSX attachments for historical insured loss
(**publisher display 27.55 KB**) and 2020 flood/wind insured
exposure (**publisher display 5.33 MB**). The original source URLs,
event identity (only **Ciara/Sabine February 2020**, not 1990
Daria), 2020-12-31 coverage vintage, NUTS2 anonymization,
sample denominator 35 groups+9 solo and **63.6% of Germany
property/fire gross written premiums**, and separate publisher
licence notice are pinned in
[`eiopa_catastrophe_hub_2023_original_dossier_v0.toml`](../../research/observations/eiopa_catastrophe_hub_2023_original_dossier_v0.toml).

**Updated original binary source result (same day):** direct original
historical-loss XLSX transfer by web tools initially failed (HTTP 429
or unsupported XLSX). A different source-proxy original-byte
retrieval then succeeded via the **exact official EIOPA download URL**.
The original XLSX returned **28,209 complete bytes**, with SHA-256
`201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6`,
independently recalculated by two different SHA-256 JS
implementations. The original ZIP central directory lists **29
members and one worksheet file**. This is a legitimate
original-linked **binary hash receipt**, not verification of
all ZIP member CRC, workbook worksheet names/cells, policy data,
publisher TLS chain independent of the retrieval proxy,
workbook-specific rights, or insurer risk/loss models.

**Second, successful official-source run:** the original
**exposure XLSX** was subsequently downloaded through a
single bounded HTTPS GET from the official EIOPA domain
in [GitHub Actions #42270505316](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42270505316):
**5,593,551 bytes**, SHA-256
`f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79`. The old source-proxy response was truncated,
but this later complete publisher TLS transfer produced a full
original-byte hash for both XLSX files. The resulting GitHub
artifact **#13528648193** contains *only* hashes, lengths and
provenance flags; raw Excel data were deleted from the runner.

**Crucial unchanged security limitation:** the original XLSX
content validator **rejected an active/external/huge OOXML
member**. It was NOT bypassed; workbook sheet contents,
all-member ZIP CRC, financial loss cells, rights and valid
insurance model dimensions remain UNVERIFIED. Source identity
is not data-model readiness. The exposure hash has not yet
been independently repeated by another download.
Both original files remain absent from the GitHub repository.
Exact no-go receipt:
`research/observations/eiopa_2023_original_xlsx_binary_source_receipt_20261106.toml`.
The acquisition workflow is now **manual-only**, not repeated
on every PR commit.


## Implemented bounded local import-quarantine gate

`research_runners/eiopa_catastrophe_2023_local_xlsx_metadata_preflight_v0.py`
is an offline stdlib-only checker that accepts two **already
available local files** and writes a small metadata/rights
**NOT MODEL ADMITTED** receipt. It does **not** make web requests
or parse any `xl/worksheets/*.xml` cells. It streams the archive
for ZIP CRC, validates that the input is a bounded non-symlink
regular .xlsx, checks OOXML ZIP structure and member paths,
protects against ZIP bombs and external workbook links/macros,
parses only the workbook's sheet **names** and records the
raw file SHA-256 and safe member statistics.

Example invocation **only after separately authorized original
downloads into an ephemeral workspace**:

```sh
python research_runners/eiopa_catastrophe_2023_local_xlsx_metadata_preflight_v0.py \
  --local-loss-xlsx /tmp/eiopa-original-loss.xlsx \
  --local-exposure-xlsx /tmp/eiopa-original-exposure.xlsx \
  --out-receipt /tmp/eiopa-2023-source-metadata-only-NOT-INSURER-MODEL.json
```

The command refuses output overwrites, local symlink inputs,
duplicate inputs, incomplete XLSX files, suspicious embedded
files/links, dangerous ZIP paths, malformed OOXML and exaggerated
decompression ratios. It emits **no insurer claims, exposure rows
or spreadsheet formulas**.

It cannot prove HTTPS provenance of arbitrary local files, EIOPA
original attached content rights, original worksheet column
meaning, aggregation coverage, NUTS2 loss precision,
matching physical wind gusts, or scientific calibration.
Its receipt explicitly says:
`publisher_web_origin_authenticated_by_this_script=false`,
`workbook_specific_reuse_rights_verified=false`,
`ciara_NUTS2_loss_schema_verified=false`,
`insured_GUL_IL_RI_OEP_AEP_calculated=false`.

The additional
`tests/test_eiopa_catastrophe_2023_local_xlsx_metadata_preflight_v0.py`
builds **synthetic original-looking but entirely invented**
tiny ZIPs from scratch and tests eight independent cases:
valid dual-file byte/CRC receipt; safe deterministic metadata output;
bad ZIPs/active content; ZIP traversal/duplicate file identity;
missing workbook parts and formula-like sheet names; compression
bombs/oversized metadata; XML entity safety; symlink and unproved
publisher origin.

These are **code tests only**; a successful test result must not
be reported as the successful ingestion of source EIOPA claims.

## Exact next admission steps

1. Acquire the original two files directly from the official
   EIOPA linked publisher endpoints, with bounded HTTPS
   download, redirect validation and rights/attribution review,
   not a third-party scraped/mirrored workbook.
2. Run the above metadata-only local checker on the original
   files and independently save a **private** original SHA-256
   provenance receipt and a no-rows disclosure; original
   workbook bytes must not be committed to the public repository.
3. Verify original workbook-specific source/third-party licence
   notices before any extraction of actual claims or redistribution.
   Keep any personal/company-sensitive data private.
4. Only with permission for the intended scientific analysis,
   separately inspect original workbook schemas and quality:
   Ciara-2020 event ID; NUTS2; residential and commercial
   cell suppression; coverage (incurred/insured building and other
   claims) and sampled insurance exposure denominators; report
   source-dependent missingness and release vintage.
5. A potential observed-loss holdout must use an **independently
   event-matched 2020 Ciara/Sabine hazard** with compatible 10 m
   3-second gust quantity and exposure vintage. Do **not**
   fit Daria 1990 or policy-level R&V gross/net losses to
   anonymized 2020 EIOPA regional loss aggregates.

The offline metadata gate is an initial safety boundary,
not EIOPA source attestation or an approved insurer calibration.
All source rights, sample scope, German building vulnerability
and annual frequency/model admission gates remain open in
[Issue #1401](https://github.com/pokekarten/OpenCatastrophe-data/issues/1401).
