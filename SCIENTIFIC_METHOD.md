<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Scientific data method and validation

OpenCatastrophe-data exists to make the evidential basis of catastrophe-risk research traceable and reproducible without turning Git into an uncontrolled data store. Software correctness, data rights, provenance quality, and scientific fitness are separate questions and must be evaluated separately.

## Evidence classes

Keep these categories explicit in public Issues when enabled, Pull Requests, source reviews, and release evidence:

1. **Repository source** — current, pinned manifests, schemas, code, tests, or accepted decision records.
2. **Authoritative external evidence** — provider documentation, licence/terms, standards, peer-reviewed literature, or stable public metadata.
3. **Inference** — a conclusion derived from evidence but not stated directly by the source.
4. **Design proposal** — a possible future admission, transformation, schema, or scientific use that is not yet accepted repository behaviour.

Do not promote an inference or design proposal into an admission decision merely because it is convenient.

## Source hierarchy

Prefer evidence in this order where applicable:

1. authoritative provider/product documentation and machine-readable metadata;
2. authoritative licence/terms and versioned release records;
3. peer-reviewed or standards documentation describing scientific meaning;
4. independently maintained secondary catalogues or software documentation;
5. community discussions only as discovery or supplementary context.

When authoritative sources conflict or are stale, mark the decision blocked or unresolved rather than selecting the most permissive interpretation.

## Reproducible data identity

For every scientifically material external asset used by a reproducible workflow, record as applicable:

- provider and product identity;
- exact version/release/query/time window;
- retrieval timestamp with timezone;
- exact byte size and SHA-256 for acquired bytes;
- licence/terms identity and review date;
- access and redistribution scope;
- transformation code/configuration identity;
- lineage to all material upstream inputs;
- spatial, temporal, coordinate/reference-system, variable, unit, and quality semantics.

A mutable URL or directory listing is discovery evidence, not a durable byte identity.

## Scientific validation of sources and transformations

Before an external source is used to support a scientific claim:

- define the intended scientific role of the source;
- verify parameter definitions, units, timestamps, coordinate/reference systems, missing-value conventions, aggregation windows, quality flags, and relevant instrument/model semantics;
- distinguish observation, analysis, reanalysis, forecast, derived product, and model output accurately;
- predefine validation windows or acceptance criteria before inspecting target values where practical;
- preserve source uncertainty, known biases, coverage limitations, and transformations;
- do not generalize a bounded source review to unsupported regions, periods, variables, or perils.

A successful schema/admission check establishes repository eligibility, not scientific validity for every downstream use.

## Transformation validation

A transformation that changes scientific meaning should have:

- an explicit input/output contract;
- deterministic configuration where possible;
- tests using independently synthetic fixtures;
- conservation/reconciliation checks where scientifically meaningful;
- explicit handling of missingness, filtering, interpolation, resampling, clipping, aggregation, and coordinate transformation;
- a versioned provenance record sufficient to reproduce the result.

Derived data do not automatically inherit unrestricted redistribution rights from their technical transformation.

## Model development and split integrity

OpenCatastrophe intends to use admitted data to build and evaluate its own models. Data provenance must therefore preserve experimental role as well as source identity.

For a scientific/model run:

- assign every materially used data input an explicit role such as `training`, `calibration`, `validation`, `holdout`, `benchmark`, or `context` before target inspection where practical;
- bind actual data bytes to an admitted manifest plus an exact SHA-256; a landscape candidate is discovery metadata and is never a model-input allow-list;
- do not represent the same exact content hash under multiple input identities or experimental roles in one run;
- keep training/calibration decisions separate from holdout evaluation; once a holdout result is used to choose features, parameters, thresholds, models, stopping rules, or other modelling decisions, that dataset is no longer an untouched holdout for the resulting model and a new independent holdout is required for a fresh holdout claim;
- predefine split/selection logic and preserve it as code/configuration or run evidence rather than reconstructing the split from memory after results are known;
- record claim scope and claim-specific limitations so evidence for one peril, geography, period, variable, or model context cannot silently become a broader claim;
- preserve exact input, output, validation and repository evidence references so a model result can be traced without hidden chat or local state.

`schemas/run-evidence-v2.schema.json` and `scripts/validate_agent_artifact.py` make these boundaries machine-checkable for new scientific/model runs. The older v1 receipt remains a compatibility profile for existing/simple execution evidence; it must not be used to imply v2-style split-integrity guarantees that it does not record.

These controls reduce accidental train/evaluation leakage, but a valid receipt is not by itself proof that a split is statistically independent, scientifically representative, legally usable, or sufficient for production modelling. Those remain explicit scientific and rights questions.

## Open standards and interoperability

OpenCatastrophe-data should evaluate established open catastrophe-modelling standards before defining project-specific exchange formats. Oasis Open Data Standards, including OED for exposure inputs and ORD for results, are important interoperability references. Compatibility should be implemented through explicit adapters and versioned mappings rather than silently changing internal scientific semantics.

Where a source or transformation is peril-specific, relevant open scientific engines and standards may be used as independent references or benchmarks. They are not hidden authorities and do not override the repository's provenance, rights, or validation contracts.

## FAIR research practice

The project should move toward FAIR research-software/data practice through machine-readable citation metadata, persistent version/release identifiers, accessible public metadata, interoperable schemas, reusable licensing information, exact provenance, and reproducible transformations. Software citation does not replace dataset citation: every external dataset retains its own authoritative attribution and citation requirements.

## Scientific change requirements

A new source, transformation, scientific interpretation, or interoperability mapping should state:

- the scientific question/use case;
- evidence classes and authoritative references;
- exact source/version/query identity;
- rights/admission state separately from scientific fitness;
- relevant units, coordinate/reference systems, time semantics, quality flags, and uncertainty;
- validation or benchmark plan and acceptance criteria;
- limitations and plausible alternative interpretations;
- whether any external bytes would enter Git and the exact permission supporting that scope.

Use the scientific/methodology Issue Form when Issues are enabled. When Issues are disabled, keep speculative candidate material out of the durable tree and open a bounded draft Pull Request only once enough authoritative public evidence exists for review.

## Current claim boundary

The repository is pre-alpha and admits external sources only within the scope recorded by each manifest. The canonical current source inventory is `docs/source-reviews/README.md` together with the machine-readable manifests in `manifests/`.

Repository checks demonstrate consistency with the current admission, provenance and public-metadata gates; they do not establish that any source is scientifically sufficient for every catastrophe-risk use case or authorize broader redistribution than the exact recorded scope. No external dataset byte becomes an OpenCatastrophe artifact merely because its metadata is admitted.
