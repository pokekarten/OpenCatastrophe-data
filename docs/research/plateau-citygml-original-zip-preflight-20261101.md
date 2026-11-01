<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# PLATEAU original CityGML ZIP: offline byte/structure preflight (2026-11-01)

## Verified provider context

Japan MLIT's PLATEAU site policy, https://www.mlit.go.jp/plateau/site-policy/ (section 3), expressly covers PLATEAU open 3D city-model data published at G-Spatial Center. It identifies local authorities as the copyright holders, generally applies the Public Data Use Terms 1.0 where no specific rights note overrides them, permits use under CC BY-compatible terms, and requires source attribution and notice of modification. The official FAQ https://www.mlit.go.jp/plateau/faq/ expressly indicates commercial PLATEAU model use is generally permitted without prior paperwork. **These are provider-level rights, not an individual 13104/Shinjuku 2024 asset admission.** Site policy notes potentially relevant public-survey / Survey Act conditions and exceptions. Exact municipal release, local attribution, individual data terms, privacy status and release-specific rights still require review before raw/derived publication.

MLIT's published CityGML ZIP structure convention provides a root folder containing `udx/bldg/*.gml` (building tiles), plus `codelists`, `metadata`, `specification` etc. The regional naming, original acquisition year, height/LoD properties and mesh coverage are NOT certified by this path convention alone. See https://www.mlit.go.jp/plateau/learning/tpc03-1/ and https://www.mlit.go.jp/plateaudocument01-04/3.html .

## Offline executable receipt step

```bash
python research_runners/plateau_citygml_original_zip_inventory_v0.py \
    --input /secure/local/previously-acquired-original.zip \
    --expected-byte-count 123456789 \
    --expected-sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

The numeric size/digest above are **synthetic examples only**, not an assertion about a real source. Both expectations are optional; when supplied they are matched against the exact local file bytes. An SHA-256 match is only as trustworthy as the separately obtained expected digest; it **does not** authenticate a provider, municipality or licence.

The runner makes **no network requests** and never extracts, decompresses or publishes ZIP contents. It reads only a local regular file, rejects final-component symlinks/FIFOs, hashes the same open file descriptor it inventories, verifies unchanged inode/size/mtime/ctime across the operation, and fails on an archive exceeding a 16-GiB local byte budget or 100,000 ZIP entries. For each entry, it rejects traversal, absolute/drive/backslash paths, duplicates (including case-fold collisions), encrypted files, UNIX symlinks/special entries, unsupported compression, excessive declared decompressed size or a high declared compression ratio. It requires at least one `udx/bldg/*.gml` entry using the official ZIP directory convention. All tests use **independently generated synthetic ZIP bytes**.

A positive receipt contains only observed local byte size, SHA-256, safe archive member counts and declared uncompressed-size totals; never original file paths or per-building content. The tool does **not** validate any member CRC, decompress/check GML/XML, detect all ZIP polyglots, prove a whole-area inventory, georeference buildings, verify observed/declared LoD, resolve the archive's native municipality/year, or make a legal source-admission decision. It always reports these limitations as false flags.

ZIP metadata validation is only a **pre-extraction and pre-processing gate**, not a security guarantee that arbitrary later extraction is safe. Any future extraction must enforce its own byte, path, parser, filesystem and entity-expansion limits. This code is unsuitable for committing third-party ZIPs or promoting a source to a verified CAT input by itself.

## Separate next-step admission requirements

1. Identify an exact municipal release / original CMS or G-Spatial archive and freeze its immutable version and the two API catalogue response hashes.
2. Review *that release's* authoritative rights/attribution and any survey law constraints in the source manifest (do not confuse PLATEAU open licence with experimental API-service permission).
3. Acquire that original ZIP lawfully **outside Git**; record UTC receipt, access path, exact bytes, SHA-256 and safe external storage identity, without signed URLs or secrets in Git.
4. Run this offline ZIP preflight, then separately CRC-check/extract bounded approved files and validate actual CityGML IDs, CRS, vertical datum, geometry topology and building-layer attribute missingness. Do not infer insured properties from municipal building polygons alone.
5. Admit derived assets only within the separately reviewed licence, privacy, provenance, scientific and repository publication scope.

No source original was downloaded or admitted as part of this change.
