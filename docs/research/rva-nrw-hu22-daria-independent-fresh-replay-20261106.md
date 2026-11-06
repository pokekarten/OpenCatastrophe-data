<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Independent HU2022 → NRW 10k → XWS Daria → CLIMADA v6.1.0 replay

**Verified 6 November 2026; research-only.** We have now successfully
recomputed the 10,000-site original-source NRW 2022 building-candidate
sample and its **single historical Daria 1990** source wind overlay
directly from the official public providers, with **no download of any
prior GitHub Actions research artifact**. This is an independent
source-rebuild proof, not actual insured R+V geolocation or a valid
German wind CAT gross/net annual EP model.

## Exact independently successful CI

- Code on `pokekarten/OpenCatastrophe-data` PR
  [#1373](https://github.com/pokekarten/OpenCatastrophe-data/pull/1373),
  source SHA **`26ecba718fd6b059e45198c30ee68322148cd548`**.
- [Independent source replay workflow run #42246960507](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42246960507):
  **SUCCESS**, with exact branch commit, on GitHub Ubuntu 24.04/Python 3.11.
- [Result receipt artifact #13517792380](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42246960507/artifacts/13517792380):
  **3,046 bytes** of no-provider-original, no-building-geocode
  source/impact-method receipts; GitHub retention **14 days**
  (reported expiry **2026-11-20T15:53:36Z**). This artifact is
  **evidence of a successfully reproducible procedure**, not the
  procedure's reusable original data input.

The separately introduced
[`.github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml`](../../.github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml)
is itself the replay recipe. It has **no `gh run download` call**, no
dependency on the expiring source artifact
`#13447603258` from `#42097472463`, and no
external GitHub original-data artifact token.

In this exact run:

1. The original fictional NRW 53-Kreis/10k input OED location and
   account CSV were regenerated **byte-for-byte** to the
   2026-11-05 SHA-256s:
   - `location.csv`: `d116f2ef749c09b2dc10f3111095e75711057a89346653b0582ea362e38d2cee`
   - `account.csv`: `fe5f7fc20bc2fbd4001c79a169d7cac5a925f71b83059737c29632658c9e20a0`.
2. The official historical
   [Geobasis NRW HU 2022 Shape ZIP](https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/2022_hu_EPSG4647_Shape.zip)
   was freshly downloaded in full:
   **901,092,946 bytes**, SHA-256
   `10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da`.
   The code checked original full archive identity, all four
   original SHP/SHX/DBF/PRJ ZIP member CRCs, source projection and the
   **11,232,755** full source record stream.
3. A fresh source-geocoded research OED output was computed:
   **10,000** source-selected public physical building candidates,
   **53** official 2022 NRW Kreise, and **EUR 4,826,029,500** entirely
   fictional 2025-like TIV. The independent output manifest
   conserves exact original source hash/CRC, counts and internally
   rehashed location/account/evidence content. **No actual R+V
   insured-risk association** is asserted.
4. The previous independently pinned original four-file
   [XWS Daria 1990 storm wind CSVs](rva-nrw-xws-daria-original-wind-source-20261105.md)
   were independently freshly retrieved and attached to **those newly
   rebuilt** physical candidate coordinates, not to a copy downloaded
   from earlier GitHub Actions runs.
5. Three unchanged official upstream
   [CLIMADA v6.1.0](rva-nrw-daria-climada61-source-challenger-20261106.md)
   GPL-3 source files were fetched in a temporary isolated runner
   directory, verified against pinned Git blob SHA-1 identities and
   interpreted at **method-body level** only
   (`from_schwierz`, `from_welker`, `change_impf`,
   `calc_mdr`). A **separate Python venv** with NumPy 1.26.4 /
   SciPy 1.14.1 executed the original numeric methods; the
   source-HU OED stage kept NumPy 2.x for modern pyarrow/pandas.
   No dependencies or version gates were relaxed.
6. Independent exact-cent methods replay
   **60,000 asset-level calculations** (10k × 3 recalibrated
   *views of one physical Daria storm* × 2 published European
   winterstorm impact approaches). **ZERO** per-site cent differences
   were observed, and all six original previous total euro-cent
   values matched:
   - Schwierz `lower95/mean/upper95`:
     **12,224 / 10,999,796 / 1,721,892,751 cents**.
   - Welker `lower95/mean/upper95`:
     **21,893 / 19,531,425 / 3,059,869,204 cents**.
7. All 901 MB official original archive bytes, temporary source
   building geocodes and original XWS/CLIMADA GPL code files were
   destroyed on CI before artifact publication. The published
   research artifact includes only self-declared source and parity
   receipts, not source site coordinates.

**Outcome:** A full fresh original-provider *research-method*
rebuild is now proved. This is stronger than merely keeping a copy of
the earlier 14-day GitHub Actions result.

## Precise remaining governance boundary

The short-lived earlier sample artifact **still exists as a
hardcoded source in the ordinary, lower-cost XWS PR workflow**.
It expires **2026-11-19T19:52:57Z**; as long as that
workflow's source path remains, it is not itself safe after expiry.
The new **full** replay is a separate opt-in high-I/O code path,
and its `workflow_dispatch` route is directly available after the
workflow code is on the repository default branch. While this
research PR is still Draft, reproducibility is demonstrated by the
above pull-request-triggered initial workflow run and by a possible
manual *rerun of the workflow run*, not by claiming that an
unmerged workflow is already available for new default-branch
dispatches.

No frequency of automated full source downloads is configured:
GitHub PR triggering is scoped strictly to **modifications of the
new full replay workflow file itself**; ordinary documentation
or model edits should not download the 901 MB ZIP again.

The official open Geobasis NRW data are described under open data
licence terms. There are differing general authority summaries,
including **DL-DE Zero 2.0** and a newer ministry page indicating
**DL-DE BY 2.0**. Relevant official references:
[Geobasis NRW general licence terms](https://www.bezreg-koeln.nrw.de/system/files/media/document/file/lizenzbedingungen_geobasis_nrw.pdf),
[NRW Interior Ministry general open-data page](https://www.im.nrw/themen/vermessung/open-data),
[GovData historical HU catalogue](https://data.gov.de/suche/daten/historische-hausumringe-nw).
Before any *persistent publication of derived 10k site-level
geocodes* outside the temporary runner, check the **exact historical
HU 2022 product record's dataset-specific metadata**, distinguish
this from BKG **HU-DE** (which has different licensing), and record
applicable source-credit conditions. The successful full replay
**did not require** public redistribution of those source bytes.

Finally, this model is not insurer-calibrated. Original 1990 hazard,
public 2022 building geometry and hypothetical 2025 valuation cannot
establish 2025 actual insured sites, original policy wordings,
vulnerability by German material/roof, building losses, annual return
frequency or gross/net OEP/AEP. The three wind variants are
**not** independent annual events. Native full CLIMADA
package installation is separately unverified; the present
method-body parity has an explicit minimal nonnumeric class adapter.

## Status of Issue #1400

The **independent-source reconstructibility P0** gate has a
successful actual CI run. Keep
[Issue #1400](https://github.com/pokekarten/OpenCatastrophe-data/issues/1400)
open until the ordinary XWS workflow no longer hardcodes the
expiring original OED artifact, the full replay workflow has an
available long-lived dispatch/merge route, and a post-2026-11-19
fresh replay proves persistence over the cutoff.
