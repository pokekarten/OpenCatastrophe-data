<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Architecture

OpenCatastrophe-data is a standalone public data registry, provenance, admission, and transformation project. It must remain understandable and auditable without access to any private repository, private service, or confidential dataset.

## Design goals

- metadata-first source admission;
- explicit source and rights provenance;
- fail-closed public redistribution;
- deterministic identities for admitted manifests and artifacts;
- separation of raw storage from Git history;
- reproducible transformation recipes;
- small, independently synthetic or explicitly redistributable fixtures;
- public interfaces suitable for automated model consumers;
- no hidden credentials or private endpoints.

## Trust boundary

```text
authoritative public source / terms
        -> candidate metadata
        -> rights + provenance review
        -> admitted manifest
        -> external raw storage (when acquisition is permitted)
        -> deterministic transformation
        -> derived artifact identity
        -> optional public fixture within approved scope
        -> public model-consumer contract
```

Source bytes and Git history are separate security domains. A source may be used in a controlled environment without being legally or operationally suitable for Git redistribution.

## Repository boundary

This repository may own:

- dataset admission metadata;
- source and licence/terms references;
- admission schemas and validators;
- retrieval/transformation source code;
- provenance and artifact hashes;
- small explicitly approved fixtures.

It does not serve as a general data lake and must not contain confidential/customer data, private credentials, unrestricted dumps of external data, or proprietary model assets.

## Admission objects

A dataset admission is a reviewable statement about one defined source/use, not a claim about an entire provider. Different products, versions, access mechanisms, regions, variables, or intended redistribution scopes may require separate admissions.

The admission model separates at least:

- source identity;
- access class;
- licence/terms evidence;
- commercial-use status;
- redistribution status and scope;
- attribution/derivative conditions;
- raw artifact identity when acquired;
- transformation identity;
- review status.

Unknown rights remain explicit and blocking.

## Raw storage

Large or restricted source bytes normally live outside Git. Storage references committed to this repository must be non-secret identifiers and must not reveal local absolute paths, credentials, signed URLs, or private hostnames.

A raw artifact identity should use content hashes and byte counts where available. Storage location is not identity.

## Transformations

Transformation code belongs in Git; large inputs/outputs do not. Transformations should be deterministic where scientifically appropriate and should record:

- input dataset/artifact identities;
- code version/identity;
- configuration identity;
- relevant environment/tool version when material;
- output hash and size;
- semantic changes such as clipping, reprojection, aggregation, imputation, or unit conversion.

Transformation never creates new redistribution rights by itself.

## Model-consumer boundary

A model consumer should depend on stable exported contracts and content identities, not repository-relative assumptions about local storage. Consumer code must not require access to restricted source bytes merely to import or test its core package.

The discovery landscape is never a model-input allow-list. Training, calibration, validation, benchmarking or holdout pipelines must bind every external data input to an admitted manifest and an exact version or content identity. Where the scientific result depends on an input's experimental role, that role and the split/selection protocol must be fixed in experiment or run evidence before target inspection. Admission for one bounded use does not silently authorize a different modelling role.

This separation is deliberate preparation for OpenCatastrophe-owned models: discovery can stay broad, while model inputs remain reproducible, rights-aware and resistant to accidental training/validation leakage.

## Public development plane

Public GitHub state is the development and coordination plane. Current `main`, Issues, Pull Requests, accepted source reviews and machine-readable contracts are sufficient to understand accepted work; hidden chats, private archives or private task trackers are not authority.

Human and AI contributors use the same review path. A draft PR is the visible implementation claim for shared/single-writer surfaces. Machine-readable agent-task and run-evidence artifacts are optional execution snapshots that improve coordination and reproducibility; they do not replace GitHub-native task state or human/scientific/data-rights review.

Root `AGENTS.md` and `.github/copilot-instructions.md` provide the intentionally small repository-wide agent surface. Durable behavior belongs in schemas, validators and tests rather than duplicated instruction layers. The repository must remain usable without a specific model provider, IDE, MCP host or paid AI service.

