<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NOAA IBTrACS v04r01 observed ALL CSV: independent offline source replay

**Research-only; no admission, rights upgrade or provider request in this change.**

## Why this exact file

Existing [executed source findings](executed-source-findings-20261103.md) record a complete **original NOAA ALL CSV** snapshot acquired on **2026-11-02**, independently of the existing [NetCDF-only documented access contract](../../access/noaa.ncei.ibtracs.v04r01.json):

- File: `ibtracs.ALL.list.v04r01.csv`, 333,183,438 original bytes
- Independent source receipt SHA-256: `7a11978ceba2953754b75bcc99bf1cfc8f00046aa5054054573edc904240d820`
- Original audited findings: 730,416 data rows, 174 columns, 13,631 distinct SID values and 10,658 native longitude values above +180°.
- Original product page: https://www.ncei.noaa.gov/products/international-best-track-archive
- Exact public distribution URL: https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.ALL.list.v04r01.csv

This is the **observed** NOAA IBTrACS historical catalogue, not the separate synthetic STORM v4 admission or a complete physical windfield. The fixed source is historical and may differ from the current provider's rolling revision. The repository's `access/noaa.ncei.ibtracs.v04r01.json` authorizes no execution and references a *different NetCDF distribution*. It must not be reused as a CSV service grant.

NOAA's [v04r01 technical documentation](https://www.ncei.noaa.gov/sites/default/files/2025-04/IBTrACS_version4r01_Technical_Details.pdf) specifies a two-row CSV header (names and units), source-agency differences and provisional/spur track distinctions. This audit checks **only** source identity, data shape, count and coordinate validity; it does not harmonize 1-minute vs 10-minute wind, interpret landfall, select scientific track types or equate positions with insured losses.

## Offline execution

After a separately authorised copy of **the already frozen exact CSV bytes** has been made available outside Git:

```bash
python research_runners/noaa_ibtracs_v04r01_csv_source_audit_v0.py \
    --original-csv /private/original/ibtracs.ALL.list.v04r01.csv
python -m unittest tests.test_noaa_ibtracs_v04r01_csv_source_audit_v0 -v
```

The runner streams SHA-256 calculation without keeping the 333 MB file in memory, rejects any wrong byte count or digest, then parses all CSV rows with original units row and per-row validation. It emits **only aggregated provenance/shape evidence**, with `source_admitted=false` and `model_input_approved=false`. Local input bytes, source rows, storm identifiers and track coordinates are never emitted or committed. This change includes synthetic negative tests; **no new original asset was reacquired or run through the full checker in this contribution**.

## Remaining independent gates

1. Exact current original-provider CSV service/automation terms and multi-agency redistribution/commercial-use rights (still *unresolved*, no implied NOAA public-domain blanket approval).
2. Full source replay on the already evidenced local original bytes, reviewing any scientific/format mismatch instead of weakening gates.
3. Storm-centre track type, multi-source wind averaging, intensity definitions, historical sampling uncertainty, landfall/footprint transformation, selected holdout, and external observation comparison.
4. Asset-specific rights and explicit source/model admission before any production or insurer simulation.

Nothing from this offline source QA may be relabelled as a calibrated tropical-cyclone hazard, insured loss, claim, TIV, return period or approved NextGen input.
