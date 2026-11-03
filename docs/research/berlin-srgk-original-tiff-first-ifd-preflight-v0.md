<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin detailed Starkregen: original GeoTIFF first-IFD metadata probe

**Research only.** No full ZIP/TIFF retrieval, raster cell interpretations,
building loss, policy exposure, source redistribution or CAT model input approval.

## Why an extra gate

The reviewed
[official source central-directory run 41414798836](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41414798836)
established exactly one `.tif` member for each official scenario ZIP:

| Source scenario | Verified member name | Original compressed / uncompressed bytes | Central SHA-256 |
| --- | --- | --- | --- |
| Rare | `wasserstand_T50_1.tif` | 132689170 / 167298853 | `9a593d9d3e39c21ee99c34d13550c16ae9c0d8c3390c653dfb566f49f00be7b3` |
| Extraordinary | `wasserstand_T100.tif` | 136928037 / 171875427 | `95083ca9e30236032ec995571d9436be82030f827c0de0fbbbaf91d80974b01b` |
| Extreme | `Wasserstand_TExtrem_1.tif` | 93562450 / 115931327 | `cae92cb9db21fef568eb5f66ca5c5a034ffa6c1190a95747eba7098fe09fbe71` |

Original archive sizes pinned by previous official HEADs are
132689382, 136928247 and 93562670 bytes, respectively. Archive
and member compressed sizes are different.

## Next bounded source step

`research_runners/berlin_srgk_original_tiff_header_prefix_v0.py`
first repeats the **official ZIP 206-only EOCD and central directory**
source gate, requires exact original full central SHA-256 and unique
original TIFF member identity, and then performs exactly three
additional fixed-source Range GETs per scenario:

1. 30-byte **ZIP local-file header**; validate DEFLATE method,
   filename/extra lengths, flags and header CRC/length where available.
2. At most **4,096 bytes** of local name/extra, checking the name
   exactly matches the central index.
3. At most **65,536 compressed bytes** from the start of the known
   DEFLATE member. Inflate at most **131,072 bytes in memory**, only
   to examine TIFF byte order, classic TIFF signature and available
   first-image-file-directory (IFD) metadata tags.

Never perform ZIP fallback `GET` without Range. A server returning
HTTP 200 instead of exact HTTP 206 is rejected **before reading
source response body**; an incorrect Content-Range, changed size,
non-identity encoding, ZIP64, encryption, changed CD digest or
metadata layout blocks. No original TIFF bytes are retained, printed
or imported into Neon. A bounded decompressed prefix may contain
arbitrary source TIFF bytes, but *no raster pixel is interpreted*
or exported. The memory cap is hard.

**Interpretation is deliberately narrower than a flood-depth claim:**
classic TIFF magic, horizontal dimensions and presence of standard
GeoTIFF/NoData tags are header facts; they are **not** proof of
EPSG code, raster bounds, actual depth units or scale, NoData
semantics, site raster coverage, return-period calibration or an
insured loss. The parser records the absence or truncation of a
complete first IFD rather than inventing missing values.

The official second model area
EPSG:25833 `[391860,5816840,392060,5817040]` is independently
verified as a study polygon but **has not yet been joined to a
particular TIFF's actual georeferenced pixels**. The source also
explicitly warns that extreme depth data are not available for
all study regions. Scenario names `T50` and `T100` do not by
themselves authorize annual frequency assumptions.

**Rights:** Berlin detailed SRGK Atom catalogue carries area-specific
CC BY 4.0 attribution for Moabit and Flughafensee alongside German
Data Licence Zero 2.0; a source ZIP may span regions, so do not
flatten rights into an unconditional redistribution approval.

This is distinct from the nationwide BKG KOSTRA Int16 depth
encoding blocker [#1086](https://github.com/pokekarten/OpenCatastrophe-data/issues/1086).
Even a fully parsed separate Berlin TIFF header does not resolve
the BKG source scale or source-area scientific comparability.

## Checks

Synthetic tests cover valid TIFF IFD data, endian/inline width/height,
IFD omission/truncation, changed source central SHA, bad local
header, malformed compressed DEFLATE stream, unsupported BigTIFF
and untrusted ZIP/HTTP Range responses. Original source requests
only run after a dedicated reviewed workflow merge into `main`.
Any source drift keeps the safety and insurance admission gates closed.
