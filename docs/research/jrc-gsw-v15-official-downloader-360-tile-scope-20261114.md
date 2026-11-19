<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# JRC Global Surface Water v1.5 — original published bulk downloader and one-tile gate (2026-11-14)

## Source-specific first-party machine-download right ≠ host quota

This review uses the European Commission's **official instructions**:
https://global-surface-water.appspot.com/gsw/Download_Instructions.html

The publisher documents its standard-library Python downloader named
\`downloadWaterData_Python3_v1_5.py\`, the **CloudFerro Swift v1.5** HTTPS
origin, six long-term summary products and both aggregated and monthly modes.
In the **aggregated mode**, the script handles **360 10° × 10° tile positions**
and downloads one GeoTIFF per available cell. It does **not** document a
single-tile selection parameter for aggregated products; its documented
\`years\` and \`tileIDs\` arguments apply to **monthlyhistory**.

The public official [download page](https://global-surface-water.appspot.com/download)
expressly makes the Copernicus dataset free of charge without restriction
of *dataset reuse*, with the required attribution **Source: EC JRC/Google**;
it links the Python 3 script, first-party instructions and CloudFerro v1.5
listing. The publisher thereby establishes a **deliberate machine-readable
delivery path**, unlike a merely guessed Swift endpoint. However neither
document states a numerical anonymous Swift service rate cap, HTTP Range
support, request concurrency/retry policy or negotiated commercial bulk
transfer agreement. A JRC data-use license is distinct from a CloudFerro
host request quota or CAT scientific model admission.

A **single fixed original response** is an appropriately narrow next
research target, but the current code and contracts deliberately allow
**zero original data-provider requests** until its exact host/origin byte
limit and anonymous service conditions are reviewed. The default publisher
download script MUST NOT be run automatically in OpenCatastrophe, as that
could initiate up to 360 original requests for just one aggregated product.
Monthlyhistory defaults can trigger far more (years × months × tile grid).

## Deterministic source preflight and controlled publisher documentation

New \`research_runners/jrc_gsw_v15_publisher_downloader_instructions_one_shot_v0.py\`
has a pure, offline \`inspect_instructions(raw)\` parser and an opt-in
\`--one-shot-instructions\` that fetches only the exact official
**publisher instructions HTML**, not the Python script or any TIFF.

The source-specific limits are:
- only \`https://global-surface-water.appspot.com/gsw/Download_Instructions.html\`;
- one fixed unauthenticated GET, no proxy, redirects, retries or arbitrary URLs;
- 32,768 original HTML bytes maximum and 20-second request timeout;
- strict original HTTP **200**, \`text/html\`, identity encoding, UTC receipt;
- emit original HTML SHA-256, byte count and typed official product/360-tile
  scope only — do not persist source HTML bytes or any source raster data;
- explicitly report **0 authorised source asset requests**, **0 TIFF downloads**,
  **0 verified corrected Occurrence pixels** and **no CAT model approval**.

The same research PR is covered by synthetic offline regression tests before
the bounded original HTML read in the branch-scoped GitHub CI. This is
**research publisher documentation evidence**, not a direct GeoTIFF source
response or a host permissions upgrade.

## Next source asset acceptance contract (not executed)

Review exactly one candidate v1.5 Occurrence tile for a 10° region:
\`https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif\`

If an approved public anonymous one-off method with an exact byte cap is
confirmed, require a source-identity/authentication gate:
1. Exact fixed endpoint and product/vintage, request cap and a single
   permitted GET (or a reviewed byte-range request if the service supports it)
   with no automatic retries, redirects or crawler defaults
2. Original response code and full original body SHA256/byte length, **or**
   precisely identified *prefix* SHA256/byte count for an approved
   \`bytes=0-4095\` Range request; a prefix digest is never a whole-file digest
3. Native TIFF/BigTIFF first-IFD parsing from at most 4,096 bytes with
   independently checked CRS, geotransform, width/height, data type, NoData,
   valid original geolocation and native value semantics as separately
   authorized; **do not** confuse RGB WMTS with numeric GeoTIFF
4. Independent proof the observed original asset contains the
   **2026-11-10 corrected Occurrence** release, not merely an unchanged
   \`_v1_5_2024.tif\` filename, an old cached Google-object copy or a
   historically corrected-but-unversioned claim
5. Scientific validation: Occurrence 0..100 is the fraction of valid
   Landsat observations with detected water; 255 is NoData. It is **not**
   flood AEP, depth, hazard frequency, insured TIV or calibrated loss.
   Retain 2022 Landsat Collection 1/2 geolocation seam warnings and the
   separate unresolved monthly-recurrence issue

Previous original JRC public publisher HTML source SHA and active JS
download URL were confirmed in [GitHub Actions run 43606072894](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43606072894)
and append-only private Neon **sample #130**. That evidence correctly shows
three sequential publisher JS \`BASE_URL\` definitions: 2021 GCS,
**overwritten** 2024 Google GCS candidate, and **active CloudFerro**. Thus
an arbitrary Google v1.5 object is not interchangeable with the currently
corrected original publisher TIFF even if it returns HTTP 200.

None of these provenance, transport or research-science gates authorizes
unattended worldwide raster acquisition. All source and insurer model
admission flags remain false; the JRC provider source access contract stays
\`documented_only\`, \`probe_contract.mode=none\`.

## Bounded original TIFF HTTP Range acceptance gate (offline only)

The new pure function
\`scripts/preflight_jrc_gsw_v15_original_range_receipt_v0.py\`
implements a future **single fixed tile** transport check over externally
supplied original response headers and exactly **4,096 bytes**. It performs
**zero provider network requests** and cannot authorize the underlying
service account/anonymous access.

A future approved request for
\`occurrence_10E_50N_v1_5_2024.tif\` would have to return:

- exactly \`206 Partial Content\` rather than \`200 OK\` (which would
  indicate the server ignored the Range header and may transmit the entire
  enormous TIFF);
- \`Content-Range: bytes 0-4095/TOTAL\` with canonical bounded declared
  total size, exact \`Content-Length: 4096\`, \`Content-Encoding: identity\`;
- \`image/tiff\` or \`application/octet-stream\` content type, exact source
  URL and strict native TIFF/BigTIFF first IFD inspection;
- only the original **4-KiB prefix SHA256**, never a false whole-file
  SHA256, whole-file checksum claim, NoData/CRS validation or assumed
  post-2026-11-10 corrected source identity.

Synthetic regression tests in
\`tests/test_preflight_jrc_gsw_v15_original_range_receipt_v0.py\`
cover a correct TIFF prefix, unhonored Range/HTTP200, compression,
invalid media types, wrong source URLs/versions, malformed TIFFs, missing
or inconsistent Content-Range/Content-Length, conflicting headers and
claims of scientific model approval. No original provider request or
pixel extraction is performed.

**The original source access contract still allows zero CloudFerro
or Google data asset HTTP requests.** This code prepares a later
reviewed single-request proof and prevents accidental bulk transfer,
not a new host permission.
