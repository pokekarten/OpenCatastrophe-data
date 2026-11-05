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
