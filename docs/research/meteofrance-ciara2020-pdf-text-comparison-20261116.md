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

The initial source run is restricted to the branch's PR; after one observed original-text result the workflow becomes manual-only to avoid repeated original downloads. The fixed source admissions remain **false**, and ERA5 model skill, storm completeness, source admission, AAL/OEP/AEP and insurer-loss calibration remain blocked.
