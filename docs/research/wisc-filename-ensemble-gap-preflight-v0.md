<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WISC filename, ensemble window and duplicate-view preflight v0

**Research-only, 2026-11-05.** This tool does not download or
admit any original Copernicus WISC files, create an occurrence-rate model,
estimate catastrophe losses or assert any annual EP probability.

## Why the identity gate is needed

The [original Copernicus WISC Synthetic Event Set Product User Guide](https://confluence.ecmwf.int/plugins/viewsource/viewpagesrc.action?pageId=255094970),
last modified **2 July 2026**, contains two details that require
fail-closed interpretation:

1. Its prose describing the NetCDF filename says the time is
   `%Y%m%d%H` (10 digits), but its actual published **Table 4**
   footprint identifiers are *12 digits* including minutes, e.g.
   `fp_ga3ups_199311201800_1708_002`. The already merged single
   tile reader expects 12 digits, which matches the published example
   rather than the conflicting prose. This preflight **accepts only a
   12-digit source filename** with the documented `_v1.nc` suffix;
   it does not reclassify 10-digit stems or fabricated variants as
   externally verified assets.
2. The guide describes a two-digit method plus final one-digit
   ensemble in the suffix and lists three recalibration sets
   (1.2, 2.0, 3.0). However its published example filenames
   contain three-digit codes such as `002`, `003`, `004`
   and `005`, whose first two digits are `00`, **not**
   `12`, `20` or `30`. We treat `00` as an unresolved legacy
   method code. Candidate method codes `12`, `20`, `30`
   are provisionally mapped to their nominal variants only, not
   authenticated against an original dataset or physical event.

Published climate-ensemble gaps, **not zero-storm years**:

| Ensemble | First unavailable month | Last unavailable month |
| --- | --- | --- |
| 4 | October 1988 | November 1998 |
| 3 | December 1988 | March 1990 |
| 4 | October 2002 | November 2002 |
| 5 | December 2008 | February 2010 |

The date and gap table applies only to the model's **simulated**
September-to-May winter-season years (1986–2011), not observational
storms that actually hit a specific country in those dates. The
Met Office guide says the model is no longer supported and may be
withdrawn from CDS. Physical loss calibration should use independently
validated historical series instead of assigning actual insured
losses to these simulated dates.

## What is executable

[`research_runners/wisc_filename_ensemble_preflight_v0.py`](../../research_runners/wisc_filename_ensemble_preflight_v0.py)
reads **only a locally supplied, bounded JSON source-inventory** with
full-original-asset SHA-256 **claims**, not the actual NetCDF content.
The entire JSON must also match a caller-specified SHA-256. All
original file hash claims remain **unverified against source bytes**.

Exact input (this is a deliberately fictional example; these are
**not** real downloaded files):

```json
{
  "schema_version": "wisc-filename-catalogue-v0",
  "source_dataset_id": "copernicus.c3s.wisc.synthetic-windstorms.22980",
  "records": [
    {
      "filename": "fp_ga3ups_199311201800_1708_002_v1.nc",
      "original_file_sha256_claim": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ]
}
```

The example's *stem* appears in the original Table 4; the
`_v1.nc` extension is appended per the documented naming convention.
The all-`a` checksum is fictional, not an original-file receipt.
This is a **metadata parsing** demonstration only.

Reproduce after placing an explicit JSON inventory in an external
working directory:

```sh
sha256sum /external/catalogue/wisc-filenames.json
python research_runners/wisc_filename_ensemble_preflight_v0.py \
  /external/catalogue/wisc-filenames.json \
  --manifest-sha256 '<exact verified inventory SHA-256>'
```

Successful parsing reports modelled calendar years, counts by two-digit
method code, candidate repeated **source-track** keys between different
recalibration methods, and the exact published unavailable ensemble
periods. Two methods with the same simulated timestamp, track ID and
ensemble number are flagged as **alternative footprint-view
candidates**, not proven independent physical events. This does
not prove that the event dates and member codes uniquely identify an
original physical storm; confirmation requires original NetCDF
attributes and publisher eventset summary metadata.

A file manifest alone cannot tell us which of the 1986–2011
source periods were genuinely observed, or which winter months
contained no storm. This gate never creates `occurrence.csv`,
`periods.csv`, `returnperiods.csv`, 1-in-N-year curves, zero loss
years, damage curves or simulated insurer payouts.

The JSON report intentionally says:
`complete_source_event_catalogue_verified=false`,
`complete_ensemble_months_or_zero_event_years_verified=false`,
`return_period_weights_verified=false`, and
`annual_oep_aep_authorized=false`.

## Tests and model integration

Run the deterministic offline tests with no third-party data or
scientific dependencies:

```sh
python -m unittest discover -s tests \
  -p 'test_wisc_filename_ensemble_preflight_v0.py' -v
```

The tests include the published Table 4 stem, conflicting 10-digit
prose, four prohibited ensemble-window ranges and their allowed
boundaries, malformed source/date/hash/JSON records, duplicates
and alternatives of the same simulated track. They never turn
positive syntax checks into source scientific approval.

This gate complements (but does not change) the independently merged
[WISC NetCDF-4 → native Oasis footprint tile PR #1388](https://github.com/pokekarten/OpenCatastrophe-data/pull/1388)
and [original WISC acquisition issue #1391](https://github.com/pokekarten/OpenCatastrophe-data/issues/1391).
Its post-acquisition role is to preserve original and simulated
storm identities while sourcing and calibrating independent
wind-vulnerability and real building locations. No unreviewed
source bytes, provider secrets or real carrier data are committed.

**Outstanding:** source account/licence-compliant download;
real NetCDF variable and attributes; exact model-set/code mapping;
`eventset_summary.csv` from original provider; complete observed
simulated-year universe; disjoint stochastic calibration/validation;
physical storm-year clustering; geographic coverage and missing-data
meaning; source-licensed vulnerability/OED terms and actual native
annual GUL/IL/RI/OEP/AEP tests.
