<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source reviews

This directory contains **accepted, durable source-specific review evidence** that supports committed manifests/admissions.

Broad source discovery is maintained separately in `landscape/`. A landscape entry is explicitly non-admission evidence: it may preserve a useful provider/product pointer before OpenCatastrophe has a current model role, completed rights review or completed scientific review. Detailed speculative plans and unresolved research discussion still belong in GitHub Issues when enabled or in bounded PR discussion when Issues are unavailable.

## Canonical facts and narrative evidence

Source reviews are human-authored narrative evidence: rationale, rights interpretation, scientific semantics, limitations and references belong here. `manifests/*.json` remains authoritative for the overlapping structured admission facts and machine contract. A source review may explain a manifest but cannot silently broaden or override its machine-readable scope.

Every admitted manifest must be referenced by exactly one canonical source review, and `tests/test_contract_consistency.py` also requires this README to list the complete current set of source-review files. Do not add a second independently maintained machine copy of source-review facts merely for convenience; any future machine projection of narrative metadata must declare its canonical source and have an explicit drift check.

## Admission trigger

The accepted registry remains **capability-driven, not a source landscape**. A scientifically strong, well-licensed or generally useful dataset is not admitted merely because it exists or appears in `landscape/`.

Add a durable source review and manifest only when the source has a named current role that existing accepted sources cannot provide, such as a required model-consumer component, a bounded interoperability dependency, or a predeclared scientific validation input with explicit comparison semantics. Keep each admission PR to one coherent source family/use case. Candidate benchmarks, baseline geography and possible future validation counterparts may remain discoverable in `landscape/` until that concrete role exists without being presented as accepted capability.

Current accepted reviews:

- `dwd-extreme-wind-v24.03.md` — supports the metadata-only DWD extreme-wind admission.
- `copernicus-c3s-european-windstorm-reanalysis-v1.0.md` — supports the metadata-only C3S Enhanced Windstorm Service admission.
- `efehr-esrm20-european-exposure-model-v1.0.md` — supports the metadata-only EFEHR ESRM20 European Exposure Model admission.
- `efehr-eshm20.md` — supports the metadata-only EFEHR ESHM20 earthquake-hazard admission.
- `efehr-esrm20-vulnerability-v1.1.md` — supports the metadata-only EFEHR ESRM20 European Building Vulnerability Database v1.1 admission.
- `microsoft-globalml-building-footprints.md` — supports the metadata-only Microsoft Global ML Building Footprints exposure-geometry admission.
- `copernicus-cems-glofas-historical.md` — supports the metadata-only CEMS GloFAS historical hydrology admission.
- `copernicus-cems-on-demand-mapping.md` — supports the metadata-only CEMS On-Demand Mapping admission as provider-derived post-event geospatial evidence for validation/model challenge, with API/service automation remaining documentation-only until separately cleared.
- `wsv-pegelonline-elbe-dresden-discharge-2020-2023.md` — supports a metadata-only PEGELONLINE Dresden `Q` observation slice with a predeclared 2020–2023 temporal holdout comparison against GloFAS v4.0.
- `storm-ibtracs-present-climate-v4.md` — supports the metadata-only STORM v4 synthetic tropical-cyclone event-catalogue admission.
- `eiopa-catastrophe-data-hub-2023.md` — supports separate metadata-only EIOPA insured-exposure and historical incurred-loss admissions; raw/derived workbook redistribution remains blocked pending exact-file rights review.
- `google-open-buildings-v3.md` — supports the metadata-only Google Open Buildings v3 exposure-geometry admission under the selected CC BY 4.0 reuse path.

A source review never broadens the machine-readable manifest scope by itself.