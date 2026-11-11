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

**Ordinary, low-cost CI artifact-dependency cutover now completed
on this research PR.** The original
[`.github/workflows/rva-nrw-xws-daria-source.yml`](../../.github/workflows/rva-nrw-xws-daria-source.yml)
has been renamed explicitly **"source preflight (NO 10k)"** and
does **not** run `gh run download` or use historical HU22
artifact `#13447603258` / run `#42097472463`. Its
source-only admission receipt explicitly reports
`actual_2022_NRW_10k_site_overlay_executed_in_this_workflow=false`,
`original_CLIMADA_source_method_body_parity_executed_in_this_workflow=false`,
`actual_insurer_RV_geographies_or_loss_calculated=false` and
`annual_frequency_or_OEP_AEP_calculated=false`. It still
downloads/verifies all **four** pinned original XWS Daria storm CSV
sources and **three** original pinned CLIMADA 6.1.0 GPL-code
identities, parses the real PAA/MDD method definitions and runs
the offline positive/negative mock-source tests. These checks do
NOT substitute for site-level or financial-model calculations.

The source-only cutover was independently executed successfully in
[GitHub Actions run #42249222937](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42249222937)
at commit `875c7349ac59d3696833eda03f1bf61ca5b651b9`,
including **five** new CI scope/integrity negative tests in
`tests/test_rva_nrw_xws_daria_source_only_ci_contract_v0.py`.
The original `#13447603258` GitHub artifact expires
**2026-11-19T19:52:57Z**, but the *updated* source-only
CI no longer needs it. This is a genuine elimination of
the cheap-run dependency, NOT proof of automatic 10k physical-model
recalculation on every PR push.

The **full** fresh-from-provider replay remains a separate opt-in
high-I/O code path. Its `workflow_dispatch` route becomes
manually available when its workflow code is merged onto the
repository's default branch. While this research PR remains Draft,
the earlier successful pull-request-triggered original full-source
execution proves the implementation, but not default-branch
manual-dispatch availability or scientific model acceptance.

**Cost/rate governance correction:** The initial success was
obtained using a temporary pull-request trigger on the new workflow.
GitHub evaluates pull-request `paths` filters against the
**entire PR diff**, not just the latest commit. Therefore the initial
trigger was **not sufficiently selective**: a subsequent documentation
edit would rerun the 901 MB acquisition. Once recognized, we removed
the `pull_request` trigger altogether; the final, safe workflow is
**`workflow_dispatch` only** and will not automatically download
large source files on ordinary commits. It can be manually dispatched
when the reviewed workflow is on the default branch; until then,
the successful previous PR-run attests to correct computation but
does not imply a currently runnable manual dispatch entry.

## Official 2022 historical HU product licence evidence (verified 2026-11-09)

The [original Geobasis NRW *Historische Hausumringe* product directory](https://www.opengeodata.nrw.de/produkte/geobasis/lk/hist/hist_hu_shp/)
explicitly lists **`2022_hu_EPSG4647_Shape.zip`** under **Datenlizenz Deutschland –
Zero – Version 2.0** and describes unrestricted use of *this product*.
This is stronger and more product-specific evidence than either the
[generic NRW ministerial open-data page](https://www.im.nrw/themen/vermessung/open-data),
which currently references DL-DE BY 2.0, or the older
[NRW Interior Ministry zero-licence announcement](https://www.im.nrw/amtliche-geobasisdaten-koennen-ohne-einschraenkungen-genutzt-werden).
The product directory also specifies CRS **EPSG:4647** and the original
2022 Shape archive; the previously independently verified full 2022
archive identity remains **901,092,946 bytes** and SHA-256
`10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da`.

**Precisely resolved:** the official product-level *source-licence label*
and 2022 archive listing are now identified. The source registry points
to this exact original directory, not a generic GovData search page.
This is not a separate claim that all inputs to a mixed insurer model,
BKG nationwide HU-DE, the original third-party XWS/CLIMADA sources or
any future merged dataset share that licence.

**Still held:** no raw 2022 source ZIP, individual 10k building geometry,
R+V insured-site identity, fictitious TIV-to-real exposure join or observed
insurer loss is committed to this public repository or admitted to a
CAT model. The replay remains ephemeral and rights-aware despite the
identified licence. For any future persistent derived release, record
the exact constituent datasets, output content, privacy/security review
and required source provenance independently. Scientific acceptance and
an executable default-branch full-replay workflow are separate gates.

Finally, this model is not insurer-calibrated. Original 1990 hazard,
public 2022 building geometry and hypothetical 2025 valuation cannot
establish 2025 actual insured sites, original policy wordings,
vulnerability by German material/roof, building losses, annual return
frequency or gross/net OEP/AEP. The three wind variants are
**not** independent annual events. Native full CLIMADA
package installation is separately unverified; the present
method-body parity has an explicit minimal nonnumeric class adapter.

## Status of Issue #1400

The **independent-source reconstructibility P0** gate
and **normal low-cost source-only CI dependency cutover** each
have successful actual GitHub Actions runs. Keep
[Issue #1400](https://github.com/pokekarten/OpenCatastrophe-data/issues/1400)
open until the now-merged default-branch manual gateway has an
independently reviewed **actual full replay run**, and a separate
*post-2026-11-19* full original-provider rebuild verifies
reproducibility after the old artifact's expiry. The gateway exists,
but its presence and the historical successful run are not a new dispatch. The exact historical
HU2022 product-level licence is now documented above; separate
multi-source scientific/privacy/publication gates remain in force. Do not treat passing source-only
CI as passing the 10,000-site full CAT model.


## 2026-11-09 operational handoff for Issue #1400 (no implicit 901 MB run)

**Status correction after PR #1466:** The reviewed default-branch gateway
is merged and visible in repository code; do not read the earlier
historical `workflow_dispatch`-availability paragraphs as current
blockers. **No new manual-gateway full replay was executed by this
documentation correction.** The expensive run requires separate,
explicit authorization and still remains a reproducibility acceptance
gate.

The original historical 2022 HU archive SHA/CRC and deterministic sample
identities are unchanged. The research branch provides an independent
`.github/workflows/rva-nrw-hu22-daria-fresh-independent-replay.yml`
with **manual `workflow_dispatch` only** (or an explicitly SHA-pinned
reusable call). Its normal PR/source-only checks do **not** download the
901,092,946-byte original archive and must not be cited as a full 10k replay.
The separate legacy `rva-nrw-hu22-full-one-shot.yml` remains manual as
well; its original ZIP cleanup now uses `if: always()` and `rm -f` after
conversion failure. The downloader cleans the output file that it created
if a Python interruption occurs and rejects pre-existing/symlinked paths.

**Owner/reviewer decision required before a costly rerun:**

1. Review R+V research PR #1373 for source rights, privacy,
   model-science labels and full test receipts. The separately reviewed
   **default-branch manual gateway already exists on `main`**, merged
   in [PR #1466](https://github.com/pokekarten/OpenCatastrophe-data/pull/1466)
   at commit `233a8ecea69b9fdba8ad47a9106a5e8ea7664cf5`.
   It is the *gateway*, not the draft research workflow, that should
   be manually selected from the default-branch Actions interface.
   Its reusable workflow and explicit checkout `source_ref` both
   pin `75dba089478927003d201032cb41303ebf587952`.
   Neither the gateway merge nor a green draft PR proves it was run.
2. Confirm permission to fetch roughly 901 MB of original historical
   Geobasis NRW source for a one-shot reproduction. Keep the immutable
   official archive identity `10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da`
   and the source-approved/ephemeral processing boundaries unchanged.
3. With explicit owner permission for the ~901 MB source fetch,
   dispatch **`.github/workflows/nrw-hu22-2022-manual-replay-gateway.yml`
   on `main`** (displayed as `P0 NRW HU2022 full original-source
   research replay (manual pinned SHA)`), **not** the draft
   `rva-nrw-hu22-daria-fresh-independent-replay.yml` directly.
   The gateway calls the immutable research workflow at
   `75dba089478927003d201032cb41303ebf587952`. Inspect actual
   run/job conclusions and preserve only privacy-safe, source/method
   receipts and logs. Require the original archive SHA-256, 10,000
   original public building candidates, 53 Kreise, unchanged
   *fictional* EUR 4,826,029,500 TIV, and six original CLIMADA
   source-method totals with zero cent-differences. Do not assume
   a successful run merely because this dispatch route is installed.
4. **After 2026-11-19T19:52:57Z**, rerun the same approved fresh-source
   route and independently verify that it no longer depends on ephemeral
   artifact #13447603258 / run #42097472463. Only then can the
   artifact-expiry part of Issue #1400 be marked complete.

No automated hourly/daily 901 MB downloads, no transfer of original site
geometries or raw survey data into Git, and no assertion of actual R+V
insured-site exposure, German physical wind vulnerability, policy loss,
or native Gross/Net OEP/AEP is authorized by this operational procedure.
