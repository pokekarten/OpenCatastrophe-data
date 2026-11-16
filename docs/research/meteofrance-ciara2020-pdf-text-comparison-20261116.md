<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ciara 2020: semantic-text comparison of one ambiguous official French station PDF pair

**16 November 2026.** The earlier original-byte proof
[research report](meteofrance-ciara2020-duplicate-pdf-source-review-20261115.md)
verified two distinct official PDFs for one 72-hour-quality-complete
Seine-Maritime station. Their exact original byte receipt binds the otherwise
unpublished station identity and the two official resource UUIDs:
`08fa1dc144c415d9485a3f2f358e0fb9b9eb952bb1db8221c2b0afe5120612d9`.

This experiment uses a standalone isolated CI job with pinned `pypdf==5.9.0` to revalidate the exact original 2020–2024 Météo-France gzip, full 72-hour quality-complete cohort, original official PDF catalogue, and **both** exact original PDFs, before comparing the PDFs' normalized extractable text. It emits only page counts, extracted character counts, neutral keyword presence, and whether normalized extracted text matches; no station names, IDs, coordinate metadata, original PDF bytes, original PDF text, source URLs or single-station gust observations are committed or logged.

**A byte difference is not evidence of a meaningful scientific difference**: PDFs can vary in metadata, images or rendering. **Extracted text equality is not visual/document equality**, especially where station graphics or embedded site history figures differ; OCR may be needed for image-only pages. Keyword presence around "vent", "anémomètre", "emplacement" or "2020" does not establish which wind instrument or station location operated during February 2020. No edition is automatically selected. Open Licence 2.0 catalogue-level status is not independently reviewed for model calibration.

Two actual original-source text analyses have now succeeded. The official networking workflow has been changed to **manual-only**, and the exact original station-bound PDF resource cohort digest remains frozen. The fixed source admissions remain **false**, and ERA5 model skill, storm completeness, source admission, AAL/OEP/AEP and insurer-loss calibration remain blocked.

## First executed original PDF content result (16 November 2026)

The first live original PDF reader succeeded in [GitHub Actions run 43974685560](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43974685560), with the old original station-bound PDF-source cohort hash unchanged: `08fa1dc144c415d9485a3f2f358e0fb9b9eb952bb1db8221c2b0afe5120612d9`. The two PDFs, already proven byte-different, are **also text-different after UTF-8 Unicode NFKC, case-folding and whitespace normalization**.

| Source-anonymized PDF order | Original pages | Pages with extracted text | Normalized text characters |
|---|---:|---:|---:|
| Document 1 | 9 | 9 | 18,347 |
| Document 2 | 9 | 9 | 18,273 |

Both original PDFs contain machine-extracted text mentioning terms associated with 2020, wind, instrumentation, site and height. **These are only words present, not date-scoped historical verification**. Differences may relate to metadata/headers or important science details; this pass did not reveal the text, determine a changed 2020 instrument, inspect page images or select a version. The follow-up runner now adds **1-based changed extracted-text page numbers only**, without publishing original source PDFs, page text, coordinates, or any station identities. Any manual reviewer must inspect the identified pages and relevant historical site/instrument context, including visual pages.


## Actual original-source text-diff receipts (16 November 2026)

- [First full-original PDF content read: GitHub Actions run 43974685560](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43974685560): both official 9-page PDFs had extractable text on **all 9 pages**, with **18,347** and **18,273** Unicode-normalized textual characters, respectively. The two text SHA-256 digests were **unequal**.
- [Second exact-original page-granularity proof: GitHub Actions run 43975113596](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43975113596): original source and PDF resource cohort digest revalidated; only **pages 1 and 2** of the two 9-page originals differ in normalized text. **Pages 3 through 9 are text-identical** at corresponding 1-based page numbers.

| Scientific observation | Result |
|---|---|
| Official 2020–2024 department 76 original gzip SHA-256 | `406dbf752f042254bfade674f606c2035eeb2560d06314324c9bd4694936780d` |
| Station-bound PDF cohort digest | `08fa1dc144c415d9485a3f2f358e0fb9b9eb952bb1db8221c2b0afe5120612d9` |
| Original candidate PDF byte count | 2 files; 1,390,940 bytes together |
| Text-extractable pages | 9 of 9 in both PDFs |
| Different normalized page text | **1 and 2** |
| Normalized page-text-equal pages | **3–9** |
| Instrument/sensor/site history for February 2020 attested | **NO** |
| Original page raster/image comparison | **NOT DONE** |
| Source/model/insurance loss calibration admitted | **NO** |

The time-scoped and instrumental implications of the page 1–2 differences remain unresolved. A human/specialized PDF reviewer must inspect **both versions of pages 1–2, including images and location/instrument tables**, and then independently cross-check any 16 April 2026 station identifier changes. No first/latest document or model-fit evidence is automatically accepted. PDF text equality on pages 3–9 cannot prove image/chart equivalence on those pages.

The synthetic tests for text normalization, page bounds and positive/negative comparisons run under standard repository CI without requiring `pypdf` at installation time; the original PDF text parser dependency is scoped only to the explicit manual research workflow.
