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
- nondeterministic manifest identity.

## Evolution rule

A convenience feature must not weaken provenance, privacy, licence review, or fail-closed publication. If automation cannot establish rights confidently, it must preserve the unresolved state for human review rather than infer permission.
