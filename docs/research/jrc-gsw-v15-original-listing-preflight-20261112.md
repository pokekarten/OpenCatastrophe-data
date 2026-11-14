<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# JRC Global Surface Water v1.5 — original file-listing preflight (2026-11-12)

**Source ID:** `ec-jrc.global-surface-water.1984-2024` (existing non-admitted landscape candidate). **Result:** the [original JRC product page](https://global-surface-water.appspot.com/download) exposes a [version 1.5 provider-hosted file listing](https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/), and the current public text listing contains the exact 10°×10° asset path:

`download2024/Aggregated/VER1-5/occurrence/occurrence_10E_50N_v1_5_2024.tif`

This is a **provider catalogue observation**, not a successful TIFF asset download, a full-file SHA-256 receipt, a usable pixel sample, or model admission. The source is *not* marked ready for CAT loss calculation. The exact listing byte stream has not been independently acquired and SHA-pinned in this change.

The original provider product page states that data may be used freely under the Copernicus framework with attribution `Source: EC JRC/Google`, and requires citing the dataset and publication. A source-use allowance does not replace exact-asset review, provenance, API/service terms or independent scientific checks. The original page also records an **occurrence >100% correction on 2026-11-10** for v1.5 and a **still unresolved monthly-recurrence sparse-observation defect**. Do not use old cached occurrence images/GeoTIFFs or treat recurrence as validated. v1.4 is deprecated.

## Repeatable next gate

After a separately authorised, bounded download of the **plain UTF-8 original listing** outside Git, run:

```bash
python scripts/preflight_jrc_gsw_v15_listing_v0.py --original-listing-file /path/to/original-provider-listing.txt
python -m unittest tests.test_preflight_jrc_gsw_v15_listing_v0 -v
```

The checker fails on absent/duplicate exact asset paths, v1.4-only lists, HTML/errors instead of a source index, and unsafe oversized/non-UTF-8 responses. It emits the listing's SHA-256 (only after local original bytes exist), the exact selected path and **negative** asset-byte/pixel/model flags. It neither contacts the provider nor emits/persists TIFF bytes.

**Next:** independently confirm the selected TIFF access, content length, current corrected-version identity, original byte SHA-256 and bounded native pixel semantics; run a scientific water-occurrence check with explicitly selected holdout before any model-input admission. Keep source-download bytes outside Git and private research staging within reviewed scope.