## Public projection model

OpenCatastrophe uses **one semantic truth, multiple verified views**. Repeating the same facts in two independently editable files is an architectural error because it creates unresolvable authority and drift questions for humans, agents and downstream tools.

Repository information therefore falls into three classes:

1. **Structured canonical facts.** Versioned JSON or another explicitly declared machine contract is authoritative. Human-readable or interoperability forms are deterministic projections and carry a generated-file marker. `landscape/sources*.json` is the first enforced example; paired `sources*.md` files are generated human views.
2. **Narrative evidence and reasoning.** Human-authored Markdown remains canonical when the content is explanation, scientific interpretation, limitations, rationale or review evidence that should not be reduced to a synthetic key/value mirror.
3. **Hybrid records.** A narrative document may refer to structured canonical facts, but overlapping facts retain one declared authority. Current source reviews are narrative evidence bound to machine-readable admissions in `manifests/`; a review cannot broaden the manifest scope by prose alone.

Generated projections obey these rules:

- the canonical source is named in the generated file;
- generation is deterministic, dependency-light and repository-owned;
- contributors change the canonical source and regenerate rather than editing the projection;
- CI runs the renderer in check mode and fails on missing, stale or orphaned generated files;
- CI never silently repairs or commits generated output;
- a new JSONL, CSV, YAML, HTML, STAC, RDLS, Oasis or other representation must state its canonical source and whether the projection is lossless or intentionally scoped;
- no projection changes data rights, scientific status, admission status or provenance by existing in another syntax.

For current landscape projections, use `python scripts/render_public_views.py --write` to regenerate and `python scripts/render_public_views.py --check` to verify parity. The central `python scripts/check_all.py` gate includes the parity check.

## Contract evolution

Public schemas and profile versions are durable interfaces. Do not silently reinterpret an existing `schema_version` or `profile_version`.

- backward-compatible clarifications may keep the same contract version only when accepted inputs and semantics are not narrowed or redefined;
- breaking semantic changes require a new version identity and an explicit compatibility/migration decision;
- schema, executable validator behavior, documentation and negative tests must evolve together;
- content identity and contract version are separate: changing JSON key order must not change deterministic manifest identity, while changing material content must;
- mutable labels such as `latest` are discovery conveniences, not durable scientific or execution identities.

A published JSON Schema is the portable structural interface for tools that understand JSON Schema. When a contract also has an executable repository validator, that validator is authoritative for documented policy, cross-record and security constraints that the structural schema cannot safely express. The schema must identify that boundary, consistency tests must bind the shared structural surface, and a schema-only pass must never be interpreted as admission, publication authorization or scientific fitness.

The repository is pre-alpha and does not yet promise a stable release line. Versioned contracts still exist so agents, scientists and downstream industry users can detect incompatible changes rather than relying on implicit behavior.

## Security model

The repository assumes eventual public disclosure of its full Git history. Prevention therefore happens before commit:

- quarantine external downloads outside Git;
- validate manifests strictly;
- scan tracked files for high-risk secrets/data;
- keep credentials in environment/secret stores only;
- never commit transient authenticated URLs;
- treat accidental sensitive commits as history contamination requiring incident response.

## Testing architecture

Unit tests use synthetic manifests and synthetic data only. Tests should include negative cases for:

- duplicate JSON keys;
- non-finite numbers;
- type confusion;
- unsafe/local/signed URLs;
- malformed timestamps and hashes;
- unknown or restricted rights;
- mismatch between redistribution scope and publication request;
- incomplete review identity;
- unsafe storage references;
- nondeterministic manifest identity;
- drift between canonical structured facts and committed generated views.

## Evolution rule

A convenience feature must not weaken provenance, privacy, licence review, or fail-closed publication. If automation cannot establish rights confidently, it must preserve the unresolved state for human review rather than infer permission.
