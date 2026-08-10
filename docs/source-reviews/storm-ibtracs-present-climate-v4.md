<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source review: STORM IBTrACS present-climate synthetic tropical cyclone tracks v4

- Review date: **2026-08-10**
- Admission state: **metadata only**
- Manifest: `manifests/storm.ibtracs.present-climate.v4.json`
- Publisher: 4TU.ResearchData / 4TU.Centre for Research Data
- Product: STORM IBTrACS present climate synthetic tropical cyclone tracks
- Version: `v4`
- DOI: `10.4121/12706085.v4`

## Why this source is useful

STORM v4 provides a public synthetic tropical-cyclone event catalogue representing 10,000 years of present-climate activity. It extends the public foundation beyond European winter windstorm and earthquake sources while testing an important boundary: a stochastic track catalogue is not automatically a spatial wind footprint, vulnerability model, loss model, or future-climate projection.

## Version identity

This review is pinned to DOI `10.4121/12706085.v4`.

The public version record documents corrections across earlier releases, including cyclone-category calculations and duplicate tracks. Version 4 is therefore treated as scientifically distinct from older releases rather than as an interchangeable alias.

A versioned DOI still does not provide byte identity. Any later raw admission must select exact v4 files, acquire them outside Git, and record independent byte size and SHA-256.

## Rights assessment

The public institutional record for version 4 identifies the dataset licence as **Creative Commons Zero v1.0 Universal (CC0-1.0)**.

Engineering interpretation:

- licence identity: `CC0-1.0`;
- commercial use: allowed;
- redistribution/adaptation: allowed;
- repository review scope: metadata only.

Scientific citation remains required by project practice even where the dataset licence does not impose a CC-BY-style attribution condition.

## Scientific semantics

### Synthetic is not observed

STORM tracks are statistically generated and must not be labelled as historical observed storms. The associated peer-reviewed publication describes a synthetic global tropical-cyclone dataset built from historical IBTrACS information.

### Present climate is not future climate

The publication states that the presented STORM dataset represents present-climate conditions and statistically resamples its historical input climate. It is not, by itself, a dataset for estimating long-term climate-change impacts.

### Tracks are not hazard footprints

Track, intensity, and size information can support tropical-cyclone hazard research, but a complete wind, surge, or wave footprint requires an independently identified transformation/model with its own parameters, inputs, grid, and validation evidence.

### Synthetic-year identity must be preserved

The 10,000-year catalogue can support rare-event analysis, but its synthetic year numbers are model output rather than calendar projections. They must not be coupled to unrelated peril catalogues merely because both contain integer year identifiers.

## Suitable initial uses

Good initial uses include tropical-cyclone event-catalogue research, event/year identity tests, basin/frequency validation, comparison with independent track generators, and input to separately reviewed hazard transformations.

It is not sufficient by itself for observed-event truth, future-climate risk, building-level wind footprints, vulnerability, insured loss, or cross-peril annual dependence.

## Requirements before raw admission

Before STORM v4 bytes can move beyond metadata-only status, a proposal must:

1. re-check the versioned DOI and v4 licence record;
2. select exact v4 files and preserve their names/structure;
3. acquire them outside Git;
4. record independent byte size and SHA-256;
5. document exact fields, units, basin/event/year identifiers and missing-value conventions from v4;
6. preserve the release/correction identity;
7. keep track-to-footprint or climate adjustments as separate transformations; and
8. obtain explicit asset-specific publication review.

Until then, no raw or derived STORM bytes belong in this repository.

## Authoritative public references

- Versioned dataset DOI: `https://doi.org/10.4121/12706085.v4`
- VU public v4 dataset record: `https://research.vu.nl/en/datasets/storm-ibtracs-present-climate-synthetic-tropical-cyclone-tracks-6/`
- Scientific publication: `https://doi.org/10.1038/s41597-020-0381-2`
