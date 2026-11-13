<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Census Grid 2021 V3: exact CSV ↔ GeoTIFF cell parity — offline gate

Date of contract review: 2026-11-13. Product is the [original Eurostat 2021 Census Grid, V3 dated 30 May 2026](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution/population-grids), **not GEOSTAT 2006/2011/2018**. Product-specific [Eurostat 2021 Census Grid rights](https://ec.europa.eu/eurostat/web/gisco/geodata/population-distribution): EU copyright / **CC BY 4.0** with attribution. CC BY 4.0 data rights alone do not override the *separate* repository provider acquisition contract.

## The specific outstanding scientific check

The existing private `insurance-risk-core` Neon research samples already have:

- **#63:** an original positive 1-km, 14-band Census 2021 V3 GeoTIFF pixel, verified by an exact 49,152-byte original HTTP Range SHA256 `80238bea7841928b220fbf61c980bafd61290f4bf2214a997686441593c09155`; native EPSG:3035 cell (row 100, column 4118); no CAT admission.
- **#65:** original 2021 GISCO one-cell ID `NO_CRS3035RES1000mN5399000E5018000`, official country and NUTS3 metadata.
- **#66:** independent official 1-km GeoJSON source polygon that agrees geometrically with the TIFF original cell, within ~0.000145 m boundary difference. This **does not independently remeasure any population**.

The remaining numeric check is **the identical cell** in **the original same-release V3 CSV**, compared against **all 14 32-bit TIFF bands**, preserving confidentiality `-8888` and missing `-9999`. The corresponding V3 CSV source row would have `GRD_ID=CRS3035RES1000mN5399000E5018000` and `CNTR_ID=NO`. Do not infer an official source row or successful equality before actually processing it.

## Source-asset identity frozen from original provider central directory (Neon #60)

| Exact ZIP member field | Expected original source value |
| --- | --- |
| Original ZIP URL | `https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip` |
| CSV member | `Eurostat_Census-GRID_2021_V3/ESTAT_Census_2021_V3.csv` |
| Local ZIP header start | `209230036` |
| Compression | raw ZIP DEFLATE (method 8), **not gzip** |
| Compressed member bytes | **49,110,575** |
| Uncompressed member bytes | **339,625,996** |
| Original central-directory CRC32 | `54cdc404` |

The exact 14-field source fingerprint is `206185ef8953f67e5c8516a8b9d95b2e66907b28b5e5f1a4d98836e913ac7ec8`, a SHA256 of comma-joined decimal values in the fixed band order `T,M,F,Y_LT15,Y_1564,Y_GE65,EMP,NAT,EU_OTH,OTH,SAME,CHG_IN,CHG_OUT,POPULATED`, **computed from private verified raster research sample #63 in Neon**. It is a reference digest, not redistributed raw provider cell bytes. The target ID and source locale are independently supported by #65/#66.

## Why not run the live 49-MB acquisition automatically?

The canonical current [`access/eurostat.gisco.census-population-grid.2021.json`](../../access/eurostat.gisco.census-population-grid.2021.json) expressly sets:

- `status=documented_only`, `probe_contract.mode=none`, `implementation_decision=document_only`.
- `operational_constraints.max_probe_bytes=65536`, `max_sample_bytes=52428800`.
- `api_terms_status=unknown` and `commercial_automation_status=unknown` with explicit notes that **no automated HEAD/GET/Range call** was authorized by that original contract.

The 49.1-MB compressed member falls below the numeric 52.4-MB sample ceiling, **but byte-size fit alone does not grant request permission**. Existing small original research byte-range observations do not retroactively upgrade that documented-only provider acquisition contract. Therefore this contribution does **not** insert a `push`, `schedule` or `workflow_dispatch` live network action, and **does not** claim source CSV value parity or a full original ZIP SHA256.

## Implemented offline reproducible preflight

[`research_runners/eurostat_census_v3_full_csv_member_parity_v0.py`](../../research_runners/eurostat_census_v3_full_csv_member_parity_v0.py) takes only a **locally pre-acquired, externally validated raw DEFLATE byte stream of this exact single CSV ZIP member**, and uses a standard-library streaming inflater. It holds at most one compressed block, bounded inflated output and one original CSV line at a time.

It independently checks total member compressed/uncompressed size, central-directory CRC32, complete DEFLATE EOF, column order, unique target grid/country, **all 14 original V3 population bands against the privately computed TIFF fingerprint**, and calculates SHA256 for both compressed and uncompressed exact CSV member. No rows, individual values or source payloads appear in its output; its receipt has `cat_model_input_approved=false`. A mismatch is a hard failure and never a partial admission.

```bash
python -m unittest tests.test_eurostat_census_v3_full_csv_member_parity_v0 -v
# Run only after the provider's exact-member acquisition has been separately
# authorized and its ZIP local-header/central-directory identity validated:
python -m research_runners.eurostat_census_v3_full_csv_member_parity_v0 \
  --raw-deflate-member /private/provider-verified/v3-csv-member.deflate
```

Only synthetic fixtures (not source values or bytes) occur in [`tests/test_eurostat_census_v3_full_csv_member_parity_v0.py`](../../tests/test_eurostat_census_v3_full_csv_member_parity_v0.py). The tests prove good synthetic matches, preserved missingness, CRC/length/deflate corruption, fingerprint mismatch, absent/duplicate/wrong-country target and bad schema fail closed. They **do not** prove the real 396-population TIFF cell equals the original V3 CSV cell. The production test has **not been executed** on original CSV bytes in this contribution.

## Next causal gate

Obtain provider-specific review/permission for a **single authenticated-or-anonymous, fully allowlisted, no-secret, bounded acquisition** of the exact *one* original ZIP CSV member: verify the original ZIP local header, exact archive version, original `Content-Range`, expected compressed member size, original central directory identity, no arbitrary redirects, and rate-limit policy before passing raw DEFLATE to this offline validator. Record **only hashes, checksum, row-count and parity Boolean** in private Neon. Keep full source bytes and personal/policy/claims data out of public Git. A completed one-cell CSV↔TIFF parity is still not whole-EU / insurer exposure approval.

### Streaming robustness added after first passing CI (13 November)

A previously untested **false rejection** was identified for a legitimate, very compressible Census CSV DEFLATE block: one bounded 65,536-byte compressed chunk can decode to more than 2 MiB. The validator now drains `zlib.decompressobj.unconsumed_tail` through repeated **2-MiB maximum output chunks**, while enforcing exact full-source uncompressed byte count, member CRC32, EOF, single-source-row limits and no-progress detection. It does **not** lift any source acquisition permissions or sample/production admission.

A new synthetic-only test contains **35,002 complete rows**, including exactly one matching target cell. The synthetic compressed fixture is under 65,536 bytes but the uncompressed source is over 2 MiB; the test exercises this bound and still checks that only one original target-row SHA fingerprint is used. The exact member length, CRC and ZIP local offset remain verified from the original provider central-directory metadata in private Neon **sample #60**.

After this change, full CI and Python 3.11–3.14 must pass again on the new commit; the earlier green run predates this change.
